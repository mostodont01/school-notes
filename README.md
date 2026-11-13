# School Notes

[![CI](https://github.com/mostodont01/school-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/mostodont01/school-notes/actions/workflows/ci.yml)

Write fast, messy notes in class → an LLM figures out the structure → a clean PDF.

```
lesson.txt ──LLM──▶ lesson.json ──renderers──▶ lesson.tex ──XeLaTeX──▶ lesson.pdf
```

- **The LLM only decides structure.** It returns JSON that must match a strict schema
  (`notes_app/schema.py`). It never writes the LaTeX document itself.
- **The renderer is deterministic.** Every element type has its own small module in
  `notes_app/render/`. The same JSON always gives the same `.tex`.
- **Elements:** headings, paragraphs, (nested) lists, tables, code, equations (LaTeX math),
  chemical reactions (mhchem), structural formulas (chemfig), callout boxes and graphs:
  functions, bar, line and pie charts.
- Made for **Czech** notes (XeLaTeX + babel czech).

Status and roadmap: see [PLAN.md](PLAN.md) and the GitHub milestones.

## Requirements

- Python ≥ 3.12 and [uv](https://docs.astral.sh/uv/)
- [Claude Code](https://claude.com/claude-code), logged in (the default LLM backend runs `claude -p`)
- XeLaTeX with these packages (Debian/Ubuntu):
  `texlive-xetex texlive-lang-czechslovak texlive-science texlive-pictures texlive-latex-extra texlive-plain-generic`

## The app

```bash
uv run school-notes-app
```

- **Sidebar:** subjects (folders) and their lessons, newest first. The dot shows the PDF state:
  green = up to date, amber = text changed since the last format, grey = not formatted yet.
- **Editor:** write messy notes. They autosave after 1.5 s, and every save keeps the previous
  version in `<subject>/.backup/`.
- **Preview:** the PDF, which keeps its scroll position when it is rebuilt. Ctrl + wheel zooms.
- **Claude usage** (bottom of the sidebar): the last format's tokens, and bars for how full your
  plan's 5-hour and weekly windows are, with reset times. The limits come from each `claude -p`
  reply and, fresher and for free, from the
  Claude Code status bar's shared snapshot (`/tmp/mugshot_ratelimits_global.json`) when it's installed. Anthropic reports
  only how full a window is, not its size in tokens.

| Key | Action |
|---|---|
| Ctrl+Enter | Format with Claude → PDF (runs in the background) |
| Ctrl+S | Save now |
| Ctrl+R | Re-render the PDF from the saved JSON (no LLM, quick) |
| Ctrl+N | New lesson in the current subject (named from its title after formatting) |
| Ctrl+Shift+N | New subject |

Notes live in `~/School/Notes/<subject>/` (configurable in `~/.config/school-notes/config.toml`):
`2026-11-12 Pohyb.txt` is what you write; the `.json`, `.tex` and `.pdf` files next to it are
generated. Formatting needs internet; writing and saving don't.

## Command line

```bash
uv sync
uv run school-notes format lesson.txt     # notes → LLM → lesson.json + .tex + .pdf
uv run school-notes render lesson.json    # JSON → .tex + .pdf (no LLM, instant)
uv run pytest                             # offline tests
uv run pytest -m live                     # real LLM calls on tests/fixtures/*_messy.txt
```

## API keys and secrets

The default backend uses your existing **Claude Code login** (`claude -p`), so no API key is
needed at all. **No key ever goes into this repository.** Other backends read credentials only from:

- environment variables (e.g. `ANTHROPIC_API_KEY`), or
- the user config file `~/.config/school-notes/config.toml`, which lives outside the repo.

`.gitignore` also blocks `.env*`, `config.toml` and `secrets*`. A
[gitleaks](https://github.com/gitleaks/gitleaks) pre-commit hook scans every commit.

## License

MIT
