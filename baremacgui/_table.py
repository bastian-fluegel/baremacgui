"""Table and ListBox, both on NSTableView with a Python-side data source."""
from __future__ import annotations

from ._bridge import AK, FN, make_target, table_source_class
from ._controls import Control
from ._options import check_columns, check_index, check_items, check_rows


class Table(Control):
    """A scrollable table of text cells with a header row.

    columns   titles, e.g. ["Name", "Size"]
    rows      list of rows; every row has one cell per column (cells become strings)
    multiple  allow several rows to be selected
    header    show the column titles

    Cells are read-only. Setting .rows or the selection from code never calls
    on_select; only user input does.
    """

    def __init__(self, columns, rows=(), multiple=False, header=True, grow=0, **size):
        ak = AK()
        titles = check_columns(columns)
        self._rows = check_rows(rows, len(titles))
        self._on_select = None
        self._muted = False

        table = ak.NSTableView.alloc().init()
        for position, title in enumerate(titles):
            column = ak.NSTableColumn.alloc().initWithIdentifier_(str(position))
            column.setTitle_(title)
            column.setEditable_(False)
            table.addTableColumn_(column)
        if not header:
            table.setHeaderView_(None)
        table.setAllowsMultipleSelection_(bool(multiple))
        table.setUsesAlternatingRowBackgroundColors_(True)
        table.setColumnAutoresizingStyle_(ak.NSTableViewUniformColumnAutoresizingStyle)
        self._source = table_source_class().alloc().initWithOwner_(self)  # the table holds it weakly
        table.setDataSource_(self._source)
        table.setDelegate_(self._source)

        scroll = ak.NSScrollView.alloc().init()
        scroll.setDocumentView_(table)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setBorderType_(ak.NSBezelBorder)
        self._table = table
        self._columns = titles

        size.setdefault("min_height", 120)
        size.setdefault("min_width", 200)
        super().__init__(scroll, grow, **size)

    # -- called by the data source ---------------------------------------
    def _selection_changed(self):
        if not self._muted and self._on_select is not None:
            self._on_select()

    # -- rows --------------------------------------------------------------
    @property
    def rows(self):
        return [list(row) for row in self._rows]

    @rows.setter
    def rows(self, values):
        self._rows = check_rows(values, len(self._columns))
        self._muted = True
        try:
            self._table.reloadData()
        finally:
            self._muted = False

    # -- selection ---------------------------------------------------------
    @property
    def indexes(self):
        """Indexes of all selected rows, ascending."""
        selection = self._table.selectedRowIndexes()
        missing = FN().NSNotFound
        found = []
        position = selection.firstIndex()
        while position != missing:
            found.append(int(position))
            position = selection.indexGreaterThanIndex_(position)
        return found

    @property
    def index(self):
        """Index of the selected row (the first one if several), or None."""
        row = int(self._table.selectedRow())
        return None if row < 0 else row

    @index.setter
    def index(self, value):
        self._muted = True
        try:
            if value is None:
                self._table.deselectAll_(None)
            else:
                check_index(value, len(self._rows), "index")
                self._table.selectRowIndexes_byExtendingSelection_(
                    FN().NSIndexSet.indexSetWithIndex_(value), False
                )
                self._table.scrollRowToVisible_(value)
        finally:
            self._muted = False

    @property
    def selected_rows(self):
        return [list(self._rows[position]) for position in self.indexes]

    @property
    def enabled(self):
        return bool(self._table.isEnabled())

    @enabled.setter
    def enabled(self, flag):
        self._table.setEnabled_(bool(flag))

    # -- handlers ----------------------------------------------------------
    def on_select(self, handler):
        """Call handler() when the user changes the selection."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._on_select = handler

    def on_double_click(self, handler):
        """Call handler() when the user double-clicks a row."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        target = make_target(handler)
        self._targets["double"] = target
        self._table.setTarget_(target)
        self._table.setDoubleAction_(b"fire:")


class ListBox(Table):
    """A scrollable list of text entries (a Table with one column and no header)."""

    def __init__(self, items=(), selected=None, multiple=False, grow=0, **size):
        entries = check_items(items)
        super().__init__(["Items"], [[entry] for entry in entries], multiple=multiple,
                         header=False, grow=grow, **size)
        if selected is not None:
            check_index(selected, len(entries), "selected")
            self.index = selected

    @property
    def items(self):
        return [row[0] for row in self._rows]

    @items.setter
    def items(self, values):
        self.rows = [[entry] for entry in check_items(values)]

    @property
    def text(self):
        """Text of the selected entry, or None."""
        position = self.index
        return None if position is None else self._rows[position][0]

    @property
    def texts(self):
        """Texts of all selected entries."""
        return [self._rows[position][0] for position in self.indexes]
