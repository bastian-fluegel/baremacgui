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
