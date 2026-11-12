# School Notes

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
- XeLaTeX with these packages (Debian/Ubuntu):
  `texlive-xetex texlive-lang-czechslovak texlive-science texlive-pictures texlive-latex-extra`

## Usage

```bash
uv sync
uv run school-notes render tests/fixtures/all_elements.json   # JSON → .tex + .pdf
uv run pytest                                                  # tests
```

## API keys and secrets

**No key ever goes into this repository.** Backends read credentials only from:

- environment variables (e.g. `ANTHROPIC_API_KEY`), or
- the user config file `~/.config/school-notes/config.toml`, which lives outside the repo.

`.gitignore` also blocks `.env*`, `config.toml` and `secrets*`. A
[gitleaks](https://github.com/gitleaks/gitleaks) pre-commit hook scans every commit.

## License

MIT
