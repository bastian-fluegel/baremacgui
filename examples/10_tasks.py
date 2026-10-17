"""An editable, sortable table: double-click a cell to edit it, click a header to sort."""
from baremacgui import App, Button, HBox, Label, Spacer, Table, VBox, Window

TASKS = [
    ["Write the report", "3", "Open"],
    ["Call the plumber", "1", "Open"],
    ["Book the train", "2", "Done"],
    ["buy stamps", "5", "Open"],
]


def open_count(rows):
    """How many rows have the status 'Open'."""
    return sum(1 for row in rows if row[2].strip().casefold() == "open")


app = App("Tasks")

with Window("Tasks", size=(520, 360), autosave="example-tasks") as win:
    with VBox(padding=16, gap=10):
        table = Table(["Task", "Priority", "Status"], TASKS, editable=[0, 1, 2], sortable=True, grow=1)
        status = Label("")
        with HBox(gap=8):
            add = Button("Add")
            remove = Button("Remove")
            Spacer()
            show = Button("Sort by priority")


def refresh():
    status.text = f"{len(table.rows)} tasks, {open_count(table.rows)} open"
    remove.enabled = table.index is not None


def add_task():
    table.rows = table.rows + [["New task", "9", "Open"]]
    table.index = len(table.rows) - 1
    refresh()


def remove_task():
    keep = [row for i, row in enumerate(table.rows) if i not in table.indexes]
    table.rows = keep
    refresh()


table.on_edit(refresh)
table.on_select(refresh)
add.on_click(add_task)
remove.on_click(remove_task)
show.on_click(lambda: table.sort(1))
refresh()

if __name__ == "__main__":
    app.run()
