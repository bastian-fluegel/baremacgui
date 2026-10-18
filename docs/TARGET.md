# BareMacGUI: target picture

## Purpose
A thin Python layer for native macOS windows: real AppKit controls, built from short `with` blocks,
with the API shape of BareWinGUI (the author's Windows library). The goal is to write a Mac tool in
tens of lines and get an app that looks and behaves like any other Mac app.

## Non-goals
- No cross-platform layer. BareMacGUI is macOS only; `import baremacgui` works elsewhere so that the
  pure-Python parts can be tested on Linux.
- No drawing of its own controls and no theme engine. Controls are AppKit views.
- No web engine and no GUI designer.
- No SwiftUI-only features (widgets, Live Activities, App Intents). These need a Swift target.
  `.ns` and `Custom(view)` give access to any AppKit view for everything the library does not wrap.

## Hard rules
- The only runtime dependency is PyObjC (`pyobjc-framework-Cocoa`).
- `import baremacgui` works on every OS and never imports AppKit; native access is lazy (`_bridge.py`).
- The UI runs on the main thread. Other threads hand work over with `App.invoke` / `App.call`.
- Handlers take no arguments. Exceptions in handlers go to `App.on_error` or the terminal and never take the app down.
- Errors are Python exceptions with readable messages (`BareMacGUIError`, `LayoutError`, `PlatformError`).
- Nothing is claimed in the docs that was not checked. Unverified things are marked as such.

## Code style
- Classes instead of IDs, properties instead of getters and setters, snake_case.
- Events through `on_*=` options, `control.on_x(handler)` or as a decorator.
- Layout from `with` blocks (`VBox`, `HBox`, `Spacer`) with `padding`, `gap`, `align`, `justify`, `grow`, sizes.

```python
from baremacgui import App, Button, HBox, Label, Spacer, TextBox, VBox, Window

app = App("Demo")
with Window("Demo", size=(420, 200)) as win:
    with VBox(padding=16, gap=8):
        name = TextBox(placeholder="Name")
        out = Label("")
        with HBox(justify="end"):
            ok = Button("OK", default=True, on_click=lambda: setattr(out, "text", f"Hello {name.text}"))
app.run()
```

## Scope of the alpha
Everything listed under "What is included" in the README, built from AppKit views, with window styles
`standard`, `unified` (Finder-like) and `sidebar` (System-Settings-like).

## After the alpha
Editable tables and sorting, rich text, drag and drop, clipboard, a drawing canvas, status-bar item,
notifications, saved settings, a web view, `.app` packaging and signing. See the roadmap.

## Definition of "alpha is done"
See `docs/CHECKLIST.md`.
