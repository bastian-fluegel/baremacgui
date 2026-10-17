# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). Before 1.0 anything may change between releases.

## [Unreleased]

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
