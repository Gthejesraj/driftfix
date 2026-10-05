"""driftfix: a dependency upgrade broke your tests, Claude fixes the code."""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

# Pinning back to the old version is not a fix. Adding a split-out package is fine.
MANIFESTS = {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "package.json"}
# The test suite runs the upgraded package's code; it shouldn't see our credentials.
SECRETS = {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"}
LOCKFILES = {"Pipfile.lock", "poetry.lock", "uv.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"}

PROMPT = """\
The dependency `{package}` was upgraded{versions}. The test suite now fails:

$ {test_command}
{output}

Fix this repository's code so it works with the new version of `{package}`.
- Read the package's changelog / migration guide for the relevant versions if you need to.
- Change application code. Change tests only where they use `{package}`'s API directly.
- Never pin, downgrade, or change the requirement for `{package}`, and never edit lock files.
- If the new version moved code into a separate package, you may add that package to the
  dependency manifest and install it into the current environment.
- Never delete or skip tests to make them pass.
- Run `{test_command}` to confirm the fix.
Your final message must be only a short markdown summary of what changed and why, for a PR description."""


@dataclass
class TestRun:
    passed: bool
    output: str


def run_tests(command: str, repo: Path, timeout: int) -> TestRun:
    try:
        proc = subprocess.run(
            command, shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout,
            env={k: v for k, v in os.environ.items() if k not in SECRETS},
        )
    except subprocess.TimeoutExpired:
        return TestRun(False, f"timed out after {timeout}s")
    lines = (proc.stdout + proc.stderr).splitlines()
    return TestRun(proc.returncode == 0, "\n".join(lines[-150:]))


def changed_files(repo: Path) -> list[str]:
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    return [line[3:].split(" -> ")[-1] for line in out.splitlines()]


def pins_package(repo: Path, path: str, package: str) -> bool:
    """Did this edit touch a lock file, or any requirement line naming the upgraded package?"""
    if Path(path).name in LOCKFILES:
        return True
    if Path(path).name not in MANIFESTS:
        return False
    diff = subprocess.run(
        ["git", "diff", "-U0", "--", path], cwd=repo, capture_output=True, text=True
    ).stdout
    lines = (
        [line[1:] for line in diff.splitlines() if line[:1] in "+-" and line[:3] not in ("+++", "---")]
        if diff else (repo / path).read_text().splitlines()  # new, untracked file
    )
    names = "|".join(re.sub(r"[-_.]", "[-_.]", n) for n in re.split(r"[,\s]+", package) if n)
    pattern = re.compile(rf"(?<![\w.-])({names})(?![\w.-])", re.IGNORECASE)
    return any(pattern.search(line) for line in lines)


def build_prompt(package: str, old: str | None, new: str | None, command: str, out: str) -> str:
    versions = f" from {old or '?'} to {new}" if new else (f" from {old}" if old else "")
    return PROMPT.format(
        package=package, versions=versions, test_command=command, output=out,
    )


async def run_agent(prompt: str, repo: Path, model: str, max_turns: int, budget: float) -> tuple[str, float]:
    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

    options = ClaudeAgentOptions(
        cwd=repo,
        model=model,
        allowed_tools=["Read", "Edit", "Write", "Glob", "Grep", "Bash", "WebFetch", "WebSearch"],
        permission_mode="bypassPermissions",  # headless; run in CI or a throwaway checkout
        max_turns=max_turns,
        max_budget_usd=budget,
        setting_sources=["project"],  # repo's CLAUDE.md, not the user's personal config
        skills=[],
    )
    summary, cost = "", 0.0
    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                summary, cost = message.result or "", message.total_cost_usd or 0.0
    except Exception as exc:  # e.g. budget reached; the cost was already reported above
        return f"Agent stopped: `{exc}`", cost
    return summary, cost


def fix(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    if changed_files(repo):
        print("Working tree is dirty. Commit or stash first so driftfix's edits are reviewable.")
        return 2
    before = run_tests(args.test, repo, args.timeout)
    if before.passed:
        print(f"Tests pass with {args.package} as installed. Nothing to fix.")
        return 0
    baseline = set(changed_files(repo))  # test-run artifacts like __pycache__

    print(f"Tests fail after upgrading {args.package}. Handing off to Claude ({args.model})...")
    prompt = build_prompt(args.package, args.from_version, args.to_version, args.test, before.output)
    try:
        summary, cost = asyncio.run(run_agent(prompt, repo, args.model, args.max_turns, args.budget))
    except Exception as exc:  # still report on the PR instead of dying silently
        summary, cost = f"Agent error: `{exc}`", 0.0

    touched = [f for f in changed_files(repo) if f not in baseline]
    pinned = [f for f in touched if pins_package(repo, f, args.package)]
    after = run_tests(args.test, repo, args.timeout)  # don't trust the agent's word
    ok = after.passed and bool(touched) and not pinned

    status = "✅ Fixed" if ok else "❌ Not fixed"
    report = f"## driftfix: {args.package}\n\n**{status}** · cost ${cost:.2f}\n\n{summary}\n"
    if pinned:
        report += f"\nRejected: agent changed the {args.package} requirement or a lock file in {pinned}.\n"
    if not after.passed:
        report += f"\nTests still failing:\n```\n{after.output[-3000:]}\n```\n"
    print(report)
    if args.summary:
        args.summary.write_text(report)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="driftfix", description=__doc__)
    p.add_argument("--version", action="version", version=f"%(prog)s {version('driftfix')}")
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fix", help="fix code broken by a dependency upgrade")
    f.add_argument("--package", required=True)
    f.add_argument("--from", dest="from_version")
    f.add_argument("--to", dest="to_version")
    f.add_argument("--test", default="pytest -q", help="test command (default: pytest -q)")
    f.add_argument("--repo", type=Path, default=Path("."))
    f.add_argument("--model", default="claude-opus-5")
    f.add_argument("--max-turns", type=int, default=50)
    f.add_argument("--budget", type=float, default=5.0, help="max spend in USD (default: 5)")
    f.add_argument("--timeout", type=int, default=600, help="test timeout in seconds")
    f.add_argument("--summary", type=Path, help="write the markdown report here")
    return fix(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
