# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Before 1.0 anything may change between releases.

## [Unreleased]

### Added
- Every control accepts `tooltip=` and `accessibility_label=` (also as properties); `Image(description=...)`. The examples label their icon-only controls.
- Example 15: several windows, each with its own menus.
- `Settings`: values that survive between runs (NSUserDefaults, one domain per app name). Example 02 uses it.
- `Window(autosave="name")`: the window remembers its position and size (NSWindow frame autosave).
- `python -m baremacgui build script.py` / `build_app()`: wraps a script in a double-clickable `.app` (Info.plist, launcher, icon from .icns or .png). Unsigned and tied to the Python that built it. `App(icon=...)` sets the Dock icon.
- `Table(kinds=[...])`: a column of checkboxes (`"check"`, cells True/False, toggling calls `on_edit`) or of SF Symbols with text (`"icon"`, cells `(symbol, text)`). Example 14.
- `DropZone`: accepts files dragged from Finder (NSDraggingDestination on an NSBox), optional extension filter, `on_drop`, `paths`. Example 13 shows it.
- `Switch` (NSSwitch), `ColorWell` (NSColorWell, hex string value) and `clipboard` (NSPasteboard text). Example 03 shows them.
- `Table(editable=..., sortable=True)`: edit cells in place (`on_edit`, `.edited`), sort by clicking a header (`on_sort`, `.sorted_by`, `.sort(column)`). Example 10.
- `SplitView`: panes with draggable dividers (NSSplitView), `fixed=`, `min_pane=`, `autosave=`, `set_position`. Example 11 (notes).
- `StatusItem` (NSStatusItem with a menu) and `App(background=True)` for menu-bar apps without Dock icon. Example 12.

### Fixed
- A window without its own `MenuBar` kept the menus of the window before it; the standard menus now come back when it becomes key. Sheets and modal windows leave the menu bar alone.

## [0.1.0a1] - unreleased

First tagged state of the project. Alpha: the automated tests build real AppKit views on macOS CI runners
(Apple Silicon and Intel), but real mouse and keyboard behaviour is only checked by hand and partly not at all
(see "Verified and unverified" in the README). Please report what you find.

### Added
- Windows from `with` blocks: `Window` (standard, unified and sidebar styles), `VBox`, `HBox`, `Spacer`, `GroupBox`,
  `TabControl`/`Tab`, `Sidebar`/`Page`, `Toolbar`, `Sheet`, `Popover`; box options `padding`, `gap`, `align`,
  `justify`, `grow`, sizes.
- Controls: `Label`, `TextBox` (single line, multi line, password), `ComboBox`, `DropDown`, `Button` (with SF Symbols),
  `CheckBox`, `RadioGroup`, `SpinBox`, `Slider`, `ProgressBar`, `Image`, `Separator`, `SearchField`,
  `SegmentedControl`, `DatePicker`, `TimePicker`, `ListBox`, `Table`, `IconGrid`, `Tree`, and `Custom` for any NSView.
- Events: every control event is an `Event` (`on_click=` option, `on_click(handler)`, decorator use, several handlers,
  assignment). Handlers take no arguments. Exceptions in handlers go to `App.on_error` or the terminal.
- `App`: `invoke` and `call` hand work to the UI thread, `on_error`, standard App/Edit/Window menus.
- Window: `on_close` (return `False` to keep it open), `on_resize`, `on_destroy`, `size`, `add_shortcut`,
  `default_button`, `cancel_button`, `show_modal`.
- Menus: `MenuBar`, `Menu`, `MenuItem` (shortcuts, check marks, SF Symbols), `MenuSeparator`, `ContextMenu`.
- `Timer`.
- Dialogs: `show_info`, `show_warning`, `show_error`, `ask_yes_no`, `ask_ok_cancel`, `input_box`, `open_file`,
  `save_file`, `choose_folder`; with `parent=` they become sheets (`then=` for the answer).
- Errors: `BareMacGUIError`, `PlatformError`, `LayoutError`.
- Seven runnable examples and a screenshot workflow that runs them on a macOS runner.
