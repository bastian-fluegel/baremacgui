"""A Finder-like window: no title text, controls in the title bar, a browsable file list."""
from baremacgui import (
    App, Button, Label, SearchField, SegmentedControl, Spacer, Table, Toolbar, VBox, Window,
)

# A small fake file system: folder name -> rows (name, kind, modified)
TREE = {
    "Home": [
        ["Documents", "Folder", "Today"],
        ["Downloads", "Folder", "Yesterday"],
        ["notes.txt", "Text", "Monday"],
    ],
    "Documents": [
        ["Reports", "Folder", "Today"],
        ["report.pdf", "PDF", "Last week"],
        ["photo.png", "Image", "Last month"],
    ],
    "Downloads": [["archive.zip", "Archive", "Yesterday"], ["setup.dmg", "Disk image", "Tuesday"]],
    "Reports": [["2026.pdf", "PDF", "Today"], ["2025.pdf", "PDF", "Last year"]],
}

history = ["Home"]
position = 0

app = App("Finder style")

with Window("Files", size=(720, 460), style="unified"):
    with Toolbar():
        back = Button("", symbol="chevron.left", tooltip="Back", accessibility_label="Back")
        forward = Button("", symbol="chevron.right", tooltip="Forward", accessibility_label="Forward")
        view = SegmentedControl(symbols=["square.grid.2x2", "list.bullet"], selected=1, accessibility_label="View as icons or list")
        Spacer()
        search = SearchField(placeholder="Search", width=200, accessibility_label="Search")
    with VBox(padding=0, gap=0, align="stretch"):
        table = Table(["Name", "Kind", "Modified"], [], grow=1)
        with VBox(padding=8):
            status = Label("")


def show():
    folder = history[position]
    query = search.text.lower()
    rows = [row for row in TREE[folder] if query in row[0].lower()]
    table.rows = rows
    back.enabled = position > 0
    forward.enabled = position < len(history) - 1
    status.text = f"{folder} | {len(rows)} items | {'icons' if view.index == 0 else 'list'} view"


def go(folder):
    global history, position
    history = history[: position + 1] + [folder]
    position += 1
    search.text = ""
    show()


def step(delta):
    global position
    position += delta
    search.text = ""
    show()


def open_selected():
    rows = table.selected_rows
    if rows and rows[0][1] == "Folder" and rows[0][0] in TREE:
        go(rows[0][0])


back.on_click(lambda: step(-1))
forward.on_click(lambda: step(1))
table.on_double_click(open_selected)
view.on_change(show)
search.on_change(show)
show()
app.run()
