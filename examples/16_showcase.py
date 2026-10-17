"""Showcase: one window with most of what BareMacGUI does, all of it real AppKit.

A System-Settings-style sidebar window; a sortable table with checkboxes and SF Symbols; an icon grid
with a segmented control and search field; switch, color well, slider with tick marks and a calendar;
text styles. Light and dark appearance, the accent color and every control come from the system.
"""
import datetime as dt

from baremacgui import (
    App, ColorWell, DatePicker, DropZone, HBox, IconGrid, Label, Page, ProgressBar, SearchField,
    SegmentedControl, Separator, Sidebar, Slider, Spacer, Switch, Table, VBox, Window,
)

TASKS = [
    [True, ("envelope", "Answer the mail"), "9:00"],
    [True, ("cart", "Buy groceries"), "10:30"],
    [False, ("phone", "Call the plumber"), "11:15"],
    [False, ("calendar", "Book the train to Munich"), "13:00"],
    [False, ("doc.text", "Write the quarterly report"), "15:30"],
    [False, ("bicycle", "Evening ride"), "18:30"],
]

LIBRARY = [
    ("Photos", "photo.on.rectangle"), ("Music", "music.note"), ("Movies", "film"), ("Books", "book"),
    ("Podcasts", "mic"), ("Maps", "map"), ("Notes", "note.text"), ("Mail", "envelope"),
    ("Calendar", "calendar"), ("Contacts", "person.crop.circle"), ("Weather", "cloud.sun"),
    ("Clock", "clock"),
]


def progress_text(rows):
    """'2 of 6 done'."""
    return f"{sum(1 for row in rows if row[0])} of {len(rows)} done"


def share_done(rows):
    """Finished share of the tasks, 0 to 100."""
    return 100.0 * sum(1 for row in rows if row[0]) / len(rows) if rows else 0.0


def filter_library(items, text):
    """The (name, symbol) pairs whose name contains `text`, ignoring case."""
    needle = text.strip().casefold()
    return [item for item in items if needle in item[0].casefold()]


app = App("Atelier")

with Window("Atelier", size=(900, 600), style="sidebar") as win:
    with Sidebar(selected=0, width=210) as sidebar:
        with Page("Today", symbol="checkmark.circle"):
            with VBox(padding=28, gap=10):
                Label("Today", style="large_title")
                Label(dt.date.today().strftime("%A, %d %B"), secondary=True)
                Spacer(6)
                table = Table(["Done", "Task", "Due"], TASKS, kinds=["check", "icon", "text"], sortable=True,
                              grow=1, accessibility_label="Tasks")
                with HBox(gap=12):
                    bar = ProgressBar(share_done(TASKS), accessibility_label="Share of tasks done")
                    summary = Label(progress_text(TASKS), secondary=True)
        with Page("Library", symbol="books.vertical"):
            with VBox(padding=28, gap=10):
                Label("Library", style="large_title")
                with HBox(gap=10):
                    SegmentedControl(symbols=["square.grid.2x2", "list.bullet"], selected=0,
                                     accessibility_label="View as icons or list")
                    Spacer()
                    search = SearchField(placeholder="Search library", width=220, accessibility_label="Search library")
                grid = IconGrid(LIBRARY, icon_size=48, grow=1, accessibility_label="Library")
                DropZone("Drop files here to import", height=64)
        with Page("Appearance", symbol="paintpalette"):
            with VBox(padding=28, gap=12):
                Label("Appearance", style="large_title")
                Label("Everything here is a system control, so it follows light and dark mode.", secondary=True)
                Spacer(8)
                with HBox():
                    Label("Accent color", style="headline")
                    Spacer()
                    accent = ColorWell("#0A84FF", accessibility_label="Accent color")
                Separator()
                with HBox():
                    Label("Reduce motion", style="headline")
                    Spacer()
                    Switch(False, accessibility_label="Reduce motion")
                Separator()
                with HBox():
                    Label("Text size", style="headline")
                    Spacer()
                    size_slider = Slider(3, 1, 5, ticks=5, snap=True, width=220, accessibility_label="Text size")
                Separator()
                with HBox():
                    Label("Density", style="headline")
                    Spacer()
                    SegmentedControl(["Compact", "Comfortable", "Spacious"], selected=1, accessibility_label="Density")
                Separator()
                with HBox():
                    Label("Next review", style="headline")
                    Spacer()
                    DatePicker(dt.date.today() + dt.timedelta(days=14), accessibility_label="Next review")
                Spacer()
        with Page("About", symbol="info.circle"):
            with VBox(padding=28, gap=8):
                Label("Atelier", style="large_title")
                Label("A demo window built with BareMacGUI: about 100 lines of Python, no Xcode, no Swift.",
                      secondary=True)
                Spacer()


def refresh_tasks():
    rows = table.rows
    bar.value = share_done(rows)
    summary.text = progress_text(rows)


def refresh_library():
    grid.items = filter_library(LIBRARY, search.text)


table.on_edit(refresh_tasks)
search.on_change(refresh_library)

if __name__ == "__main__":
    app.run()
