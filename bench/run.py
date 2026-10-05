"""Benchmark driftfix on real breaking upgrades.

    python bench/run.py --check        # sanity: each case passes on old, fails on new (free)
    python bench/run.py [case ...]     # run driftfix on each case (costs API credits)
"""

import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASES = Path(__file__).parent / "cases"
TEST = ".venv/bin/python -m pytest -q"


def sh(cmd: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)


def setup(case: Path, spec: str, python: str = "3.12") -> Path:
    """Copy a case into a fresh git repo with `spec` (space-separated) installed in .venv."""
    repo = Path(tempfile.mkdtemp(prefix=f"driftfix-{case.name}-"))
    shutil.copytree(case, repo, dirs_exist_ok=True)
    (repo / ".gitignore").write_text(".venv/\n__pycache__/\n.pytest_cache/\n")
    for cmd in (
        f"uv venv -q --seed -p {python} .venv",
        f"uv pip install -q -p .venv/bin/python pytest {' '.join(map(shlex.quote, spec.split()))}"
        + (" -b build-constraints.txt" if (case / "build-constraints.txt").exists() else ""),
        "git init -q && git add -A && git -c user.email=b@b -c user.name=bench commit -qm init",
    ):
        if (r := sh(cmd, repo)).returncode:
            sys.exit(f"{case.name}: `{cmd}` failed\n{r.stderr}")
    return repo


def version(repo: Path, package: str) -> str:
    code = f"import importlib.metadata as m; print(m.version('{package}'))"
    return sh(f".venv/bin/python -c \"{code}\"", repo).stdout.strip()


def main(args: list[str]) -> None:
    check = "--check" in args
    names = [a for a in args if a != "--check"] or sorted(p.name for p in CASES.iterdir())
    rows = []
    for name in names:
        case = CASES / name
        meta = json.loads((case / "case.json").read_text())
        py = meta.get("python", "3.12")
        if check:
            old_ok = sh(TEST, setup(case, meta["old"], py)).returncode == 0
            new_ok = sh(TEST, setup(case, meta["new"], py)).returncode == 0
            print(f"{name:12} old {'pass' if old_ok else 'FAIL'}  new {'pass' if new_ok else 'fail'}"
                  f"  {'ok' if old_ok and not new_ok else '<-- broken case'}")
            continue

        repo = setup(case, meta["new"], py)
        old = re.sub(r"^[^0-9]*", "", meta["old"].split()[0])
        new = version(repo, meta["package"])
        report = repo / ".driftfix.md"
        r = sh(f"driftfix fix --package {meta['package']} --from {old} --to {new} "
               f"--test '{TEST}' --budget 1.5 --summary {report}", repo)
        text = report.read_text() if report.exists() else r.stdout + r.stderr
        cost = re.search(r"cost \$([\d.]+)", text)
        diff = sh("git diff --stat -- . ':!.driftfix.md' | tail -1", repo).stdout.strip()
        rows.append((name, f"{old} → {new}", "✅" if r.returncode == 0 else "❌",
                     f"${cost.group(1)}" if cost else "?", diff))
        print(*rows[-1], repo, sep="  |  ", flush=True)

    if rows:
        table = "| Package | Upgrade | Fixed | Cost | Diff |\n|---|---|---|---|---|\n"
        table += "".join(f"| {' | '.join(row)} |\n" for row in rows)
        (Path(__file__).parent / "RESULTS.md").write_text(table)
        print("\n" + table)


if __name__ == "__main__":
    main(sys.argv[1:])
