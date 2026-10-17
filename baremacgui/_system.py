"""Switch, ColorWell and the clipboard."""
from __future__ import annotations

from ._bridge import AK
from ._controls import Control
from ._events import event
from ._options import format_color, parse_color


class Switch(Control):
    """The on/off switch (native NSSwitch, macOS 10.15+). `checked` is a bool.

    Native NSSwitch has no label; put a Label next to it (the usual System Settings look).
    Assigning .checked never calls on_change; only the user does.
    """

    on_change = event()

    def __init__(self, checked=False, grow=0, **size):
        ak = AK()
        if not hasattr(ak, "NSSwitch"):
            raise RuntimeError("Switch needs macOS 10.15 or newer")
        ns = ak.NSSwitch.alloc().init()
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)
        self.checked = checked

    @property
    def checked(self):
        return int(self.ns.state()) == int(AK().NSControlStateValueOn)

    @checked.setter
    def checked(self, value):
        ak = AK()
        self.ns.setState_(ak.NSControlStateValueOn if value else ak.NSControlStateValueOff)


class ColorWell(Control):
    """A color swatch that opens the system color panel when clicked (native NSColorWell).

    `value` is a string '#RRGGBB' (or '#RRGGBBAA'). on_change fires while the user picks a color.
    Assigning .value never calls on_change. The color panel is the one shared panel of the app and
    is not modal; that is how macOS works.

    alpha=True lets the user pick transparency too (the shared panel then shows its opacity slider,
    for every ColorWell of the app); by default values are opaque.
    """

    on_change = event()

    def __init__(self, value="#3366FF", alpha=False, grow=0, **size):
        ak = AK()
        ns = ak.NSColorWell.alloc().init()
        self.alpha = bool(alpha)
        if self.alpha:
            ak.NSColorPanel.sharedColorPanel().setShowsAlpha_(True)
        size.setdefault("width", 44)
        size.setdefault("height", 24)
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)
        self.value = value

    @property
    def value(self):
        ak = AK()
        color = self.ns.color().colorUsingColorSpace_(ak.NSColorSpace.sRGBColorSpace())
        return format_color(color.redComponent(), color.greenComponent(), color.blueComponent(), color.alphaComponent())

    @value.setter
    def value(self, text):
        r, g, b, a = parse_color(text)
        if not self.alpha:
            a = 1.0
        self.ns.setColor_(AK().NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, a))


class Clipboard:
    """The general pasteboard (NSPasteboard). Use the ready-made object `clipboard`.

        clipboard.text = "copied"
        clipboard.text            # "copied", or "" when the clipboard holds no text
        clipboard.clear()
    """

    @property
    def text(self):
        value = AK().NSPasteboard.generalPasteboard().stringForType_(AK().NSPasteboardTypeString)
        return "" if value is None else str(value)

    @text.setter
    def text(self, value):
        ak = AK()
        board = ak.NSPasteboard.generalPasteboard()
        board.clearContents()
        board.setString_forType_(str(value), ak.NSPasteboardTypeString)

    def clear(self):
        AK().NSPasteboard.generalPasteboard().clearContents()


clipboard = Clipboard()
