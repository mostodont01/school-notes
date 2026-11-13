import datetime as dt
import shutil
from pathlib import Path

import pytest

from notes_app.config import Config
from notes_app.llm import LLMError
from notes_app.pipeline import load_document
from notes_app.ui import backend as backend_module
from notes_app.ui.backend import NotesBackend

FIXTURE = load_document(Path(__file__).parent / "fixtures" / "all_elements.json")
needs_tex = pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")


@pytest.fixture
def notes(tmp_path, qtbot):
    b = NotesBackend(Config(notes_dir=tmp_path / "Notes"))
    yield b
    b.shutdown()


def test_starts_empty_then_creates_subject_and_lesson(notes, tmp_path):
    assert notes.subjects == [] and notes.lessons == []
    assert notes.newSubject("Fyzika")
    assert notes.subjects == ["Fyzika"] and notes.currentSubject == "Fyzika"
    notes.newLesson()
    assert len(notes.lessons) == 1
    assert Path(notes.currentPath).name == f"{dt.date.today().isoformat()}.txt"


def test_edit_save_and_reload(notes):
    notes.newSubject("Fyzika")
    notes.newLesson()
    notes.edit("v = s/t")
    assert notes.dirty
    assert notes.save() and not notes.dirty
    assert Path(notes.currentPath).read_text() == "v = s/t"


def test_autosave(notes, qtbot):
    notes.newSubject("M")
    notes.newLesson()
    notes.edit("rychle poznamky")
    qtbot.waitUntil(lambda: not notes.dirty, timeout=4000)
    assert Path(notes.currentPath).read_text() == "rychle poznamky"


def test_switching_lessons_saves_first(notes):
    notes.newSubject("M")
    notes.newLesson()
    first = notes.currentPath
    notes.edit("prvni")
    notes.newLesson()
    assert Path(first).read_text() == "prvni"


@needs_tex
def test_format_writes_pdf_and_names_the_lesson(notes, qtbot, monkeypatch):
    monkeypatch.setattr(backend_module, "format_notes", lambda text, config: FIXTURE)
    notes.newSubject("Fyzika")
    notes.newLesson()
    notes.edit("pohyb ...")
    with qtbot.waitSignal(notes._jobFinished, timeout=60000):
        notes.format()
    assert notes.statusKind == "ok", notes.status
    assert not notes.busy
    assert Path(notes.currentPath).name.endswith("Pohyb a chemické reakce.txt")
    assert notes.pdfUrl.toLocalFile().endswith(".pdf") and Path(notes.pdfUrl.toLocalFile()).exists()
    assert notes.lessons[0]["state"] == "ok"

    # Re-render from the cached JSON, without the LLM.
    monkeypatch.setattr(backend_module, "format_notes", lambda *a: pytest.fail("LLM called"))
    revision = notes.pdfRevision
    with qtbot.waitSignal(notes._jobFinished, timeout=60000):
        notes.rerender()
    assert notes.pdfRevision == revision + 1


def test_offline_error_keeps_text(notes, qtbot, monkeypatch):
    def offline(text, config):
        raise LLMError("claude failed (exit 1): getaddrinfo ENOTFOUND api.anthropic.com")

    monkeypatch.setattr(backend_module, "format_notes", offline)
    notes.newSubject("M")
    notes.newLesson()
    notes.edit("poznamky v hodine")
    with qtbot.waitSignal(notes._jobFinished, timeout=10000):
        notes.format()
    assert notes.statusKind == "error" and "offline" in notes.status
    assert Path(notes.currentPath).read_text() == "poznamky v hodine"
    assert notes.pdfUrl.isEmpty()


def test_empty_lesson_is_not_sent(notes, monkeypatch):
    monkeypatch.setattr(backend_module, "format_notes", lambda *a: pytest.fail("LLM called"))
    notes.newSubject("M")
    notes.newLesson()
    notes.format()
    assert not notes.busy
