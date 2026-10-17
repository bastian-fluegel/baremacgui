"""Table and ListBox, both on NSTableView with a Python-side data source."""
from __future__ import annotations

from ._bridge import AK, FN, make_target, table_source_class
from ._collections import _symbol_image
from ._controls import Control
from ._events import event
from ._options import check_columns, check_editable, check_index, check_items, check_kinds, check_rows, sort_order


class Table(Control):
    """A scrollable table of text cells with a header row.

    columns   titles, e.g. ["Name", "Size"]
    rows      list of rows; every row has one cell per column (cells become strings)
    multiple  allow several rows to be selected
    header    show the column titles
    striped   alternating row backgrounds (off by default; modern macOS lists are plain)

    editable  True, or a list of column indexes: double-click a cell to edit it (on_edit fires; the
              position is in .edited, the new text is in .rows)
    sortable  clicking a column header sorts by it (numbers numerically, text case-insensitive)
    kinds     one entry per column: "text" (default), "check" or "icon".
              A "check" column shows a checkbox per row; its cells are True/False and the user toggles
              them (on_edit fires, .edited holds the position). An "icon" column shows an SF Symbol
              before the text; its cells are (symbol, text) tuples, or a plain string for no icon.

    Setting .rows, the selection or the sort order from code never calls the handlers; only user
    input does.

    Native counterpart: NSTableView with view-based cells (NSTableCellView with a text field, an image
    view, or an NSButton checkbox). Difference: one cell kind per column, not per row.
    """

    on_edit = event()
    on_sort = event()

    on_select = event()
    on_double_click = event()

    def __init__(self, columns, rows=(), multiple=False, header=True, striped=False, grow=0,
                 editable=False, sortable=False, kinds=None, **size):
        ak = AK()
        titles = check_columns(columns)
        self._kinds = check_kinds(kinds, len(titles))
        self._rows = self._checked(rows, len(titles))
        self._muted = False
        self._quiet = False
        self._sorted_by = None
        self.edited = None
        self._editable = check_editable(editable, len(titles))

        table = ak.NSTableView.alloc().init()
        for position, title in enumerate(titles):
            column = ak.NSTableColumn.alloc().initWithIdentifier_(str(position))
            column.setTitle_(title)
            column.setEditable_(False)
            if sortable:
                column.setSortDescriptorPrototype_(ak.NSSortDescriptor.sortDescriptorWithKey_ascending_(str(position), True))
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

    def _checked(self, rows, width):
        """Validated rows; the symbols of icon cells must exist."""
        result = check_rows(rows, width, self._kinds)
        for row in result:
            for kind, cell in zip(self._kinds, row):
                if kind == "icon" and cell[0]:
                    _symbol_image(cell[0])
        return result

    def _menu_view(self):
        return self._table

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

    def _sort_changed(self):
        if self._quiet:
            return
        descriptors = self._table.sortDescriptors()
        if not len(descriptors):
            return
        first = descriptors[0]
        self._apply_sort(int(str(first.key())), bool(first.ascending()))
        self.on_sort.emit()

    def _apply_sort(self, column, ascending):
        chosen = [self._rows[i] for i in self.indexes]
        order = sort_order(self._rows, column, ascending)
        self._rows = [self._rows[i] for i in order]
        self._sorted_by = (column, ascending)
        self._muted = True
        try:
            self._table.reloadData()
            keep = [i for i, row in enumerate(self._rows) if any(row is c for c in chosen)]
            if keep:
                indexes = FN().NSMutableIndexSet.indexSet()
                for i in keep:
                    indexes.addIndex_(i)
                self._table.selectRowIndexes_byExtendingSelection_(indexes, False)
        finally:
            self._muted = False

    def _edited(self, field):
        row = int(self._table.rowForView_(field))
        column = int(self._table.columnForView_(field))
        if row < 0 or column < 0:
            return
        text = str(field.stringValue())
        old = self._rows[row][column]
        if self._kinds[column] == "icon":
            if text == old[1]:
                return
            self._rows[row][column] = (old[0], text)
        else:
            if text == old:
                return
            self._rows[row][column] = text
        self.edited = (row, column)
        self.on_edit.emit()

    def _toggled(self, button):
        row = int(self._table.rowForView_(button))
        column = int(self._table.columnForView_(button))
        if row < 0 or column < 0 or self._kinds[column] != "check":
            return
        self._rows[row][column] = int(button.state()) == int(AK().NSControlStateValueOn)
        self.edited = (row, column)
        self.on_edit.emit()

    @property
    def sorted_by(self):
        """(column, ascending) of the current sort, or None."""
        return self._sorted_by

    def sort(self, column, ascending=True):
        """Sort by a column from code (the header arrow follows). Does not call on_sort."""
        sort_order(self._rows, column, ascending)  # validates the column
        self._quiet = True
        try:
            descriptor = AK().NSSortDescriptor.sortDescriptorWithKey_ascending_(str(column), bool(ascending))
            self._table.setSortDescriptors_([descriptor])
            self._apply_sort(column, bool(ascending))
        finally:
            self._quiet = False

    # -- rows --------------------------------------------------------------
    @property
    def rows(self):
        return [list(row) for row in self._rows]

    @rows.setter
    def rows(self, values):
        self._rows = [list(row) for row in self._checked(values, len(self._columns))]
        if self._sorted_by is not None:
            column, ascending = self._sorted_by
            self._rows = [self._rows[i] for i in sort_order(self._rows, column, ascending)]
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
