"""Pure-Python option checks. No PyObjC in here, so this runs (and is tested) on any OS."""
from __future__ import annotations

from .errors import LayoutError

SIZE_KEYS = ("width", "height", "min_width", "max_width", "min_height", "max_height")

_ALIGN = {
    "VBox": ("start", "center", "end", "stretch"),
    "HBox": ("start", "center", "end", "stretch"),
}


def _number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise LayoutError(f"{name} must be a number >= 0, got {value!r}")
    return float(value)


def check_grow(grow):
    return _number("grow", grow)


def check_padding(padding):
    return _number("padding", padding)


def check_size(options):
    """Validate width/height/min_*/max_* keyword options; None values are dropped."""
    unknown = sorted(set(options) - set(SIZE_KEYS))
    if unknown:
        raise TypeError("unexpected option(s): " + ", ".join(unknown))
    checked = {key: _number(key, value) for key, value in options.items() if value is not None}
    for axis in ("width", "height"):
        low, high = checked.get("min_" + axis), checked.get("max_" + axis)
        if low is not None and high is not None and low > high:
            raise LayoutError(f"min_{axis} ({low:g}) is larger than max_{axis} ({high:g})")
    return checked


def check_align(kind, align):
    """Resolve the cross-axis alignment of a VBox/HBox (None gives the default)."""
    allowed = _ALIGN[kind]
    if align is None:
        return "start" if kind == "VBox" else "center"
    if align not in allowed:
        raise LayoutError(f"{kind} align must be one of {', '.join(allowed)}; got {align!r}")
    return align


def check_window_size(size):
    try:
        width, height = size
    except (TypeError, ValueError):
        raise LayoutError(f"size must be a (width, height) pair, got {size!r}") from None
    for name, value in (("width", width), ("height", height)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise LayoutError(f"window {name} must be a number > 0, got {value!r}")
    return float(width), float(height)


def clamp(value, low, high):
    return max(low, min(high, value))


def check_spin_range(value, minimum, maximum, step):
    for name, number in (("value", value), ("minimum", minimum), ("maximum", maximum), ("step", step)):
        if isinstance(number, bool) or not isinstance(number, int):
            raise TypeError(f"SpinBox {name} must be an int, got {number!r}")
    if minimum > maximum:
        raise ValueError(f"SpinBox minimum ({minimum}) is larger than maximum ({maximum})")
    if step <= 0:
        raise ValueError("SpinBox step must be > 0")
    return clamp(value, minimum, maximum)


def parse_int(text):
    """Return the int in `text`, or None if it is not a plain integer."""
    try:
        return int(str(text).strip())
    except ValueError:
        return None


def normalize_filetypes(filetypes):
    """['.TXT', 'png'] -> ['txt', 'png']; None or empty -> None."""
    if filetypes is None:
        return None
    if isinstance(filetypes, str):
        filetypes = [filetypes]
    result = []
    for entry in filetypes:
        if not isinstance(entry, str) or not entry.strip().lstrip("."):
            raise ValueError("file types must be non-empty strings like 'txt' or '.png'")
        result.append(entry.strip().lstrip(".").lower())
    return result or None


def check_float_range(value, minimum, maximum):
    """Slider/progress range: numbers only, minimum < maximum; returns value clamped."""
    for name, number in (("value", value), ("minimum", minimum), ("maximum", maximum)):
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise TypeError(f"{name} must be a number, got {number!r}")
    if minimum >= maximum:
        raise ValueError(f"minimum ({minimum}) must be smaller than maximum ({maximum})")
    return float(clamp(value, minimum, maximum))


def check_index(index, count, what="index"):
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError(f"{what} must be an int, got {index!r}")
    if not 0 <= index < count:
        detail = f"outside 0..{count - 1}" if count else "invalid: the list is empty"
        raise ValueError(f"{what} {index} is {detail}")
    return index


def check_items(items, minimum=0, what="items"):
    """A list of labels as strings. A bare string is a mistake, not a list of letters."""
    if isinstance(items, str):
        raise TypeError(f"{what} must be a list of strings, not a single string")
    result = [str(item) for item in items]
    if len(result) < minimum:
        raise ValueError(f"needs at least {minimum} {what}, got {len(result)}")
    return result


def check_columns(columns):
    if isinstance(columns, str):
        raise TypeError("columns must be a list of column titles, not a single string")
    result = [str(column) for column in columns]
    if not result:
        raise ValueError("a Table needs at least one column")
    return result


def check_rows(rows, width):
    """Rows of cells, each exactly `width` long; every cell becomes a string."""
    result = []
    for number, row in enumerate(rows):
        if isinstance(row, str):
            raise TypeError(f"row {number} must be a list of cells, not a string")
        cells = [str(cell) for cell in row]
        if len(cells) != width:
            raise ValueError(f"row {number} has {len(cells)} cells, expected {width}")
        result.append(cells)
    return result


WINDOW_STYLES = ("standard", "unified", "sidebar")


def check_window_style(style):
    if style not in WINDOW_STYLES:
        raise LayoutError(f"Window style must be one of {', '.join(WINDOW_STYLES)}; got {style!r}")
    return style


def check_icon_items(items, default_symbol="doc"):
    """IconGrid entries: each a label, or a (label, symbol) pair. Returns [(label, symbol), ...]."""
    if isinstance(items, str):
        raise TypeError("items must be a list, not a single string")
    result = []
    for number, entry in enumerate(items):
        if isinstance(entry, str):
            result.append((entry, str(default_symbol)))
        elif isinstance(entry, (tuple, list)) and len(entry) == 2 and all(isinstance(part, str) for part in entry):
            result.append((entry[0], entry[1]))
        else:
            raise TypeError(f"item {number} must be a label or a (label, symbol) pair, got {entry!r}")
    return result


def check_nodes(nodes, _depth=0):
    """Tree nodes. Each node is one of:

        "Label"                                a leaf
        ("Label", [children])                  a node with children
        {"text": ..., "symbol": ..., "children": [...]}   symbol and children optional

    Returns a list of {"text", "symbol", "children"} dicts (children normalized too).
    """
    if isinstance(nodes, (str, dict)):
        raise TypeError("nodes must be a list")
    if _depth > 50:
        raise ValueError("tree is nested too deeply")
    result = []
    for number, node in enumerate(nodes):
        if isinstance(node, str):
            node = {"text": node}
        elif isinstance(node, (tuple, list)):
            if len(node) != 2 or not isinstance(node[0], str):
                raise TypeError(f"node {number}: a tuple must be (label, [children]), got {node!r}")
            node = {"text": node[0], "children": node[1]}
        elif not isinstance(node, dict):
            raise TypeError(f"node {number} must be a string, a (label, children) pair or a dict, got {node!r}")
        unknown = sorted(set(node) - {"text", "symbol", "children"})
        if unknown:
            raise TypeError(f"node {number}: unexpected key(s): {', '.join(unknown)}")
        if not isinstance(node.get("text"), str):
            raise TypeError(f"node {number} needs a string under 'text'")
        symbol = node.get("symbol")
        if symbol is not None and not isinstance(symbol, str):
            raise TypeError(f"node {number}: symbol must be a string")
        result.append({
            "text": node["text"],
            "symbol": symbol,
            "children": check_nodes(node.get("children") or [], _depth + 1),
        })
    return result


def find_node_path(nodes, texts):
    """Follow `texts` down normalized `nodes`; return the list of matching dicts, or None."""
    found, level = [], nodes
    for text in texts:
        match = next((node for node in level if node["text"] == text), None)
        if match is None:
            return None
        found.append(match)
        level = match["children"]
    return found


POPOVER_EDGES = ("bottom", "top", "left", "right")


def check_popover_edge(edge):
    if edge not in POPOVER_EDGES:
        raise ValueError(f"edge must be one of {', '.join(POPOVER_EDGES)}; got {edge!r}")
    return edge


_MODIFIERS = {
    "cmd": "cmd", "command": "cmd", "ctrl": "cmd",  # Ctrl is the Windows spelling: it becomes Cmd
    "control": "ctrl", "shift": "shift", "alt": "alt", "option": "alt", "opt": "alt",
}
_NAMED_KEYS = {
    "return", "enter", "escape", "esc", "tab", "space", "delete", "backspace",
    "up", "down", "left", "right", "home", "end", "pageup", "pagedown",
}
_ALIASES = {"enter": "return", "esc": "escape", "backspace": "delete"}


def parse_shortcut(text):
    """Split "Cmd+Shift+S" into ("s", frozenset({"cmd", "shift"})).

    Modifiers: Cmd/Command/Ctrl (all Command; so code written for BareWinGUI keeps
    its "Ctrl+S"), Control (the real Control key), Shift, Alt/Option.
    Keys: one character, F1..F12, or Return, Escape, Tab, Space, Delete, Up, Down,
    Left, Right, Home, End, PageUp, PageDown. A shortcut needs at least one modifier
    unless it is a function key or a named key.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"shortcut must be a non-empty string like 'Cmd+S', got {text!r}")
    parts = [part.strip() for part in text.split("+")]
    if parts[-1] == "" and len(parts) >= 2:  # "Cmd++" means the plus key
        parts = parts[:-2] + ["+"]
    *mods, key = parts
    modifiers = set()
    for name in mods:
        found = _MODIFIERS.get(name.lower())
        if found is None:
            raise ValueError(f"unknown modifier {name!r} in shortcut {text!r}")
        modifiers.add(found)
    lowered = key.lower()
    if lowered in _NAMED_KEYS:
        key = _ALIASES.get(lowered, lowered)
    elif len(lowered) >= 2 and lowered[0] == "f" and lowered[1:].isdigit() and 1 <= int(lowered[1:]) <= 12:
        key = lowered
    elif len(key) == 1:
        key = key.lower()
        if not modifiers:
            raise ValueError(f"shortcut {text!r} needs a modifier (Cmd, Control, Alt or Shift)")
    else:
        raise ValueError(f"unknown key {key!r} in shortcut {text!r}")
    return key, frozenset(modifiers)


JUSTIFY = ("start", "center", "end", "space_between")


def check_justify(justify):
    if justify not in JUSTIFY:
        raise LayoutError(f"justify must be one of {', '.join(JUSTIFY)}; got {justify!r}")
    return justify


def check_interval(seconds):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not seconds > 0:
        raise ValueError(f"interval must be a number > 0 (seconds), got {seconds!r}")
    return float(seconds)


# -- key mapping (pure data; the AppKit constants are applied in _menus.py) ---------------------
_MENU_KEYS = {
    "return": "\r", "escape": "\x1b", "tab": "\t", "space": " ", "delete": "\x08",
    "up": "", "down": "", "left": "", "right": "",
    "home": "", "end": "", "pageup": "", "pagedown": "",
}
for _n in range(1, 13):
    _MENU_KEYS[f"f{_n}"] = chr(0xF703 + _n)
_KEYCODES = {
    36: "return", 76: "return", 53: "escape", 48: "tab", 49: "space", 51: "delete",
    123: "left", 124: "right", 125: "down", 126: "up", 115: "home", 119: "end", 116: "pageup", 121: "pagedown",
}
for _n, _code in enumerate((122, 120, 99, 118, 96, 97, 98, 100, 101, 109, 103, 111), start=1):
    _KEYCODES[_code] = f"f{_n}"
_FLAG_BITS = ((1 << 17, "shift"), (1 << 18, "ctrl"), (1 << 19, "alt"), (1 << 20, "cmd"))


def menu_key_equivalent(key):
    """The NSMenuItem key-equivalent string for a key name from parse_shortcut."""
    return _MENU_KEYS.get(key, key)


def event_shortcut(characters, keycode, flags):
    """Turn a key event (characters ignoring modifiers, key code, modifier flags) into (key, modifiers)."""
    key = _KEYCODES.get(int(keycode))
    if key is None:
        key = (characters or "").lower()
    mods = frozenset(name for bit, name in _FLAG_BITS if int(flags) & bit)
    return key, mods


def check_setting_key(key):
    if not isinstance(key, str) or not key or key.startswith("."):
        raise ValueError(f"a setting name must be a non-empty string, got {key!r}")
    return key


def check_setting_value(value, _path="value"):
    """Settings hold what a property list holds: bool, int, float, str, and lists/dicts of those."""
    if isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [check_setting_value(item, f"{_path}[{i}]") for i, item in enumerate(value)]
    if isinstance(value, dict):
        for k in value:
            if not isinstance(k, str):
                raise TypeError(f"{_path}: dict keys must be strings, got {k!r}")
        return {k: check_setting_value(v, f"{_path}[{k!r}]") for k, v in value.items()}
    raise TypeError(f"{_path}: cannot store {type(value).__name__} (use bool, int, float, str, list or dict)")


def plain_value(value):
    """Turn what NSUserDefaults returns (NSArray, NSDictionary, NSNumber proxies) into plain Python."""
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, int):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [plain_value(item) for item in value]
    if hasattr(value, "items"):
        return {str(k): plain_value(v) for k, v in value.items()}
    return value
