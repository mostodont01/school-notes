"""Document -> complete LaTeX source. Deterministic: same Document, same .tex."""

from collections.abc import Callable
from pathlib import Path

from ..schema import Document
from .callout import callout
from .code import code
from .equation import equation
from .graph import bar_chart, function_graph, line_chart, pie_chart
from .heading import heading
from .inline import inline
from .list import list_block
from .paragraph import paragraph
from .reaction import reaction
from .rule import rule
from .structure import structure
from .table import table

RENDERERS: dict[str, Callable] = {
    "heading": heading,
    "paragraph": paragraph,
    "list": list_block,
    "table": table,
    "code": code,
    "rule": rule,
    "equation": equation,
    "reaction": reaction,
    "structure": structure,
    "callout": callout,
    "function_graph": function_graph,
    "bar_chart": bar_chart,
    "line_chart": line_chart,
    "pie_chart": pie_chart,
}

PREAMBLE = (Path(__file__).parent / "preamble.tex").read_text(encoding="utf-8")


def render_body(doc: Document) -> str:
    parts = [RENDERERS[block.type](block) for block in doc.blocks]
    return "\n\n".join(p for p in parts if p) + "\n"


def _title_block(doc: Document) -> str:
    meta = " \\hfill ".join(inline(x) for x in (doc.subject, doc.date) if x.strip())
    lines = []
    if meta:
        lines.append(f"{{\\small\\color{{gray}} {meta}}}\\par")
    if doc.title.strip():
        lines.append(f"{{\\LARGE\\bfseries {inline(doc.title)}}}\\par")
    if lines:
        lines.append(r"\vspace{2pt}\noindent\rule{\linewidth}{0.8pt}")
    return "\n".join(lines)


def render_document(doc: Document) -> str:
    title = _title_block(doc)
    return (
        PREAMBLE
        + "\n\\begin{document}\n\n"
        + (title + "\n\n" if title else "")
        + render_body(doc)
        + "\n\\end{document}\n"
    )
