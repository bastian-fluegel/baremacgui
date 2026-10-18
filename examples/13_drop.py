"""Drag files from Finder onto the window: a DropZone collects them in a table."""
import os

from baremacgui import App, Button, DropZone, HBox, Label, Spacer, Table, VBox, Window


def human_size(size):
    """1536 -> '1.5 KB'."""
    value = float(size)
    for unit in ("bytes", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{int(value)} bytes" if unit == "bytes" else f"{value:.1f} {unit}"
        value /= 1024


app = App("Drop")

with Window("Drop files", size=(520, 380)) as win:
    with VBox(padding=16, gap=10):
        zone = DropZone("Drop files here (folders are fine too)")
        table = Table(["Name", "Size", "Folder"], [], widths=[220, 90, None], grow=1)
        with HBox(gap=8):
            summary = Label("Nothing dropped yet")
            Spacer()
            clear = Button("Clear")


def received():
    for path in zone.paths:
        size = "" if os.path.isdir(path) else human_size(os.path.getsize(path))
        table.rows = table.rows + [[os.path.basename(path), size, os.path.dirname(path)]]
    summary.text = f"{len(table.rows)} item(s)"


def clear_all():
    table.rows = []
    summary.text = "Nothing dropped yet"


zone.on_drop(received)
clear.on_click(clear_all)

if __name__ == "__main__":
    app.run()
