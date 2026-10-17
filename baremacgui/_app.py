"""The application object: event loop, menu bar and thread hand-over."""
from __future__ import annotations

import os
import sys
import threading

from ._bridge import AK, FN, delegate_class, safe_call
from ._events import set_error_hook


def _default_name():
    stem = os.path.splitext(os.path.basename(sys.argv[0] or ""))[0]
    return stem if stem and not stem.startswith("-") else "App"


class App:
    """Create one App before any Window, then call run().

    name  shown in the menu bar entries (best effort for a plain script; a
          packaged .app takes its name from its bundle)
    menu  install the standard App/Edit/Window menus (needed for Cmd+C/V/Q)
    icon  path of an image (.icns or .png) for the Dock icon while the app runs. A script started from an
          .app built with `python -m baremacgui build ... --icon` gets it without this argument.
    background  a menu-bar app: no Dock icon, no menu bar of its own, and it keeps running when the
          last window closes (use it with StatusItem; quit with app.quit() from a menu item).
          Native counterpart: activation policy "accessory" (LSUIElement in a packaged app).
    """

    def __init__(self, name=None, menu=True, background=False, icon=None):
        ak = AK()
        self.name = str(name) if name else os.environ.get("BAREMACGUI_APP_NAME") or _default_name()
        try:  # best effort: the menu bar title of a plain script comes from the bundle name
            bundle = FN().NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if info is not None:
                info["CFBundleName"] = self.name
        except Exception:  # noqa: BLE001 - cosmetic only
            pass
        self._on_error = None
        self.ns = ak.NSApplication.sharedApplication()
        icon = icon or os.environ.get("BAREMACGUI_ICON")  # set by the launcher of a built .app
        if icon:
            image = ak.NSImage.alloc().initWithContentsOfFile_(os.path.abspath(str(icon)))
            if image is None:
                raise ValueError(f"cannot load the icon: {icon!r}")
            self.ns.setApplicationIconImage_(image)
        self.background = bool(background)
        self.ns.setActivationPolicy_(
            ak.NSApplicationActivationPolicyAccessory if self.background else ak.NSApplicationActivationPolicyRegular
        )
        self._delegate = delegate_class().alloc().init()  # the application holds its delegate weakly
        self._delegate._quit_on_close = not self.background
        self.ns.setDelegate_(self._delegate)
        if menu:
            from ._menu import install_menu

            install_menu(self.ns, self.name)

    @property
    def on_error(self):
        """Function that receives an exception raised in any handler (instead of the terminal).

            app.on_error = lambda exc: show_error(str(exc))

        Set it to None to print tracebacks again.
        """
        return self._on_error

    @on_error.setter
    def on_error(self, handler):
        if handler is not None and not callable(handler):
            raise TypeError("on_error must be callable or None")
        self._on_error = handler
        set_error_hook(handler)

    def call(self, function, *args, **kwargs):
        """Run function(*args, **kwargs) on the UI thread and return its result.

        Blocks the calling worker thread until the UI thread has run it; an
        exception in function is raised again in the caller. On the UI thread
        itself the function runs immediately. Never call this from the UI
        thread while the UI thread waits for the worker (deadlock).
        """
        if threading.current_thread() is threading.main_thread():
            return function(*args, **kwargs)
        done = threading.Event()
        box = {}

        def run():
            try:
                box["value"] = function(*args, **kwargs)
            except BaseException as exc:  # noqa: BLE001 - handed back to the caller
                box["error"] = exc
            finally:
                done.set()

        from PyObjCTools import AppHelper

        AppHelper.callAfter(run)
        done.wait()
        if "error" in box:
            raise box["error"]
        return box.get("value")

    def invoke(self, function, *args):
        """Run function(*args) on the UI thread. Call this from worker threads.

        Never touch controls from another thread; hand the result over with invoke().
        """
        from PyObjCTools import AppHelper

        AppHelper.callAfter(safe_call, function, *args)

    def run(self):
        """Show the windows and run until the last one is closed."""
        try:
            self.ns.activate()  # macOS 14 and newer
        except AttributeError:
            self.ns.activateIgnoringOtherApps_(True)
        self.ns.run()

    def quit(self):
        self.ns.terminate_(None)
