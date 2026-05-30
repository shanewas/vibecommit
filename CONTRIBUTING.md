# Contributing to VibeCommit 🪄

Thank you for considering contributing! We love small, high-impact PRs that add new vibes, improve detection, make the wizard prettier, or fix sneaky bugs.

## How to contribute

1. **Fork** the repo and create your branch from `main`
2. **Make your change** — keep it focused and fun
3. **Test** — `pytest` + `ruff check .` should pass
4. **Open a PR** with a clear description + before/after if visual

## Adding a new vibe

Vibes live in `src/vibecommit/cli.py` in the `VIBES` dict.

Each vibe needs:
- Unique emoji
- Short personality description
- `flavor` text used in suggestions
- Optional custom formatting logic in `generate_suggestions()`

Example PR title: `feat: add zen vibe 🩷 for mindful commits`

## Code style & principles

- Keep the core delightful and fast (<250 LOC for cli.py is ideal)
- Use **Rich** for every bit of terminal output (no raw `print`)
- Prefer small pure functions for detection logic
- New dependencies only with very strong justification (we like zero-config installs)
- Interactive wizard should feel like magic, not a form

## Running tests

```bash
pip install -e ".[dev]"
pytest -q --cov=src/vibecommit
ruff check .
```

## Questions?

Open an issue or ping [@shanewas](https://github.com/shanewas) on X/Twitter.

Let's make git history beautiful together. ✨

---

**Note:** This project follows [Conventional Commits](https://www.conventionalcommits.org/) (ironically, we dogfood VibeCommit for all our commits).