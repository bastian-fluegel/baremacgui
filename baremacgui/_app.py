"""The application object: event loop, menu bar and thread hand-over."""
from __future__ import annotations

import os
import sys

from ._bridge import AK, FN, delegate_class, safe_call


def _default_name():
    stem = os.path.splitext(os.path.basename(sys.argv[0] or ""))[0]
    return stem if stem and not stem.startswith("-") else "App"


class App:
    """Create one App before any Window, then call run().

    name  shown in the menu bar entries (best effort for a plain script; a
          packaged .app takes its name from its bundle)
    menu  install the standard App/Edit/Window menus (needed for Cmd+C/V/Q)
    """

    def __init__(self, name=None, menu=True):
        ak = AK()
        self.name = str(name) if name else _default_name()
        try:  # best effort: the menu bar title of a plain script comes from the bundle name
            bundle = FN().NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if info is not None:
                info["CFBundleName"] = self.name
        except Exception:  # noqa: BLE001 - cosmetic only
            pass
        self.ns = ak.NSApplication.sharedApplication()
        self.ns.setActivationPolicy_(ak.NSApplicationActivationPolicyRegular)
        self._delegate = delegate_class().alloc().init()  # the application holds its delegate weakly
        self.ns.setDelegate_(self._delegate)
        if menu:
            from ._menu import install_menu

            install_menu(self.ns, self.name)

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
