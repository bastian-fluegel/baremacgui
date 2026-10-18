# Checklist: from beta to 1.0

Tick a box only when it is really done. "Checked by CI" means a test builds the object on a macOS runner;
it does not mean a person clicked it.

## Done
- [x] Tests run automatically on Ubuntu, macOS (Apple Silicon) and macOS (Intel) for Python 3.10 and 3.14
- [x] Pure logic is tested on Linux (`_options.py`, `_events.py`)
- [x] Every control and container is built and its properties are exercised on macOS CI
- [x] Wheel builds and installs into a clean environment; `import baremacgui` works without AppKit (CI job `package`)
- [x] Changelog, contributing guide, security policy, issue forms
- [x] Screenshots of every example from a macOS runner (workflow "Screenshots")

## To check by hand on a real Mac
- [ ] Mouse: icon double-click, Tree and Table double-click, popover, sheets, delete button in example 06
- [ ] Keyboard: menu shortcuts, `Window.add_shortcut`, `default_button` (Return) and `cancel_button` (Escape)
- [ ] Right-click menus on Table, IconGrid, Tree, TextBox
- [ ] `TextBox.on_change` while typing, in single-line and multi-line boxes
- [ ] `Window.on_close` veto with the red button, `show_modal`
- [ ] Blocking sheet dialogs (without `then=`), file dialogs, `input_box`
- [x] StatusItem: icon and title in the menu bar, menu actions, quit from the menu and Ctrl-C (example 12)
- [ ] SplitView: drag the divider, minimum pane size, divider position remembered after restart (example 11)
- [ ] Table: double-click edit, Return/Tab/Escape in the editor, header click sorting, selection kept after sorting
- [x] `Settings` values and `Window(autosave=)` position survive a real quit and restart (example 02)
- [ ] Several windows (example 15): clicking between windows swaps the menus, the Window menu lists the windows, a sheet or modal dialog keeps the menus of its window
- [x] Built `.app`: starts, Finder and Dock show the name and the default icon
- [x] Standalone `.app` (`build --standalone`, example 16): starts on the Intel Mac, also from an unpacked ZIP copy
- [ ] Standalone `.app`: downloaded copy (Gatekeeper dialog), Apple Silicon
- [ ] Install creator: the wizard window (all four steps, icon preview, system icons, build with log), `--dmg` opens and drags to Applications, `--zip`, saved `*.bmc.json`
- [ ] Built `.app`: `--background` leaves no Dock icon; a custom `--icon`
- [ ] Table checkbox column: click toggles, selection and sorting by that column behave (example 14)
- [x] DropZone: files and folders dragged from Finder (example 13)
- [ ] DropZone: highlight while hovering, "not allowed" cursor for refused items
- [ ] `choose_color` and `choose_font`: the panels open, picking by mouse works, closing returns the pick; vertical Slider with ticks
- [ ] ColorWell opens the color panel and reports picks; Switch by mouse; clipboard paste in another app
- [ ] `notify`: the banner appears (allow notifications for Script Editor in System Settings); `Table(widths=)` looks right
- [ ] Light and dark appearance of every example
- [ ] Sidebar window: divider drag, hide, minimum size
- [ ] Apple Silicon, other macOS versions (the author uses an Intel Mac with macOS 15.5)

## Before 1.0
- [x] API names decided (`Table` and `Tree` stay); the README lists which parts are stable and which are still moving
- [ ] Menu bar behaviour with several windows reviewed by hand (example 15: menus change when you click another window, the Window menu lists all windows, Cmd+N)
- [ ] Accessibility: turn VoiceOver on (Cmd+F5) and walk through examples 04 and 06; tooltips appear on hover; keyboard-only use (Tab, Space) reaches every control
