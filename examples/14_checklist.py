"""A table with a checkbox column and a column with SF Symbols (Table kinds)."""
from baremacgui import App, Label, Table, VBox, Window

ITEMS = [
    [True, ("envelope", "Answer the mail"), "Mon"],
    [False, ("cart", "Buy groceries"), "Tue"],
    [False, ("phone", "Call the plumber"), "Tue"],
    [True, ("calendar", "Book the train"), "Wed"],
    [False, ("doc.text", "Write the report"), "Fri"],
]


def progress_text(rows):
    """'2 of 5 done'."""
    return f"{sum(1 for row in rows if row[0])} of {len(rows)} done"


app = App("Checklist")

with Window("Checklist", size=(460, 320)) as win:
    with VBox(padding=16, gap=10):
        table = Table(["Done", "Task", "Day"], ITEMS, kinds=["check", "icon", "text"], sortable=True, grow=1)
        status = Label("")


def refresh():
    status.text = progress_text(table.rows)


table.on_edit(refresh)
refresh()

if __name__ == "__main__":
    app.run()
