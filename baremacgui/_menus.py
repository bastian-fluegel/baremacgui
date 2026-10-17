"""MenuBar, Menu, MenuItem, MenuSeparator and ContextMenu.

A Mac has one menu bar for the whole app, so a MenuBar belongs to a window: while
that window is the key window its menus are the menu bar. The standard App, Edit and
Window menus are always there; your menus sit between App and Edit.

    with Window("Editor") as win:
        with MenuBar():
            with Menu("File"):
                MenuItem("New", shortcut="Cmd+N", on_click=new)
                MenuSeparator()
                MenuItem("Save", shortcut="Cmd+S", on_click=save)
"""
from __future__ import annotations

from . import _core
from ._bridge import AK, make_target
from ._events import connect_options, event, split_options
from ._menu import _state, activate, build_bar
from ._options import menu_key_equivalent, parse_shortcut


def _plain(text):
    """Text without BareWinGUI-style access-key markers: "&File" -> "File", "&&" -> "&"."""
    return str(text).replace("&&", "\0").replace("&", "").replace("\0", "&")


def _modifier_mask(mods):
    ak = AK()
    mask = 0
    for name, flag in (
        ("cmd", ak.NSEventModifierFlagCommand), ("shift", ak.NSEventModifierFlagShift),
        ("alt", ak.NSEventModifierFlagOption), ("ctrl", ak.NSEventModifierFlagControl),
    ):
        if name in mods:
            mask |= flag
    return mask


class _Container:
    """Common code of Menu and ContextMenu: holds an NSMenu and takes MenuItems."""

    def _init_container(self, title):
        ak = AK()
        self.ns = ak.NSMenu.alloc().initWithTitle_(_plain(title))
        self.ns.setAutoenablesItems_(False)  # enabled/disabled is decided by the program
        self._entries = []

    def _add(self, entry):
        self._entries.append(entry)
        self.ns.addItem_(entry.holder if isinstance(entry, Menu) else entry.ns)

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        return False

    @property
    def items(self):
        """The MenuItems and submenus in order (separators excluded)."""
        return [entry for entry in self._entries if not isinstance(entry, MenuSeparator)]


def _parent_container(what):
    parent = _core.current()
    if not isinstance(parent, _Container):
        raise RuntimeError(f"{what} goes inside a `with Menu(...)` or `with ContextMenu()` block.")
    return parent


class MenuItem:
    """One menu entry.

    shortcut   "Cmd+S", "Cmd+Shift+N", "F5" ... ("Ctrl" means Cmd, as a convenience)
    checkable  a click toggles the check mark before on_click runs
    checked    show a check mark
    symbol     SF Symbol shown next to the text (macOS 11+)
    """

    on_click = event()

    def __init__(self, text, shortcut=None, checkable=False, checked=False, enabled=True, symbol=None, **options):
        ak = AK()
        handlers = split_options(options)
        if options:
            raise TypeError(f"MenuItem got unexpected options: {sorted(options)}")
        parent = _parent_container("MenuItem")
        key, mods = ("", frozenset()) if shortcut is None else parse_shortcut(shortcut)
        self.ns = ak.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            _plain(text), b"fire:", menu_key_equivalent(key)
        )
        if shortcut is not None:
            self.ns.setKeyEquivalentModifierMask_(_modifier_mask(mods))
        if symbol is not None:
            image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(symbol), None)
            if image is None:
                raise ValueError(f"unknown system symbol: {symbol!r}")
            self.ns.setImage_(image)
        self.checkable = bool(checkable)
        self._target = make_target(self._activate)  # a menu item keeps its target weakly
        self.ns.setTarget_(self._target)
        self.checked = checked
        self.enabled = enabled
        connect_options(self, handlers)
        parent._add(self)

    def _activate(self):
        if self.checkable:
            self.checked = not self.checked
        self.on_click.emit()

    def click(self):
        """Do what a click does (toggle if checkable, call the handlers)."""
        self._activate()

    @property
    def text(self):
        return str(self.ns.title())

    @text.setter
    def text(self, value):
        self.ns.setTitle_(_plain(value))

    @property
    def checked(self):
        return int(self.ns.state()) == int(AK().NSControlStateValueOn)

    @checked.setter
    def checked(self, value):
        ak = AK()
        self.ns.setState_(ak.NSControlStateValueOn if value else ak.NSControlStateValueOff)

    @property
    def enabled(self):
        return bool(self.ns.isEnabled())

    @enabled.setter
    def enabled(self, value):
        self.ns.setEnabled_(bool(value))


class MenuSeparator:
    """A dividing line between menu entries."""

    def __init__(self):
        self.ns = AK().NSMenuItem.separatorItem()
        _parent_container("MenuSeparator")._add(self)


class Menu(_Container):
    """A menu in a MenuBar, or a submenu inside another Menu or a ContextMenu."""

    def __init__(self, text):
        ak = AK()
        parent = _core.current()
        if not isinstance(parent, (MenuBar, _Container)):
            raise RuntimeError("Menu goes inside a `with MenuBar()` or another Menu.")
        self._init_container(text)
        self.title = _plain(text)
        self.holder = ak.NSMenuItem.alloc().init()  # the entry in the parent that opens this menu
        self.holder.setTitle_(self.title)
        self.holder.setSubmenu_(self.ns)
        parent._add(self)


class MenuBar:
    """The window's menus. Create it directly inside the `with Window(...)` block."""

    def __init__(self, edit=True):
        from ._layout import Window

        window = _core.current()
        if not isinstance(window, Window):
            raise RuntimeError("MenuBar goes directly inside `with Window(...)`.")
        if getattr(window, "_menubar", None) is not None:
            raise ValueError("A Window has only one MenuBar.")
        self._window = window
        self._edit = bool(edit)
        self._menus = []
        self.ns = None
        self._window_menu = None

    def _add(self, menu):
        self._menus.append(menu)

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        edit = self._edit and not any(menu.title == "Edit" for menu in self._menus)
        self.ns, self._window_menu = build_bar(_state["name"], [menu.holder for menu in self._menus], edit)
        self._window._menubar = self
        return False

    @property
    def menus(self):
        return list(self._menus)

    def activate(self):
        """Make these menus the menu bar now (done automatically when the window becomes key)."""
        activate(self.ns, self._window_menu)


class ContextMenu(_Container):
    """A pop-up menu for right-click (Control-click). Build it anywhere, then attach it::

        with ContextMenu() as menu:
            MenuItem("Delete", on_click=delete)
        table.context_menu = menu
        menu.popup()                      # or show it at the mouse by hand
    """

    def __init__(self):
        self._init_container("")

    def popup(self):
        """Show the menu at the mouse pointer."""
        location = AK().NSEvent.mouseLocation()
        self.ns.popUpMenuPositioningItem_atLocation_inView_(None, location, None)

