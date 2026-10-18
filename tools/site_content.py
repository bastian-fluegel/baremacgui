"""Hand-written content of the documentation web app (docs/site). Used by tools/make_site.py.

Every Python snippet is compiled by `make_site.py --check`, so a typo cannot reach the site.
Nothing here claims more than the README does: what only CI has seen is marked as such.
"""

# example file stem -> screenshot in docs/screenshots (when there is one)
SCREENSHOTS = {
    "02_settings": "settings.png",
    "03_widgets": "widgets.png",
    "04_finder": "finder.png",
    "05_settings_sidebar": "sidebar.png",
    "06_everything": "file-browser.png",
    "07_editor": "editor.png",
    "08_form": "form.png",
    "09_progress": "progress.png",
    "16_showcase": "showcase.png",
}

# "I need ..." -> control names (all must exist in baremacgui)
NEEDS = [
    ("Show text", ["Label"]),
    ("Type text", ["TextBox", "SearchField", "ComboBox"]),
    ("Pick one of a few", ["DropDown", "RadioGroup", "SegmentedControl", "ComboBox"]),
    ("Turn something on or off", ["CheckBox", "Switch"]),
    ("Pick a number", ["SpinBox", "Slider"]),
    ("Pick a date or time", ["DatePicker", "TimePicker"]),
    ("Pick a color or font", ["ColorWell", "choose_color", "choose_font"]),
    ("Show progress", ["ProgressBar"]),
    ("Show many rows", ["Table", "ListBox", "Tree", "IconGrid"]),
    ("Edit cells or tick rows", ["Table"]),
    ("Take dropped files", ["DropZone", "open_file"]),
    ("Ask the user", ["show_info", "ask_yes_no", "input_box", "Sheet"]),
    ("Group and arrange", ["VBox", "HBox", "GroupBox", "TabControl", "SplitView", "Sidebar"]),
    ("Add menus and shortcuts", ["MenuBar", "MenuItem", "ContextMenu", "StatusItem"]),
    ("Tell the user in the background", ["notify", "StatusItem"]),
    ("Run something later", ["Timer"]),
    ("Remember settings", ["Settings"]),
    ("Use any AppKit view", ["Custom"]),
]

# (topic, BareMacGUI, BareWinGUI, why)
DIFFERENCES = [
    ("Table and tree", "Table, Tree", "ListView, TreeView",
     "The native classes are NSTableView and NSOutlineView, and \"Table\" is the usual Mac word."),
    ("Date field", "DatePicker(calendar=True)", "DatePicker(long=True)",
     "NSDatePicker has a calendar style; the long date format is a Windows option."),
    ("Slider ticks", "Slider(ticks=5, snap=True)", "Slider(ticks=True, tick_frequency=...)",
     "NSSlider counts its tick marks."),
    ("Dialog answers", "show_info(..., parent=win, then=handler)", "show_info(..., parent=win)",
     "On macOS a dialog with a parent is a sheet; it answers later, so `then=` gets the result."),
    ("Color result", "choose_color() returns '#RRGGBB'", "choose_color() returns (r, g, b)",
     "Same format as ColorWell.value."),
    ("Cancel in panels", "choose_color and choose_font have no Cancel", "Both return None when cancelled",
     "The system color and font panels have no OK and Cancel buttons."),
    ("Shortcut modifier", "\"Cmd+S\" (and \"Ctrl+S\" also means Cmd)", "\"Ctrl+S\"",
     "One shortcut string works on both systems."),
    ("Radio buttons", "RadioGroup(items)", "single radio buttons",
     "AppKit radio buttons need a group; one control with `items` is the shorter form."),
]

# Each topic: id, title, summary, blocks. A block is one of
#   ("p", text) ("code", python) ("shell", text) ("note", text) ("native", text) ("unverified", text)
GUIDE = [
    {
        "id": "start",
        "title": "Install and first window",
        "summary": "From a clone to a window in five minutes.",
        "blocks": [
            ("p", "You need a Mac and Python 3.10 or newer. PyObjC is installed with it. BareMacGUI is a beta, so pip needs `--pre`; the examples come with a clone."),
            ("shell", "pip install --pre baremacgui\n\n# or, to run the examples, from a clone:\ngit clone https://github.com/bastian-fluegel/baremacgui\ncd baremacgui\npython3 -m venv .venv\nsource .venv/bin/activate\npip install -e \".[examples]\"\npython examples/00_hello.py"),
            ("p", "`import baremacgui` also works on Linux and Windows, because AppKit is only loaded when a window is built. That is what lets the pure parts be tested everywhere."),
            ("p", "This is the whole first program. A `with` block builds the tree, the window shows itself when its block ends, and `app.run()` starts the event loop."),
            ("code", '''from baremacgui import App, Button, Label, VBox, Window, show_info

app = App("Hello")

with Window("Hello", size=(320, 160)) as win:
    with VBox(padding=16, gap=8):
        Label("Hello world")
        button = Button("Click me", default=True)

button.on_click(lambda: show_info("It works!", "Hello", parent=win))
app.run()'''),
            ("native", "Every control here is a real AppKit view (NSTextField, NSButton, NSStackView). Nothing is drawn by the library, so fonts, Dark Mode and the accent color come from macOS."),
        ],
    },
    {
        "id": "layout",
        "title": "Layout",
        "summary": "VBox, HBox, Spacer and the sizing options.",
        "blocks": [
            ("p", "A window holds exactly one child, normally a `VBox` (top to bottom) or an `HBox` (left to right). Controls created inside a `with` block join that box. Boxes can be nested as deep as you like."),
            ("code", '''from baremacgui import App, Button, HBox, Label, Spacer, TextBox, VBox, Window

app = App("Layout")

with Window("Layout", size=(420, 220)):
    with VBox(padding=16, gap=10):
        Label("Name")
        TextBox(placeholder="Your name")
        TextBox(multiline=True, grow=1)      # takes the free height
        with HBox(gap=8):
            Spacer()                          # pushes the buttons to the right
            Button("Cancel")
            Button("Save", default=True)

app.run()'''),
            ("p", "`grow` is a flex weight: a control with `grow=1` takes the free space, `grow=2` twice the share. `Spacer()` is flexible space, `Spacer(24)` a fixed gap of 24 points. Every control also takes `width`, `height`, `min_width`, `max_width`, `min_height` and `max_height` in points."),
            ("p", "`VBox(justify=\"center\")` (also `end` and `space_between`) places the children along the box, `align=` along the other axis. `GroupBox`, `TabControl` with `Tab`, and `SplitView` follow the same with-block pattern."),
            ("code", '''from baremacgui import App, GroupBox, Label, Tab, TabControl, VBox, Window

app = App("Tabs")

with Window("Tabs", size=(360, 240)):
    with TabControl():
        with Tab("General"):
            with VBox(padding=12):
                with GroupBox("Options"):
                    with VBox(gap=6):
                        Label("Inside a group box")
        with Tab("About"):
            with VBox(padding=12):
                Label("A second tab")

app.run()'''),
            ("native", "Boxes are NSStackView. Group boxes, tabs and split views are NSBox, NSTabView and NSSplitView."),
            ("unverified", "GroupBox and TabControl sizing and the spacing of fillers in boxes are the places most likely to need a fix after a first look on other Macs. CI screenshots look right."),
        ],
    },
    {
        "id": "events",
        "title": "Handlers and events",
        "summary": "Handlers take no arguments. Four ways to attach one.",
        "blocks": [
            ("p", "A handler is a function without arguments. If it needs the control, read the control by name: handlers are closures, so the variable is in reach."),
            ("code", '''from baremacgui import App, Button, CheckBox, Label, TextBox, VBox, Window

app = App("Events")

with Window("Events", size=(320, 200)):
    with VBox(padding=16, gap=8):
        name = TextBox(placeholder="Name", on_change=lambda: greet())   # 1. as an option
        agree = CheckBox("I agree")
        out = Label("")
        send = Button("Send")


def greet():
    out.text = "Hello " + name.text


@send.on_click                      # 2. as a decorator
def sent():
    out.text = "Sent" if agree.checked else "Please agree first"


agree.on_change(greet)              # 3. by calling the event
# 4. send.on_click = other         (assignment replaces all handlers)

app.run()'''),
            ("p", "Setting a value from code never calls the handler. `box.checked = True` does not fire `on_change`; only the user does. To run the handlers yourself, call `emit()`: `agree.on_change.emit()`."),
            ("p", "An exception inside a handler is printed and does not stop the app. Set `app.on_error = lambda exc: show_error(str(exc))` to show it in a dialog instead."),
            ("native", "Handlers are called through target-action and delegates, wrapped so a Python error never reaches AppKit."),
        ],
    },
    {
        "id": "threads",
        "title": "Background work and timers",
        "summary": "Never touch a control from another thread; hand the result back.",
        "blocks": [
            ("p", "AppKit views may only be used on the main thread. Do slow work in a thread and hand every UI change back with `app.invoke(function, *args)`."),
            ("code", '''import threading
import time

from baremacgui import App, Button, Label, ProgressBar, VBox, Window

app = App("Worker")

with Window("Worker", size=(320, 160)):
    with VBox(padding=16, gap=10):
        status = Label("Ready")
        bar = ProgressBar(0, 0, 10)
        start = Button("Start")


def work():
    for step in range(1, 11):
        time.sleep(0.3)                                  # the slow part
        app.invoke(lambda s=step: setattr(bar, "value", s))
    app.invoke(lambda: setattr(status, "text", "Done"))


def begin():
    status.text = "Working..."
    threading.Thread(target=work, daemon=True).start()


start.on_click(begin)
app.run()'''),
            ("p", "`app.call(function)` is the blocking variant: it runs the function on the UI thread, waits and returns the result. Never call it from the UI thread while that thread waits for the worker."),
            ("p", "For things that should happen every so often, use `Timer(seconds, handler)`. It runs on the UI thread, so the handler may touch controls, and it keeps ticking while a menu is open."),
            ("code", '''import datetime as dt

from baremacgui import App, Label, Timer, VBox, Window

app = App("Clock")

with Window("Clock", size=(240, 100)):
    with VBox(padding=20):
        clock = Label("")


def tick():
    clock.text = dt.datetime.now().strftime("%H:%M:%S")


Timer(1.0, tick)
tick()
app.run()'''),
        ],
    },
    {
        "id": "menus",
        "title": "Menus and shortcuts",
        "summary": "A MenuBar per window, key shortcuts, context menus and menu-bar items.",
        "blocks": [
            ("p", "Put a `MenuBar` directly inside the window. Your menus sit between the App menu and the standard Edit and Window menus, which BareMacGUI adds so that Cmd+C, Cmd+V and Cmd+Q work."),
            ("code", '''from baremacgui import App, Menu, MenuBar, MenuItem, MenuSeparator, TextBox, VBox, Window, show_info

app = App("Notes")

with Window("Notes", size=(480, 320)) as win:
    with MenuBar():
        with Menu("File"):
            new = MenuItem("New", shortcut="Cmd+N", on_click=lambda: show_info("New", parent=win))
            MenuSeparator()
            MenuItem("Wrap lines", checkable=True, checked=True)
    with VBox(padding=0):
        TextBox(multiline=True, grow=1)

app.run()'''),
            ("p", "\"Cmd\" and \"Ctrl\" in a shortcut string both mean the Command key, so one string works in BareMacGUI and BareWinGUI. `win.add_shortcut(\"F5\", handler)` adds a shortcut without a menu item. `win.default_button` is clicked by Return and `win.cancel_button` by Escape."),
            ("p", "A Mac has one menu bar. It follows the key window: a window shows its own `MenuBar`, or the standard menus if it has none. Sheets and modal windows leave it alone."),
            ("p", "`ContextMenu` is a pop-up for a right-click: build it with a `with ContextMenu() as menu:` block and assign it, for example `table.context_menu = menu`. `StatusItem` puts an entry in the menu bar; with `App(background=True)` the app has no Dock icon and keeps running without windows."),
            ("native", "Menus are NSMenu and NSMenuItem with standard responder-chain actions, the window key handling is performKeyEquivalent."),
            ("unverified", "Shortcuts, default and cancel buttons, context menus and the menu bar switching between windows are driven from code in CI. Clicking and typing them on a real Mac is still to be checked (docs/CHECKLIST.md)."),
        ],
    },
    {
        "id": "data",
        "title": "Lists, tables and trees",
        "summary": "Table with editable cells, sorting, checkboxes and symbols; ListBox, Tree, IconGrid.",
        "blocks": [
            ("p", "`Table(columns, rows)` shows rows of cells. Cells are strings, except in columns you give a kind: `\"check\"` columns hold True and False and show a checkbox; `\"icon\"` columns hold `(symbol, text)` pairs and show an SF Symbol before the text."),
            ("code", '''from baremacgui import App, Label, Table, VBox, Window

TASKS = [
    [True, ("envelope", "Answer the mail"), "9:00"],
    [False, ("cart", "Buy groceries"), "10:30"],
    [False, ("phone", "Call the plumber"), "11:15"],
]

app = App("Tasks")

with Window("Tasks", size=(460, 300)):
    with VBox(padding=16, gap=8):
        table = Table(["Done", "Task", "Due"], TASKS, kinds=["check", "icon", "text"],
                      sortable=True, grow=1)
        status = Label("")


def refresh():
    done = sum(1 for row in table.rows if row[0])
    status.text = f"{done} of {len(table.rows)} done"


table.on_edit(refresh)       # a click on a checkbox counts as an edit
refresh()
app.run()'''),
            ("p", "`editable=True` (or a list of column numbers) lets the user edit cells with a double-click; the position is in `table.edited`, the new text in `table.rows`. `sortable=True` sorts by a header click, numbers numerically and text case-insensitively. `table.sort(1)` sorts from code. `widths=[200, None, 80]` sets column widths in points (None is automatic)."),
            ("p", "Selection: `table.index` (first selected row or None), `table.indexes`, `table.selected_rows`. `on_select` fires when the user selects; `on_activate` when they double-click a row. Setting `rows` or `index` from code never fires them."),
            ("p", "`DropDown` starts with its first entry selected (`selected=0`) because it always shows one; `ComboBox`, `ListBox` and `IconGrid` start with nothing selected (`selected=None`)."),
            ("p", "`ListBox` is a one-column table with `items`, `Tree` an expandable outline (set `sidebar=True` for the translucent source-list look) and `IconGrid` a wrapping grid of icons with labels. All four take `multi=True` and share `on_select` and `on_activate`."),
            ("native", "NSTableView and NSOutlineView with view-based cells, NSCollectionView for the icon grid. One cell kind per column, not per cell."),
        ],
    },
    {
        "id": "dialogs",
        "title": "Dialogs, files and the clipboard",
        "summary": "Message boxes, file panels, sheets, drag and drop.",
        "blocks": [
            ("p", "Without `parent=` a dialog is application-modal and returns the answer. With `parent=win` it becomes a sheet on that window; give `then=handler` to receive the answer later (handler gets the result as its one argument)."),
            ("code", '''from baremacgui import App, Button, VBox, Window, ask_yes_no, open_file, show_info

app = App("Dialogs")

with Window("Dialogs", size=(300, 140)) as win:
    with VBox(padding=16, gap=8):
        ask = Button("Delete...")
        pick = Button("Open...")


def answered(yes):
    if yes:
        show_info("Deleted", parent=win)


ask.on_click(lambda: ask_yes_no("Delete this item?", "Delete", parent=win, then=answered))
pick.on_click(lambda: print(open_file("Choose a file", filetypes=[("Text", ["txt", "md"])])))
app.run()'''),
            ("p", "Also available: `show_warning`, `show_error`, `ask_ok_cancel`, `input_box`, `save_file`, `pick_folder`, `choose_color` and `choose_font`. The color and font panels have no Cancel button, so they return what is selected when the user closes them."),
            ("p", "`notify(text, title=\"\", subtitle=\"\", sound=None)` posts a banner in Notification Center, for example when a background job is done. It is posted through the system's `osascript`, so it is attributed to Script Editor and only shows if notifications are allowed for it."),
            ("p", "`DropZone` accepts files dragged from Finder, optionally limited by extension. `clipboard.text` reads and writes plain text."),
            ("code", '''from baremacgui import App, DropZone, Label, VBox, Window

app = App("Drop")

with Window("Drop", size=(360, 220)):
    with VBox(padding=16, gap=8):
        zone = DropZone("Drop pictures here", extensions=["png", "jpg"])
        names = Label("")

zone.on_drop(lambda: setattr(names, "text", ", ".join(zone.paths)))
app.run()'''),
            ("unverified", "That a `notify` banner really appears on a Mac is not checked; CI only checks that the command starts. Sheets, file panels, DropZone and the color and font panels are covered by CI through code. The real mouse drag from Finder and the look of the panels are still to be checked."),
        ],
    },
    {
        "id": "settings",
        "title": "Remembering things",
        "summary": "Settings, window position and divider positions between runs.",
        "blocks": [
            ("p", "`Settings(name, defaults=...)` is a small dictionary kept between runs. Values may be bool, int, float, str and lists or dicts of those."),
            ("code", '''from baremacgui import App, CheckBox, Settings, VBox, Window

app = App("Prefs")
prefs = Settings("my-tool", defaults={"dark_hint": True})

with Window("Prefs", size=(300, 120), autosave="my-tool-window"):
    with VBox(padding=16):
        hint = CheckBox("Show hints", checked=prefs["dark_hint"])

hint.on_change(lambda: prefs.__setitem__("dark_hint", hint.checked))
app.run()'''),
            ("p", "`Window(autosave=\"name\")` makes the window remember its position and size, and `SplitView(autosave=\"name\")` remembers the divider. Values are stored in the app's preferences (NSUserDefaults)."),
            ("unverified", "CI only checks that a second Settings object sees the values. A real quit and restart is still to be checked."),
        ],
    },
    {
        "id": "native",
        "title": "Looking native",
        "summary": "Text styles, SF Symbols, accessibility and the escape hatch.",
        "blocks": [
            ("p", "`Label(text, style=\"large_title\")` uses the system text styles (`title`, `headline`, `caption` and so on); `secondary=True` gives the grey secondary color. Buttons, menu items, pages and table cells take SF Symbol names with `symbol=`."),
            ("p", "Light and dark appearance, the accent color and the fonts follow the system. You do not set colors; a `ColorWell` or a `Switch` already is the system control."),
            ("p", "Every control takes `tooltip=` and `accessibility_label=`. Controls with visible text are read from their title; give a label to everything without text of its own: icon buttons, images, sliders, progress bars, symbol-only segmented controls."),
            ("code", '''from baremacgui import App, Button, HBox, Image, Label, Slider, VBox, Window

app = App("Native")

with Window("Native", size=(360, 200)):
    with VBox(padding=20, gap=10):
        Label("Settings", style="large_title")
        Label("These are system controls.", secondary=True)
        with HBox(gap=10):
            Image(symbol="gearshape", description="Settings", width=24, height=24)
            Slider(40, accessibility_label="Volume")
            Button("", symbol="trash", tooltip="Delete", accessibility_label="Delete")

app.run()'''),
            ("p", "When something is missing, every control has `.ns`, the underlying AppKit view, and `Custom(view)` puts any NSView into the layout. Methods of PyObjC subclasses become Objective-C selectors; mark helpers with `@objc.python_method`."),
            ("note", "Needs Swift, not Python: widgets, App Intents and Live Activities. BareMacGUI does not try to cover them."),
        ],
    },
    {
        "id": "package",
        "title": "Make it an .app",
        "summary": "A double-clickable bundle with name and icon.",
        "blocks": [
            ("shell", 'python -m baremacgui build my_script.py --name "My Tool" --icon icon.png'),
            ("p", "This creates `My Tool.app` next to where you run it: an Info.plist, your script and a small launcher. Options: `--dest`, `--identifier`, `--version`, `--background` (menu-bar app without Dock icon), `--include` (extra files or folders, repeatable). From code: `baremacgui.build_app(...)`."),
            ("note", "The bundle starts the Python that built it, so it only runs on that Mac and stops working when that Python is removed. It is not signed or notarized. For a bundle that starts without Python, use `--standalone` (below)."),
            ("shell", 'pip install "baremacgui[standalone]"\npython -m baremacgui build my_script.py --standalone'),
            ("p", "`--standalone` bundles an own interpreter and PyObjC with PyInstaller and signs the app ad hoc (`codesign --sign -`, no identity). It is bytecode in a bundle, not compiled machine code. On the Mac that built it the app starts without a warning; a copy downloaded elsewhere is blocked by Gatekeeper until the user allows it, because it is not notarized. From code: `baremacgui.build_standalone(...)`."),
            ("p", "To hand an app to someone, the install creator makes a disk image (`.dmg`, with a link to Applications) or a ZIP, with a window or from the terminal:"),
            ("shell", 'python -m baremacgui installer\npython -m baremacgui build my_script.py --system-icon GenericApplicationIcon --dmg --zip\npython -m baremacgui icons --filter folder'),
            ("p", "The window is a wizard in four steps: script and name, icon (a file, a folder of icons or the icons macOS ships, with a preview), what the script needs (extra files and folders, packages to take along; imports found in the script are listed), and what to make. `Save settings` writes a `*.bmc.json` file that `build --spec file.bmc.json` or `installer file.bmc.json` reads again. From code: `baremacgui.BuildSpec` and `baremacgui.create_installer(spec)`. The creator itself is built with BareMacGUI (example 17)."),
            ("unverified", "A standalone app of example 16 starts on the author's Intel Mac (macOS 15.5), also from a ZIP copied and unpacked there. Not checked: the Gatekeeper dialog for a downloaded copy, Apple Silicon, other macOS versions, the install creator window and disk images (CI only builds them)."),
            ("unverified", "CI builds a bundle and runs its launcher. Double-clicking in Finder, the Finder icon and the Dock name and icon are still to be checked."),
        ],
    },
    {
        "id": "limits",
        "title": "What is checked",
        "summary": "Where the claims on this site come from.",
        "blocks": [
            ("p", "The author cannot run macOS code in the place where the library is developed. So three levels exist, and the docs keep them apart."),
            ("p", "Checked by CI: every control and container is built on macOS runners (Intel and Apple Silicon, Python 3.10 and 3.14), properties and handlers are exercised from code, and screenshots of the examples are taken in light and dark appearance."),
            ("p", "Not checked: real mouse and keyboard behavior, anything that needs a restart or another app, other macOS versions, and how VoiceOver speaks the labels. The list is in docs/CHECKLIST.md, and each page of this guide marks its own open points."),
            ("p", "The library is a beta (0.1.0b1). Names are decided; small changes can still happen."),
        ],
    },
]
