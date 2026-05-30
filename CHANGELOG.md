# Changelog

All notable changes to VibeCommit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-30

### Highlights
- 🎉 **First stable release** — production-ready OSS CLI
- Interactive wizard is now the default experience (`vibecommit` with no args)
- Git hooks, breaking changes, smart detection, full multi-line messages
- 100% test pass + clean lint on Python 3.10–3.12
- Complete documentation and GitHub community health files

## [0.5.0] - 2026-05-30 (pre-release)

### Added
- 🪄 Complete rewrite targeting the `vibecommit` package (canonical repo)
- Interactive wizard (`vibecommit` or `vc` with no args) — the flagship UX
- Full support for breaking changes (`--breaking`, `!` marker, BREAKING CHANGE footer)
- `vc hooks install` — automatic prepare-commit-msg git hook
- `vc types` — beautiful reference for all conventional commit types
- `vc check` — validate messages against conventional format
- `vc suggest --quiet` — machine-readable suggestions for scripts/hooks
- Smart scope detection from file paths + diff analysis
- Enhanced type detection (test-only changes, docs-only, ci, build, revert, etc.)
- Rich multi-line full commit message formatting (body + footers + closes)
- Vibe-flavored random quotes and delightful micro-copy everywhere
- Two entry points: `vibecommit` + `vc`
- Comprehensive pytest suite + ruff + mypy config
- Full CI matrix (3.10–3.12) + build artifacts
- Professional README, CONTRIBUTING, CHANGELOG, SECURITY, CODE_OF_CONDUCT

### Changed
- Package renamed from `vibe-commit` → `vibecommit` for cleaner branding
- All URLs, docs, and metadata point to https://github.com/shanewas/vibecommit
- CLI help text and epilog updated to 🪄 branding

### Fixed
- Various edge cases in detection when no staged changes or no git repo

## [0.1.0] - 2026-05-30 (prototype)

- Initial prototype with 4 vibes, quick `vc commit`, clipboard, Rich output
- Basic smart detection
- See `shanewas/vibe-commit` for history

[1.0.0]: https://github.com/shanewas/vibecommit/releases/tag/v1.0.0
[0.5.0]: https://github.com/shanewas/vibecommit/releases/tag/v0.5.0
[0.1.0]: https://github.com/shanewas/vibe-commit/releases/tag/v0.1.0