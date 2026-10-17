"""Sidebar and Page: the System-Settings-style window."""
from __future__ import annotations

from . import _core
from ._bridge import AK, FN, safe_call, sidebar_source_class
from ._options import check_index, check_size


class Page:
    """One entry of a Sidebar with its content. Takes exactly one child, normally a VBox.

        with Sidebar():
            with Page("General", symbol="gearshape"):
                with VBox(padding=20): ...
    """

    def __init__(self, title, symbol=None):
        sidebar = _core.current()
        if not isinstance(sidebar, Sidebar):
            raise RuntimeError("Page goes inside a `with Sidebar():` block.")
        self.title = str(title)
        self.symbol = None if symbol is None else str(symbol)
        self._sidebar = sidebar
        self._item = None

    def accept(self, item):
        if self._item is not None:
            raise ValueError("A Page takes exactly one child. Wrap several controls in a VBox or HBox.")
        self._item = item

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        if self._item is None:
            raise ValueError(f"Page {self.title!r} is empty.")
        self._sidebar._pages.append(self)
        return False


class Sidebar:
    """A list of pages on the left, the selected page on the right.

    Use it as the only content of Window(..., style="sidebar"). selected is the
    page shown first; width is the preferred sidebar width in points. The window
    title follows the selected page, like System Settings.
    """

    def __init__(self, selected=0, width=200):
        from ._layout import Window

        window = _core.current()
        if not isinstance(window, Window) or window.style != "sidebar":
            raise RuntimeError('Sidebar goes directly inside `with Window(..., style="sidebar")`.')
        if window._sidebar is not None:
            raise ValueError("A Window has only one Sidebar.")
        self._window = window
        self._selected = selected
        self._width = check_size({"width": width})["width"]
        self._pages = []
        self._on_change = None
        self._muted = False
        self.ns = None

    def accept(self, item):
        raise ValueError("A Sidebar holds Page blocks only; put controls inside a Page.")

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        if not self._pages:
            raise ValueError("A Sidebar needs at least one Page.")
        check_index(self._selected, len(self._pages), "selected")
        ak = AK()
        window = self._window

        # Left: a source list (view-based table in the sidebar style).
        table = ak.NSTableView.alloc().init()
        column = ak.NSTableColumn.alloc().initWithIdentifier_("0")
        table.addTableColumn_(column)
        table.setHeaderView_(None)
        if hasattr(table, "setStyle_"):
            table.setStyle_(ak.NSTableViewStyleSourceList)
        else:
            table.setSelectionHighlightStyle_(ak.NSTableViewSelectionHighlightStyleSourceList)
        table.setAllowsEmptySelection_(False)
        self._source = sidebar_source_class().alloc().initWithOwner_(self)  # held weakly by the table
        table.setDataSource_(self._source)
        table.setDelegate_(self._source)
        scroll = ak.NSScrollView.alloc().init()
        scroll.setDocumentView_(table)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setDrawsBackground_(False)
        scroll.setBorderType_(ak.NSNoBorder)
        wish = scroll.widthAnchor().constraintEqualToConstant_(self._width)
        wish.setPriority_(250)  # a preference: the user can still drag the divider
        wish.setActive_(True)
        self._table = table

        # Right: all pages stacked in one container; only the selected one is visible.
        container = ak.NSView.alloc().init()
        fit_w = fit_h = 0.0
        self._views = []
        for page in self._pages:
            view = page._item.view
            size = view.fittingSize()
            fit_w, fit_h = max(fit_w, size.width), max(fit_h, size.height)
            container.addSubview_(view)
            view.setTranslatesAutoresizingMaskIntoConstraints_(False)
            view.leadingAnchor().constraintEqualToAnchor_(container.leadingAnchor()).setActive_(True)
            view.trailingAnchor().constraintEqualToAnchor_(container.trailingAnchor()).setActive_(True)
            view.bottomAnchor().constraintEqualToAnchor_(container.bottomAnchor()).setActive_(True)
            self._views.append(view)

        side_controller = ak.NSViewController.alloc().init()
        side_controller.setView_(scroll)
        content_controller = ak.NSViewController.alloc().init()
        content_controller.setView_(container)
        side_item = ak.NSSplitViewItem.sidebarWithViewController_(side_controller)
        side_item.setMinimumThickness_(min(self._width, 160.0))
        side_item.setMaximumThickness_(max(self._width * 1.6, 320.0))
        content_item = ak.NSSplitViewItem.splitViewItemWithViewController_(content_controller)
        split = ak.NSSplitViewController.alloc().init()
        split.addSplitViewItem_(side_item)
        split.addSplitViewItem_(content_item)
        self._split = split  # keep the controller alive

        window.ns.setContentViewController_(split)
        guide = container.safeAreaLayoutGuide()  # below the title bar
        for view in self._views:
            view.topAnchor().constraintEqualToAnchor_(guide.topAnchor()).setActive_(True)

        extra = 28.0
        window.ns.setContentMinSize_((160.0 + fit_w, fit_h + extra))
        width, height = window._size
        window.ns.setContentSize_((max(width, 160.0 + fit_w), max(height, fit_h + extra)))

        self._show(self._selected)
        self._select_row(self._selected)
        self.ns = split
        window._sidebar = self
        return False

    # -- internals ---------------------------------------------------------
    def _show(self, index):
        for position, view in enumerate(self._views):
            view.setHidden_(position != index)
        self._window.ns.setTitle_(self._pages[index].title)

    def _select_row(self, index):
        self._muted = True
        try:
            self._table.selectRowIndexes_byExtendingSelection_(
                FN().NSIndexSet.indexSetWithIndex_(index), False
            )
        finally:
            self._muted = False

    def _selection_changed(self):
        if self._muted:
            return
        row = int(self._table.selectedRow())
        if row < 0:
            return
        self._show(row)
        if self._on_change is not None:
            self._on_change()

    # -- public ------------------------------------------------------------
    @property
    def index(self):
        """Index of the shown page."""
        row = int(self._table.selectedRow())
        return self._selected if row < 0 else row

    @index.setter
    def index(self, value):
        check_index(value, len(self._pages), "index")
        self._show(value)
        self._select_row(value)

    @property
    def text(self):
        """Title of the shown page."""
        return self._pages[self.index].title

    def on_change(self, handler):
        """Call handler() when the user picks another page."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._on_change = handler
