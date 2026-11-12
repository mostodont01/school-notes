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
    with tempfile.TemporaryDirectory(prefix="school-notes-") as tmp:
        try:
            proc = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                 "-output-directory", tmp, str(tex_path)],
                cwd=tex_path.parent, capture_output=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(False, errors=[f"xelatex timed out after {timeout:.0f} s"])
        log_file = Path(tmp) / (tex_path.stem + ".log")
        log = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() \
            else proc.stdout.decode(errors="replace")
        built = Path(tmp) / (tex_path.stem + ".pdf")
        if proc.returncode != 0 or not built.exists():
            return CompileResult(False, errors=_errors_from_log(log) or ["xelatex failed"], log=log)
        pdf = tex_path.with_suffix(".pdf")
        shutil.copyfile(built, pdf)
        return CompileResult(True, pdf=pdf, log=log)
