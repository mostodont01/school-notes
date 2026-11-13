import configparser
import os

from notes_app import desktop


def test_install_and_uninstall(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = desktop.install(python="/x/.venv/bin/python", workdir=tmp_path / "repo")
    entry = configparser.ConfigParser(interpolation=None)
    entry.read(path, encoding="utf-8")
    e = entry["Desktop Entry"]
    assert e["Name"] == "School Notes" and e["Terminal"] == "false"
    assert e["Exec"] == '"/x/.venv/bin/python" -m notes_app.ui.app'
    assert e["Icon"] == e["StartupWMClass"] == "school-notes"
    assert desktop.icon_file().read_bytes() == desktop.ICON.read_bytes()
    desktop.uninstall()
    assert not path.exists() and not desktop.icon_file().exists()


def test_icon_is_a_valid_svg(qtbot):
    from PySide6.QtSvg import QSvgRenderer
    assert QSvgRenderer(str(desktop.ICON)).isValid()


def test_find_claude_falls_back_to_local_bin(tmp_path, monkeypatch):
    from notes_app.llm import claude_cli
    monkeypatch.setenv("PATH", "/nonexistent")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert claude_cli.find_claude() is None
    binary = tmp_path / ".local" / "bin" / "claude"
    binary.parent.mkdir(parents=True)
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    assert claude_cli.find_claude() == str(binary)
