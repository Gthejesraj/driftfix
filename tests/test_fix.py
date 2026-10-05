import subprocess
import sys
from pathlib import Path

from driftfix.cli import main
import driftfix.cli as cli


def make_repo(tmp_path: Path, ok: bool) -> Path:
    (tmp_path / "app.py").write_text(f"OK = {ok}\n")
    (tmp_path / "requirements.txt").write_text("lib==2\n")
    for cmd in (["init", "-q"], ["add", "."], ["-c", "user.email=a@b", "-c", "user.name=a", "commit", "-qm", "init"]):
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
    from driftfix.cli import pins_package
    import tempfile
    repo = Path(tempfile.mkdtemp())
    (repo / "poetry.lock").write_text("x")
    (repo / "requirements.txt").write_text("Pydantic_Core==1\n")
    assert pins_package(repo, "poetry.lock", "anything")
    assert pins_package(repo, "requirements.txt", "pydantic-core")  # name normalization
    assert not pins_package(repo, "requirements.txt", "pydantic")   # pydantic-core is a different package
    assert not pins_package(repo, "app.py", "pydantic")
