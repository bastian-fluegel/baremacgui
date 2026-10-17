"""A tour of the standard controls: radio buttons, drop-down, slider, switch, color well,
clipboard, list, table, progress bar."""
import threading
import time

from baremacgui import (
    App, Button, ColorWell, DropDown, HBox, Image, Label, ListBox, ProgressBar, RadioGroup, Separator, Slider,
    Spacer, Switch, Table, VBox, Window, clipboard, show_info,
)

FRUIT = ["Apple", "Banana", "Cherry", "Fig", "Grape", "Lemon", "Mango", "Orange", "Pear", "Plum"]
FILES = [
    ["notes.txt", "4 KB", "Today"],
    ["report.pdf", "1.2 MB", "Yesterday"],
    ["photo.png", "3.4 MB", "Monday"],
    ["archive.zip", "88 MB", "Last week"],
]

app = App("Widgets")

with Window("Widgets", size=(640, 520)):
    with VBox(padding=16, gap=12, align="stretch"):
        with HBox(gap=8):
            Image(symbol="slider.horizontal.3", description="Settings", width=28, height=28)
            Label("Standard controls")
        Separator()
        with HBox(gap=32):
            with VBox(gap=6):
                Label("Priority")
                priority = RadioGroup(["Low", "Normal", "High"], selected=1)
            with VBox(gap=6):
                Label("Sort by")
                sort_by = DropDown(["Name", "Size", "Date"])
                Label("Volume")
                volume = Slider(40, accessibility_label="Volume")
        with HBox(gap=8):
            Label("Notifications")
            notify = Switch(True)
            Spacer(size=16)
            Label("Accent")
            accent = ColorWell("#3366FF")
            Spacer()
            copy = Button("Copy status")
        with HBox(gap=12, grow=1, align="stretch"):
            fruit = ListBox(FRUIT, selected=0, grow=1)
            files = Table(["Name", "Size", "Modified"], FILES, grow=2)
        status = Label("")
        with HBox(gap=8):
            bar = ProgressBar(grow=1)
            run = Button("Run")


def update_status():
    chosen = ", ".join(row[0] for row in files.selected_rows) or "none"
    status.text = (
        f"Notifications {'on' if notify.checked else 'off'} | accent {accent.value} | priority {priority.text} | sort by {sort_by.text} | volume {volume.value:.0f} | "
        f"fruit {fruit.text} | files {chosen}"
    )


def set_progress(step):
    bar.value = step


def finished():
    run.enabled = True
    bar.value = 0


def work():  # worker thread: only app.invoke touches the controls
    for step in range(101):
        time.sleep(0.02)
        app.invoke(set_progress, step)
    app.invoke(finished)


def start():
    run.enabled = False
    threading.Thread(target=work, daemon=True).start()


for control in (priority, sort_by, volume, notify, accent):
    control.on_change(update_status)
fruit.on_select(update_status)
files.on_select(update_status)
files.on_double_click(
    lambda: files.selected_rows and show_info(" / ".join(files.selected_rows[0]), "Selected file")
)
run.on_click(start)
copy.on_click(lambda: setattr(clipboard, "text", status.text))
update_status()
if __name__ == "__main__":
    app.run()
