"""Control and layout tests. They build real AppKit views, so they run on macOS only.

Windows are created with visible=False and never run an event loop.
"""
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="needs macOS and PyObjC")

if sys.platform == "darwin":
    from baremacgui import (
        Button, CheckBox, ComboBox, DropDown, GroupBox, HBox, Image, Label, ListBox, ProgressBar, RadioGroup,
        SearchField, SegmentedControl, Separator, Slider, SpinBox, Spacer, Tab, TabControl, Table, TextBox, Toolbar,
        VBox, Window,
    )
    from baremacgui import Custom, IconGrid, Page, Popover, Sheet, Sidebar, Tree
    from baremacgui import show_info
    from baremacgui import ContextMenu, DatePicker, Menu, MenuBar, MenuItem, MenuSeparator, Timer, TimePicker
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


def test_radiogroup_selection():
    radio = build(("radio", lambda: RadioGroup(["a", "b", "c"], selected=1)))["radio"]
    assert radio.index == 1 and radio.text == "b"
    radio.index = 2
    assert radio.index == 2 and radio.text == "c"
    with pytest.raises(ValueError):
        radio.index = 5


def test_radiogroup_needs_two_items():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError):
                RadioGroup(["only"])


def test_dropdown():
    dropdown = build(("dd", lambda: DropDown(["x", "y"], selected=1)))["dd"]
    assert dropdown.text == "y" and dropdown.index == 1
    dropdown.items = ["a", "b", "c"]
    assert dropdown.items == ["a", "b", "c"]
    dropdown.index = 2
    assert dropdown.text == "c"


def test_slider_clamps():
    slider = build(("s", lambda: Slider(10, minimum=0, maximum=20)))["s"]
    assert slider.value == 10.0
    slider.value = 99
    assert slider.value == 20.0


def test_progressbar_value_and_no_enabled():
    bar = build(("p", lambda: ProgressBar(5, maximum=10)))["p"]
    bar.value = 7
    assert bar.value == 7.0
    with pytest.raises(TypeError):
        bar.enabled = False


def test_image_symbol_and_errors():
    image = build(("img", lambda: Image(symbol="gearshape", width=16, height=16)))["img"]
    assert image.ns is not None
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(FileNotFoundError):
                Image(path="/nonexistent/picture.png")
            with pytest.raises(ValueError):
                Image()


def test_separator_is_added():
    box = build(("sep", Separator))["vbox"]
    assert box.ns.arrangedSubviews().count() == 2  # separator + filler


def test_listbox_selection_and_items():
    listbox = build(("lb", lambda: ListBox(["a", "b", "c"], selected=1)))["lb"]
    assert listbox.index == 1 and listbox.text == "b" and listbox.items == ["a", "b", "c"]
    listbox.index = None
    assert listbox.index is None and listbox.text is None
    listbox.items = ["x"]
    assert listbox.items == ["x"]


def test_table_rows_and_selection():
    table = build(("t", lambda: Table(["A", "B"], [[1, 2], [3, 4]], multiple=True)))["t"]
    assert table.rows == [["1", "2"], ["3", "4"]]
    table.index = 1
    assert table.selected_rows == [["3", "4"]]
    with pytest.raises(ValueError):
        table.rows = [["only one"]]


def test_selection_from_code_does_not_call_handler():
    calls = []
    listbox = build(("lb", lambda: ListBox(["a", "b"])))["lb"]
    listbox.on_select(lambda: calls.append(1))
    listbox.index = 1
    listbox.items = ["c", "d"]
    assert calls == []


def test_hbox_stretch_builds():
    with Window("test", visible=False):
        with HBox(align="stretch") as row:
            Label("a")
            Label("b")
    assert row.ns is not None


def test_search_field_text():
    field = build(("f", lambda: SearchField(placeholder="Find")))["f"]
    field.text = "abc"
    assert field.text == "abc"


def test_segmented_control():
    seg = build(("s", lambda: SegmentedControl(["A", "B", "C"], selected=1)))["s"]
    assert seg.index == 1 and seg.text == "B"
    seg.index = 2
    assert seg.index == 2
    with pytest.raises(ValueError):
        seg.index = 3
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError):
                SegmentedControl()
            with pytest.raises(ValueError):
                SegmentedControl(["a", "b"], symbols=["gear", "gear"])


def test_button_symbol():
    button = build(("b", lambda: Button("", symbol="chevron.left")))["b"]
    assert button.title == ""
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError):
                Button("x", symbol="no.such.symbol.at.all")


def test_unified_window_with_toolbar():
    with Window("test", style="unified", visible=False) as win:
        with Toolbar() as bar:
            Button("", symbol="chevron.left")
            Spacer()
            SearchField()
        with VBox(padding=8):
            Label("body")
    assert bar.ns is not None and win.ns.toolbar() is not None
    assert not _core._stack


def test_toolbar_rules():
    with pytest.raises(RuntimeError):
        Toolbar()
    with Window("test", visible=False):
        with Toolbar():
            Label("a")
        with pytest.raises(ValueError, match="one Toolbar"):
            Toolbar()
        with VBox():
            Label("x")
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(RuntimeError, match="directly inside"):
                Toolbar()


def test_window_style_validated():
    with pytest.raises(ValueError):
        Window("x", style="weird", visible=False)


def _sidebar_window(**kwargs):
    with Window("test", style="sidebar", visible=False) as win:
        with Sidebar(**kwargs) as side:
            with Page("One", symbol="gearshape"):
                with VBox(padding=8):
                    Label("1")
            with Page("Two"):
                with VBox(padding=8):
                    Label("2")
    return win, side


def test_sidebar_pages_and_selection():
    win, side = _sidebar_window(selected=1)
    assert side.index == 1 and side.text == "Two" and win.title == "Two"
    side.index = 0
    assert side.index == 0 and win.title == "One"
    with pytest.raises(ValueError):
        side.index = 2


def test_sidebar_code_changes_do_not_call_handler():
    calls = []
    win, side = _sidebar_window()
    side.on_change(lambda: calls.append(1))
    side.index = 1
    assert calls == []


def test_sidebar_rules():
    with pytest.raises(RuntimeError):
        Sidebar()
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(RuntimeError, match="style"):
                Sidebar()
    with pytest.raises(ValueError, match="Sidebar"):
        with Window("test", style="sidebar", visible=False):
            pass
    with pytest.raises(ValueError, match="at least one Page"):
        with Window("test", style="sidebar", visible=False):
            with Sidebar():
                pass
    with pytest.raises(ValueError, match="holds only"):
        with Window("test", style="sidebar", visible=False):
            Label("x")
    assert not _core._stack


def test_page_outside_sidebar_raises():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(RuntimeError, match="Sidebar"):
                Page("x")


def test_custom_embeds_view_and_visible():
    from AppKit import NSColorWell

    custom = build(("c", lambda: Custom(NSColorWell.alloc().init(), width=44, height=24)))["c"]
    assert custom.visible
    custom.visible = False
    assert not custom.visible
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(TypeError):
                Custom(None)
            with pytest.raises(TypeError):
                Custom("not a view")


def test_icongrid_items_and_selection():
    grid = build(("g", lambda: IconGrid(["a", ("b", "gear")], selected=1)))["g"]
    assert grid.items == ["a", "b"] and grid.index == 1 and grid.text == "b"
    grid.index = None
    assert grid.index is None and grid.texts == []
    grid.items = ["x", "y", "z"]
    grid.index = 2
    assert grid.indexes == [2]
    with pytest.raises(ValueError):
        grid.index = 3


def test_icongrid_errors():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError):
                IconGrid(["a"], symbol="no.such.symbol.at.all")
            with pytest.raises(ValueError):
                IconGrid(["a"], icon_size=4)
            with pytest.raises(ValueError):
                IconGrid([("a", "no.such.symbol.at.all")])


def test_icongrid_code_changes_do_not_call_handler():
    calls = []
    grid = build(("g", lambda: IconGrid(["a", "b"])))["g"]
    grid.on_select(lambda: calls.append(1))
    grid.index = 1
    grid.items = ["c"]
    assert calls == []
    grid.on_double_click(lambda: None)


def test_tree_path_selection():
    tree = build(("t", lambda: Tree([("Home", [("Docs", ["a.txt"]), "Pics"]), "Other"], expanded=True)))["t"]
    assert tree.path is None and tree.text is None
    tree.path = ["Home", "Docs"]
    assert tree.path == ["Home", "Docs"] and tree.text == "Docs"
    tree.path = ["Home", "Docs", "a.txt"]
    assert tree.paths == [["Home", "Docs", "a.txt"]]
    with pytest.raises(ValueError):
        tree.path = ["Home", "Nope"]
    tree.path = None
    assert tree.path is None


def test_tree_collapsed_path_still_selectable_and_nodes_replace():
    calls = []
    tree = build(("t", lambda: Tree([("A", ["b"])], sidebar=True)))["t"]
    tree.on_select(lambda: calls.append(1))
    tree.path = ["A", "b"]
    assert tree.path == ["A", "b"]
    tree.nodes = [("X", ["y"])]
    assert tree.nodes[0]["text"] == "X"
    tree.expand_all()
    tree.collapse_all()
    assert calls == []


def test_tree_bad_symbol():
    with Window("test", visible=False):
        with VBox():
            with pytest.raises(ValueError):
                Tree([{"text": "a", "symbol": "no.such.symbol.at.all"}])


def test_sheet_builds_and_checks_parent():
    with Window("test", visible=False) as win:
        with VBox():
            Label("x")
    with pytest.raises(TypeError):
        Sheet(object())
    with Sheet(win, size=(300, 120)) as sheet:
        with VBox(padding=10):
            Label("hi")
            Button("Close").on_click(sheet.close)
    assert not sheet.is_open and not _core._stack
    sheet.close()  # closing a sheet that is not open does nothing


def test_popover_builds_and_checks():
    with Popover() as pop:
        with VBox(padding=10):
            Label("hi")
    assert pop.ns is not None and not pop.is_open
    with pytest.raises(ValueError, match="needs content"):
        with Popover():
            pass
    with pytest.raises(ValueError, match="exactly one child"):
        with Popover():
            Label("a")
            Label("b")
    with Window("test", visible=False):
        with VBox():
            label = Label("anchor")
    with pytest.raises(ValueError):
        pop.show(label, edge="middle")
    assert not _core._stack


def test_dialog_arguments_are_checked():
    with pytest.raises(ValueError, match="needs parent"):
        show_info("x", then=print)
    with pytest.raises(TypeError):
        show_info("x", parent=object())


# -- events -----------------------------------------------------------------
def test_constructor_options_and_multiple_handlers():
    calls = []
    button = build(("b", lambda: Button("x", on_click=lambda: calls.append("opt"))))["b"]
    button.on_click(lambda: calls.append("second"))
    button.on_click.emit()
    assert calls == ["opt", "second"]


def test_unknown_event_option_is_rejected():
    with pytest.raises(TypeError):
        build(("b", lambda: Button("x", on_nothing=print)))


def test_every_control_event_can_be_emitted():
    calls = []
    note = lambda: calls.append(1)  # noqa: E731
    r = build(
        ("check", lambda: CheckBox("c", on_change=note)),
        ("text", lambda: TextBox("t", on_enter=note, on_change=note)),
        ("combo", lambda: ComboBox(["a"], on_change=note)),
        ("drop", lambda: DropDown(["a", "b"], on_change=note)),
        ("slider", lambda: Slider(on_change=note)),
        ("spin", lambda: SpinBox(on_change=note)),
        ("list", lambda: ListBox(["a"], on_select=note, on_double_click=note)),
        ("grid", lambda: IconGrid(["a"], on_select=note, on_double_click=note)),
        ("tree", lambda: Tree(["a"], on_select=note, on_double_click=note)),
        ("radio", lambda: RadioGroup(["a", "b"], on_change=note)),
        ("segments", lambda: SegmentedControl(["a", "b"], on_change=note)),
        ("search", lambda: SearchField(on_change=note)),
    )
    for name, control in r.items():
        if name == "vbox":
            continue
        for event_name in ("on_enter", "on_change", "on_select", "on_double_click"):
            if hasattr(type(control), event_name):
                getattr(control, event_name).emit()
    assert len(calls) == 16


def test_textbox_typing_event_not_fired_from_code():
    calls = []
    box = build(("t", lambda: TextBox("a", on_change=lambda: calls.append(1))))["t"]
    box.text = "b"
    assert calls == []  # unverified assumption on a real Mac: setting text posts no edit notification


def test_window_close_veto_and_destroy():
    seen = []
    with Window("w", visible=False, on_close=lambda: seen.append("close") or False) as win:
        with VBox():
            Label("x")
    assert win._should_close() is False
    win.on_close = None
    assert win._should_close() is True
    win.on_destroy(lambda: seen.append("destroy"))
    win.on_destroy.emit()
    assert seen == ["close", "destroy"]
    assert win.size[0] > 0


def test_window_rejects_unknown_option():
    with pytest.raises(TypeError):
        Window("w", visible=False, on_nothing=print)


def test_app_on_error_and_call():
    from baremacgui import App, _events

    app = App("test", menu=False)
    seen = []
    app.on_error = seen.append
    try:
        Button_event = build(("b", lambda: Button("x", on_click=lambda: 1 / 0)))["b"]
        Button_event.on_click.emit()
    finally:
        app.on_error = None
    assert isinstance(seen[0], ZeroDivisionError)
    assert app.call(lambda a, b=1: a + b, 1, b=2) == 3  # on the main thread: runs directly
    assert _events._error_hook[0] is None


# -- menus, shortcuts, timer, pickers, justify ---------------------------------
def test_menubar_items_shortcuts_and_clicks():
    calls = []
    with Window("w", visible=False) as win:
        with MenuBar() as bar:
            with Menu("&File"):
                new = MenuItem("&New", shortcut="Cmd+N", on_click=lambda: calls.append("new"))
                MenuSeparator()
                flag = MenuItem("Flag", checkable=True)
                with Menu("Sub"):
                    MenuItem("Deep")
        with VBox():
            Label("x")
    assert new.text == "New"
    assert str(new.ns.keyEquivalent()) == "n"
    new.click()
    assert calls == ["new"]
    assert not flag.checked
    flag.click()
    assert flag.checked
    flag.enabled = False
    assert not flag.enabled
    assert [menu.title for menu in bar.menus] == ["File"]
    assert bar.ns is not None and win._menubar is bar
    titles = [str(item.submenu().title()) for item in bar.ns.itemArray()]
    assert titles[1] == "File" and titles[-1] == "Window" and "Edit" in titles


def test_menu_item_outside_menu_and_bad_shortcut():
    with pytest.raises(RuntimeError):
        MenuItem("x")
    with Window("w", visible=False):
        with MenuBar():
            with Menu("M"):
                with pytest.raises(ValueError):
                    MenuItem("bad", shortcut="S")
        with VBox():
            Label("x")


def test_context_menu_attaches_to_controls():
    with ContextMenu() as menu:
        MenuItem("Delete")
        MenuSeparator()
    r = build(("table", lambda: Table(["a"], [["1"]])), ("text", lambda: TextBox("t", multiline=True)),
              ("grid", lambda: IconGrid(["a"])), ("tree", lambda: Tree(["a"])), ("button", lambda: Button("b")))
    for name in ("table", "text", "grid", "tree", "button"):
        r[name].context_menu = menu
        assert r[name].context_menu is menu
    assert [item.text for item in menu.items] == ["Delete"]
    r["table"].context_menu = None
    assert r["table"].context_menu is None


def test_window_shortcuts_and_buttons():
    calls = []
    with Window("w", visible=False) as win:
        with VBox():
            ok = Button("OK")
            cancel = Button("Cancel")
    win.add_shortcut("Cmd+K", lambda: calls.append("k"))
    win._shortcuts[("k", frozenset({"cmd"}))].emit()
    assert calls == ["k"]
    with pytest.raises(ValueError):
        win.add_shortcut("K", print)
    win.default_button = ok
    win.cancel_button = cancel
    assert str(ok.ns.keyEquivalent()) == "\r" and str(cancel.ns.keyEquivalent()) == "\x1b"
    win.default_button = None
    assert str(ok.ns.keyEquivalent()) == ""


def _spin(seconds, until=None):
    """Run the main run loop for up to `seconds`, in short steps (runUntilDate_ may return early)."""
    import time

    from Foundation import NSDate, NSDefaultRunLoopMode, NSRunLoop

    end = time.monotonic() + seconds
    while time.monotonic() < end and not (until is not None and until()):
        NSRunLoop.currentRunLoop().runMode_beforeDate_(NSDefaultRunLoopMode, NSDate.dateWithTimeIntervalSinceNow_(0.02))


def test_timer_ticks_and_stops():
    ticks = []
    timer = Timer(0.05, lambda: ticks.append(1))
    assert timer.running
    _spin(5.0, until=lambda: len(ticks) >= 3)
    timer.stop()
    count = len(ticks)
    assert count >= 2, f"only {count} ticks in 5 s (timer was running: {timer.running})"
    assert not timer.running
    _spin(0.2)
    assert len(ticks) == count
    once = []
    Timer(0.05, lambda: once.append(1), repeat=False)
    _spin(5.0, until=lambda: bool(once))
    _spin(0.3)
    assert once == [1]
    with pytest.raises(ValueError):
        Timer(0)


def test_date_and_time_picker_roundtrip():
    import datetime as dt

    r = build(("date", lambda: DatePicker(dt.date(2026, 3, 9))), ("time", lambda: TimePicker(dt.time(14, 30))),
              ("cal", lambda: DatePicker(calendar=True)))
    assert r["date"].value == dt.date(2026, 3, 9)
    r["date"].value = dt.date(2027, 1, 31)
    assert r["date"].value == dt.date(2027, 1, 31)
    assert r["time"].value == dt.time(14, 30)
    r["time"].value = dt.time(7, 5, 9)
    assert r["time"].value.hour == 7 and r["time"].value.minute == 5
    assert r["cal"].value == dt.date.today()
    with pytest.raises(TypeError):
        r["date"].value = "2026-01-01"
    with pytest.raises(TypeError):
        r["time"].value = dt.datetime.now()


def test_box_justify_builds_for_all_modes():
    for mode in ("start", "center", "end", "space_between"):
        with Window("w", visible=False):
            with HBox(justify=mode) as row:
                Label("a")
                Label("b")
                Label("c")
        assert row.ns.fittingSize().width > 0
    with pytest.raises(ValueError):
        HBox(justify="middle")
