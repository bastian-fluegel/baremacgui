"""Run an example, drive it from code and take screenshots. For CI and for looking at the windows.

    python tools/shoot.py <scenario> <output-dir> [--dark]

macOS only. Real mouse clicks are not simulated: the scenarios call the same functions the
handlers call, or set controls from code. So this shows how things look, not that every
click path works.
"""
import os
import subprocess
import sys
import threading
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# name -> (example file, steps). A step is (action(globals) or None, seconds to wait, screenshot name or None).
SCENARIOS = {
    "hello": ("00_hello.py", [(None, 1.0, "hello")]),
    "settings": ("02_settings.py", [(None, 1.0, "settings")]),
    "widgets": ("03_widgets.py", [(None, 1.0, "widgets")]),
    "finder": ("04_finder.py", [
        (None, 1.0, "finder-start"),
        (lambda g: g["go"]("Documents"), 0.8, "finder-documents"),
        (lambda g: g["step"](-1), 0.8, "finder-back"),
    ]),
    "sidebar": ("05_settings_sidebar.py", [
        (None, 1.0, "sidebar-general"),
        (lambda g: setattr(g["sidebar"], "index", 1), 0.8, "sidebar-appearance"),
        (lambda g: setattr(g["sidebar"], "index", 3), 0.8, "sidebar-about"),
    ]),
    "everything": ("06_everything.py", [
        (None, 1.0, "everything-list"),
        (lambda g: (setattr(g["view"], "index", 0), g["set_view"]()), 1.0, "everything-icons"),
        (lambda g: (setattr(g["tree"], "path", ["Home", "Documents"]), g["refresh"]()), 1.0, "everything-documents"),
        (lambda g: setattr(g["grid"], "index", 1), 0.6, "everything-icon-selected"),
        (lambda g: g["show_info_popover"](), 1.2, "everything-popover"),
        (lambda g: g["info"].close(), 0.6, None),
        (lambda g: g["open_new_sheet"](), 1.2, "everything-sheet"),
        (lambda g: g["new_sheet"].close(), 0.8, None),
        (lambda g: g["delete_selected"](), 1.2, "everything-delete-sheet"),
    ]),
}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dark = "--dark" in sys.argv
    if len(args) != 2 or args[0] not in SCENARIOS:
        sys.exit(f"usage: shoot.py <{'|'.join(SCENARIOS)}> <output-dir> [--dark]")
    scenario, outdir = args
    example, steps = SCENARIOS[scenario]
    os.makedirs(outdir, exist_ok=True)

    def watchdog():
        print("WATCHDOG: scenario did not finish in 60 seconds", flush=True)
        os._exit(2)

    timer = threading.Timer(60.0, watchdog)
    timer.daemon = True
    timer.start()
    print(f"start {scenario} {'dark' if dark else 'light'}", flush=True)
    suffix = "-dark" if dark else "-light"
    failures = []

    import baremacgui
    from PyObjCTools import AppHelper

    namespace = {"__name__": "__main__", "__file__": os.path.join(ROOT, "examples", example)}

    def capture(name):
        path = os.path.join(outdir, f"{name}{suffix}.png")
        result = subprocess.run(["screencapture", "-x", path], capture_output=True, text=True)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        print(f"screenshot {name}{suffix}: exit {result.returncode}, {size} bytes {result.stderr.strip()}", flush=True)
        if result.returncode != 0 or size == 0:
            failures.append(name)

    def run(self):
        import AppKit

        if dark:
            self.ns.setAppearance_(AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameDarkAqua))

        def advance(index):
            if index >= len(steps):
                print("scenario finished", flush=True)
                self.ns.terminate_(None)
                return
            action, wait, shot = steps[index]
            if action is not None:
                try:
                    action(namespace)
                except Exception:  # noqa: BLE001 - report and carry on
                    traceback.print_exc()
                    failures.append(f"step {index}")

            def after():
                if shot:
                    capture(shot)
                advance(index + 1)

            AppHelper.callLater(wait, after)

        AppHelper.callLater(1.5, lambda: advance(0))
        try:
            self.ns.activate()
        except AttributeError:
            self.ns.activateIgnoringOtherApps_(True)
        self.ns.run()

    baremacgui.App.run = run
    path = namespace["__file__"]
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    exec(compile(source, path, "exec"), namespace)  # noqa: S102 - our own example files
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
