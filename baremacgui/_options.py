"""Pure-Python option checks. No PyObjC in here, so this runs (and is tested) on any OS."""
from __future__ import annotations

SIZE_KEYS = ("width", "height", "min_width", "max_width", "min_height", "max_height")

_ALIGN = {
    "VBox": ("start", "center", "end", "stretch"),
    "HBox": ("start", "center", "end"),
}


def _number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise ValueError(f"{name} must be a number >= 0, got {value!r}")
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
            raise ValueError(f"min_{axis} ({low:g}) is larger than max_{axis} ({high:g})")
    return checked


def check_align(kind, align):
    """Resolve the cross-axis alignment of a VBox/HBox (None gives the default)."""
    allowed = _ALIGN[kind]
    if align is None:
        return "start" if kind == "VBox" else "center"
    if align not in allowed:
        raise ValueError(f"{kind} align must be one of {', '.join(allowed)}; got {align!r}")
    return align


def check_window_size(size):
    try:
        width, height = size
    except (TypeError, ValueError):
        raise ValueError(f"size must be a (width, height) pair, got {size!r}") from None
    for name, value in (("width", width), ("height", height)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ValueError(f"window {name} must be a number > 0, got {value!r}")
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
