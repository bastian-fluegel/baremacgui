"""The install creator: a wizard window, built with BareMacGUI itself.

    python -m baremacgui installer [script.py | settings.bmc.json]

Four steps (App, Icon, Needs, Build). The build runs in a worker thread; its output lines are handed back
with App.invoke. The same builds work without a window: `python -m baremacgui build --dmg ...`.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import threading
import time
from types import SimpleNamespace

from . import _installer as inst
from ._app import App
from ._controls import Button, CheckBox, Label, TextBox
from ._dialogs import open_file, pick_folder, save_file
from ._layout import HBox, Spacer, VBox, Window
from ._table import ListBox
from .errors import BareMacGUIError
from ._widgets import Image, ProgressBar, RadioGroup, SearchField, Separator

STEPS = (
    ("Your app", "Which script, and what should the app be called?"),
    ("Icon", "Pick the icon the app shows in Finder and the Dock."),
    ("What it needs", "Files next to the script and packages to take along."),
    ("Build", "Choose what to make, then build."),
)
ICON_SOURCES = ("Plain default icon", "An icon file", "A folder of icons", "Icons from macOS")


def lines_of(text):
    """The non-empty, stripped lines of a text."""
    return [line.strip() for line in str(text).splitlines() if line.strip()]


def build(app=None, path=None, window_args=None):
    """Create the wizard window. Returns a namespace with the controls and handler functions (for tests and
    screenshots); `run` is the normal way to start it."""
    app = app or App("Install Creator")
    state = SimpleNamespace(setting=False, step=0, icon_choices=[], name_is_auto=True, building=False, results=[])
    start = inst.BuildSpec()
    if path and str(path).endswith(".py"):
        start.script = str(path)
    elif path:
        start = inst.load_spec(path)
    pyinstaller_ok = importlib.util.find_spec("PyInstaller") is not None

    with Window("Install Creator", size=(680, 560), **(window_args or {})) as win:
        with VBox(padding=20, gap=10):
            title = Label(STEPS[0][0], style="title")
            hint = Label(STEPS[0][1], secondary=True)
            Separator()

            # ---- step 1: the app -------------------------------------------------------------
            with VBox(gap=10, grow=1) as page_app:
                Label("Script")
                with HBox(gap=8):
                    script = TextBox(start.script, placeholder="my_script.py", grow=1)
                    pick_script = Button("Choose…")
                Label("App name")
                name = TextBox(start.name, placeholder="My Tool")
                with HBox(gap=8):
                    Label("Version")
                    version = TextBox(start.version, width=80)
                    Label("Identifier")
                    identifier = TextBox(start.identifier, placeholder="optional, e.g. com.example.mytool", grow=1)
                background = CheckBox("Menu-bar app (no Dock icon)", checked=start.background)

            # ---- step 2: the icon ------------------------------------------------------------
            with VBox(gap=10, grow=1) as page_icon:
                with HBox(gap=16, grow=1):
                    with VBox(gap=8, width=220):
                        icon_source = RadioGroup(ICON_SOURCES, selected=0)
                        pick_icon = Button("Choose file…")
                        icon_filter = SearchField(placeholder="Filter")
                        Spacer()
                    with VBox(gap=8, grow=1):
                        icon_list = ListBox([], grow=1)
                    with VBox(gap=8, width=140):
                        preview = Image(symbol="doc", description="Icon preview", width=128, height=128)
                        icon_label = Label("Default", secondary=True)
                        Spacer()

            # ---- step 3: needs ---------------------------------------------------------------
            with VBox(gap=10, grow=1) as page_needs:
                found = Label("", secondary=True)
                Label("Files and folders the script reads (they are put into the app)")
                include_list = ListBox([], grow=1)
                with HBox(gap=8):
                    add_file = Button("Add file…")
                    add_folder = Button("Add folder…")
                    remove_include = Button("Remove")
                    Spacer()
                Label("Packages to take along completely, one per line (only if the app misses one)")
                packages = TextBox("\n".join(start.packages), multiline=True, height=60)

            # ---- step 4: build ---------------------------------------------------------------
            with VBox(gap=10, grow=1) as page_build:
                make_dmg = CheckBox("Disk image (.dmg), to hand out", checked="dmg" in start.outputs)
                make_zip = CheckBox("ZIP", checked="zip" in start.outputs)
                make_app = CheckBox("The app itself", checked="app" in start.outputs)
                standalone = CheckBox("Runs without Python on the other Mac (needs PyInstaller)",
                                      checked=start.standalone)
                with HBox(gap=8):
                    Label("Save to")
                    dest = TextBox(start.dest if start.dest != "." else os.path.expanduser("~/Desktop"), grow=1)
                    pick_dest = Button("Choose…")
                warning = Label("", secondary=True)
                bar = ProgressBar(0, indeterminate=True)
                log = TextBox("", multiline=True, readonly=True, grow=1, height=120)
                with HBox(gap=8):
                    status = Label("", grow=1)
                    show = Button("Show in Finder")

            problem = Label("", secondary=True)
            Separator()
            with HBox(gap=8):
                save = Button("Save settings…")
                Spacer()
                back = Button("Back")
                nxt = Button("Next", default=True)

    pages = (page_app, page_icon, page_needs, page_build)
    bar.visible = False
    show.visible = False

    # ---- state -> spec ------------------------------------------------------------------------------
    def outputs():
        return [kind for kind, box in (("dmg", make_dmg), ("zip", make_zip), ("app", make_app)) if box.checked]

    def current_icon():
        index = icon_source.index
        if index == 0:
            return ""
        if index == 1:
            return getattr(state, "file_icon", "")
        row = icon_list.index
        return state.icon_choices[row][1] if row is not None and row < len(state.icon_choices) else ""

    def spec():
        return inst.BuildSpec(
            script=script.text.strip(), name=name.text.strip(), identifier=identifier.text.strip(),
            version=version.text.strip() or "1.0", icon=current_icon(), background=background.checked,
            standalone=standalone.checked, include=list(include_list.items), packages=lines_of(packages.text),
            hidden_imports=list(start.hidden_imports), outputs=outputs(), dest=dest.text.strip() or ".")

    def problem_for(step):
        """Why the wizard cannot leave `step` yet, or None. Only the fields up to that step count."""
        current = spec()
        if not current.script:
            return "Choose your script."
        if step < 3:
            current.outputs = ["app"]
        if step < 2:
            current.include, current.packages = [], []
        if step < 1:
            current.icon = ""
        try:
            inst.check_spec(current)
        except ValueError as exc:
            return str(exc)
        return None

    # ---- step handling ------------------------------------------------------------------------------
    def refresh():
        for position, page in enumerate(pages):
            page.visible = position == state.step
        title.text, hint.text = STEPS[state.step]
        reason = problem_for(state.step)
        problem.text = reason or ""
        last = state.step == len(STEPS) - 1
        nxt.text = "Build" if last else "Next"
        nxt.enabled = reason is None and not state.building
        back.enabled = state.step > 0 and not state.building
        save.enabled = not state.building
        warning.text = ("PyInstaller is not installed: python -m pip install pyinstaller"
                        if standalone.checked and not pyinstaller_ok else "")
        if last and standalone.checked and not pyinstaller_ok:
            nxt.enabled = False

    def go_back():
        state.step = max(0, state.step - 1)
        refresh()

    def go_next():
        if state.building or problem_for(state.step):
            return
        if state.step == len(STEPS) - 1:
            begin_build()
            return
        state.step += 1
        if state.step == 2:
            scan_script()
        refresh()

    # ---- step 1 -------------------------------------------------------------------------------------
    def choose_script():
        def chosen(path):
            if path:
                script.text = path
                script_changed()

        chosen(open_file("Choose your script", filetypes=["py"]))

    def script_changed():
        if state.name_is_auto:
            guess = inst.default_name(script.text) if script.text.strip() else ""
            state.setting = True
            name.text = guess
            state.setting = False
        refresh()

    def name_typed():
        if not state.setting:
            state.name_is_auto = False
        refresh()

    # ---- step 2 -------------------------------------------------------------------------------------
    def load_icon_choices():
        index = icon_source.index
        if index == 3:
            state.all_icons = inst.system_icons()
        elif index == 2 and getattr(state, "icon_folder", None):
            state.all_icons = inst.local_icons(state.icon_folder)
        else:
            state.all_icons = []
        filter_icons()

    def filter_icons():
        needle = icon_filter.text.strip().lower()
        state.icon_choices = [(n, p) for n, p in getattr(state, "all_icons", []) if needle in n.lower()]
        icon_list.items = [n for n, _ in state.icon_choices]
        show_icon()

    def icon_source_changed():
        index = icon_source.index
        pick_icon.visible = index in (1, 2)
        pick_icon.text = "Choose file…" if index == 1 else "Choose folder…"
        icon_filter.visible = index in (2, 3)
        icon_list.visible = index in (2, 3)
        load_icon_choices()

    def choose_icon():
        def got_file(path):
            if path:
                state.file_icon = path
            show_icon()

        def got_folder(path):
            if path:
                state.icon_folder = path
                load_icon_choices()
            show_icon()

        if icon_source.index == 1:
            got_file(open_file("Choose an icon", filetypes=["png", "icns"]))
        else:
            got_folder(pick_folder("Choose a folder with icons"))

    def show_icon():
        chosen = current_icon()
        try:
            if chosen:
                preview.path = chosen
                icon_label.text = os.path.splitext(os.path.basename(chosen))[0]
            else:
                preview.path = None
                icon_label.text = "Default"
        except (OSError, ValueError):
            preview.path = None
            icon_label.text = "Cannot show this icon"
        refresh()

    # ---- step 3 -------------------------------------------------------------------------------------
    def scan_script():
        try:
            with open(script.text.strip(), encoding="utf-8") as handle:
                modules = inst.detect_imports(handle.read())
        except (OSError, SyntaxError, ValueError):
            found.text = "Could not read the script to look for imports."
            return
        if not modules:
            found.text = "The script imports nothing outside Python itself and BareMacGUI."
            return
        parts = [f"{m} ({'installed' if inst.is_installed(m) else 'not installed'})" for m in modules]
        found.text = "Found in your script: " + ", ".join(parts) + ". Installed ones are taken along by themselves."

    def add_files():
        def chosen(paths):
            if paths:
                include_list.items = list(include_list.items) + [c for c in paths if c not in include_list.items]
            refresh()

        chosen(open_file("Add files", multiple=True))

    def add_folders():
        def chosen(path):
            if path and path not in include_list.items:
                include_list.items = list(include_list.items) + [path]
            refresh()

        chosen(pick_folder("Add a folder"))

    def remove_included():
        row = include_list.index
        if row is not None:
            include_list.items = [p for i, p in enumerate(include_list.items) if i != row]
        refresh()

    # ---- step 4 -------------------------------------------------------------------------------------
    def choose_dest():
        def chosen(path):
            if path:
                dest.text = path
            refresh()

        chosen(pick_folder("Where should the results go?"))

    def save_settings():
        def chosen(target):
            if target:
                inst.save_spec(spec(), target)
                status.text = f"Settings saved: {os.path.basename(target)}"

        chosen(save_file("Save settings", default_name=(name.text.strip() or "app") + inst.SPEC_SUFFIX))

    def begin_build():
        reason = problem_for(3)
        if reason:
            problem.text = reason
            return
        chosen = inst.check_spec(spec())
        state.building = True
        state.results = []
        log.text = ""
        status.text = "Building… this takes a minute or two."
        bar.visible = True
        show.visible = False
        refresh()
        pending, last_flush = [], [time.monotonic()]

        def append(lines):
            log.text = log.text + "\n".join(lines) + "\n"

        def say(line):  # worker thread: only app.invoke touches the window
            pending.append(line)
            if time.monotonic() - last_flush[0] > 0.3:
                batch, pending[:] = list(pending), []
                last_flush[0] = time.monotonic()
                app.invoke(append, batch)

        def finished(made, error):
            state.building = False
            bar.visible = False
            if pending:
                append(list(pending))
                pending.clear()
            if error:
                status.text = "Failed: " + error
            else:
                state.results = made
                status.text = "Done: " + ", ".join(os.path.basename(m) for m in made)
                show.visible = True
            refresh()

        def work():
            made, error = [], None
            try:
                made = inst.create_installer(chosen, log=say)
            except (BareMacGUIError, OSError, ValueError, subprocess.CalledProcessError) as exc:
                error = str(exc)
            app.invoke(finished, made, error)

        threading.Thread(target=work, daemon=True).start()

    def show_in_finder():
        if state.results:
            subprocess.run(["open", "-R", state.results[0]], check=False)

    # ---- wiring -------------------------------------------------------------------------------------
    script.on_change(script_changed)
    name.on_change(name_typed)
    for control in (version, identifier, dest):
        control.on_change(refresh)
    for control in (background, make_dmg, make_zip, make_app, standalone):
        control.on_change(refresh)
    packages.on_change(refresh)
    pick_script.on_click(choose_script)
    icon_source.on_change(icon_source_changed)
    icon_filter.on_change(filter_icons)
    icon_list.on_select(show_icon)
    pick_icon.on_click(choose_icon)
    add_file.on_click(add_files)
    add_folder.on_click(add_folders)
    remove_include.on_click(remove_included)
    pick_dest.on_click(choose_dest)
    save.on_click(save_settings)
    show.on_click(show_in_finder)
    back.on_click(go_back)
    nxt.on_click(go_next)

    if start.script:
        state.name_is_auto = not start.name
        if not start.name:
            state.setting = True
            name.text = inst.default_name(start.script)
            state.setting = False
    if start.include:
        include_list.items = [str(p) for p in start.include]
    icon_source_changed()
    refresh()

    def settle_layout():
        """Hiding the other pages after the window was built leaves stale frames until the next layout pass;
        until then a mouse click can miss its button (seen on a real Mac: "Choose" did nothing)."""
        try:
            win.ns.contentView().layoutSubtreeIfNeeded()
            win.ns.displayIfNeeded()
        except Exception:  # noqa: BLE001 - cosmetic safety net
            pass

    settle_layout()
    try:
        from PyObjCTools import AppHelper

        AppHelper.callLater(0.2, settle_layout)
    except ImportError:
        pass
    wizard = SimpleNamespace(**{k: v for k, v in locals().items() if not k.startswith("_")})
    # AppKit holds button targets weakly: keep every control and handler alive as long as the app lives,
    # even when the caller drops the return value (seen on a real Mac: "Choose" did nothing).
    app._wizard = wizard
    return wizard


def run(path=None):
    """Open the wizard and run the app."""
    app = App("Install Creator")
    wizard = build(app, path)  # keep it: see build()
    app.run()
    del wizard
