"""A Finder-like window: no title text, controls in the title bar, a file list below."""
from baremacgui import (
    App, Button, HBox, Label, SearchField, SegmentedControl, Spacer, Table, Toolbar, VBox, Window,
)

FILES = [
    ["Documents", "Folder", "Today"],
    ["Downloads", "Folder", "Yesterday"],
    ["notes.txt", "Text", "Monday"],
    ["report.pdf", "PDF", "Last week"],
    ["photo.png", "Image", "Last month"],
]

app = App("Finder style")

with Window("Files", size=(720, 460), style="unified"):
    with Toolbar():
        back = Button("", symbol="chevron.left")
        forward = Button("", symbol="chevron.right")
        view = SegmentedControl(symbols=["square.grid.2x2", "list.bullet"], selected=1)
        Spacer()
        search = SearchField(placeholder="Search", width=200)
    with VBox(padding=0, gap=0, align="stretch"):
        table = Table(["Name", "Kind", "Modified"], FILES, grow=1)
        with VBox(padding=8):
            status = Label("")


def show():
    shown = [row for row in FILES if search.text.lower() in row[0].lower()]
    table.rows = shown
    status.text = f"{len(shown)} items | view: {'icons' if view.index == 0 else 'list'}"


def say(text):
    status.text = text


back.on_click(lambda: say("Back"))
forward.on_click(lambda: say("Forward"))
view.on_change(show)
search.on_change(show)
show()
app.run()
