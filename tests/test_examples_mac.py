"""Run every example up to (not including) app.run() and test the pure helpers they define.

macOS only: the examples build real windows. Windows stay hidden and no event loop runs.
"""
import datetime as dt
import runpy
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="needs macOS and PyObjC")

EXAMPLES = sorted((Path(__file__).resolve().parent.parent / "examples").glob("[0-9][0-9]_*.py"))


@pytest.fixture
def headless(monkeypatch):
    """No event loop, no visible windows, no network."""
    import baremacgui
    from baremacgui import _core

    _core._stack.clear()
    monkeypatch.setattr(baremacgui.App, "run", lambda self: None)
    original = baremacgui.Window.__init__

    def hidden(self, *args, **kwargs):
        kwargs["visible"] = False
        original(self, *args, **kwargs)

    monkeypatch.setattr(baremacgui.Window, "__init__", hidden)
    yield
    _core._stack.clear()


def run_example(path):
    return runpy.run_path(str(path), run_name="example")


def test_there_are_examples():
    assert len(EXAMPLES) >= 14


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.stem)
def test_example_builds(headless, path):
    namespace = run_example(path)
    assert "app" in namespace or "App" in namespace


def example(name):
    return next(path for path in EXAMPLES if path.stem == name)


def test_editor_helpers_and_menu(headless):
    ns = run_example(example("07_editor"))
    assert ns["summary"]("") == "0 characters, 0 words"
    assert ns["summary"]("a b") == "3 characters, 2 words"
    assert ns["summary"]("x") == "1 character, 1 word"
    assert ns["win"].title == "Untitled - Editor"
    ns["editor"].on_change.emit()
    assert ns["win"].title == "* Untitled - Editor"


def test_form_validation_and_button_state(headless):
    ns = run_example(example("08_form"))
    validate = ns["validate"]
    today = dt.date(2026, 1, 1)
    assert "name" in validate("", "a@b.de", "12345678", True, None, today)
    assert "e-mail" in validate("A", "nope", "12345678", True, None, today)
    assert "8" in validate("A", "a@b.de", "123", True, None, today)
    assert "future" in validate("A", "a@b.de", "12345678", True, dt.date(2030, 1, 1), today)
    assert "terms" in validate("A", "a@b.de", "12345678", False, None, today)
    assert validate("A", "a@b.de", "12345678", True, None, today) is None
    assert not ns["submit"].enabled  # an empty form cannot be submitted
    ns["name"].text, ns["email"].text, ns["password"].text = "Ada", "ada@example.com", "longenough"
    ns["terms"].checked = True
    ns["refresh"]()
    assert ns["submit"].enabled and ns["problem"].text == ""


def test_progress_helper(headless):
    ns = run_example(example("09_progress"))
    assert ns["format_elapsed"](0) == "0:00"
    assert ns["format_elapsed"](65.4) == "1:05"
    assert not ns["cancel"].enabled


def test_drop_example_collects_files(headless, tmp_path):
    ns = run_example(example("13_drop"))
    assert ns["human_size"](0) == "0 bytes"
    assert ns["human_size"](1536) == "1.5 KB"
    assert ns["human_size"](5 * 1024 ** 2) == "5.0 MB"
    note = tmp_path / "note.txt"
    note.write_bytes(b"x" * 2048)
    assert ns["zone"]._drop([str(note), str(tmp_path)])
    rows = ns["table"].rows
    assert [r[0] for r in rows] == ["note.txt", tmp_path.name] and rows[0][1] == "2.0 KB" and rows[1][1] == ""
    assert ns["summary"].text == "2 item(s)"
    ns["clear"].on_click.emit()
    assert ns["table"].rows == [] and ns["summary"].text == "Nothing dropped yet"
