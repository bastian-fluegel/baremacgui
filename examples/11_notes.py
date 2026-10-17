"""A notes app: SplitView with a list and an editor, notes remembered with Settings."""
from baremacgui import (
    App, Button, HBox, Label, ListBox, Settings, SplitView, Spacer, TextBox, VBox, Window,
)


def title_of(body):
    """First non-empty line, shortened, as the list entry."""
    for line in body.splitlines():
        if line.strip():
            return line.strip()[:40]
    return "(empty note)"


app = App("Notes")
prefs = Settings("example-notes", defaults={"notes": ["Welcome\nWrite something here."]})
notes = list(prefs["notes"])

with Window("Notes", size=(640, 420), autosave="example-notes") as win:
    with VBox(padding=0, gap=0):
        with SplitView(fixed=[0], min_pane=140, autosave="example-notes-split", grow=1) as split:
            with VBox(padding=8, gap=8):
                listing = ListBox([title_of(n) for n in notes], selected=0, grow=1)
                with HBox(gap=6):
                    add = Button("New")
                    remove = Button("Delete")
                    Spacer()
            with VBox(padding=8, gap=8):
                editor = TextBox("", multiline=True, grow=1)
                status = Label("")

state = {"current": None}


def show(index):
    state["current"] = index
    editor.text = notes[index] if index is not None else ""
    editor.enabled = index is not None
    remove.enabled = index is not None
    status.text = f"{len(notes)} notes"


def refresh_list(select):
    listing.items = [title_of(n) for n in notes]
    if select is not None and notes:
        listing.index = min(select, len(notes) - 1)
    show(listing.index)


def picked():
    show(listing.index)


def typed():
    index = state["current"]
    if index is None:
        return
    notes[index] = editor.text
    prefs["notes"] = notes
    listing.items = [title_of(n) for n in notes]
    listing.index = index  # setting the list from code does not fire on_select


def new_note():
    notes.append("New note")
    prefs["notes"] = notes
    refresh_list(len(notes) - 1)
    editor.text = notes[-1]


def delete_note():
    index = state["current"]
    if index is None:
        return
    del notes[index]
    prefs["notes"] = notes
    refresh_list(index if notes else None)


listing.on_select(picked)
editor.on_change(typed)
add.on_click(new_note)
remove.on_click(delete_note)
show(listing.index)

if __name__ == "__main__":
    app.run()
