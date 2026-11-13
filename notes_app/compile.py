"""Run XeLaTeX on a .tex file and report errors in a readable form."""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CompileResult:
    ok: bool
    pdf: Path | None = None
    errors: list[str] = field(default_factory=list)
    log: str = ""


def _errors_from_log(log: str) -> list[str]:
    """Each LaTeX error starts with '!' and is followed by the 'l.<n>' line."""
    errors = []
    lines = log.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("!"):
            where = next((l.strip() for l in lines[i + 1:i + 12] if l.startswith("l.")), "")
            errors.append(f"{line[1:].strip()} {where}".strip())
    return errors


def compile_tex(tex_path: Path, timeout: float = 90) -> CompileResult:
    """Compile tex_path; on success the PDF is written next to it."""
    if shutil.which("xelatex") is None:
        return CompileResult(False, errors=["xelatex is not installed"])
    tex_path = tex_path.resolve()
    # Compile a copy with a plain name: TeX copes badly with spaces, dots and
    # non-ASCII letters in file names ("2026-11-09 1. světová válka.tex").
    with tempfile.TemporaryDirectory(prefix="school-notes-") as tmp:
        work = Path(tmp) / "doc.tex"
        shutil.copyfile(tex_path, work)
        try:
            proc = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "doc.tex"],
                cwd=tmp, capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(False, errors=[f"xelatex timed out after {timeout:.0f} s"])
        log_file = Path(tmp) / "doc.log"
        log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() \
            else proc.stdout.decode(errors="replace")
        built = Path(tmp) / "doc.pdf"
        if proc.returncode != 0 or not built.exists():
            return CompileResult(False, errors=_errors_from_log(log) or ["xelatex failed"], log=log)
        pdf = tex_path.parent / (tex_path.stem + ".pdf")
        tmp_pdf = pdf.parent / (pdf.name + ".tmp")
        shutil.copyfile(built, tmp_pdf)
        tmp_pdf.replace(pdf)  # atomic, so the preview never reads half a file
        return CompileResult(True, pdf=pdf, log=log)
