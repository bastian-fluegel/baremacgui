"""A small file browser that uses the newer pieces together:

Finder-style window with a Toolbar, a source-list Tree, a Table and an IconGrid that you switch
between, a Popover (info button), a Sheet (new folder), sheet dialogs (delete) and Custom.
The file system is fake: it only lives in this script.
"""
from AppKit import NSColorWell

from baremacgui import (
    App, Button, CheckBox, Custom, HBox, IconGrid, Label, Popover, SearchField, SegmentedControl,
    Separator, Sheet, Spacer, Table, TextBox, Toolbar, Tree, VBox, Window, ask_yes_no, show_info,
)

FILES = {
    "Home": [["Documents", "Folder", "Today"], ["Downloads", "Folder", "Yesterday"],
             ["Pictures", "Folder", "Monday"], ["notes.txt", "Text", "Monday"]],
    "Documents": [["Reports", "Folder", "Today"], ["report.pdf", "PDF", "Last week"],
                  ["budget.txt", "Text", "Last month"]],
    "Reports": [["2026.pdf", "PDF", "Today"], ["2025.pdf", "PDF", "Last year"]],
    "Downloads": [["archive.zip", "Archive", "Yesterday"], ["setup.dmg", "Archive", "Tuesday"]],
    "Pictures": [["beach.png", "Image", "August"], ["family.png", "Image", "June"]],
}
SYMBOL = {"Folder": "folder", "Text": "doc.text", "PDF": "doc.richtext", "Image": "photo",
          "Archive": "doc.zipper"}

app = App("Files")

with Window("Files", size=(980, 600), style="unified") as win:
    with Toolbar():
        view = SegmentedControl(symbols=["square.grid.2x2", "list.bullet"], selected=1)
        Spacer()
        info_button = Button("", symbol="info.circle")
        new_button = Button("", symbol="folder.badge.plus")
        delete_button = Button("", symbol="trash")
        search = SearchField(placeholder="Search", width=180)
    with HBox(gap=0, align="stretch"):
        tree = Tree(
            [{"text": "Home", "symbol": "house", "children": [
                {"text": "Documents", "symbol": "folder", "children": [
                    {"text": "Reports", "symbol": "folder"}]},
                {"text": "Downloads", "symbol": "arrow.down.circle"},
                {"text": "Pictures", "symbol": "photo.on.rectangle"},
            ]}],
            sidebar=True, expanded=True, width=210,
        )
        with VBox(gap=0, grow=1, align="stretch"):
            table = Table(["Name", "Kind", "Modified"], [], grow=1)
            grid = IconGrid([], icon_size=56, grow=1)
            with VBox(padding=8):
                status = Label("")

with Popover() as info:
    with VBox(padding=14, gap=8):
        info_title = Label("")
        info_detail = Label("")
        Separator()
        with HBox(gap=8):
            Label("Label colour")
            Custom(NSColorWell.alloc().init(), width=44, height=24)
        CheckBox("Show hidden files")

with Sheet(win, size=(380, 150)) as new_sheet:
    with VBox(padding=20, gap=12):
        Label("Name of the new folder")
        new_name = TextBox(placeholder="Untitled folder")
        with HBox(gap=8):
            Spacer()
            cancel = Button("Cancel")
            create = Button("Create", default=True)


def folder():
    return tree.text or "Home"


def shown_rows():
    query = search.text.lower()
    return [row for row in FILES.get(folder(), []) if query in row[0].lower()]


def refresh():
    rows = shown_rows()
    table.rows = rows
    grid.items = [(row[0], SYMBOL.get(row[1], "doc")) for row in rows]
    mode = "icons" if view.index == 0 else "list"
    status.text = f"{' / '.join(tree.path or ['Home'])} | {len(rows)} items | {mode}"


def set_view():
    table.visible = view.index == 1
    grid.visible = view.index == 0
    refresh()


def selected_name():
    chosen = grid.text if view.index == 0 else (table.selected_rows[0][0] if table.selected_rows else None)
    return chosen


def open_selected():
    name = selected_name()
    if name is None:
        return
    try:
        tree.path = (tree.path or ["Home"]) + [name]
    except ValueError:
        show_info(f"'{name}' is not a folder in this demo.", "Open", parent=win, then=lambda _: None)
        return
    refresh()


def show_info_popover():
    name = selected_name() or folder()
    info_title.text = name
    info_detail.text = f"{len(shown_rows())} items in {folder()}"
    info.show(info_button, edge="bottom")


def open_new_sheet():
    new_name.text = ""
    new_sheet.show()


def create_folder():
    name = new_name.text.strip()
    if name:
        FILES.setdefault(folder(), []).append([name, "Folder", "Now"])
        refresh()
    new_sheet.close()


def delete_selected():
    name = selected_name()
    if name is None:
        show_info("Select an item first.", "Delete", parent=win, then=lambda _: None)
        return

    def after(yes):
        if yes:
            FILES[folder()] = [row for row in FILES[folder()] if row[0] != name]
            refresh()

    ask_yes_no(f"Delete '{name}'?", "Delete", parent=win, then=after)


tree.path = ["Home"]
tree.on_select(refresh)
view.on_change(set_view)
search.on_change(refresh)
table.on_double_click(open_selected)
grid.on_double_click(open_selected)
info_button.on_click(show_info_popover)
new_button.on_click(open_new_sheet)
delete_button.on_click(delete_selected)
cancel.on_click(new_sheet.close)
create.on_click(create_folder)
set_view()
app.run()
