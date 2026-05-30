# VibeCommit Improvement Ideas — Reliability for Every Developer

**Goal**: Make VibeCommit something *any* developer can use confidently on any machine, any repo, any OS, without surprises.

## Core Reliability Principles
- Fail gracefully, never lose the user's work
- Give clear, actionable diagnostics (`doctor` command)
- Work the same on Linux / macOS / Windows / CI / containers / git worktrees
- Zero-config by default + powerful per-repo config when needed
- Transparent decision making (`--debug`)
- Excellent test coverage with real git operations

---

## Prioritized Ideas (High Impact → Lower)

### P0 — Must-Have for Reliability (Implement Soon)

1. **`vc doctor`** (Highest priority)
   - Checks: git repo? git version? python + package version? clipboard backend? hook installed & executable? write permission on .git/hooks? config files found? terminal interactive?
   - Suggests exact fixes (e.g. "Run `vc hooks install`")
   - `--fix` mode for safe automatic repairs
   - Outputs machine-readable JSON with `--json` for CI/tooling

2. **Real Configuration System**
   - Read `[tool.vibecommit]` from `pyproject.toml`
   - Or `.vibecommit.toml` / `.vibecommit.json` in repo root or `$HOME`
   - Supported keys (start small):
     - `default_vibe = "pro"`
     - `max_subject_length = 72`
     - `extra_vibes = [{name = "zen", emoji = "🪷", ...}]`
     - `preferred_scopes = ["api", "auth", "ui"]`
     - `disabled_types = ["chore"]`
     - `auto_install_hook = false`
   - Environment variable overrides (e.g. `VIBECOMMIT_DEFAULT_VIBE=chill`)

3. **Cross-Platform Hardening + Windows CI**
   - Full GitHub Actions matrix: ubuntu, macos, windows (Python 3.10+)
   - Hook installation must work on Windows (avoid fragile shebang; prefer calling the installed `vibecommit` entrypoint or `python -m vibecommit.suggest`)
   - All Path handling via `pathlib` (already mostly done)
   - Test clipboard on Windows runners
   - Handle CRLF in diffs gracefully

4. **Dramatically Better Error Handling & UX**
   - Never let clipboard failure crash the program
   - Clear "Not a git repository" early with helpful message
   - Handle `git` not in PATH
   - Graceful handling of extremely large diffs / monorepos (truncate analysis after N files or N KB)
   - Proper KeyboardInterrupt handling in wizard (clean exit)
   - Better messages when running in non-interactive CI (auto `--no-copy`, no prompts)

5. **Transparency: `--debug` / `--explain` flag**
   - Shows exactly why it chose `fix(auth)` instead of `feat`
   - Dumps detected files, scopes, breaking signals, config sources
   - Invaluable for users to trust the tool and for bug reports

### P1 — High Value

6. **Shell Completions (First-Class)**
   - `vibecommit --install-completion` (Typer native)
   - Or `vc completion install`
   - Full support for subcommands, vibes, types, etc.

7. **Robust Real Git Integration Tests**
   - Use `tmp_path` + `subprocess` to create real disposable git repos in tests
   - Test the full flow: stage files → run `vc commit ... --commit` → inspect `git log`
   - Test hook installation + firing
   - Test doctor in various broken states

8. **Hook Script Improvements**
   - Instead of embedding a giant heredoc, install a small, robust wrapper
   - Better handling when `vibecommit` is installed via pipx (different python)
   - Support skipping via `VIBECOMMIT_SKIP_HOOK=1` or `.git/vibecommit-skip`

9. **Advanced Commit Features**
   - `vc commit --amend`
   - Support for co-authors / trailers (`--trailer "Co-authored-by: ..."` or detect from git config)
   - `vc commit --no-verify` passthrough

10. **`vc commit --dry-run` + validation against commitlint / husky if present**

### P2 — Future Polish / Distribution

- Standalone single-binary builds (PyInstaller / Nuitka) for `curl | bash` style installs
- Official Homebrew formula + Scoop + Chocolatey
- MkDocs or GitHub Pages documentation site
- Optional AI backend (Ollama / OpenAI) behind `vibecommit ai commit` with opt-in + clear privacy note
- Pre-built Docker image for CI use
- Integration with commitizen / semantic-release ecosystems

---

## How to Prioritize Future Work

Use this rubric:
- Does it prevent a user from losing a carefully worded commit message?
- Does it reduce "it works on my machine" support burden?
- Does it increase trust ("I understand why it suggested this")?
- Does it work for the 80% of developers who are not power users?

**Current v1.0.0 is already delightful.** These improvements turn it from "fun tool" into "the reliable default for my entire team".

---

*Generated during the v1.1 reliability hardening cycle — May 2026*