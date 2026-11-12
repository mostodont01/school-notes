from pathlib import Path

from notes_app.render import render_document
from notes_app.render.list import list_block
from notes_app.render.table import table
from notes_app.schema import Document, ListBlock, ListItem, Table

FIXTURES = Path(__file__).parent / "fixtures"


def test_nested_list():
    block = ListBlock(type="list", ordered=False, items=[
        ListItem(text="a", level=0), ListItem(text="b", level=1),
        ListItem(text="c", level=0),
    ])
    out = list_block(block)
    assert out.count(r"\begin{itemize}") == 2
    assert out.count(r"\end{itemize}") == 2
    assert out.index(r"\item b") < out.index(r"\item c")


def test_list_level_jump_is_clamped():
    block = ListBlock(type="list", ordered=True, items=[ListItem(text="a", level=3)])
    assert list_block(block).count(r"\begin{enumerate}") == 1


def test_table_pads_short_rows():
    out = table(Table(type="table", headers=["A", "B", "C"], rows=[["1"]]))
    assert r"1 &  &  \\" in out


def test_full_document_renders_every_block():
    doc = Document.model_validate_json((FIXTURES / "all_elements.json").read_text())
    tex = render_document(doc)
    assert tex.startswith(r"\documentclass")
    assert tex.rstrip().endswith(r"\end{document}")
    for snippet in [r"\section*", r"\ce{2 H2 + O2 -> 2 H2O}", r"\chemfig", r"\begin{tcolorbox}",
                    r"\begin{axis}", r"\begin{lstlisting}[language=Python]", r"\begin{tabularx}"]:
        assert snippet in tex


def test_render_is_deterministic():
    doc = Document.model_validate_json((FIXTURES / "all_elements.json").read_text())
    assert render_document(doc) == render_document(doc)
