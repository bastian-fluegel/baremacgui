"""Standard menu bar.

A plain Python process has no menu bar, so Cmd+C, Cmd+V, Cmd+A and Cmd+Q do
nothing in text fields. This installs the usual App, Edit and Window menus.
The actions are standard responder-chain selectors; nothing here needs a handler.
Labels are English; the system does not localise them for a script.
"""
from __future__ import annotations

from ._bridge import AK


_state = {"name": "App", "default": None}


def _helpers():
    ak = AK()

    def submenu(bar, title):
        holder = ak.NSMenuItem.alloc().init()
        bar.addItem_(holder)
        menu = ak.NSMenu.alloc().initWithTitle_(title)
        holder.setSubmenu_(menu)
        return menu

    def entry(menu, title, action, key="", mask=None):
        item = ak.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key)
        if mask is not None:
            item.setKeyEquivalentModifierMask_(mask)
        menu.addItem_(item)
        return item

    def separator(menu):
        menu.addItem_(ak.NSMenuItem.separatorItem())

    return submenu, entry, separator


def build_bar(name, user_holders=(), edit=True):
    """The standard App / Edit / Window menus with the user's menus between App and Window.

    user_holders are NSMenuItems that each carry a submenu. Returns (bar, window_menu).
    """
    ak = AK()
    cmd = ak.NSEventModifierFlagCommand
    shift = ak.NSEventModifierFlagShift
    option = ak.NSEventModifierFlagOption
    submenu, entry, separator = _helpers()

    bar = ak.NSMenu.alloc().init()

    app_menu = submenu(bar, name)
    entry(app_menu, f"About {name}", "orderFrontStandardAboutPanel:")
    separator(app_menu)
    entry(app_menu, f"Hide {name}", "hide:", "h", cmd)
    entry(app_menu, "Hide Others", "hideOtherApplications:", "h", cmd | option)
    entry(app_menu, "Show All", "unhideAllApplications:")
    separator(app_menu)
    entry(app_menu, f"Quit {name}", "terminate:", "q", cmd)

    for holder in user_holders:
        bar.addItem_(holder)

    if edit:
        edit_menu = submenu(bar, "Edit")
        entry(edit_menu, "Undo", "undo:", "z", cmd)
        entry(edit_menu, "Redo", "redo:", "z", cmd | shift)
        separator(edit_menu)
        entry(edit_menu, "Cut", "cut:", "x", cmd)
        entry(edit_menu, "Copy", "copy:", "c", cmd)
        entry(edit_menu, "Paste", "paste:", "v", cmd)
        entry(edit_menu, "Select All", "selectAll:", "a", cmd)

    window_menu = submenu(bar, "Window")
    entry(window_menu, "Minimize", "performMiniaturize:", "m", cmd)
    entry(window_menu, "Zoom", "performZoom:")
    separator(window_menu)
    entry(window_menu, "Close", "performClose:", "w", cmd)
    return bar, window_menu


def activate(bar, window_menu):
    app = AK().NSApplication.sharedApplication()
    app.setMainMenu_(bar)
    app.setWindowsMenu_(window_menu)


def install_menu(app, name):
    _state["name"] = name
    bar, window_menu = build_bar(name)
    _state["default"] = (bar, window_menu)
    activate(bar, window_menu)
