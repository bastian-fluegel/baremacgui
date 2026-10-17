# Checklist: from alpha to beta

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
- [ ] StatusItem: icon and title in the menu bar, menu actions, quit from the menu (example 12); a background App stays alive without windows
- [ ] SplitView: drag the divider, minimum pane size, divider position remembered after restart (example 11)
- [ ] Table: double-click edit, Return/Tab/Escape in the editor, header click sorting, selection kept after sorting
- [ ] `Settings` values and `Window(autosave=)` position survive a real quit and restart
- [ ] Table checkbox column: click toggles, selection and sorting by that column behave (example 14)
- [ ] DropZone: drag files and folders from Finder onto it (example 13); highlight while hovering, "not allowed" cursor for refused items
- [ ] ColorWell opens the color panel and reports picks; Switch by mouse; clipboard paste in another app
- [ ] Light and dark appearance of every example
- [ ] Sidebar window: divider drag, hide, minimum size
- [ ] Apple Silicon, other macOS versions (the author uses an Intel Mac with macOS 15.5)

## Before beta
- [ ] API names stable; experimental parts marked in the docs
- [ ] Menu bar behaviour with several windows reviewed
- [ ] Accessibility (VoiceOver labels) reviewed
- [ ] `.app` packaging documented
