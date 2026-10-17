"""Control and layout tests. They build real AppKit views, so they run on macOS only.

Windows are created with visible=False and never run an event loop.
"""
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="needs macOS and PyObjC")

if sys.platform == "darwin":
    from baremacgui import (
        Button, CheckBox, ComboBox, GroupBox, HBox, Label, SpinBox, Spacer, Tab, TabControl, TextBox, VBox, Window,
    )
    from baremacgui import _core


@pytest.fixture(autouse=True)
def clean_stack():
    _core._stack.clear()
    yield
    assert not _core._stack, "a with-block was left open"
    _core._stack.clear()


def build(*make):
    """Build a window around the given factory, return what the factory returned."""
    result = {}
    with Window("test", visible=False):
        with VBox(padding=8) as box:
            for name, factory in make:
                result[name] = factory()
    result["vbox"] = box  # own key: a factory named "box" must not collide with it
    return result


def test_label_text_roundtrip():
    r = build(("label", lambda: Label("a")))
    r["label"].text = "b"
    assert r["label"].text == "b"


def test_textbox_single_line():
    r = build(("box", lambda: TextBox("x", placeholder="p")))
    assert r["box"].text == "x"
    r["box"].text = "y"
    assert r["box"].text == "y"


def test_textbox_multiline_append_and_readonly():
    r = build(("box", lambda: TextBox("a", multiline=True, readonly=True)))
    r["box"].append("b")
    assert r["box"].text == "ab"
    assert r["box"].readonly


def test_textbox_rejects_mixed_options():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(TypeError):
                TextBox(multiline=True, password=True)


def test_combobox_selection():
    r = build(("combo", lambda: ComboBox(["a", "b", "c"], selected=1)))
    combo = r["combo"]
    assert combo.text == "b" and combo.index == 1
    combo.index = 2
    assert combo.text == "c"
    combo.items = ["x", "y"]
    assert combo.items == ["x", "y"]


def test_checkbox_state():
    r = build(("check", lambda: CheckBox("c", checked=True)))
    assert r["check"].checked
    r["check"].checked = False
    assert not r["check"].checked


def test_spinbox_clamps_and_reads_value():
    r = build(("spin", lambda: SpinBox(5, minimum=0, maximum=10)))
    spin = r["spin"]
    spin.value = 99
    assert spin.value == 10
    spin.value = -4
    assert spin.value == 0


def test_button_title_and_enabled():
    r = build(("button", lambda: Button("go")))
    r["button"].title = "stop"
    r["button"].enabled = False
    assert r["button"].title == "stop" and not r["button"].enabled


def test_control_outside_window_raises():
    with pytest.raises(RuntimeError, match="inside a `with Window"):
        Label("x")


def test_window_takes_one_child():
    with pytest.raises(ValueError, match="exactly one child"):
        with Window("test", visible=False):
            Label("a")
            Label("b")


def test_groupbox_takes_one_child():
    with pytest.raises(ValueError, match="exactly one child"):
        with Window("test", visible=False):
            with VBox():
                with GroupBox("g"):
                    Label("a")
                    Label("b")


def test_tab_outside_tabcontrol_raises():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(RuntimeError, match="TabControl"):
                with Tab("t"):
                    pass


def test_tabcontrol_rejects_direct_children():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError, match="Tab"):
                with TabControl():
                    Label("a")


def test_tabs_selection():
    with Window("test", visible=False):
        with VBox():
            with TabControl() as tabs:
                with Tab("one"):
                    with VBox():
                        Label("1")
                with Tab("two"):
                    with VBox():
                        Label("2")
    assert tabs.selected == 0
    tabs.selected = 1
    assert tabs.selected == 1


def test_box_adds_filler_only_without_grow():
    r = build(("a", lambda: Label("a")), ("b", lambda: Button("b")))
    assert r["vbox"].ns.arrangedSubviews().count() == 3  # two children + filler
    with Window("test", visible=False):
        with HBox() as row:
            Label("a")
            Spacer()
    assert row.ns.arrangedSubviews().count() == 2


def test_exception_in_block_leaves_no_open_container():
    with pytest.raises(KeyError):
        with Window("test", visible=False):
            with VBox():
                raise KeyError("boom")
    assert not _core._stack
