"""🪄 VibeCommit CLI - Beautiful, smart & fun conventional commits with vibes.

A delightful tool to make your git history look like it was written by a pro with personality.
"""

from __future__ import annotations

import os
import random
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pyperclip
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from vibecommit import __version__

# =============================================================================
# GLOBAL STATE & DEBUG
# =============================================================================

# Windows Unicode/emoji support: prevent cp1252 encode errors in CI & consoles
# Must be done early before any rich/console output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass  # pre-3.7 or restricted env; rich will degrade gracefully

DEBUG = False
CONFIG: dict[str, Any] = {}


def set_debug(enabled: bool) -> None:
    global DEBUG
    DEBUG = enabled


def debug_log(msg: str) -> None:
    if DEBUG:
        console.print(f"[dim][debug] {msg}[/dim]")


# =============================================================================
# CONFIG LOADING (zero hard deps, graceful)
# =============================================================================


def _load_toml_simple(path: Path) -> dict[str, Any]:
    """Very small TOML loader for our known keys. Supports only flat tables we care about."""
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}

    data: dict[str, Any] = {}
    current_table = None

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_table = line[1:-1].strip()
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if current_table == "tool.vibecommit":
                data[key] = val
            elif current_table and current_table.startswith("tool.vibecommit"):
                # nested like [tool.vibecommit.something] - ignore for v1.1
                pass
    return data


def load_config() -> dict[str, Any]:
    """Discover and load VibeCommit configuration from multiple sources (lowest to highest priority)."""
    global CONFIG
    if CONFIG:
        return CONFIG

    candidates: list[Path] = []

    # 1. Repo root pyproject.toml
    git_root = run_git(["rev-parse", "--show-toplevel"])
    if git_root:
        candidates.append(Path(git_root) / "pyproject.toml")
        candidates.append(Path(git_root) / ".vibecommit.toml")

    # 2. User home
    home = Path.home()
    candidates.append(home / ".config" / "vibecommit" / "config.toml")
    candidates.append(home / ".vibecommit.toml")

    merged: dict[str, Any] = {}
    for p in candidates:
        if p.exists():
            debug_log(f"Loading config from {p}")
            try:
                if p.suffix == ".toml":
                    partial = _load_toml_simple(p)
                else:
                    partial = _load_toml_simple(p)
                merged.update(
                    {k: v for k, v in partial.items() if not k.startswith("_")}
                )
            except Exception as e:
                debug_log(f"Failed to parse {p}: {e}")

    # Env var overrides (highest priority)
    if os.environ.get("VIBECOMMIT_DEFAULT_VIBE"):
        merged["default_vibe"] = os.environ["VIBECOMMIT_DEFAULT_VIBE"].lower()
    if os.environ.get("VIBECOMMIT_MAX_SUBJECT"):
        merged["max_subject_length"] = os.environ["VIBECOMMIT_MAX_SUBJECT"]

    CONFIG = merged
    debug_log(f"Final config: {CONFIG}")
    return CONFIG


def get_config_value(key: str, default: Any = None) -> Any:
    return load_config().get(key, default)


app = typer.Typer(
    name="vibecommit",
    help=(
        "🪄 VibeCommit — Beautiful, smart & fun conventional commits with vibes.\n\n"
        "Make every commit a work of art. Perfect conventional format + personality in seconds."
    ),
    add_completion=True,  # Enables --install-completion and --show-completion
    rich_markup_mode="rich",
    epilog="Made with ✨ vibes by [link=https://github.com/shanewas]@shanewas[/link]",
)


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"🪄 [bold]vibecommit[/bold] v{__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Show internal decision making and config sources"
    ),
    version: bool = typer.Option(
        None, "--version", callback=_version_callback, is_eager=True
    ),
) -> None:
    """Global options for all commands."""
    if debug:
        set_debug(True)
        debug_log("Debug mode enabled")
    load_config()  # eager load so all commands benefit

    if ctx.invoked_subcommand is None:
        # Default behavior: launch the beautiful interactive wizard
        run_interactive_wizard()


console = Console(
    force_terminal=True,
    legacy_windows=True,
    width=100,
    emoji=True,
    highlight=True,
)

# =============================================================================
# VIBES & TYPES
# =============================================================================

VIBES = {
    "chill": {
        "emoji": "🧘",
        "desc": "Relaxed, thoughtful",
        "style": "cyan",
        "flavor": "calm & collected",
    },
    "hype": {
        "emoji": "🔥",
        "desc": "Energetic, exciting",
        "style": "orange1",
        "flavor": "let's GOOO",
    },
    "pro": {
        "emoji": "📋",
        "desc": "Clean, professional",
        "style": "blue",
        "flavor": "pro move",
    },
    "meme": {
        "emoji": "😂",
        "desc": "Fun, playful, chaotic",
        "style": "magenta",
        "flavor": "it just works™",
    },
}

CONVENTIONAL_TYPES = {
    "feat": {"emoji": "✨", "desc": "A new feature"},
    "fix": {"emoji": "🐛", "desc": "A bug fix"},
    "docs": {"emoji": "📚", "desc": "Documentation only changes"},
    "style": {
        "emoji": "🎨",
        "desc": "Changes that do not affect the meaning of the code",
    },
    "refactor": {
        "emoji": "♻️",
        "desc": "A code change that neither fixes a bug nor adds a feature",
    },
    "perf": {"emoji": "⚡", "desc": "A code change that improves performance"},
    "test": {
        "emoji": "🧪",
        "desc": "Adding missing tests or correcting existing tests",
    },
    "build": {
        "emoji": "🏗️",
        "desc": "Changes that affect the build system or external dependencies",
    },
    "ci": {"emoji": "🔄", "desc": "Changes to our CI configuration files and scripts"},
    "chore": {
        "emoji": "🔧",
        "desc": "Other changes that don't modify src or test files",
    },
    "revert": {"emoji": "⏪", "desc": "Reverts a previous commit"},
}

VIBE_QUOTES = [
    "Your git history is your legacy. Make it beautiful.",
    "Every commit tells a story. Make yours legendary.",
    "Clean commits, clear mind.",
    "Future you will thank present you for these commits.",
    "Vibe check: passed ✅",
    "Shipping vibes since 2026.",
    "One beautiful commit at a time.",
]

# =============================================================================
# GIT & ANALYSIS HELPERS
# =============================================================================


def run_git(cmd: list[str], timeout: int = 10) -> str:
    """Run a git command safely, return stdout or empty."""
    try:
        result = subprocess.run(
            ["git", *cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        return result.stdout.strip()
    except Exception:
        return ""


def get_staged_diff() -> str:
    """Get the current staged git diff (full)."""
    return run_git(["diff", "--staged", "--no-color", "--unified=0"])


def get_staged_files() -> list[str]:
    """Return list of staged file paths."""
    out = run_git(["diff", "--staged", "--name-only", "--no-color"])
    return [f for f in out.splitlines() if f.strip()]


def detect_scope_from_files(files: list[str]) -> str | None:
    """Heuristically pick a good scope from changed files."""
    if not files:
        return None

    # Common top-level folders as scopes
    dirs = set()
    for f in files:
        parts = Path(f).parts
        if len(parts) > 1:
            top = parts[0]
            if top not in {".github", "tests", "test", "docs", "doc"}:
                dirs.add(top.lower())

    # Prioritize common ones
    priority = [
        "api",
        "auth",
        "ui",
        "frontend",
        "backend",
        "core",
        "db",
        "models",
        "cli",
        "utils",
    ]
    for p in priority:
        if p in dirs:
            return p

    # Fallback to first interesting dir
    if dirs:
        return sorted(dirs)[0][:12]  # keep short

    # File extension hints
    exts = {Path(f).suffix.lower() for f in files}
    if exts == {".md"} or all("readme" in f.lower() for f in files):
        return "docs"
    if any("test" in f.lower() or f.startswith("tests/") for f in files):
        return "test"

    return None


def detect_commit_type(msg: str, diff: str, files: list[str]) -> str:
    """Smart conventional type detection from message, diff and files."""
    text = (msg + " " + diff).lower()

    # File-based first (strong signals)
    if files:
        test_files = [f for f in files if "test" in f.lower() or f.startswith("tests/")]
        doc_files = [
            f for f in files if f.endswith((".md", ".rst", ".txt")) or "docs/" in f
        ]
        if len(test_files) == len(files) and files:
            return "test"
        if len(doc_files) == len(files) and files:
            return "docs"
        ci_files = [
            f
            for f in files
            if "ci" in f.lower() or ".github" in f or "workflow" in f.lower()
        ]
        if len(ci_files) == len(files) and files:
            return "ci"
        # Build files only -> build type if the *message* indicates dep/package work
        # (avoid false "build" when pyproject.toml etc are staged but change is a fix/feat)
        build_files = any(
            f.endswith(
                ("Dockerfile", ".toml", ".yaml", ".yml", "setup.py", "pyproject.toml")
            )
            for f in files
        )
        if build_files and any(
            k in msg.lower() for k in ["dep", "lock", "package", "bump", "requirements"]
        ):
            return "build"

    # Message + diff keywords (order matters for precedence)
    if any(k in text for k in ["revert ", "reverts ", "undo ", "rollback"]):
        return "revert"
    if any(
        k in text
        for k in ["fix", "bug", "error", "crash", "issue", "broken", "regression"]
    ):
        return "fix"
    if any(
        k in text
        for k in ["add", "new ", "implement", "feature", "introduce", "support for"]
    ):
        return "feat"
    if any(
        k in text for k in ["perf", "speed", "slow", "memory", "optimize", "faster"]
    ):
        return "perf"
    if any(
        k in text
        for k in ["refactor", "clean", "improve structure", "restructure", "extract"]
    ):
        return "refactor"
    if any(k in text for k in ["test", "spec", "coverage", "pytest", "unittest"]):
        return "test"
    if any(k in text for k in ["doc", "readme", "comment", "example", "guide"]):
        return "docs"
    if any(
        k in text
        for k in ["style", "format", "lint", "prettier", "black", "ruff", "indent"]
    ):
        return "style"
    if any(k in text for k in ["ci", "workflow", "github action", "pipeline"]):
        return "ci"
    if any(
        k in text
        for k in ["build", "deps", "dependency", "package", "lockfile", "requirements"]
    ):
        return "build"

    return "chore"


def is_breaking_change(msg: str, diff: str) -> bool:
    """Detect if this should be marked as breaking change."""
    text = (msg + " " + diff).lower()
    breaking_keywords = [
        "breaking",
        "incompatible",
        "remove",
        "delete api",
        "drop support",
        "major change",
        "not backward",
        "breaking change",
        "api change",
        "remove ",
        "deprecated and removed",
    ]
    return any(k in text for k in breaking_keywords)


def generate_suggestions(
    msg: str,
    vibe: str,
    diff: str,
    files: list[str],
    include_body: bool = False,
    breaking: bool = False,
) -> list[str]:
    """Generate 3 beautiful, conventional commit message suggestions."""
    vibe_info = VIBES.get(vibe, VIBES["hype"])
    vibe_emoji = vibe_info["emoji"]
    ctype = detect_commit_type(msg, diff, files)
    type_emoji = CONVENTIONAL_TYPES.get(ctype, CONVENTIONAL_TYPES["chore"])["emoji"]

    base_msg = msg.strip().rstrip(".").strip()
    if not base_msg:
        base_msg = "update code"

    # Keep subject short and imperative
    if len(base_msg) > 50:
        base_msg = base_msg[:47] + "..."

    scope = detect_scope_from_files(files)
    scope_str = f"({scope})" if scope else ""

    breaking_marker = "!" if breaking else ""

    suggestions: list[str] = []

    # Suggestion 1: Clean & minimal (always good)
    s1 = f"{type_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg}"
    suggestions.append(s1)

    # Suggestion 2: Vibe-flavored
    flavor = vibe_info["flavor"]
    if vibe == "hype":
        s2 = f"{vibe_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg} (let's GOOO 🚀)"
    elif vibe == "chill":
        s2 = f"{vibe_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg} — {flavor} 🧘"
    elif vibe == "meme":
        s2 = f"{vibe_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg} ({flavor} 😂)"
    else:
        s2 = f"{vibe_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg} [{flavor} 📋]"
    suggestions.append(s2)

    # Suggestion 3: With context or emoji boost
    if vibe == "pro":
        s3 = f"{type_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg}"
    else:
        extra = random.choice(["✨", "🚀", "💫", "🔥", "🧠"])
        s3 = f"{vibe_emoji} {ctype}{scope_str}{breaking_marker}: {base_msg} {extra}"
    suggestions.append(s3)

    return suggestions


def format_full_commit_message(
    subject: str,
    body: str = "",
    breaking_desc: str = "",
    closes: str = "",
    vibe: str = "hype",
) -> str:
    """Format a full multi-line conventional commit message."""
    vibe_info = VIBES.get(vibe, VIBES["hype"])
    emoji = vibe_info["emoji"]

    ctype = detect_commit_type(subject, "", [])
    scope = detect_scope_from_files(get_staged_files())
    scope_str = f"({scope})" if scope else ""
    breaking = "!" if breaking_desc else ""

    msg = f"{emoji} {ctype}{scope_str}{breaking}: {subject.strip()}"

    if body:
        msg += f"\n\n{body.strip()}"

    footers = []
    if breaking_desc:
        footers.append(f"BREAKING CHANGE: {breaking_desc.strip()}")
    if closes:
        footers.append(f"Closes {closes.strip()}")

    if footers:
        msg += "\n\n" + "\n".join(footers)

    return msg


def get_vibe_quote() -> str:
    return random.choice(VIBE_QUOTES)


# =============================================================================
# INTERACTIVE WIZARD
# =============================================================================


def run_interactive_wizard(default_vibe: str | None = None) -> None:
    if default_vibe is None:
        default_vibe = get_config_value("default_vibe", "hype")
    """Beautiful interactive commit message builder."""
    console.print()
    console.rule("[bold magenta]🪄 VibeCommit Interactive Wizard[/bold magenta]")
    console.print("[dim]Answer a few questions → get perfect commit messages[/dim]\n")

    # 1. Vibe selection
    console.print("[bold]Choose your vibe:[/bold]")
    vibe_table = Table(show_header=False, box=None, padding=(0, 2))
    vibe_table.add_column("Key", style="dim")
    vibe_table.add_column("Vibe", style="bold")
    vibe_table.add_column("Personality")

    vibe_keys = list(VIBES.keys())
    for i, (name, info) in enumerate(VIBES.items(), 1):
        vibe_table.add_row(f"[{i}]", f"{info['emoji']} {name}", info["desc"])

    console.print(vibe_table)

    vibe_choice = Prompt.ask(
        "\nVibe number or name",
        choices=vibe_keys + [str(i) for i in range(1, 5)],
        default=default_vibe,
        show_choices=False,
    )
    if vibe_choice.isdigit():
        vibe = vibe_keys[int(vibe_choice) - 1]
    else:
        vibe = vibe_choice.lower()

    vibe_info = VIBES[vibe]
    console.print(
        f"→ Selected {vibe_info['emoji']} [bold {vibe_info['style']}]{vibe}[/] vibe\n"
    )

    # 2. Quick description
    subject = Prompt.ask(
        "[bold]Short description[/bold] (imperative, present tense, <50 chars)",
        default="update code",
    ).strip()

    # 3. Breaking?
    breaking = Confirm.ask("Is this a [bold red]breaking change[/]?", default=False)
    breaking_desc = ""
    if breaking:
        breaking_desc = Prompt.ask("BREAKING CHANGE description (one sentence)")

    # 4. Optional body
    add_body = Confirm.ask("Add a body paragraph?", default=False)
    body = ""
    if add_body:
        body = Prompt.ask("[dim]Body (explain why / what / context)[/dim]", default="")

    # 5. Closes issues?
    closes = ""
    if Confirm.ask("Reference issues this closes? (e.g. #42, #1337)", default=False):
        closes = Prompt.ask("Issue references", default="#42")

    # Generate
    files = get_staged_files()
    diff = get_staged_diff()
    suggestions = generate_suggestions(subject, vibe, diff, files, bool(body), breaking)

    # Show suggestions
    console.print()
    console.rule(
        f"[bold {vibe_info['style']}]🎨 {vibe.upper()} VIBE — {vibe_info['desc']}[/bold {vibe_info['style']}]"
    )

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("#", style="dim", width=4)
    table.add_column("Commit Message", style="bold")

    for i, s in enumerate(suggestions, 1):
        table.add_row(f"[{i}]", s)

    console.print(table)

    # Full preview option
    full_msg = format_full_commit_message(subject, body, breaking_desc, closes, vibe)
    if body or breaking or closes:
        console.print(
            Panel(full_msg, title="📝 Full Message Preview", border_style="green")
        )

    # Action
    action = Prompt.ask(
        "\n[bold]Action[/bold]",
        choices=["1", "2", "3", "copy", "commit", "edit", "cancel"],
        default="copy",
        show_choices=False,
    )

    chosen = suggestions[0]
    if action.isdigit() and 1 <= int(action) <= 3:
        chosen = suggestions[int(action) - 1]
    elif action == "edit":
        chosen = Prompt.ask("Edit the message", default=chosen)
    elif action == "cancel":
        console.print("[yellow]Vibe preserved. Aborted.[/yellow]")
        return

    # Use full if body/breaking present
    if (body or breaking_desc or closes) and action != "edit":
        chosen = full_msg

    # Copy / Commit
    if action in ("copy", "1", "2", "3") or action == "edit":
        try:
            pyperclip.copy(chosen)
            console.print(
                Panel(
                    f"[green]✅ Copied to clipboard![/green]\n\n"
                    f'[bold]git commit -m "{chosen.splitlines()[0]}..."[/bold]\n\n'
                    f"[dim]{get_vibe_quote()}[/dim]",
                    title="🚀 Ready to ship",
                    border_style="green",
                )
            )
        except Exception as e:
            console.print(f"[yellow]⚠️  Clipboard failed: {e}[/yellow]")
            console.print(
                f"\n[bold green]Run this:[/bold green]\n[green]{chosen}[/green]"
            )

    if action == "commit":
        try:
            result = subprocess.run(
                ["git", "commit", "-m", chosen],
                check=True,
                capture_output=True,
                text=True,
            )
            console.print(
                Panel(
                    f"[bold green]✅ Committed with {vibe_info['emoji']} {vibe} vibes![/bold green]\n\n"
                    f"[dim]{result.stdout or 'All good.'}[/dim]",
                    title="Shipped ✨",
                    border_style="green",
                )
            )
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Commit failed:[/red] {e.stderr or e}")


# =============================================================================
# HOOKS
# =============================================================================

HOOK_SCRIPT = '''#!/usr/bin/env python3
# VibeCommit prepare-commit-msg hook
# Installed by `vibecommit hooks install`
# This script is deliberately robust across pip, pipx, conda, different Pythons, Windows etc.

import os
import subprocess
import sys
from pathlib import Path


def get_vibecommit_candidates() -> list[list[str]]:
    """Return ordered list of [cmd, ...] to try for maximum reliability."""
    candidates: list[list[str]] = []

    # 1. pipx isolated (common for user installs)
    pipx_bin = Path.home() / ".local" / "bin" / "vibecommit"
    if pipx_bin.exists():
        candidates.append([str(pipx_bin), "suggest", "--quiet"])

    # 2. The normal console script (pip/pipx/editable installs put it on PATH)
    candidates.append(["vibecommit", "suggest", "--quiet"])

    # 3. Explicit python -m (most reliable when package is importable in this python)
    py = sys.executable or "python3"
    candidates.append([py, "-m", "vibecommit", "suggest", "--quiet"])

    # 4. Fallback python3 -m (covers shebang cases on some systems)
    if py != "python3":
        candidates.append(["python3", "-m", "vibecommit", "suggest", "--quiet"])

    # Windows pipx / appdata common locations (best effort)
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            win_pipx = Path(appdata) / "Python" / "Scripts" / "vibecommit.exe"
            if win_pipx.exists():
                candidates.insert(0, [str(win_pipx), "suggest", "--quiet"])

    # Dedup while preserving order
    seen = set()
    uniq = []
    for c in candidates:
        key = tuple(c)
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq


def main() -> None:
    if len(sys.argv) < 2:
        return
    commit_msg_file = sys.argv[1]

    content = Path(commit_msg_file).read_text(errors="ignore").strip()
    if content and not content.startswith("#"):
        return  # user already provided a message

    for cmd in get_vibecommit_candidates():
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=6,
                env={**os.environ, "VIBECOMMIT_SKIP_HOOK": "1"},  # prevent recursion
            )
            suggestion = (result.stdout or "").strip()
            if suggestion and result.returncode == 0:
                Path(commit_msg_file).write_text(suggestion + "\\n\\n" + content)
                return  # success, done
        except Exception:
            continue  # try next candidate

    # All strategies failed - never break the user's commit flow
    pass


if __name__ == "__main__":
    main()
'''


@app.command("hooks")
def hooks_cmd(
    action: str = typer.Argument(..., help="install | uninstall | status"),
) -> None:
    """🪝 Manage git hooks for VibeCommit (prepare-commit-msg)."""
    git_dir = Path(run_git(["rev-parse", "--git-dir"]) or ".git")
    hooks_dir = git_dir / "hooks"
    hook_file = hooks_dir / "prepare-commit-msg"

    if action == "install":
        if not git_dir.exists():
            console.print("[red]Not inside a git repository.[/red]")
            raise typer.Exit(1)

        hooks_dir.mkdir(exist_ok=True)
        hook_file.write_text(HOOK_SCRIPT)
        hook_file.chmod(0o755)
        console.print(
            Panel(
                "[green]✅ Hook installed![/green]\n\n"
                "Next time you `git commit` without -m, VibeCommit will suggest a message.\n"
                "Edit the hook at: " + str(hook_file),
                title="🪝 VibeCommit Hook",
                border_style="green",
            )
        )

    elif action == "uninstall":
        if hook_file.exists():
            hook_file.unlink()
            console.print("[green]✅ Hook removed.[/green]")
        else:
            console.print("[yellow]No hook found.[/yellow]")

    elif action == "status":
        if hook_file.exists() and "vibecommit" in hook_file.read_text():
            console.print("[green]🪝 VibeCommit hook is active[/green]")
        else:
            console.print(
                "[yellow]No VibeCommit hook installed.[/yellow] Run `vibecommit hooks install`"
            )
    else:
        console.print("[red]Unknown action. Use: install | uninstall | status[/red]")
        raise typer.Exit(1)


@app.command("suggest")
def suggest_cmd(
    msg: str = typer.Argument("", help="Optional base message"),
    vibe: str = typer.Option(get_config_value("default_vibe", "hype"), "--vibe", "-v"),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Print only the best suggestion"
    ),
) -> None:
    """💡 Generate suggestions without interactive UI (great for hooks/scripts)."""
    diff = get_staged_diff()
    files = get_staged_files()
    suggestions = generate_suggestions(msg or "update", vibe, diff, files)

    if quiet:
        print(suggestions[0])
    else:
        for i, s in enumerate(suggestions, 1):
            print(f"{i}. {s}")


# =============================================================================
# MAIN COMMANDS
# =============================================================================


@app.command()
def commit(
    msg: str = typer.Argument(..., help="Short description of the change"),
    vibe: str = typer.Option(
        get_config_value("default_vibe", "hype"),
        "--vibe",
        "-v",
        help="Vibe: chill | hype | pro | meme",
    ),
    copy: bool = typer.Option(True, "--copy/--no-copy"),
    commit_now: bool = typer.Option(
        False, "--commit", "-c", help="Actually run git commit"
    ),
    show_diff: bool = typer.Option(False, "--diff", "-d"),
    breaking: bool = typer.Option(
        False, "--breaking", "-b", help="Mark as breaking change"
    ),
) -> None:
    """✨ Generate beautiful vibe-powered conventional commit messages.

    Examples:
      vibecommit commit "add dark mode toggle" --vibe=chill
      vibecommit commit "fix auth crash" --commit --breaking
    """
    diff = get_staged_diff()
    files = get_staged_files()

    if not diff:
        console.print(
            "[yellow]⚠️  No staged changes detected.[/yellow] Using message only.\n"
        )

    if show_diff and diff:
        console.print(
            Panel(
                diff[:800] + ("..." if len(diff) > 800 else ""),
                title="📄 Staged Diff",
                border_style="dim",
            )
        )

    vibe = vibe.lower()
    if vibe not in VIBES:
        console.print(f"[red]Unknown vibe '{vibe}'.[/red] Falling back to 'hype'.")
        vibe = "hype"

    vibe_info = VIBES[vibe]
    suggestions = generate_suggestions(msg, vibe, diff, files, breaking=breaking)

    console.print()
    console.rule(
        f"[bold {vibe_info['style']}]🪄 {vibe.upper()} VIBE — {vibe_info['desc']}[/bold {vibe_info['style']}]"
    )
    console.print()

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Option", style="dim", width=6)
    table.add_column("Commit Message", style="bold")

    for i, s in enumerate(suggestions, 1):
        table.add_row(f"[{i}]", s)

    console.print(table)
    console.print()

    best = suggestions[0]

    if commit_now:
        try:
            subprocess.run(["git", "commit", "-m", best], check=True)
            console.print(
                Panel(
                    f"[bold green]✅ Committed with {vibe_info['emoji']} {vibe} vibes![/bold green]\n\n[dim]{get_vibe_quote()}[/dim]",
                    title="Shipped ✨",
                    border_style="green",
                )
            )
            return
        except subprocess.CalledProcessError as e:
            console.print(f"[red]git commit failed:[/red] {e}")
            raise typer.Exit(1) from None

    if copy:
        try:
            pyperclip.copy(best)
            console.print(
                Panel(
                    f"[green]✅ Copied to clipboard![/green]\n\n"
                    f'[bold]git commit -m "{best}"[/bold]\n\n'
                    f"[dim]{get_vibe_quote()}[/dim]",
                    title="🚀 Ready to ship",
                    border_style="green",
                )
            )
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not copy ({e}).[/yellow]")
            console.print(
                f'\n[bold]Run:[/bold] [green]git commit -m "{best}"[/green]\n'
            )
    else:
        console.print(
            Panel(
                f'[bold]git commit -m "{best}"[/bold]',
                title="🚀 Ready to ship",
                border_style="green",
            )
        )

    console.print(
        "[dim]Tip: vibecommit interactive  |  vibecommit hooks install  |  --vibe=pro[/dim]\n"
    )


@app.command("interactive")
def interactive_cmd(
    vibe: str = typer.Option(get_config_value("default_vibe", "hype"), "--vibe", "-v"),
) -> None:
    """🧙 Launch the full interactive wizard (recommended for best experience)."""
    run_interactive_wizard(vibe)


@app.command("types")
def list_types() -> None:
    """📋 List all conventional commit types with their emojis."""
    table = Table(
        title="🪄 Conventional Commit Types",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Type", style="bold cyan", width=10)
    table.add_column("Emoji", justify="center", width=6)
    table.add_column("Description")

    for name, info in CONVENTIONAL_TYPES.items():
        table.add_row(name, info["emoji"], info["desc"])

    console.print(table)
    console.print('\n[dim]Use with: vibecommit commit "msg" --vibe=chill[/dim]\n')


@app.command("list-vibes")
def list_vibes() -> None:
    """🧘 List all available vibe modes."""
    table = Table(
        title="🪄 Available Vibe Modes", show_header=True, header_style="bold magenta"
    )
    table.add_column("Vibe", style="bold", width=10)
    table.add_column("Emoji", justify="center", width=6)
    table.add_column("Personality", style="dim")
    table.add_column("Flavor", style="italic")

    for name, info in VIBES.items():
        table.add_row(name, info["emoji"], info["desc"], info.get("flavor", ""))

    console.print(table)
    console.print(
        '\n[italic]Example: [bold]vibecommit commit "fixed auth bug" --vibe=pro[/bold][/italic]\n'
    )


@app.command()
def version() -> None:
    """Show current version and fun fact."""
    console.print(f"🪄 [bold]vibecommit[/bold] v{__version__}")
    console.print(f"[dim]{get_vibe_quote()}[/dim]")


# =============================================================================
# DOCTOR — The #1 reliability feature
# =============================================================================


def _check_git_repo() -> tuple[str, str, str | None]:
    root = run_git(["rev-parse", "--show-toplevel"])
    if root:
        return "ok", f"Git repository at {root}", None
    return (
        "error",
        "Not inside a git repository",
        "cd into a git repo or run `git init`",
    )


def _check_git_available() -> tuple[str, str, str | None]:
    ver = run_git(["--version"])
    if ver:
        return "ok", ver, None
    return "error", "git command not found in PATH", "Install git (https://git-scm.com)"


def _check_vibecommit_version() -> tuple[str, str, str | None]:
    return "ok", f"vibecommit {__version__}", None


def _check_clipboard() -> tuple[str, str, str | None]:
    try:
        # pyperclip will try multiple backends
        test = "vibecommit-doctor-test"
        pyperclip.copy(test)
        got = pyperclip.paste()
        if test in str(got):
            return "ok", "Clipboard backend working", None
        return (
            "warn",
            "Clipboard wrote but read-back was odd",
            "Install xclip / xsel (Linux) or ensure terminal supports clipboard",
        )
    except Exception as e:
        return (
            "warn",
            f"Clipboard unavailable: {e}",
            "Use --no-copy or install system clipboard tools (xclip, wl-clipboard, pbcopy)",
        )


def _check_hooks() -> tuple[str, str, str | None]:
    git_dir = run_git(["rev-parse", "--git-dir"])
    if not git_dir:
        return "warn", "Cannot determine .git directory", None
    hook = Path(git_dir) / "hooks" / "prepare-commit-msg"
    if hook.exists() and "vibecommit" in hook.read_text(errors="ignore"):
        return "ok", f"Hook installed at {hook}", None
    return (
        "warn",
        "No VibeCommit git hook installed",
        "Run `vibecommit hooks install` for automatic suggestions",
    )


def _check_python_env() -> tuple[str, str, str | None]:
    py = sys.executable
    return "ok", f"Python {sys.version.split()[0]} ({py})", None


def _check_config_sources() -> tuple[str, str, str | None]:
    load_config()  # ensure it's populated
    sources = []
    git_root = run_git(["rev-parse", "--show-toplevel"])
    if git_root:
        for name in ["pyproject.toml", ".vibecommit.toml"]:
            p = Path(git_root) / name
            if p.exists():
                sources.append(str(p))
    home = Path.home()
    for p in [home / ".config/vibecommit/config.toml", home / ".vibecommit.toml"]:
        if p.exists():
            sources.append(str(p))
    if sources:
        return "ok", "Config found: " + ", ".join(sources), None
    return "ok", "No config files (using defaults — this is fine)", None


@app.command("doctor")
def doctor_cmd(
    fix: bool = typer.Option(
        False, "--fix", help="Attempt safe automatic fixes where possible"
    ),
    json_output: bool = typer.Option(False, "--json", help="Machine readable output"),
) -> None:
    """🩺 Run diagnostics to verify VibeCommit will work reliably in this environment.

    This is the single best command to run when something feels off.
    """
    console.print(
        "\n[bold]🩺 VibeCommit Doctor[/bold] — checking your environment...\n"
    )

    checks = [
        ("Git available", _check_git_available()),
        ("Inside git repo", _check_git_repo()),
        ("vibecommit version", _check_vibecommit_version()),
        ("Python environment", _check_python_env()),
        ("Clipboard", _check_clipboard()),
        ("Git hooks", _check_hooks()),
        ("Configuration", _check_config_sources()),
    ]

    table = Table(
        title="Diagnostic Results", show_header=True, header_style="bold cyan"
    )
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    errors: list[str] = []
    warnings: list[str] = []
    fixes: list[str] = []

    for name, (status, detail, suggestion) in checks:
        if status == "ok":
            status_str = "[green]✓ OK[/green]"
        elif status == "warn":
            status_str = "[yellow]⚠ WARN[/yellow]"
            warnings.append(f"{name}: {detail}")
            if suggestion:
                fixes.append(suggestion)
        else:
            status_str = "[red]✗ ERROR[/red]"
            errors.append(f"{name}: {detail}")
            if suggestion:
                fixes.append(suggestion)

        table.add_row(name, status_str, detail)

    console.print(table)

    if json_output:
        import json

        result = {
            "version": __version__,
            "checks": {name: {"status": s, "detail": d} for name, (s, d, _) in checks},
            "errors": errors,
            "warnings": warnings,
            "suggested_fixes": fixes,
        }
        console.print(json.dumps(result, indent=2))
        raise typer.Exit(0 if not errors else 1)

    if errors:
        console.print(
            Panel(
                "\n".join(f"• {e}" for e in errors),
                title="[red]Critical Issues[/red]",
                border_style="red",
            )
        )
    if warnings:
        console.print(
            Panel(
                "\n".join(f"• {w}" for w in warnings),
                title="[yellow]Warnings[/yellow]",
                border_style="yellow",
            )
        )

    if fixes:
        console.print("\n[bold]Recommended fixes:[/bold]")
        for f in fixes:
            console.print(f"  → {f}")

    if fix:
        console.print("\n[dim]--fix mode: attempting safe repairs...[/dim]")
        # Currently only hook is auto-fixable
        if any("hook" in f.lower() for f in fixes):
            try:
                hooks_cmd("install")
            except Exception as e:
                console.print(f"[red]Auto-fix for hook failed: {e}[/red]")

    if not errors and not warnings:
        console.print(
            Panel(
                "[bold green]Everything looks great! VibeCommit should work reliably here.[/bold green]",
                border_style="green",
            )
        )
    elif not errors:
        console.print(
            "\n[dim]No critical errors — you should be good to go. Warnings are usually easy to address.[/dim]"
        )

    raise typer.Exit(0 if not errors else 1)


@app.command("check")
def check_cmd(
    message: str | None = typer.Argument(
        None, help="Commit message to validate (or last commit if omitted)"
    ),
) -> None:
    """✅ Validate a commit message against conventional format (basic)."""
    if not message:
        # Get last commit message
        message = run_git(["log", "-1", "--pretty=%B"])
        if not message:
            console.print("[red]No commit message found.[/red]")
            raise typer.Exit(1)
        console.print("[dim]Checking last commit message...[/dim]\n")

    # Very simple conventional check (handles "✨ feat: ..." or "feat: ..." or "feat(api)!: ...")
    pattern = r"^(\S+)(?:\s+\w+)?(\(\w+\))?(!)?: .+"
    if re.match(pattern, message.strip()):
        console.print(
            Panel(
                "[green]✅ Looks like a good conventional commit![/green]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠️  Message may not follow conventional format.[/yellow]\n\n"
                "Expected: <type>(<scope>)!: <description>\n"
                "Types: feat, fix, docs, refactor, etc.",
                title="Check Result",
                border_style="yellow",
            )
        )
        raise typer.Exit(1)


# =============================================================================
# ENTRY
# =============================================================================


# The main_callback above handles global options + default wizard behavior
# We keep a lightweight fallback for the no-subcommand case inside main_callback if needed.

if __name__ == "__main__":
    app()
