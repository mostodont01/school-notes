"""Live tests: real LLM calls on messy notes. Opt-in: uv run pytest -m live

They check what can be checked automatically: the reply validates, every
element renders and the PDF compiles. Faithfulness (nothing invented or
lost) still needs a human or Claude reading the PDFs, which this test keeps
in tests/fixtures/live-out/.
"""

import shutil
from pathlib import Path

import pytest

from notes_app.llm import format_notes
from notes_app.pipeline import build_pdf, save_document

FIXTURES = Path(__file__).parent / "fixtures"
OUT = FIXTURES / "live-out"
NOTES = sorted(FIXTURES.glob("*_messy.txt"))

pytestmark = pytest.mark.live


@pytest.mark.parametrize("txt", NOTES, ids=[p.stem for p in NOTES])
def test_format_and_compile(txt: Path):
    doc = format_notes(txt.read_text(encoding="utf-8"))
    assert doc.blocks, "empty document"
    OUT.mkdir(exist_ok=True)
    base = OUT / txt.stem
    save_document(doc, base.with_suffix(".json"))
    result = build_pdf(doc, base)
    assert result.ok, result.errors
