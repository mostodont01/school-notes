"""File-level steps. For lesson.txt the siblings are lesson.json, .tex and .pdf."""

from pathlib import Path

from .compile import CompileResult, compile_tex
from .render import render_document
from .schema import Document


def load_document(json_path: Path) -> Document:
    return Document.model_validate_json(json_path.read_text(encoding="utf-8"))


def save_document(doc: Document, json_path: Path) -> None:
    json_path.write_text(doc.model_dump_json(indent=2) + "\n", encoding="utf-8")


def build_pdf(doc: Document, base: Path) -> CompileResult:
    """Write base.tex from the document and compile it to base.pdf."""
    tex = base.with_suffix(".tex")
    tex.write_text(render_document(doc), encoding="utf-8")
    return compile_tex(tex)
