# Contributing

Thanks for trying BareMacGUI. The most useful thing right now is feedback from real Macs: open an issue
(bug report or feedback form) with your macOS version, chip (Apple Silicon or Intel), Python and PyObjC
version, and a small script.

Code changes:

```bash
python -m pip install -e ".[test]"
python -m pytest        # logic tests run everywhere, view tests on macOS only
```

- The only runtime dependency is PyObjC (`pyobjc-framework-Cocoa`). Please do not add another one without a reason and a test.
- `import baremacgui` must work on every OS and must not import AppKit. Native access goes through `_bridge.py`,
  always inside functions.
- Keep the API shape: `with` blocks build the tree, handlers take no arguments, controls are never touched from
  other threads (`App.invoke` / `App.call`).
- Pure logic goes into `_options.py` and is tested on Linux. Code that builds views is tested in
  `tests/test_controls_mac.py` (macOS only).
- In PyObjC subclasses every method becomes a selector: helper methods need `@objc.python_method`.
- Do not claim in the README that something works unless it was checked; mark the rest as unverified.
- Please open an issue before a larger change.
