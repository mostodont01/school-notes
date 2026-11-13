# Plan

Day-to-day progress is tracked in Claude Code tasks; the GitHub milestones mirror the big steps. This file has the overview and the decisions behind them.

## Architecture

```
lesson.txt ─▶ LLM backend ─▶ lesson.json ─▶ render/ ─▶ lesson.tex ─▶ xelatex ─▶ lesson.pdf
              (structure only,   (Pydantic-     (one module
               schema-forced)     validated)     per element)
```

**Decisions** (change only with a concrete reason):
1. Raw notes go straight to the LLM; there is no hand-written parser in front of it.
2. `notes_app/schema.py` is the single source of truth: it is the JSON schema the LLM is forced to follow, and it validates the result. Field descriptions double as LLM instructions.
3. The LLM decides structure and wording but writes no document LaTeX. The only exceptions are small, wrapped snippets: math (`<m>`, `equation`), mhchem (`<ce>`, `reaction`) and chemfig (`structure`).
4. The renderer is deterministic. Inline text is escaped, so no stray character can break the compile.
5. XeLaTeX (Czech/UTF-8, mhchem, chemfig, pgfplots). All four files (`.txt .json .tex .pdf`) are kept side by side.
6. Lists are flat, with a `level` on each item (easier for an LLM than recursion).
7. The UI is PySide6 + QML. Ctrl+S saves; Ctrl+Enter formats in the background; Ctrl+R re-renders from the JSON.
8. Secrets only ever come from environment variables or `~/.config/school-notes/config.toml`, never from the repo.

## Milestones

### M1: Renderer and PDF ✅
- [x] Schema (14 element types)
- [x] Inline tags → LaTeX, with escaping
- [x] Renderers for every element, including the full document and preamble
- [x] XeLaTeX compile with readable errors
- [x] CLI: `school-notes render file.json`
- [x] Tests, plus a visual check of the all-elements fixture

### M2: LLM backends
- [x] System prompt (`prompt.md`) + a cleaned JSON-schema export for all backends
- [x] `claude_cli` backend, **the default** (`claude -p --json-schema`): uses the existing Claude Code login, so there are no API keys to manage or leak
- [ ] `ollama` backend (optional; `format: <schema>`, configurable URL, so it can reach the desktop over Tailscale)
- [x] Config file + backend selection
- [x] Messy Czech fixture notes (math, physics, chemistry, history) + opt-in live tests
- Dropped: a direct Claude API backend (it would need an API key; the CLI login covers it)

### M3: QML app ✅
- [x] Notes library: subjects = folders, dated lessons, auto-named from the title after formatting
- [x] Window in VL's style: sidebar | editor | PDF preview (own ListView of PdfPageImage)
- [x] Shortcuts: Ctrl+Enter / Ctrl+S / Ctrl+R / Ctrl+N / Ctrl+Shift+N
- [x] Background worker with status, offline-friendly errors; autosave; backups in .backup/
- [x] Preview keeps its scroll position on reload
- [x] Headless UI tests (fail on any Qt warning) + screenshot check

### M4: Later
- [ ] Per-section caching: only changed parts go to the LLM
- [ ] Automatic retry: send the compile error back to the LLM once
- [ ] Nicer graph styling, more element types if needed
- [ ] Packaging (AppImage) / a desktop launcher
- [ ] Rename and delete lessons/subjects from the sidebar
