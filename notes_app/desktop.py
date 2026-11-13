"""Add School Notes to the Linux app menu (for the current user).

    school-notes install-desktop      # menu entry + icon
    school-notes install-desktop --uninstall

The entry starts the app with this checkout's Python, so no terminal and no
uv are needed. Run it again if the project folder moves.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_ID = "school-notes"  # = QGuiApplication.desktopFileName, so the window matches the entry
ICON = Path(__file__).parent / "assets" / "school-notes.svg"


def data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def desktop_file() -> Path:
    return data_home() / "applications" / f"{APP_ID}.desktop"


def icon_file() -> Path:
    return data_home() / "icons" / "hicolor" / "scalable" / "apps" / f"{APP_ID}.svg"


def desktop_entry(python: str, workdir: Path) -> str:
    return f"""[Desktop Entry]
Type=Application
Name=School Notes
GenericName=Note taking
Comment=Messy notes in, clean PDF out
Exec="{python}" -m notes_app.ui.app
Path={workdir}
Icon={APP_ID}
Terminal=false
Categories=Office;
Keywords=notes;school;poznámky;škola;PDF;LaTeX;Claude;
StartupWMClass={APP_ID}
StartupNotify=true
"""


def _refresh() -> None:
    for cmd in (["update-desktop-database", str(desktop_file().parent)],
                ["gtk-update-icon-cache", "-q", "-t", str(data_home() / "icons" / "hicolor")]):
        if shutil.which(cmd[0]):
            subprocess.run(cmd, capture_output=True)


def install(python: str | None = None, workdir: Path | None = None) -> Path:
    python = python or sys.executable
    workdir = workdir or Path(__file__).resolve().parent.parent
    desktop_file().parent.mkdir(parents=True, exist_ok=True)
    icon_file().parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ICON, icon_file())
    desktop_file().write_text(desktop_entry(python, workdir), encoding="utf-8")
    _refresh()
    return desktop_file()


def uninstall() -> None:
    desktop_file().unlink(missing_ok=True)
    icon_file().unlink(missing_ok=True)
    _refresh()
