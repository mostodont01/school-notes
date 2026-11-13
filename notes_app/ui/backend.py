"""The bridge between QML and the pipeline. All logic lives here or below;
the QML only shows state and calls slots.

Slow work (LLM, XeLaTeX) runs on one worker thread, so the UI never blocks.
A job remembers which lesson it belongs to: switching lessons while it runs
is fine, and its result is applied to the right files.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot

from ..config import Config, load_config
from ..library import Lesson, Library
from ..llm import LLMError, format_notes
from ..pipeline import build_pdf, load_document, save_document

_OFFLINE_HINTS = ("enotfound", "econnrefused", "network", "getaddrinfo", "connection", "offline", "timed out")


def _friendly(error: Exception) -> str:
    text = str(error)
    if any(h in text.lower() for h in _OFFLINE_HINTS):
        return "Can't reach Claude (offline?). Your notes are saved; format them later with Ctrl+Enter."
    return text.strip().splitlines()[0][:300] if text.strip() else type(error).__name__


class NotesBackend(QObject):
    subjectsChanged = Signal()
    lessonsChanged = Signal()
    currentChanged = Signal()
    textLoaded = Signal(str)          # new text for the editor
    dirtyChanged = Signal()
    busyChanged = Signal()
    statusChanged = Signal()
    pdfChanged = Signal()
    _jobFinished = Signal(object)     # emitted from the worker thread

    def __init__(self, config: Config | None = None, parent=None):
        super().__init__(parent)
        self._config = config or load_config()
        self._library = Library(self._config.notes_dir)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._subject = ""
        self._lesson: Lesson | None = None
        self._text = ""
        self._dirty = False
        self._busy = False
        self._status = ""
        self._status_kind = "info"
        self._pdf_revision = 0
        self._jobFinished.connect(self._on_job_finished)

        # Autosave: a crash or a closed lid must never lose class notes.
        self._autosave = QTimer(self, singleShot=True, interval=1500)
        self._autosave.timeout.connect(self.save)

        subjects = self._library.subjects()
        if subjects:
            self.selectSubject(subjects[0])

    # -- properties ---------------------------------------------------------

    @Property(str, constant=True)
    def notesDir(self):
        return str(self._library.root)

    @Property("QStringList", notify=subjectsChanged)
    def subjects(self):
        return self._library.subjects()

    @Property(str, notify=currentChanged)
    def currentSubject(self):
        return self._subject

    @Property("QVariantList", notify=lessonsChanged)
    def lessons(self):
        return [
            {"path": str(l.path), "topic": l.topic or "(untitled)", "date": l.date, "state": l.state}
            for l in self._library.lessons(self._subject)
        ] if self._subject else []

    @Property(str, notify=currentChanged)
    def currentPath(self):
        return str(self._lesson.path) if self._lesson else ""

    @Property(str, notify=currentChanged)
    def currentTitle(self):
        if not self._lesson:
            return ""
        return f"{self._lesson.topic or '(untitled)'}  ·  {self._lesson.date}".strip(" ·")

    @Property(str, notify=currentChanged)
    def text(self):
        """The current lesson's text (the editor reads it once when created)."""
        return self._text

    @Property(bool, notify=dirtyChanged)
    def dirty(self):
        return self._dirty

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property(str, notify=statusChanged)
    def statusKind(self):
        return self._status_kind

    @Property(QUrl, notify=pdfChanged)
    def pdfUrl(self):
        if self._lesson and self._lesson.pdf.exists():
            return QUrl.fromLocalFile(str(self._lesson.pdf))
        return QUrl()

    @Property(int, notify=pdfChanged)
    def pdfRevision(self):
        """Bumped whenever the PDF file is rewritten, so the view reloads it."""
        return self._pdf_revision

    # -- navigation ---------------------------------------------------------

    @Slot(str)
    def selectSubject(self, name: str):
        self.save()
        self._subject = name
        lessons = self._library.lessons(name)
        self._open(lessons[0] if lessons else None)
        self.lessonsChanged.emit()

    @Slot(str)
    def openLesson(self, path: str):
        self.save()
        self._open(Lesson(Path(path)))

    @Slot(str, result=bool)
    def newSubject(self, name: str) -> bool:
        try:
            name = self._library.new_subject(name)
        except ValueError as e:
            self._set_status(str(e), "error")
            return False
        self.subjectsChanged.emit()
        self.selectSubject(name)
        return True

    @Slot()
    def newLesson(self):
        if not self._subject:
            self._set_status("Create a subject first (Ctrl+Shift+N).", "error")
            return
        self.save()
        self._open(self._library.new_lesson(self._subject))
        self.lessonsChanged.emit()
        self._set_status("New lesson. It gets its name from the title after formatting.", "info")

    def _open(self, lesson: Lesson | None):
        self._lesson = lesson
        self._text = lesson.path.read_text(encoding="utf-8") if lesson and lesson.path.exists() else ""
        self._set_dirty(False)
        self.currentChanged.emit()
        self.textLoaded.emit(self._text)
        self.pdfChanged.emit()

    # -- editing ------------------------------------------------------------

    @Slot(str)
    def edit(self, text: str):
        """Called by the editor on every change."""
        if text == self._text:
            return
        self._text = text
        self._set_dirty(True)
        self._autosave.start()

    @Slot(result=bool)
    def save(self) -> bool:
        self._autosave.stop()
        if not self._lesson or not self._dirty:
            return True
        try:
            self._library.save_text(self._lesson, self._text)
        except OSError as e:
            self._set_status(f"Saving failed: {e}", "error")
            return False
        self._set_dirty(False)
        self.lessonsChanged.emit()  # state may turn "stale"
        return True

    # -- formatting ---------------------------------------------------------

    @Slot()
    def format(self):
        if not self._lesson or self._busy or not self.save():
            return
        if not self._text.strip():
            self._set_status("Nothing to format yet.", "info")
            return
        self._start("Formatting with Claude…", "format", self._lesson, self._text)

    @Slot()
    def rerender(self):
        if not self._lesson or self._busy:
            return
        if not self._lesson.json.exists():
            self._set_status("Nothing to re-render: format the lesson first (Ctrl+Enter).", "info")
            return
        self._start("Rendering…", "render", self._lesson, None)

    def _start(self, message: str, kind: str, lesson: Lesson, text: str | None):
        self._set_busy(True)
        self._set_status(message, "busy")
        future = self._executor.submit(self._run_job, kind, lesson, text, self._config)
        future.add_done_callback(lambda f: self._jobFinished.emit(f.result()))

    @staticmethod
    def _run_job(kind: str, lesson: Lesson, text: str | None, config: Config) -> dict:
        """Runs on the worker thread. Never raises: returns a result dict."""
        try:
            if kind == "format":
                doc = format_notes(text, config)
                save_document(doc, lesson.json)
            else:
                doc = load_document(lesson.json)
            result = build_pdf(doc, lesson.path.with_suffix(""))
            return {"lesson": lesson, "title": doc.title, "ok": result.ok,
                    "error": "; ".join(result.errors[:2]) if not result.ok else ""}
        except (LLMError, OSError, ValueError) as e:
            return {"lesson": lesson, "title": "", "ok": False, "error": _friendly(e)}

    def _on_job_finished(self, result: dict):
        self._set_busy(False)
        lesson: Lesson = result["lesson"]
        if result["ok"]:
            # Untitled lessons take their name from the document title.
            if not lesson.topic and result["title"].strip():
                renamed = self._library.rename_lesson(lesson, result["title"])
                if self._lesson and self._lesson.path == lesson.path:
                    self._lesson = renamed
                    self.currentChanged.emit()
            self._pdf_revision += 1
            self._set_status("PDF updated.", "ok")
        else:
            self._set_status(f"Failed: {result['error']}", "error")
        self.lessonsChanged.emit()
        self.pdfChanged.emit()

    # -- helpers ------------------------------------------------------------

    def _set_dirty(self, value: bool):
        if value != self._dirty:
            self._dirty = value
            self.dirtyChanged.emit()

    def _set_busy(self, value: bool):
        if value != self._busy:
            self._busy = value
            self.busyChanged.emit()

    def _set_status(self, text: str, kind: str):
        self._status, self._status_kind = text, kind
        self.statusChanged.emit()

    def shutdown(self):
        self.save()
        self._executor.shutdown(wait=False, cancel_futures=True)
