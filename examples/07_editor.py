"""A small text editor: menu bar, shortcuts, file dialogs, a status line, and a close check."""
from pathlib import Path

from baremacgui import (
    App, HBox, Label, Menu, MenuBar, MenuItem, MenuSeparator, Spacer, TextBox, VBox, Window,
    ask_yes_no, open_file, save_file, show_error,
)


def summary(text):
    """'12 characters, 3 words' for the status line."""
    words = len(text.split())
    return f"{len(text)} character{'s' if len(text) != 1 else ''}, {words} word{'s' if words != 1 else ''}"


app = App("Editor")
state = {"path": None, "dirty": False}

with Window("Untitled - Editor", size=(640, 460)) as win:
    with MenuBar():
        with Menu("File"):
            new_item = MenuItem("New", shortcut="Cmd+N")
            open_item = MenuItem("Open...", shortcut="Cmd+O")
            MenuSeparator()
            save_item = MenuItem("Save", shortcut="Cmd+S")
            save_as_item = MenuItem("Save As...", shortcut="Cmd+Shift+S")
        with Menu("View"):
            wrap_item = MenuItem("Show Word Count", checkable=True, checked=True)
    with VBox(padding=0, gap=0):
        editor = TextBox(multiline=True, grow=1)
        with HBox(padding=6):
            status = Label("")
            Spacer()


def refresh():
    name = Path(state["path"]).name if state["path"] else "Untitled"
    win.title = f"{'* ' if state['dirty'] else ''}{name} - Editor"
    status.text = summary(editor.text) if wrap_item.checked else ""
    status.visible = wrap_item.checked


def changed():
    state["dirty"] = True
    refresh()


def write(path):
    try:
        Path(path).write_text(editor.text, encoding="utf-8")
    except OSError as error:
        show_error(str(error), "Could not save", parent=win)
        return False
    state.update(path=path, dirty=False)
    refresh()
    return True


def save_as():
    path = save_file("Save as", default_name="note.txt", filetypes=["txt"], parent=win)
    return bool(path) and write(path)


def save():
    return write(state["path"]) if state["path"] else save_as()


def discard_ok(then):
    """Call then() at once, or after the user agreed to drop the unsaved changes."""
    if not state["dirty"]:
        then()
    else:
        ask_yes_no("Discard the unsaved changes?", "Editor", parent=win,
                   then=lambda yes: then() if yes else None)


def load(path):
    try:
        editor.text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        show_error(str(error), "Could not open", parent=win)
        return
    state.update(path=path, dirty=False)
    refresh()


def new():
    editor.text = ""
    state.update(path=None, dirty=False)
    refresh()


def choose_and_load():
    open_file("Open a text file", filetypes=["txt", "md"], parent=win,
              then=lambda path: load(path) if path else None)


editor.on_change(changed)
new_item.on_click(lambda: discard_ok(new))
open_item.on_click(lambda: discard_ok(choose_and_load))
save_item.on_click(save)
save_as_item.on_click(save_as)
wrap_item.on_click(refresh)
refresh()

if __name__ == "__main__":
    app.run()
