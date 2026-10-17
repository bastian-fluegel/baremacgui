"""IconGrid (icon view) and Tree (outline view)."""
from __future__ import annotations

from ._bridge import AK, FN, icon_classes, make_target, outline_source_class
from ._controls import Control
from ._events import event
from ._options import check_icon_items, check_index, check_nodes, find_node_path


def _symbol_image(symbol):
    if not symbol:
        return None
    image = AK().NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(symbol), None)
    if image is None:
        raise ValueError(f"unknown system symbol: {symbol!r}")
    return image


class IconGrid(Control):
    """Icons with a label underneath in a wrapping grid, like Finder's icon view.

    items        labels, or (label, symbol) pairs; symbol is an SF Symbol name
    symbol       the symbol for plain labels (default "doc")
    icon_size    icon edge in points
    multiple     allow several icons to be selected
    selected     index selected at the start

    Selecting from code never calls on_select; only user input does.
    """

    on_select = event()
    on_double_click = event()

    def __init__(self, items=(), symbol="doc", icon_size=64, multiple=False, selected=None, grow=0, **size):
        ak = AK()
        if isinstance(icon_size, bool) or not isinstance(icon_size, (int, float)) or icon_size < 16:
            raise ValueError(f"icon_size must be a number >= 16, got {icon_size!r}")
        self._default_symbol = str(symbol)
        _symbol_image(self._default_symbol)  # fail early on a bad default
        self._entries = check_icon_items(items, self._default_symbol)
        for _, entry_symbol in self._entries:
            _symbol_image(entry_symbol)  # fail early, not while drawing
        self._icon_size = float(icon_size)
        self._muted = False
        self._images = {}

        view_class, item_class, source_class = icon_classes()
        view = view_class.alloc().initWithFrame_(((0, 0), (400, 300)))
        layout = ak.NSCollectionViewFlowLayout.alloc().init()
        layout.setItemSize_((self._icon_size + 32.0, self._icon_size + 48.0))
        layout.setMinimumInteritemSpacing_(8.0)
        layout.setMinimumLineSpacing_(8.0)
        layout.setSectionInset_(self._insets(12.0))
        view.setCollectionViewLayout_(layout)
        view.setSelectable_(True)
        view.setAllowsMultipleSelection_(bool(multiple))
        view.setAutoresizingMask_(ak.NSViewWidthSizable)
        view.registerClass_forItemWithIdentifier_(item_class, "BareMacIcon")
        self._source = source_class.alloc().initWithOwner_(self)  # held weakly by the view
        view.setDataSource_(self._source)
        view.setDelegate_(self._source)

        scroll = ak.NSScrollView.alloc().init()
        scroll.setDocumentView_(view)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setBorderType_(ak.NSNoBorder)
        self._view = view
        size.setdefault("min_height", 140)
        size.setdefault("min_width", 200)
        super().__init__(scroll, grow, **size)
        view._double = self.on_double_click.emit
        if selected is not None:
            self.index = selected

    @staticmethod
    def _insets(value):
        module = AK()
        make = getattr(module, "NSEdgeInsetsMake", None) or getattr(FN(), "NSEdgeInsetsMake")
        return make(value, value, value, value)

    def _image(self, symbol):  # called by the data source
        if symbol not in self._images:
            self._images[symbol] = _symbol_image(symbol)
        return self._images[symbol]

    def _selection_changed(self):
        if not self._muted:
            self.on_select.emit()

    def _menu_view(self):
        return self._view

    # -- items -------------------------------------------------------------
    @property
    def items(self):
        return [label for label, _ in self._entries]

    @items.setter
    def items(self, values):
        entries = check_icon_items(values, self._default_symbol)
        for _, symbol in entries:
            _symbol_image(symbol)
        self._entries = entries
        self._muted = True
        try:
            self._view.reloadData()
        finally:
            self._muted = False

    # -- selection ---------------------------------------------------------
    @property
    def indexes(self):
        """Indexes of all selected icons, ascending."""
        return sorted(int(path.item()) for path in self._view.selectionIndexPaths())

    @property
    def index(self):
        found = self.indexes
        return found[0] if found else None

    @index.setter
    def index(self, value):
        self._muted = True
        try:
            if value is None:
                self._view.setSelectionIndexPaths_(FN().NSSet.set())
            else:
                check_index(value, len(self._entries), "index")
                path = FN().NSIndexPath.indexPathForItem_inSection_(value, 0)
                self._view.setSelectionIndexPaths_(FN().NSSet.setWithObject_(path))
        finally:
            self._muted = False

    @property
    def text(self):
        """Label of the selected icon, or None."""
        position = self.index
        return None if position is None else self._entries[position][0]

    @property
    def texts(self):
        return [self._entries[position][0] for position in self.indexes]

    @property
    def enabled(self):
        return bool(self._view.isSelectable())

    @enabled.setter
    def enabled(self, flag):
        self._view.setSelectable_(bool(flag))



class _Node:
    """Python-side tree node handed to NSOutlineView as the item object."""

    __slots__ = ("text", "symbol", "children", "parent")

    def __init__(self, spec, parent=None):
        self.text = spec["text"]
        self.symbol = spec["symbol"]
        self.parent = parent
        self.children = [_Node(child, self) for child in spec["children"]]

    def path(self):
        node, found = self, []
        while node is not None:
            found.append(node.text)
            node = node.parent
        return found[::-1]


class Tree(Control):
    """An expandable tree (outline view), e.g. a folder tree.

    nodes     list of "Label", ("Label", [children]) or
              {"text": ..., "symbol": SF Symbol name, "children": [...]}
    sidebar   use the translucent source-list look (for a left-hand navigation pane)
    expanded  open all branches at the start
    multiple  allow several rows to be selected

    Selecting from code (path = [...]) never calls on_select; only user input does.
    """

    on_select = event()
    on_double_click = event()

    def __init__(self, nodes=(), sidebar=False, expanded=False, multiple=False, grow=0, **size):
        ak = AK()
        self._specs = check_nodes(nodes)
        self._roots = [_Node(spec) for spec in self._specs]
        self._muted = False
        self._images = {}
        self._check_symbols(self._specs)

        view = ak.NSOutlineView.alloc().init()
        column = ak.NSTableColumn.alloc().initWithIdentifier_("0")
        view.addTableColumn_(column)
        view.setOutlineTableColumn_(column)
        view.setHeaderView_(None)
        if hasattr(view, "setStyle_"):
            view.setStyle_(ak.NSTableViewStyleSourceList if sidebar else ak.NSTableViewStyleInset)
        elif sidebar:
            view.setSelectionHighlightStyle_(ak.NSTableViewSelectionHighlightStyleSourceList)
        view.setRowHeight_(24.0)
        view.setAllowsMultipleSelection_(bool(multiple))
        view.setColumnAutoresizingStyle_(ak.NSTableViewUniformColumnAutoresizingStyle)
        self._source = outline_source_class().alloc().initWithOwner_(self)  # held weakly by the view
        view.setDataSource_(self._source)
        view.setDelegate_(self._source)

        scroll = ak.NSScrollView.alloc().init()
        scroll.setDocumentView_(view)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setBorderType_(ak.NSNoBorder)
        if sidebar:
            scroll.setDrawsBackground_(False)
        self._view = view
        size.setdefault("min_height", 120)
        size.setdefault("min_width", 160)
        super().__init__(scroll, grow, **size)
        target = make_target(self._double_clicked)
        self._targets["double"] = target
        view.setTarget_(target)
        view.setDoubleAction_(b"fire:")
        if expanded:
            self.expand_all()

    def _check_symbols(self, specs):
        for spec in specs:
            _symbol_image(spec["symbol"])
            self._check_symbols(spec["children"])

    def _image(self, symbol):  # called by the data source
        if not symbol:
            return None
        if symbol not in self._images:
            self._images[symbol] = _symbol_image(symbol)
        return self._images[symbol]

    def _selection_changed(self):
        if not self._muted:
            self.on_select.emit()

    def _menu_view(self):
        return self._view

    def _double_clicked(self):
        if int(self._view.clickedRow()) >= 0:
            self.on_double_click.emit()

    def _node_at(self, row):
        return self._view.itemAtRow_(row)

    # -- content -----------------------------------------------------------
    @property
    def nodes(self):
        """The tree as normalized dicts (text, symbol, children)."""
        return self._specs

    @nodes.setter
    def nodes(self, values):
        specs = check_nodes(values)
        self._check_symbols(specs)
        self._specs = specs
        self._roots = [_Node(spec) for spec in specs]
        self._muted = True
        try:
            self._view.reloadData()
        finally:
            self._muted = False

    def expand_all(self):
        self._view.expandItem_expandChildren_(None, True)

    def collapse_all(self):
        self._view.collapseItem_collapseChildren_(None, True)

    # -- selection ---------------------------------------------------------
    @property
    def path(self):
        """Labels from the top down to the selected row, e.g. ["Home", "Documents"]; None if nothing is selected."""
        row = int(self._view.selectedRow())
        return None if row < 0 else self._node_at(row).path()

    @path.setter
    def path(self, texts):
        self._muted = True
        try:
            if texts is None:
                self._view.deselectAll_(None)
                return
            texts = list(texts)
            if find_node_path(self._specs, texts) is None or not texts:
                raise ValueError(f"no such tree path: {texts!r}")
            node = None
            level = self._roots
            for text in texts:
                node = next(candidate for candidate in level if candidate.text == text)
                if node.children:
                    self._view.expandItem_(node)
                level = node.children
            row = int(self._view.rowForItem_(node))
            self._view.selectRowIndexes_byExtendingSelection_(FN().NSIndexSet.indexSetWithIndex_(row), False)
            self._view.scrollRowToVisible_(row)
        finally:
            self._muted = False

    @property
    def text(self):
        """Label of the selected row, or None."""
        found = self.path
        return None if found is None else found[-1]

    @property
    def paths(self):
        """Paths of all selected rows."""
        selection = self._view.selectedRowIndexes()
        missing = FN().NSNotFound
        found, position = [], selection.firstIndex()
        while position != missing:
            found.append(self._node_at(int(position)).path())
            position = selection.indexGreaterThanIndex_(position)
        return found

    @property
    def enabled(self):
        return bool(self._view.isEnabled())

    @enabled.setter
    def enabled(self, flag):
        self._view.setEnabled_(bool(flag))
