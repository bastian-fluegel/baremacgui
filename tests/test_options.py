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
    with pytest.raises(ValueError):
        o.check_align("HBox", "stretch")


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
