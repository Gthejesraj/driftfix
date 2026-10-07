import subprocess
import sys
from pathlib import Path

import driftfix.cli as cli
from driftfix.cli import main


def make_repo(tmp_path: Path, ok: bool) -> Path:
    (tmp_path / "app.py").write_text(f"OK = {ok}\n")
    (tmp_path / "requirements.txt").write_text("lib==2\n")
    commit = ["-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "init"]
    for cmd in (["init", "-q"], ["add", "."], commit):
        subprocess.run(["git", *cmd], cwd=tmp_path, check=True)
    return tmp_path


TEST = f"{sys.executable} -c 'import app; assert app.OK'"


def run(tmp_path, agent, monkeypatch):
    monkeypatch.setattr(cli, "run_agent", agent)
    return main(["fix", "--package", "lib", "--test", TEST, "--repo", str(tmp_path)])


def test_green_tests_skip_agent(tmp_path, monkeypatch):
    async def agent(*a):
        raise AssertionError("agent should not run")
    assert run(make_repo(tmp_path, True), agent, monkeypatch) == 0


def test_agent_fix_is_verified(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, False)
    async def agent(prompt, *a):
        assert "assert app.OK" in prompt  # failure output reaches the agent
        (repo / "app.py").write_text("OK = True\n")
        return "fixed", 0.1
    assert run(repo, agent, monkeypatch) == 0


def test_agent_lying_still_fails(tmp_path, monkeypatch):
    async def agent(*a):
        return "fixed, trust me", 0.1
    assert run(make_repo(tmp_path, False), agent, monkeypatch) == 1


def test_pinning_back_is_rejected(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, False)
    async def agent(*a):
        (repo / "requirements.txt").write_text("lib==1\n")
        (repo / "app.py").write_text("OK = True\n")
        return "pinned", 0.1
    assert run(repo, agent, monkeypatch) == 1


def test_agent_crash_is_reported(tmp_path, monkeypatch):
    async def agent(*a):
        raise RuntimeError("Not logged in")
    summary = tmp_path / "report.md"
    monkeypatch.setattr(cli, "run_agent", agent)
    code = main(["fix", "--package", "lib", "--test", TEST, "--repo", str(make_repo(tmp_path, False)),
                 "--summary", str(summary)])
    assert code == 1 and "Not logged in" in summary.read_text()


def test_adding_a_split_out_package_is_allowed(tmp_path, monkeypatch):
    repo = make_repo(tmp_path, False)
    async def agent(*a):
        (repo / "requirements.txt").write_text("lib==2\nlib-settings>=2\n")
        (repo / "app.py").write_text("OK = True\n")
        return "added lib-settings", 0.1
    assert run(repo, agent, monkeypatch) == 0


def test_pins_package():
    import tempfile

    from driftfix.cli import pins_package
    repo = Path(tempfile.mkdtemp())
    (repo / "poetry.lock").write_text("x")
    (repo / "requirements.txt").write_text("Pydantic_Core==1\n")
    assert pins_package(repo, "poetry.lock", "anything")
    assert pins_package(repo, "requirements.txt", "pydantic-core")  # name normalization
    assert not pins_package(repo, "requirements.txt", "pydantic")   # pydantic-core is a different package
    assert not pins_package(repo, "app.py", "pydantic")


def test_tests_cannot_see_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-secret")
    leak = f"{sys.executable} -c 'import os, sys; sys.exit(\"ANTHROPIC_API_KEY\" in os.environ)'"
    assert cli.run_tests(leak, tmp_path, 30).passed


def test_cost_survives_agent_error(monkeypatch):
    import asyncio
    import sys as _sys
    import types

    class ResultMessage:
        result, total_cost_usd = "", 1.02

    async def query(**kw):
        yield ResultMessage()
        raise RuntimeError("Reached maximum budget ($1)")

    fake = types.SimpleNamespace(
        ClaudeAgentOptions=lambda **kw: None, ResultMessage=ResultMessage, query=query
    )
    monkeypatch.setitem(_sys.modules, "claude_agent_sdk", fake)
    summary, cost = asyncio.run(cli.run_agent("p", Path("."), "m", 1, 1.0))
    assert cost == 1.02 and "maximum budget" in summary


def test_loosening_cap_is_allowed_pinning_back_is_not(tmp_path):
    from driftfix.cli import pins_package
    repo = make_repo(tmp_path, True)
    (repo / "requirements.txt").write_text("lib>=2.0.0\n")         # was lib==2, loosened
    assert not pins_package(repo, "requirements.txt", "lib", "2.13.5")
    (repo / "requirements.txt").write_text("lib<2\n")              # pinned back
    assert pins_package(repo, "requirements.txt", "lib", "2.13.5")
    (repo / "requirements.txt").write_text("lib>=2.0.0\n")         # unknown target version: be strict
    assert pins_package(repo, "requirements.txt", "lib", None)
    assert pins_package(repo, "requirements.txt", "lib", "1.x")    # unparsable version: be strict


def test_guard_reads_requirements_inside_code(tmp_path):
    from driftfix.cli import pins_package
    repo = make_repo(tmp_path, True)
    (repo / "setup.py").write_text("install_requires=['lib>=1.4,<2.0'],\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    commit = ["git", "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "s"]
    subprocess.run(commit, cwd=repo, check=True)
    (repo / "setup.py").write_text("install_requires=['lib>=2.0', 'other<1'],\n")   # widened
    assert not pins_package(repo, "setup.py", "lib", "2.13.5")
    (repo / "setup.py").write_text("install_requires=['lib>=1.4,<2.0', 'x'],\n")    # still excludes 2.x
    assert pins_package(repo, "setup.py", "lib", "2.13.5")
