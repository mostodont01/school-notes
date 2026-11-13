"""Headless QML tests: the window loads without warnings and the controls work."""

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QtMsgType, qInstallMessageHandler
from PySide6.QtQuickControls2 import QQuickStyle

from notes_app.config import Config
from notes_app.pipeline import build_pdf, load_document
from notes_app.ui.app import create_engine
from notes_app.ui.backend import NotesBackend

FIXTURE = Path(__file__).parent / "fixtures" / "all_elements.json"


@pytest.fixture
def ui(tmp_path, qtbot):
    QQuickStyle.setStyle("Fusion")
    notes = NotesBackend(Config(notes_dir=tmp_path / "Notes"))
    warnings = []
    engine = None

    # Catch every Qt warning, not only the engine's: some QML problems
    # (e.g. deprecated handler parameters, PdfDocument errors) only log.
    def handler(kind, context, message):
        if kind != QtMsgType.QtDebugMsg:
            warnings.append(message)
    previous = qInstallMessageHandler(handler)

    def start():
        nonlocal engine
        engine = create_engine(notes)
        engine.warnings.connect(lambda ws: warnings.extend(w.toString() for w in ws))
        assert engine.rootObjects(), "Main.qml failed to load"
        return engine.rootObjects()[0]

    yield notes, start, warnings
    qInstallMessageHandler(previous)
    notes.shutdown()
    if engine:
        engine.deleteLater()  # also deletes notes (its child), after the QML
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert warnings == [], warnings


def find(root, name):
    item = root.findChild(QObject, name)
    assert item is not None, name
    return item


def test_loads_without_warnings_when_empty(ui, qtbot):
    notes, start, warnings = ui
    start()
    qtbot.wait(200)
    assert warnings == []


def test_editor_typing_reaches_backend(ui, qtbot):
    notes, start, warnings = ui
    notes.newSubject("Fyzika")
    notes.newLesson()
    root = start()
    editor = find(root, "editor")
    editor.setProperty("text", "v = s/t")
    assert notes.dirty
    assert notes.save()
    assert Path(notes.currentPath).read_text() == "v = s/t"
    # Switching lessons loads the other text into the editor.
    notes.newLesson()
    assert editor.property("text") == ""
    assert warnings == []


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_pdf_preview_shows_pages(ui, qtbot):
    notes, start, warnings = ui
    notes.newSubject("Fyzika")
    notes.newLesson()
    result = build_pdf(load_document(FIXTURE), Path(notes.currentPath).with_suffix(""))
    assert result.ok
    notes.openLesson(notes.currentPath)
    root = start()
    pages = find(root, "pdfPages")
    qtbot.waitUntil(lambda: pages.property("count") >= 4, timeout=10000)
    assert warnings == []


def test_opening_does_not_overwrite_notes(tmp_path, ui, qtbot):
    """Regression: the editor's empty start value was autosaved over the file."""
    notes, start, warnings = ui
    notes.newSubject("Fyzika")
    notes.newLesson()
    notes.edit("důležité poznámky")
    notes.save()
    path = Path(notes.currentPath)
    notes.openLesson(str(path))  # as if the app was just started on it
    root = start()
    assert find(root, "editor").property("text") == "důležité poznámky"
    qtbot.wait(2500)  # longer than the autosave delay
    assert path.read_text() == "důležité poznámky"
    assert not notes.dirty


@pytest.mark.skipif(shutil.which("xelatex") is None, reason="xelatex not installed")
def test_pdf_reload_and_lesson_without_pdf(ui, qtbot):
    notes, start, warnings = ui
    notes.newSubject("Fyzika")
    notes.newLesson()
    with_pdf = notes.currentPath
    assert build_pdf(load_document(FIXTURE), Path(with_pdf).with_suffix("")).ok
    notes.openLesson(with_pdf)
    root = start()
    pages = find(root, "pdfPages")
    qtbot.waitUntil(lambda: pages.property("count") >= 4, timeout=10000)

    # Same file rebuilt: the view reloads it (new revision), still visible.
    notes._pdf_revision += 1
    notes.pdfChanged.emit()
    qtbot.waitUntil(lambda: pages.property("count") >= 4 and pages.property("visible"), timeout=10000)

    # A lesson without a PDF hides the preview instead of showing the old one.
    notes.newLesson()
    qtbot.waitUntil(lambda: not pages.property("visible"), timeout=5000)
