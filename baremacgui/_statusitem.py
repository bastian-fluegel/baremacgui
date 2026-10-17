"""StatusItem: an icon or text in the menu bar with a menu."""
from __future__ import annotations

from ._bridge import AK
from ._menus import _Container, _plain


class StatusItem(_Container):
    """An entry on the right side of the menu bar (native NSStatusItem) that opens a menu.

        app = App("Clock", background=True)
        with StatusItem(symbol="clock", title="12:00") as item:
            MenuItem("Say hello", on_click=hello)
            MenuSeparator()
            MenuItem("Quit", shortcut="Cmd+Q", on_click=app.quit)
        item.title = "12:01"              # change it later (UI thread)

    symbol  an SF Symbol name shown as the icon (macOS 11+)
    title   text next to (or instead of) the icon

    Needs an App. Keep the StatusItem object alive: the entry disappears when it is deleted.
    Differences from native: only a menu is supported, not a popover or a custom view.
    """

    def __init__(self, title="", symbol=None):
        ak = AK()
        self._init_container("")
        self._item = ak.NSStatusBar.systemStatusBar().statusItemWithLength_(ak.NSVariableStatusItemLength)
        self._item.setMenu_(self.ns)
        self.symbol = symbol
        self.title = title
        if not str(title) and symbol is None:
            raise ValueError("a StatusItem needs a title or a symbol")

    @property
    def title(self):
        return str(self._item.button().title())

    @title.setter
    def title(self, value):
        self._item.button().setTitle_(_plain(value))

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, name):
        self._symbol = name
        if name is None:
            self._item.button().setImage_(None)
            return
        image = AK().NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(name), None)
        if image is None:
            raise ValueError(f"unknown system symbol: {name!r}")
        image.setTemplate_(True)  # follows the menu bar's light/dark colors
        self._item.button().setImage_(image)

    @property
    def visible(self):
        return bool(self._item.isVisible())

    @visible.setter
    def visible(self, value):
        self._item.setVisible_(bool(value))

    def remove(self):
        """Take the entry out of the menu bar."""
        AK().NSStatusBar.systemStatusBar().removeStatusItem_(self._item)
