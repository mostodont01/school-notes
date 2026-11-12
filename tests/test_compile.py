import os
import shutil
from pathlib import Path

import pytest

from notes_app.pipeline import build_pdf, load_document

FIXTURES = Path(__file__).parent / "fixtures"


# In CI the compile must really run, so it is never skipped there.
@pytest.mark.skipif(shutil.which("xelatex") is None and not os.environ.get("CI"),
                    reason="xelatex not installed")
def test_all_elements_compile(tmp_path):
    doc = load_document(FIXTURES / "all_elements.json")
    result = build_pdf(doc, tmp_path / "all_elements")
    assert result.ok, result.errors
    assert result.pdf.stat().st_size > 10_000
