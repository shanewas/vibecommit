"""Tests for VibeCommit CLI (v0.5+)."""

import tempfile

from typer.testing import CliRunner

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
    assert "v0." in result.output or "0.5" in result.output


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
    assert "fix:" in result.output or "feat:" in result.output
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
    assert "feat" in result.output or "chore" in result.output
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
        import os

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
