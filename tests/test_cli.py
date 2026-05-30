"""Tests for VibeCommit CLI (v0.5+)."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from vibecommit import __version__ as _vc_version
from vibecommit.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "VibeCommit" in result.output
    assert "interactive" in result.output
    assert "commit" in result.output


def test_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "vibecommit" in result.output.lower()
    # Support any 1.x version (1.0, 1.1+, dev etc)
    assert _vc_version.split(".")[0] in result.output or _vc_version in result.output


def test_list_vibes():
    result = runner.invoke(app, ["list-vibes"])
    assert result.exit_code == 0
    assert "chill" in result.output
    assert "hype" in result.output
    assert "🧘" in result.output
    assert "🪄" in result.output


def test_list_types():
    result = runner.invoke(app, ["types"])
    assert result.exit_code == 0
    assert "feat" in result.output
    assert "fix" in result.output
    assert "✨" in result.output
    assert "Conventional Commit Types" in result.output


def test_commit_basic_suggestions():
    """Core quick path still works."""
    result = runner.invoke(
        app, ["commit", "fixed the login flow", "--vibe=pro", "--no-copy"]
    )
    assert result.exit_code == 0
    assert "pro" in result.output.lower() or "📋" in result.output
    # Scope may be present: "fix(src):" or "fix:"
    assert (
        "fix(" in result.output
        or "fix:" in result.output
        or "feat(" in result.output
        or "feat:" in result.output
    )
    assert "git commit" in result.output.lower()


def test_commit_unknown_vibe_falls_back():
    result = runner.invoke(
        app, ["commit", "quick patch", "--vibe=unknown", "--no-copy"]
    )
    assert result.exit_code == 0
    assert "git commit" in result.output.lower()


def test_suggest_command():
    result = runner.invoke(
        app, ["suggest", "add user profile page", "--vibe=chill", "--quiet"]
    )
    assert result.exit_code == 0
    # With scope or without: "feat(...):" contains "feat"
    assert "feat" in result.output or "chore" in result.output or "fix" in result.output
    # quiet mode prints single line
    assert len(result.output.strip().splitlines()) <= 2


def test_check_good_message():
    result = runner.invoke(app, ["check", "✨ feat(auth): add magic login"])
    assert result.exit_code == 0
    assert "good conventional" in result.output.lower() or "✅" in result.output


def test_check_bad_message():
    result = runner.invoke(
        app, ["check", "just a random commit message with no format"]
    )
    assert result.exit_code != 0
    assert "may not follow" in result.output.lower() or "⚠️" in result.output


def test_hooks_status_outside_git():
    """Hooks status should handle non-git dirs gracefully in most cases."""
    with tempfile.TemporaryDirectory() as tmp:
        # CliRunner doesn't support cwd directly in all versions; run from inside the tmp by changing process dir
        old = os.getcwd()
        try:
            os.chdir(tmp)
            result = runner.invoke(app, ["hooks", "status"])
            assert result.exit_code in (0, 1)
            out = (result.output or "").lower()
            assert "hook" in out or "git" in out or "error" in out or "not" in out
        finally:
            os.chdir(old)


def test_interactive_help_text():
    """Interactive command exists and shows help."""
    result = runner.invoke(app, ["interactive", "--help"])
    assert result.exit_code == 0
    assert "wizard" in result.output.lower() or "Interactive" in result.output


def test_default_no_args_launches_wizard(monkeypatch):
    """Running vibecommit with no args should invoke wizard (we just check it doesn't crash hard)."""
    # We can't easily simulate full interactive in CliRunner without heavy mocking,
    # so we at least ensure the callback path doesn't explode on --help or basic parse.
    result = runner.invoke(app, ["--help"])
    assert (
        "interactive wizard" in result.output.lower() or "VibeCommit" in result.output
    )


# =============================================================================
# REAL GIT REPO INTEGRATION TESTS (the gold for reliability)
# =============================================================================


def _init_real_git_repo(tmp_path: Path) -> Path:
    """Create a real disposable git repo for end-to-end testing."""
    repo = tmp_path / "testrepo"
    repo.mkdir()
    subprocess.check_call(
        ["git", "init", "-b", "main"], cwd=repo, stdout=subprocess.DEVNULL
    )
    subprocess.check_call(["git", "config", "user.name", "Test User"], cwd=repo)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=repo)
    return repo


def test_doctor_runs_cleanly():
    result = runner.invoke(app, ["doctor"])
    # Should never hard crash
    assert result.exit_code in (0, 1)
    assert "VibeCommit Doctor" in result.output or "doctor" in result.output.lower()


def test_real_commit_flow(tmp_path: Path):
    """End-to-end: create real repo, stage a file, generate + commit via CLI (using subprocess for real cwd)."""
    repo = _init_real_git_repo(tmp_path)

    # Create and stage a change
    (repo / "hello.py").write_text("print('hello vibecommit')")
    subprocess.check_call(["git", "add", "."], cwd=repo)

    env = os.environ.copy()
    env["VIBECOMMIT_DEFAULT_VIBE"] = "pro"

    # Make the console script (entry point) reliably discoverable even if not on global $PATH.
    # pip install -e puts "vibecommit" (and .exe on Windows) in the python's bin/Scripts dir.
    scripts_dir = str(Path(sys.executable).parent)
    env["PATH"] = scripts_dir + os.pathsep + env.get("PATH", "")

    # Use the real installed binary name (tests the console script entrypoint + full UX)
    proc = subprocess.run(
        ["vibecommit", "commit", "add hello vibe script", "--commit", "--vibe=pro"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert proc.returncode == 0, f"vibecommit failed: {proc.stdout}\\n{proc.stderr}"

    # Should have actually committed
    log = subprocess.check_output(
        ["git", "log", "--oneline", "-1"], cwd=repo, text=True
    )
    assert "add hello vibe script" in log.lower() or "hello vibe" in log.lower()


def test_doctor_detects_no_git_repo(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    old = os.getcwd()
    try:
        os.chdir(empty)
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code in (0, 1)
        assert (
            "Not inside a git repository" in result.output
            or "git repository" in result.output.lower()
        )
    finally:
        os.chdir(old)
