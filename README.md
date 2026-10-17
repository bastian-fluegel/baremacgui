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
- **Containers:** `GroupBox`, `TabControl` with `Tab`.
- **Dialogs:** `show_info`, `show_warning`, `show_error`, `ask_yes_no`, `open_file`, `save_file`, `choose_folder`.
- **Menu bar:** the standard App, Edit and Window menus, so Cmd+C, Cmd+V, Cmd+A and Cmd+Q work.
- **Threads:** run slow work in a thread and hand the result back with `app.invoke(function, *args)`. Controls are never touched from other threads.

Handlers are plain functions without arguments. Exceptions inside a handler are printed to the terminal; they do not crash the app.

Examples: `examples/` has a hello window, a security-header checker (a real small tool), a settings window with tabs, a tour of the standard controls and a Finder-style window.

## What is verified

Checked by hand on an Intel Mac (macOS 15.5) with Python 3.14 and PyObjC 12.2.2, in dark appearance (light appearance only with an early prototype):
- All four examples start and render: boxes, `Spacer`, `TextBox`, `ComboBox`, `Button`, `CheckBox`, `SpinBox`, `GroupBox`, `TabControl` (General tab), `RadioGroup`, `DropDown`, `Slider`, `ProgressBar` (driven from a worker thread via `App.invoke`), `Image` (SF Symbol), `Separator`, `ListBox`, `Table`, `HBox(align="stretch")`, `show_info`, `on_click`, `on_change`, `on_select` and `on_double_click`.
- Example 03 also looked right in light appearance.
- The test suite passes on macOS (`python -m pytest`: 42 passed, 3 skipped, the skipped ones are the non-macOS tests).

Not yet checked on real hardware:
- `Window(style="unified")`, `Toolbar`, `SearchField`, `SegmentedControl`, `Button(symbol=...)` and example 04 (written, never run on a Mac).
- The Advanced tab, `ask_yes_no`, the file dialogs.
- The menu bar shortcuts (Cmd+C, Cmd+V, Cmd+A, Cmd+Q).
- Light appearance for the other examples.
- Apple Silicon, other macOS versions, multiple displays.
- The CI workflow itself.

## Limits

- macOS only, standard AppKit controls only. No custom drawing, no rich text, no editable tables, no column sorting.
- Needs PyObjC. "Bare" here means thin, not dependency-free.
- Dialogs are application-modal; there are no window-modal sheets yet.
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
