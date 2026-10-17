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
    assert len(EXAMPLES) >= 10


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
