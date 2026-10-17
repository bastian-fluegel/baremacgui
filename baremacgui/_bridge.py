"""Lazy access to PyObjC.

Nothing in the package imports AppKit at import time, so ``import baremacgui``
also works on Linux or Windows. That keeps the pure-Python parts testable
everywhere; anything that needs a window raises a clear error instead.
"""
from __future__ import annotations

import functools
import sys
import traceback

_NEEDS_PYOBJC = "baremacgui needs PyObjC: pip install pyobjc-framework-Cocoa"


def require_macos():
    if sys.platform != "darwin":
        raise RuntimeError(f"baremacgui only runs on macOS (this is {sys.platform}).")


def _load(name):
    require_macos()
    try:
        return __import__(name)
    except ImportError as exc:
        raise RuntimeError(_NEEDS_PYOBJC) from exc


@functools.lru_cache(maxsize=None)
def AK():
    """The AppKit module."""
    return _load("AppKit")


@functools.lru_cache(maxsize=None)
def FN():
    """The Foundation module."""
    return _load("Foundation")


@functools.lru_cache(maxsize=None)
def OBJC():
    """The objc module."""
    return _load("objc")


def ensure_app():
    """Make sure the shared NSApplication exists (dialogs and windows need it)."""
    return AK().NSApplication.sharedApplication()


def safe_call(function, *args):
    """Run a Python callback coming from AppKit.

    An uncaught exception inside an Objective-C callback can take the whole
    app down; print it to the terminal instead and keep the window alive.
    """
    try:
        return function(*args)
    except Exception:  # noqa: BLE001 - deliberately broad, see docstring
        traceback.print_exc()
        return None


@functools.lru_cache(maxsize=None)
def target_class():
    """NSObject subclass that forwards an action message to a Python callable."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacTarget(NSObject):
        def initWithCallback_(self, callback):
            self = objc.super(BareMacTarget, self).init()
            if self is None:
                return None
            self._callback = callback
            return self

        @objc.IBAction
        def fire_(self, sender):
            safe_call(self._callback)

    return BareMacTarget


def make_target(callback):
    return target_class().alloc().initWithCallback_(callback)


@functools.lru_cache(maxsize=None)
def delegate_class():
    """Application delegate: quit when the last window closes."""
    NSObject = FN().NSObject

    class BareMacDelegate(NSObject):
        def applicationShouldTerminateAfterLastWindowClosed_(self, app):
            return True

    return BareMacDelegate


@functools.lru_cache(maxsize=None)
def table_source_class():
    """Data source and delegate for Table/ListBox; reads the rows of its owner."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacTableSource(NSObject):
        def initWithOwner_(self, owner):
            self = objc.super(BareMacTableSource, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def numberOfRowsInTableView_(self, table):
            return len(self._owner._rows)

        def tableView_objectValueForTableColumn_row_(self, table, column, row):
            return self._owner._rows[row][int(column.identifier())]

        def tableViewSelectionDidChange_(self, notification):
            safe_call(self._owner._selection_changed)

    return BareMacTableSource


@functools.lru_cache(maxsize=None)
def toolbar_delegate_class():
    """NSToolbar delegate: hands out one NSToolbarItem per entry, each wrapping a view."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacToolbarDelegate(NSObject):
        def initWithEntries_(self, entries):
            # entries: list of (identifier, view or None); view None = system space item
            self = objc.super(BareMacToolbarDelegate, self).init()
            if self is None:
                return None
            self._entries = list(entries)
            return self

        def toolbarAllowedItemIdentifiers_(self, toolbar):
            return [identifier for identifier, _ in self._entries]

        def toolbarDefaultItemIdentifiers_(self, toolbar):
            return [identifier for identifier, _ in self._entries]

        def toolbar_itemForItemIdentifier_willBeInsertedIntoToolbar_(self, toolbar, identifier, flag):
            for entry_id, view in self._entries:
                if entry_id == identifier and view is not None:
                    item = AK().NSToolbarItem.alloc().initWithItemIdentifier_(identifier)
                    item.setView_(view)
                    return item
            return None

    return BareMacToolbarDelegate
