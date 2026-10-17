# BareMacGUI: notes for Claude

The project is called BareMacGUI (package and import name `baremacgui`, shorthand "bmc").
Thin Python layer for native macOS GUIs on AppKit via PyObjC. Its API shape follows BareWinGUI,
the author's Windows library; the Windows project is a different project and never the name of this one.

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

## Looking at the windows (no Mac needed)
- The GitHub workflow "Screenshots" runs every example on a macOS runner, drives it with `tools/shoot.py` and pushes the PNGs and a log to the branch `ci-screenshots`. Start it with `gh api -X POST repos/bastian-fluegel/baremacgui/actions/workflows/screenshots.yml/dispatches -f ref=main` (the `gh workflow` commands need GraphQL, which is blocked here), wait for the run via `gh api .../actions/runs/<id>`, then `git fetch origin ci-screenshots` and `git archive FETCH_HEAD` into the scratchpad and view the images. Artifact downloads and job logs are blocked from this sandbox; that is why the images go to a branch.
- Scenarios call handlers and set controls from code; real clicks are not simulated. Add a step to `SCENARIOS` in `tools/shoot.py` for new features. `dump_window` prints the view tree with frames for layout bugs.
- The runner's macOS is newer than the author's Mac (15.5). Layout differences between the two are real findings.
- In PyObjC subclasses every method becomes a selector: helper methods need `@objc.python_method`.
