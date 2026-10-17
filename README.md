# baremacgui

A thin Python layer for native macOS windows. Real AppKit controls through PyObjC, put together with short `with` blocks. No own drawing layer, no widget toolkit of its own: Dark Mode, system fonts and standard behaviour come from macOS.

Same API shape as [BareWinGUI](https://github.com/bastian-fluegel/barewingui), its Windows sibling.

> **Status: pre-alpha.** The API will change. See "What is verified" below.

```python
from baremacgui import App, Button, Label, VBox, Window, show_info

app = App("Hello")

with Window("Hello", size=(320, 160)) as win:
    with VBox(padding=16, gap=8):
        Label("Hello world")
        button = Button("Click me", default=True)

button.on_click(lambda: show_info("It works!", "Hello", parent=win))
app.run()
```

## Install

Not on PyPI yet. From a clone:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[examples]"
python examples/00_hello.py
```

Needs macOS and Python 3.10 or newer. The one dependency is PyObjC (`pyobjc-framework-Cocoa`), installed automatically.

## What it offers

- **Layout:** `Window`, `VBox`, `HBox`, `Spacer`. Flexbox-like: `grow` weights, `padding`, `gap`, `align`, `width`/`height`/`min_*`/`max_*`. The minimum window size follows from the content.
- **Controls:** `Label`, `TextBox` (single and multi-line), `ComboBox`, `DropDown` (the standard pop-up menu), `Button`, `CheckBox`, `RadioGroup`, `SpinBox`, `Slider`, `ProgressBar`, `Image` (file or system symbol), `Separator`, `SearchField`, `SegmentedControl`, `ListBox` and `Table` (read-only text cells, single or multiple selection).
- **Finder-style window:** `Window(..., style="unified")` hides the title text and lets the content start below a transparent title bar; `with Toolbar():` puts buttons (`Button("", symbol="chevron.left")`), `SegmentedControl`, `SearchField` and `Spacer` into that title bar. See `examples/04_finder.py`.
- **Settings-style window:** `Window(..., style="sidebar")` with `with Sidebar():` and one `with Page("General", symbol="gearshape"):` per entry: a system sidebar on the left, the selected page on the right, window title follows the page. See `examples/05_settings_sidebar.py`.
- **Icon view and tree:** `IconGrid` (icons with labels in a wrapping grid, SF Symbols) and `Tree` (expandable outline, optional source-list look; select by path).
- **Containers:** `GroupBox`, `TabControl` with `Tab`.
- **Sheets and popovers:** `Sheet(parent_window)` is a window built like a `Window` that slides down over its parent; `Popover` is a bubble next to a control (`popover.show(button)`).
- **Escape hatch:** `Custom(view)` puts any AppKit view you made yourself into the layout; every control exposes its view as `.ns`.
- **Dialogs:** `show_info`, `show_warning`, `show_error`, `ask_yes_no`, `open_file`, `save_file`, `choose_folder`. Give `parent=window` to get a sheet on that window; with `then=function` the call returns at once and function(result) runs later.
- **Menu bar:** the standard App, Edit and Window menus, so Cmd+C, Cmd+V, Cmd+A and Cmd+Q work.
- **Threads:** run slow work in a thread and hand the result back with `app.invoke(function, *args)`. Controls are never touched from other threads.

Handlers are plain functions without arguments. Exceptions inside a handler are printed to the terminal; they do not crash the app.

Examples: `examples/` has a hello window, a security-header checker (a real small tool), a settings window with tabs, a tour of the standard controls, a Finder-style window, a settings window with a sidebar, and a small file browser (`06_everything.py`) that combines toolbar, tree, table, icon grid, popover, sheet and sheet dialogs.

## What is verified

Checked by hand on an Intel Mac (macOS 15.5) with Python 3.14 and PyObjC 12.2.2, in dark appearance (light appearance only with an early prototype):
- All four examples start and render: boxes, `Spacer`, `TextBox`, `ComboBox`, `Button`, `CheckBox`, `SpinBox`, `GroupBox`, `TabControl` (General tab), `RadioGroup`, `DropDown`, `Slider`, `ProgressBar` (driven from a worker thread via `App.invoke`), `Image` (SF Symbol), `Separator`, `ListBox`, `Table`, `HBox(align="stretch")`, `show_info`, `on_click`, `on_change`, `on_select` and `on_double_click`.
- Example 03 also looked right in light appearance.
- `Window(style="sidebar")` with `Sidebar` and `Page` (example 05: sidebar with symbols, page switching, window title following the page, `on_change`) in dark appearance.
- `Window(style="unified")` with `Toolbar`, `SearchField`, `SegmentedControl` and icon `Button`s (example 04) in dark appearance; the view-based `Table` restyle and the navigation added to the example afterwards were not rechecked.
- The test suite passes on macOS (`python -m pytest`: 53 passed, 3 skipped, the skipped ones are the non-macOS tests).

Not yet checked on real hardware:
- `IconGrid`, `Tree`, `Custom`, `Sheet`, `Popover`, sheet dialogs (`parent=`, `then=`), `Control.visible` and example 06 (written, never run on a Mac). The most fragile: the blocking sheet form (without `then`), the double-click on icons, and hiding/showing the table and icon grid in example 06.
- `Sidebar` details: dragging the divider, hiding it, the minimum window size, light appearance.
- Example 04 after the `Table` restyle: back/forward navigation, double-click into folders, search filter, light appearance.
- The Advanced tab, `ask_yes_no`, the file dialogs.
- The menu bar shortcuts (Cmd+C, Cmd+V, Cmd+A, Cmd+Q).
- Light appearance for the other examples.
- Apple Silicon, other macOS versions, multiple displays.
- The CI workflow itself.

## Limits

- macOS only, standard AppKit controls only. No custom drawing, no rich text, no editable tables, no column sorting.
- Needs PyObjC. "Bare" here means thin, not dependency-free.
- Dialogs without `parent` are application-modal. With `parent` and without `then`, the call waits through a nested modal loop (see the unverified list); `then=` is the dependable form.
- Menu labels are English.
- Running a script from a terminal gives a plain Python process: the menu bar title and Dock icon are Python's. A packaged `.app` is a separate step.

## Development

Design, decisions and acceptance testing are by the author. Most of the code, tests and documentation were written by an AI (Claude, Anthropic) to the author's specification. Anything marked unverified above has not been run on a Mac yet.

```
pip install -e ".[test]"
python -m pytest
```

Off macOS only the pure-Python tests run; the control tests are skipped.

## License

MIT, see `LICENSE`.
