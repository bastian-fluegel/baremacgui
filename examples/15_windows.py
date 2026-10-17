"""Several windows: each document window has its own menus, and the menu bar follows the key window."""
from baremacgui import App, HBox, Label, Menu, MenuBar, MenuItem, MenuSeparator, Spacer, TextBox, VBox, Window

app = App("Documents")
counter = {"made": 0, "open": 0}


def new_document():
    counter["made"] += 1
    counter["open"] += 1
    number = counter["made"]
    with Window(f"Document {number}", size=(420, 280)) as doc:
        with MenuBar():
            with Menu("File"):
                MenuItem("New Document", shortcut="Cmd+N", on_click=new_document)
                MenuSeparator()
                MenuItem(f"Rename to 'Document {number} (renamed)'", on_click=lambda: setattr(doc, "title", f"Document {number} (renamed)"))
            with Menu(f"Only in document {number}"):
                MenuItem("Say hello", on_click=lambda: setattr(info, "text", f"Hello from document {number}"))
        with VBox(padding=12, gap=8):
            info = Label(f"Document {number}: this window's menu is 'Only in document {number}'.")
            TextBox(multiline=True, grow=1)
            with HBox():
                Spacer()
                Label("Cmd+N makes another one")
    doc.on_destroy(lambda: counter.update(open=counter["open"] - 1))
    return doc


first = new_document()

if __name__ == "__main__":
    app.run()
