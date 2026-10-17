"""Pure-Python tests for the event helper and the error classes (run on any OS)."""
import contextlib
import io

import pytest

import baremacgui
from baremacgui import _events as ev
from baremacgui._options import check_align, check_grow, check_size


class Thing:
    on_click = ev.event()


def test_events_are_per_instance():
    a, b = Thing(), Thing()
    calls = []
    a.on_click(lambda: calls.append("a"))
    b.on_click.emit()
    assert calls == []
    a.on_click.emit()
    assert calls == ["a"]


def test_several_handlers_run_in_order_and_decorator_returns_handler():
    t, calls = Thing(), []

    @t.on_click
    def first():
        calls.append(1)

    t.on_click(lambda: calls.append(2))
    assert callable(first)
    t.on_click.emit()
    assert calls == [1, 2]


def test_assignment_replaces_and_none_clears():
    t, calls = Thing(), []
    t.on_click(lambda: calls.append("old"))
    t.on_click = lambda: calls.append("new")
    t.on_click.emit()
    assert calls == ["new"]
    t.on_click = None
    assert len(t.on_click) == 0


def test_non_callable_is_rejected():
    with pytest.raises(TypeError):
        Thing().on_click(3)


def test_exception_does_not_stop_other_handlers():
    t, calls = Thing(), []
    t.on_click(lambda: 1 / 0)
    t.on_click(lambda: calls.append("second"))
    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        t.on_click.emit()
    assert calls == ["second"]
    assert "ZeroDivisionError" in err.getvalue()


def test_error_hook_receives_exception():
    seen = []
    ev.set_error_hook(seen.append)
    try:
        t = Thing()
        t.on_click(lambda: 1 / 0)
        t.on_click.emit()
    finally:
        ev.set_error_hook(None)
    assert len(seen) == 1 and isinstance(seen[0], ZeroDivisionError)


def test_connect_options():
    t, calls = Thing(), []
    ev.connect_options(t, {"on_click": [lambda: calls.append(1), lambda: calls.append(2)]})
    t.on_click.emit()
    assert calls == [1, 2]
    ev.connect_options(t, {"on_click": None})
    with pytest.raises(TypeError):
        ev.connect_options(t, {"on_nothing": print})


def test_split_options():
    options = {"width": 3, "on_click": print, "on_change": None}
    handlers = ev.split_options(options)
    assert options == {"width": 3}
    assert set(handlers) == {"on_click", "on_change"}


def test_layout_errors_are_value_errors():
    for call in (lambda: check_grow(-1), lambda: check_size({"width": -2}), lambda: check_align("VBox", "nope")):
        with pytest.raises(baremacgui.LayoutError):
            call()
    assert issubclass(baremacgui.LayoutError, ValueError)
    assert issubclass(baremacgui.PlatformError, RuntimeError)
    assert issubclass(baremacgui.LayoutError, baremacgui.BareMacGUIError)
