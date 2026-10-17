"""Pure-Python checks; these run on every OS."""
import pytest

from baremacgui import _options as o


def test_check_grow():
    assert o.check_grow(0) == 0
    assert o.check_grow(2) == 2.0
    for bad in (-1, "1", None, True):
        with pytest.raises(ValueError):
            o.check_grow(bad)


def test_check_size_keeps_valid_values_and_drops_none():
    assert o.check_size({"min_width": 100, "height": None}) == {"min_width": 100.0}


def test_check_size_rejects_unknown_and_inverted():
    with pytest.raises(TypeError, match="colour"):
        o.check_size({"colour": 1})
    with pytest.raises(ValueError, match="larger than"):
        o.check_size({"min_width": 200, "max_width": 100})


def test_check_align_defaults_and_limits():
    assert o.check_align("VBox", None) == "start"
    assert o.check_align("HBox", None) == "center"
    assert o.check_align("VBox", "stretch") == "stretch"
    assert o.check_align("HBox", "stretch") == "stretch"
    with pytest.raises(ValueError):
        o.check_align("HBox", "diagonal")


def test_check_window_size():
    assert o.check_window_size((320, 160)) == (320.0, 160.0)
    for bad in ((0, 10), (10,), "ab", (True, 5), None):
        with pytest.raises(ValueError):
            o.check_window_size(bad)


def test_spin_range_clamps_value_and_validates():
    assert o.check_spin_range(99, 0, 10, 1) == 10
    assert o.check_spin_range(-5, 0, 10, 1) == 0
    with pytest.raises(ValueError):
        o.check_spin_range(1, 10, 0, 1)
    with pytest.raises(ValueError):
        o.check_spin_range(1, 0, 10, 0)
    with pytest.raises(TypeError):
        o.check_spin_range(1.5, 0, 10, 1)


def test_parse_int():
    assert o.parse_int(" 42 ") == 42
    assert o.parse_int("-3") == -3
    assert o.parse_int("4x") is None
    assert o.parse_int("") is None


def test_normalize_filetypes():
    assert o.normalize_filetypes(None) is None
    assert o.normalize_filetypes("PNG") == ["png"]
    assert o.normalize_filetypes([".TXT", "md"]) == ["txt", "md"]
    assert o.normalize_filetypes([]) is None
    with pytest.raises(ValueError):
        o.normalize_filetypes(["."])


def test_check_float_range():
    assert o.check_float_range(5, 0, 10) == 5.0
    assert o.check_float_range(50, 0, 10) == 10.0
    assert o.check_float_range(-1.5, 0, 10) == 0.0
    with pytest.raises(ValueError):
        o.check_float_range(1, 5, 5)
    with pytest.raises(TypeError):
        o.check_float_range("1", 0, 10)


def test_check_index():
    assert o.check_index(0, 3) == 0
    assert o.check_index(2, 3) == 2
    for bad in (-1, 3):
        with pytest.raises(ValueError, match="outside"):
            o.check_index(bad, 3)
    with pytest.raises(ValueError, match="empty"):
        o.check_index(0, 0)
    with pytest.raises(TypeError):
        o.check_index(1.0, 3)


def test_check_items():
    assert o.check_items([1, "b"]) == ["1", "b"]
    with pytest.raises(TypeError):
        o.check_items("abc")
    with pytest.raises(ValueError, match="at least 2"):
        o.check_items(["a"], minimum=2)


def test_check_columns_and_rows():
    assert o.check_columns(["A", "B"]) == ["A", "B"]
    for bad in ([], ()):
        with pytest.raises(ValueError):
            o.check_columns(bad)
    with pytest.raises(TypeError):
        o.check_columns("AB")
    assert o.check_rows([[1, 2], ("x", None)], 2) == [["1", "2"], ["x", "None"]]
    with pytest.raises(ValueError, match="row 1 has 1 cells"):
        o.check_rows([["a", "b"], ["c"]], 2)
    with pytest.raises(TypeError):
        o.check_rows(["ab"], 2)


def test_check_window_style():
    assert o.check_window_style("standard") == "standard"
    assert o.check_window_style("unified") == "unified"
    with pytest.raises(ValueError):
        o.check_window_style("fancy")


def test_check_icon_items():
    assert o.check_icon_items(["a", ("b", "gear")], "doc") == [("a", "doc"), ("b", "gear")]
    with pytest.raises(TypeError):
        o.check_icon_items("abc")
    with pytest.raises(TypeError):
        o.check_icon_items([("a",)])
    with pytest.raises(TypeError):
        o.check_icon_items([3])


def test_check_nodes_forms():
    nodes = o.check_nodes([
        "leaf",
        ("branch", ["x", ("y", ["z"])]),
        {"text": "full", "symbol": "folder", "children": ["c"]},
    ])
    assert [n["text"] for n in nodes] == ["leaf", "branch", "full"]
    assert nodes[0] == {"text": "leaf", "symbol": None, "children": []}
    assert nodes[1]["children"][1]["children"][0]["text"] == "z"
    assert nodes[2]["symbol"] == "folder"


def test_check_nodes_rejects_bad_input():
    for bad in ("abc", {"text": "a"}, [3], [("a",)], [("a", "b", "c")], [{"symbol": "x"}],
                [{"text": "a", "colour": 1}], [{"text": "a", "symbol": 3}]):
        with pytest.raises(TypeError):
            o.check_nodes(bad)


def test_find_node_path():
    nodes = o.check_nodes([("a", [("b", ["c"])]), "d"])
    assert [n["text"] for n in o.find_node_path(nodes, ["a", "b", "c"])] == ["a", "b", "c"]
    assert o.find_node_path(nodes, ["a", "x"]) is None
    assert o.find_node_path(nodes, []) == []


def test_check_popover_edge():
    assert o.check_popover_edge("top") == "top"
    with pytest.raises(ValueError):
        o.check_popover_edge("middle")


def test_parse_shortcut():
    assert o.parse_shortcut("Cmd+S") == ("s", frozenset({"cmd"}))
    assert o.parse_shortcut("Ctrl+Shift+S") == ("s", frozenset({"cmd", "shift"}))
    assert o.parse_shortcut("Control+Option+Q") == ("q", frozenset({"ctrl", "alt"}))
    assert o.parse_shortcut("F5") == ("f5", frozenset())
    assert o.parse_shortcut("Cmd+Enter") == ("return", frozenset({"cmd"}))
    assert o.parse_shortcut("Escape") == ("escape", frozenset())
    assert o.parse_shortcut("Cmd++") == ("+", frozenset({"cmd"}))
    for bad in ("", "S", "Hyper+S", "Cmd+Foo", "Cmd+F13", 3):
        with pytest.raises(ValueError):
            o.parse_shortcut(bad)


def test_check_justify_and_interval():
    assert o.check_justify("center") == "center"
    with pytest.raises(ValueError):
        o.check_justify("middle")
    assert o.check_interval(1) == 1.0
    for bad in (0, -1, True, "1"):
        with pytest.raises(ValueError):
            o.check_interval(bad)


def test_key_mapping():
    assert o.menu_key_equivalent("s") == "s"
    assert o.menu_key_equivalent("return") == "\r"
    assert o.menu_key_equivalent("f1") == ""
    assert o.menu_key_equivalent("f12") == ""
    assert o.event_shortcut("S", 1, (1 << 20) | (1 << 17)) == ("s", frozenset({"cmd", "shift"}))
    assert o.event_shortcut("", 36, 0) == ("return", frozenset())
    assert o.event_shortcut("", 96, 0) == ("f5", frozenset())


def test_setting_checks_and_plain_value():
    assert o.check_setting_value({"a": [1, 2.5, "x", True]}) == {"a": [1, 2.5, "x", True]}
    assert o.check_setting_value((1, 2)) == [1, 2]
    for bad in (None, {1: 2}, [object()], b"x"):
        with pytest.raises(TypeError):
            o.check_setting_value(bad)
    for bad in ("", ".x", 3):
        with pytest.raises(ValueError):
            o.check_setting_key(bad)
    assert o.plain_value({"k": [1, True, "s"]}) == {"k": [1, True, "s"]}


def test_color_parse_and_format():
    assert o.parse_color("#FF0000") == (1.0, 0.0, 0.0, 1.0)
    assert o.parse_color("0f0") == (0.0, 1.0, 0.0, 1.0)
    assert o.parse_color("#00000080")[3] == pytest.approx(128 / 255)
    assert o.format_color(1, 0.2, 0) == "#FF3300"
    assert o.format_color(0, 0, 0, 0.5) == "#00000080"
    assert o.format_color(*o.parse_color("#3366FF")) == "#3366FF"
    for bad in ("", "#12", "#GGGGGG", "#1234567"):
        with pytest.raises(ValueError):
            o.parse_color(bad)
    with pytest.raises(TypeError):
        o.parse_color(0xFF0000)


def test_sort_order_numbers_and_text():
    rows = [["b", "10"], ["A", "9"], ["c", "x"], ["a", "2,5"]]
    assert o.sort_order(rows, 1) == [3, 1, 0, 2]          # numbers first, then text
    assert o.sort_order(rows, 1, False) == [2, 0, 1, 3]
    assert o.sort_order(rows, 0) == [1, 3, 0, 2]          # case-insensitive, stable
    assert o.sort_order([], 0) == []
    for bad in (-1, 2, True, "0"):
        with pytest.raises(ValueError):
            o.sort_order(rows, bad)


def test_check_editable():
    assert o.check_editable(True, 3) == frozenset({0, 1, 2})
    assert o.check_editable(False, 3) == frozenset()
    assert o.check_editable([1], 3) == frozenset({1})
    with pytest.raises(ValueError):
        o.check_editable([3], 3)
    with pytest.raises(TypeError):
        o.check_editable(5, 3)
