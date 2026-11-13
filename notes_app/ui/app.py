"""Start the app:  uv run school-notes-app"""

import sys
from pathlib import Path

from PySide6.QtCore import QLoggingCategory, QUrl
from PySide6.QtGui import QFontDatabase, QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from ..config import Config
from .backend import NotesBackend

QML_DIR = Path(__file__).parent / "qml"
ICON = Path(__file__).parent.parent / "assets" / "school-notes.svg"


def create_engine(notes: NotesBackend) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    # The engine owns the backend, so on shutdown the QML is destroyed first
    # and no binding ever sees a missing "notes" object.
    notes.setParent(engine)
    engine.rootContext().setContextProperty("notes", notes)
    engine.rootContext().setContextProperty(
        "monoFont", QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family())
    engine.load(QUrl.fromLocalFile(str(QML_DIR / "Main.qml")))
    return engine


def main(argv: list[str] | None = None, config: Config | None = None) -> int:
    # Same setup as VL: Fusion everywhere, quiet Wayland text-input warnings.
    QLoggingCategory.setFilterRules("qt.qpa.wayland.textinput=false")
    QQuickStyle.setStyle("Fusion")
    app = QGuiApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("School Notes")
    app.setDesktopFileName("school-notes")  # matches school-notes.desktop
    app.setWindowIcon(QIcon(str(ICON)))

    notes = NotesBackend(config)
    engine = create_engine(notes)
    if not engine.rootObjects():
        return 1
    app.aboutToQuit.connect(notes.shutdown)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
