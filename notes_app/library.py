"""The notes library: subjects are folders, lessons are .txt files in them.

    ~/School/Notes/
        Fyzika/
            2026-11-12 Pohyb.txt      <- what you write (the master copy)
            2026-11-12 Pohyb.json     <- generated
            2026-11-12 Pohyb.tex      <- generated
            2026-11-12 Pohyb.pdf      <- generated

No UI code here, so it is easy to test and script.
"""

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

GENERATED = (".json", ".tex", ".pdf")
_DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})\s*(.*)$")
_BAD_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def clean_name(name: str) -> str:
    """Make a string safe as a file or folder name (keeps Czech letters)."""
    name = _BAD_CHARS.sub(" ", name)
    return re.sub(r"\s+", " ", name).strip(" .")


@dataclass(frozen=True)
class Lesson:
    path: Path

    @property
    def date(self) -> str:
        m = _DATE_PREFIX.match(self.path.stem)
        return m.group(1) if m else ""

    @property
    def topic(self) -> str:
        m = _DATE_PREFIX.match(self.path.stem)
        return m.group(2) if m else self.path.stem

    @property
    def pdf(self) -> Path:
        return self.path.with_suffix(".pdf")

    @property
    def json(self) -> Path:
        return self.path.with_suffix(".json")

    @property
    def state(self) -> str:
        """'none' (never formatted), 'stale' (text changed since) or 'ok'."""
        if not self.pdf.exists():
            return "none"
        if self.path.exists() and self.path.stat().st_mtime > self.pdf.stat().st_mtime + 1:
            return "stale"
        return "ok"


class Library:
    def __init__(self, root: Path):
        self.root = Path(root).expanduser()

    def subjects(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted((p.name for p in self.root.iterdir()
                       if p.is_dir() and not p.name.startswith(".")), key=str.casefold)

    def lessons(self, subject: str) -> list[Lesson]:
        folder = self.root / subject
        if not folder.is_dir():
            return []
        # Newest first: names start with the date.
        return [Lesson(p) for p in sorted(folder.glob("*.txt"), key=lambda p: p.name, reverse=True)]

    def new_subject(self, name: str) -> str:
        name = clean_name(name)
        if not name:
            raise ValueError("Subject name is empty")
        (self.root / name).mkdir(parents=True, exist_ok=True)
        return name

    def new_lesson(self, subject: str, topic: str = "", date: dt.date | None = None) -> Lesson:
        folder = self.root / self.new_subject(subject)
        stem = (date or dt.date.today()).isoformat()
        if clean_name(topic):
            stem += " " + clean_name(topic)
        path = _unique(folder, stem)
        path.write_text("", encoding="utf-8")
        return Lesson(path)

    def rename_lesson(self, lesson: Lesson, topic: str) -> Lesson:
        """Change the topic part of the name; generated siblings move along."""
        stem = (lesson.date + " " if lesson.date else "") + clean_name(topic)
        if not clean_name(topic) or stem == lesson.path.stem:
            return lesson
        new = _unique(lesson.path.parent, stem.strip())
        for ext in (".txt", *GENERATED):
            old = lesson.path.with_suffix(ext)
            if old.exists():
                old.rename(new.with_suffix(ext))
        return Lesson(new)


def _unique(folder: Path, stem: str) -> Path:
    path, n = folder / f"{stem}.txt", 2
    while path.exists():
        path, n = folder / f"{stem} ({n}).txt", n + 1
    return path
