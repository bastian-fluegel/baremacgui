"""Table and ListBox, both on NSTableView with a Python-side data source."""
from __future__ import annotations

from ._bridge import AK, FN, make_target, table_source_class
from ._controls import Control
from ._events import event
from ._options import check_columns, check_index, check_items, check_rows


class Table(Control):
    """A scrollable table of text cells with a header row.

    columns   titles, e.g. ["Name", "Size"]
    rows      list of rows; every row has one cell per column (cells become strings)
    multiple  allow several rows to be selected
    header    show the column titles
    striped   alternating row backgrounds (off by default; modern macOS lists are plain)

    Cells are read-only. Setting .rows or the selection from code never calls
    on_select; only user input does.
    """

    on_select = event()
    on_double_click = event()

    def __init__(self, columns, rows=(), multiple=False, header=True, striped=False, grow=0, **size):
        ak = AK()
        titles = check_columns(columns)
        self._rows = check_rows(rows, len(titles))
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
        table.setUsesAlternatingRowBackgroundColors_(bool(striped))
        if hasattr(table, "setStyle_"):  # macOS 11+: rounded selection and side margins
            table.setStyle_(ak.NSTableViewStyleInset)
        table.setRowHeight_(24.0)
        table.setColumnAutoresizingStyle_(ak.NSTableViewUniformColumnAutoresizingStyle)
        self._source = table_source_class().alloc().initWithOwner_(self)  # the table holds it weakly
        table.setDataSource_(self._source)
        table.setDelegate_(self._source)

        scroll = ak.NSScrollView.alloc().init()
        scroll.setDocumentView_(table)
        scroll.setHasVerticalScroller_(True)
        scroll.setAutohidesScrollers_(True)
        scroll.setBorderType_(ak.NSNoBorder)
        self._table = table
        self._columns = titles

        size.setdefault("min_height", 120)
        size.setdefault("min_width", 200)
        super().__init__(scroll, grow, **size)
        self._bind_double(table)

    def _bind_double(self, table):
        target = make_target(self._double_clicked)
        self._targets["double"] = target
        table.setTarget_(target)
        table.setDoubleAction_(b"fire:")

    def _double_clicked(self):
        if int(self._table.clickedRow()) >= 0:  # not on the header or on empty space
            self.on_double_click.emit()

    # -- called by the data source ---------------------------------------
    def _selection_changed(self):
        if not self._muted:
            self.on_select.emit()

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


class ListBox(Table):
    """A scrollable list of text entries (a Table with one column and no header)."""

    def __init__(self, items=(), selected=None, multiple=False, striped=False, grow=0, **size):
        entries = check_items(items)
        super().__init__(["Items"], [[entry] for entry in entries], multiple=multiple,
                         header=False, striped=striped, grow=grow, **size)
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
