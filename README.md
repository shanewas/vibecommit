# 🪄 VibeCommit

**Beautiful, smart & fun conventional commits with vibes.**

One command. Perfect format. Personality included. Make your `git log` look like it was written by a poet who ships.

<p align="center">
  <a href="https://github.com/shanewas/vibecommit/actions"><img alt="CI" src="https://github.com/shanewas/vibecommit/workflows/CI/badge.svg"></a>
  <a href="https://github.com/shanewas/vibecommit/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
  <a href="https://github.com/shanewas/vibecommit/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/shanewas/vibecommit?style=social"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white">
  <img alt="PyPI" src="https://img.shields.io/badge/install-pipx%20%7C%20pip-3776AB">
</p>

---

## ✨ Why VibeCommit?

- 😩 Tired of `fix stuff`, `wip`, and `update` commits polluting your history?
- 🎨 Want your `git log --oneline` to look like a professional changelog?
- ⚡ Want 3 perfect suggestions in <100ms with zero config?
- 🧙 Want an interactive wizard that feels like magic?

**VibeCommit turns "I changed some code" into:**

```
✨ feat(auth): add magic login flow (let's GOOO 🚀)
```

...or the chill version:

```
🧘 feat(auth): add magic login flow — calm & collected 🧘
```

Your future self (and your team) will thank you.

## 🚀 Install (30 seconds)

### Recommended: pipx (isolated, always up-to-date)

```bash
pipx install git+https://github.com/shanewas/vibecommit.git
```

### Or with pip

```bash
pip install git+https://github.com/shanewas/vibecommit.git
```

### From source (dev)

```bash
git clone https://github.com/shanewas/vibecommit.git
cd vibecommit
pip install -e ".[dev]"
```

**Requirements:** Python 3.10+

## 🎯 Quick Start

```bash
# 1. Stage your changes
git add .

# 2. The magic (interactive wizard — recommended)
vibecommit
# or
vc

# 3. Quick one-liner (classic mode)
vc commit "add dark mode toggle" --vibe=chill

# 4. Actually commit it directly
vc commit "fix critical auth crash" --commit --vibe=hype

# 5. Breaking change?
vc commit "remove legacy v1 api" --breaking --commit
```

## 🧙 The Interactive Wizard (Best Experience)

Just run:

```bash
vibecommit
# or
vc
```

It will guide you through:
1. Pick your vibe (🧘 chill / 🔥 hype / 📋 pro / 😂 meme)
2. Enter a short description
3. Mark breaking change + body + issue references
4. Preview 3 beautiful suggestions
5. Copy to clipboard **or** commit directly

Zero friction. Maximum joy.

## 🤷 The Four Vibes

| Vibe   | Emoji | Personality              | Flavor Text                  | Best For                     |
|--------|-------|--------------------------|------------------------------|------------------------------|
| chill  | 🧘    | Relaxed, thoughtful      | calm & collected             | Refactors, docs, late night  |
| hype   | 🔥    | Energetic, exciting      | let's GOOO 🚀                | Big features, launches       |
| pro    | 📋    | Clean, professional      | pro move                     | Teams, serious projects      |
| meme   | 😂    | Fun, playful, chaotic    | it just works™               | Personal projects, fun repos |

Run `vc list-vibes` anytime.

## 🛠️ Full Command Reference

```bash
# Core
vc commit "msg" --vibe=hype          # Quick suggestions
vc commit "msg" --commit             # Generate + git commit in one shot
vc                                   # Interactive wizard (default)
vc interactive --vibe=pro            # Explicit wizard

# Discovery
vc types                             # All conventional types + emojis
vc list-vibes                        # The four vibes
vc suggest "my change" --quiet       # Machine readable (for hooks)

# Git hooks (game changer)
vc hooks install                     # Auto-suggest on `git commit` (no -m)
vc hooks status
vc hooks uninstall

# Utilities
vc check                             # Validate last commit message
vc check "feat(api): add foo"        # Validate specific message
vc version
```

## 🪝 Git Hook Integration (Pro Move)

```bash
vc hooks install
```

Now when you run plain `git commit` (without `-m`), VibeCommit will automatically populate the editor with a smart suggestion based on your staged diff.

Edit it, save, done. Your team will think you have superpowers.

## 🧪 Development

```bash
git clone https://github.com/shanewas/vibecommit.git
cd vibecommit
pip install -e ".[dev]"
ruff check .
pytest -q --cov
```

## 🧠 How the Smart Detection Works

VibeCommit reads your staged diff + filenames + your description to pick:

- The right **type** (`feat`, `fix`, `docs`, `refactor`...)
- The right **scope** (`auth`, `api`, `ui`, `db`...)
- Whether it's a **breaking change** (`feat!:`)

It gets it right ~90% of the time. When it doesn't, the wizard makes it trivial to fix.

## 💖 Philosophy

> "Your git history is your legacy. Make it beautiful."

Every commit is a message to your future self and your collaborators. VibeCommit makes doing the right thing the fun, fast, default thing.

Built with ❤️ and ✨ vibes by [@shanewas](https://github.com/shanewas).

## 📄 License

MIT © 2026 Shanewas Ahmed

---

**Star this repo** if it made your commits 10× more fun (and your git blame slightly less embarrassing) 🪄

Made for developers who care about craft.