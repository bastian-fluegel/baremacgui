"""Toolbar: controls in the title bar of a Window."""
from __future__ import annotations

from . import _core
from ._bridge import AK, toolbar_delegate_class


class Toolbar:
    """Put controls into the window's title bar. Use it directly inside a Window:

        with Window("Files", style="unified"):
            with Toolbar():
                Button("", symbol="chevron.left")
                Spacer()
                SearchField()
            with VBox(): ...

    Controls appear left to right. Spacer() is flexible space, Spacer(size=n) a
    fixed gap. Controls keep their natural size unless you give width/min_width.
    """

    def __init__(self):
        from ._layout import Window  # local: _layout imports this module's siblings

        window = _core.current()
        if not isinstance(window, Window):
            raise RuntimeError("Toolbar goes directly inside a `with Window(...)` block.")
        if window._toolbar is not None:
            raise ValueError("A Window has only one Toolbar.")
        self._window = window
        self._items = []
        self.ns = None

    def accept(self, item):
        self._items.append(item)

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        ak = AK()
        entries = []
        for number, item in enumerate(self._items):
            if item.spacer:
                if item.fixed is not None:
                    entries.append((ak.NSToolbarSpaceItemIdentifier, None))
                else:
                    entries.append((ak.NSToolbarFlexibleSpaceItemIdentifier, None))
            else:
                entries.append((f"baremacgui.item.{number}", item.view))
        toolbar = ak.NSToolbar.alloc().initWithIdentifier_("baremacgui.toolbar")
        delegate = toolbar_delegate_class().alloc().initWithEntries_(entries)
        toolbar.setDelegate_(delegate)
        toolbar.setDisplayMode_(ak.NSToolbarDisplayModeIconOnly)
        toolbar.setAllowsUserCustomization_(False)
        self._delegate = delegate  # NSToolbar holds its delegate weakly
        self.ns = toolbar
        self._window._toolbar = self
        self._window.ns.setToolbar_(toolbar)
        return False
