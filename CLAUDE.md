# baremacgui: notes for Claude

Thin Python layer for native macOS GUIs on AppKit via PyObjC. Sibling of BareWinGUI
(github.com/bastian-fluegel/barewingui): same API shape, same names.

## Rules
- The only runtime dependency is PyObjC (`pyobjc-framework-Cocoa`). Add nothing else without a reason and a test.
- `import baremacgui` must work on any OS and must not import AppKit. Native access goes through `_bridge.py` (`AK()`, `FN()`, `OBJC()`), always inside functions.
- Keep the API shape of BareWinGUI: `with` blocks build the tree, handlers take no arguments, `App.invoke` hands work back to the UI thread, controls are never touched from other threads.
- Pure logic lives in `_options.py` and is tested on Linux. Everything that builds views is tested on macOS only (`tests/test_controls_mac.py`).
- Callbacks from AppKit go through `safe_call`, so a Python exception never takes the app down.
- No claim in README or docs that has not been checked. Mark unverified things as unverified.
- Nothing personal (past, age, career) in code, docs or commit messages.

## Working with the author
- The author tests on a real Mac (Intel, Python 3.14, PyObjC 12.x) and reports back. Claude cannot run macOS code here: say so, never claim a macOS test passed.
- Answer the author in German. Code, comments, README and commit messages are English.
- Most likely to need fixes after the first real run: GroupBox and TabControl sizing, the filler spacing in boxes, the menu bar selectors.
