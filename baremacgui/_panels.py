"""choose_color and choose_font: the system color and font panels, run until the user closes them.

macOS has one shared, non-modal color panel and font panel for the whole app. These functions open the
panel, run it modally and return what is selected when the user closes it. Native difference to the
Windows dialogs: the panels have no OK and Cancel buttons, so there is no "cancelled" result.
"""
from __future__ import annotations

from typing import NamedTuple

from ._bridge import AK, FN, ensure_app, make_target
from ._options import format_color, parse_color


class FontChoice(NamedTuple):
    name: str  # family, e.g. "Helvetica Neue"
    size: float  # points
    bold: bool
    italic: bool


def _run_until_closed(panel):
    """Run `panel` as a modal window and return when the user closes it."""
    app = ensure_app()
    ak = AK()
    target = make_target(lambda: app.stopModal())
    center = FN().NSNotificationCenter.defaultCenter()
    center.addObserver_selector_name_object_(target, b"fire:", ak.NSWindowWillCloseNotification, panel)
    try:
        panel.makeKeyAndOrderFront_(None)
        app.runModalForWindow_(panel)
    finally:
        center.removeObserver_(target)
        panel.orderOut_(None)


def choose_color(initial="#FFFFFF", alpha=False):
    """Open the system color panel; return the chosen color as '#RRGGBB' (or '#RRGGBBAA' with alpha=True).

    Blocks until the user closes the panel; the result is the color selected at that moment.
    """
    ak = AK()
    r, g, b, a = parse_color(initial)
    panel = ak.NSColorPanel.sharedColorPanel()
    panel.setShowsAlpha_(bool(alpha))
    panel.setColor_(ak.NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, a if alpha else 1.0))
    _run_until_closed(panel)
    color = panel.color().colorUsingColorSpace_(ak.NSColorSpace.sRGBColorSpace())
    return format_color(color.redComponent(), color.greenComponent(), color.blueComponent(),
                        color.alphaComponent() if alpha else 1.0)


def _font_of(choice):
    ak = AK()
    manager = ak.NSFontManager.sharedFontManager()
    traits = (ak.NSBoldFontMask if choice.bold else 0) | (ak.NSItalicFontMask if choice.italic else 0)
    font = manager.fontWithFamily_traits_weight_size_(choice.name, traits, 5, float(choice.size))
    return font or ak.NSFont.systemFontOfSize_(float(choice.size))


def _choice_of(font):
    ak = AK()
    traits = int(ak.NSFontManager.sharedFontManager().traitsOfFont_(font))
    return FontChoice(str(font.familyName()), float(font.pointSize()),
                      bool(traits & int(ak.NSBoldFontMask)), bool(traits & int(ak.NSItalicFontMask)))


def choose_font(initial=None):
    """Open the system font panel; return a FontChoice(name, size, bold, italic).

    `initial` is a FontChoice (default: the system font at 13 points). Blocks until the user closes
    the panel; the result is the font selected at that moment.
    """
    ak = AK()
    start = _font_of(initial or FontChoice(str(ak.NSFont.systemFontOfSize_(13.0).familyName()), 13.0, False, False))
    panel = ak.NSFontPanel.sharedFontPanel()
    panel.setPanelFont_isMultiple_(start, False)
    _run_until_closed(panel)
    return _choice_of(panel.panelConvertFont_(start))
