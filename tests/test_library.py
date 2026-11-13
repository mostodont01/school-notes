import datetime as dt
import os

import pytest

from notes_app.library import Library, clean_name

DAY = dt.date(2026, 11, 13)


def test_clean_name_keeps_czech_and_drops_path_chars():
    assert clean_name("  Fyzika / Chemie: \"pohyb\"? ") == "Fyzika Chemie pohyb"
    assert clean_name("Dějepis") == "Dějepis"


def test_subjects_and_lessons(tmp_path):
    lib = Library(tmp_path / "Notes")
    assert lib.subjects() == []
    a = lib.new_lesson("Fyzika", "Pohyb", DAY)
    b = lib.new_lesson("Fyzika", "", dt.date(2026, 11, 20))
    lib.new_subject("chemie")
    assert lib.subjects() == ["chemie", "Fyzika"]          # case-insensitive order
    assert [l.path.name for l in lib.lessons("Fyzika")] == [b.path.name, a.path.name]  # newest first
    assert a.date == "2026-11-13" and a.topic == "Pohyb"
    assert b.topic == ""


def test_duplicate_names_get_a_number(tmp_path):
    lib = Library(tmp_path)
    first = lib.new_lesson("M", "Fce", DAY)
    second = lib.new_lesson("M", "Fce", DAY)
    assert second.path.name == "2026-11-13 Fce (2).txt" and first.path != second.path


def test_state(tmp_path):
    lesson = Library(tmp_path).new_lesson("M", "x", DAY)
    assert lesson.state == "none"
    lesson.pdf.write_bytes(b"%PDF")
    assert lesson.state == "ok"
    old = lesson.pdf.stat().st_mtime - 100
    os.utime(lesson.pdf, (old, old))
    assert lesson.state == "stale"


def test_rename_moves_generated_files(tmp_path):
    lib = Library(tmp_path)
    lesson = lib.new_lesson("M", "", DAY)
    lesson.pdf.write_bytes(b"%PDF")
    lesson.json.write_text("{}")
    renamed = lib.rename_lesson(lesson, "Kvadratická funkce")
    assert renamed.path.name == "2026-11-13 Kvadratická funkce.txt"
    assert renamed.pdf.exists() and renamed.json.exists()
    assert not lesson.path.exists() and not lesson.pdf.exists()


def test_empty_subject_rejected(tmp_path):
    with pytest.raises(ValueError):
        Library(tmp_path).new_subject(" / ")


def test_save_keeps_previous_version(tmp_path):
    lib = Library(tmp_path)
    lesson = lib.new_lesson("M", "x", DAY)
    lib.save_text(lesson, "first version")
    lib.save_text(lesson, "")            # e.g. a bug or select-all + delete
    lib.save_text(lesson, "new typing")  # the backup must survive this
    backup = lesson.path.parent / ".backup" / lesson.path.name
    assert backup.read_text() == "first version"
    assert lesson.path.read_text() == "new typing"
    assert [l.path.name for l in lib.lessons("M")] == [lesson.path.name]  # backups aren't lessons


def test_dotted_topic(tmp_path):
    lesson = Library(tmp_path).new_lesson("Dějepis", "1. světová válka", DAY)
    assert lesson.topic == "1. světová válka"
    assert lesson.pdf.name == "2026-11-13 1. světová válka.pdf"
