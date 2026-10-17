"""Lazy access to PyObjC.

Nothing in the package imports AppKit at import time, so ``import baremacgui``
also works on Linux or Windows. That keeps the pure-Python parts testable
everywhere; anything that needs a window raises a clear error instead.
"""
from __future__ import annotations

import functools
import sys

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
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        from ._events import report_error

        report_error(exc)
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
def window_delegate_class():
    """NSWindow delegate: forwards close, resize and destroy to the Python Window."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacWindowDelegate(NSObject):
        def initWithOwner_(self, owner):
            self = objc.super(BareMacWindowDelegate, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def windowShouldClose_(self, sender):
            result = safe_call(self._owner._should_close)
            return True if result is None else bool(result)

        def windowDidResize_(self, notification):
            safe_call(self._owner.on_resize.emit)

        def windowWillClose_(self, notification):
            safe_call(self._owner.on_destroy.emit)

    return BareMacWindowDelegate


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

        def tableView_viewForTableColumn_row_(self, table, column, row):
            # View-based cells: this is what gives the modern inset look and rounded selection.
            ak = AK()
            cell = table.makeViewWithIdentifier_owner_("BareMacCell", self)
            if cell is None:
                cell = ak.NSTableCellView.alloc().init()
                cell.setIdentifier_("BareMacCell")
                field = ak.NSTextField.labelWithString_("")
                field.setTranslatesAutoresizingMaskIntoConstraints_(False)
                field.setLineBreakMode_(ak.NSLineBreakByTruncatingTail)
                cell.addSubview_(field)
                cell.setTextField_(field)
                field.leadingAnchor().constraintEqualToAnchor_constant_(cell.leadingAnchor(), 2.0).setActive_(True)
                field.trailingAnchor().constraintEqualToAnchor_constant_(cell.trailingAnchor(), -2.0).setActive_(True)
                field.centerYAnchor().constraintEqualToAnchor_(cell.centerYAnchor()).setActive_(True)
            cell.textField().setStringValue_(self._owner._rows[row][int(column.identifier())])
            return cell

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


@functools.lru_cache(maxsize=None)
def sidebar_source_class():
    """Data source and delegate for the Sidebar list; reads the pages of its owner."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacSidebarSource(NSObject):
        def initWithOwner_(self, owner):
            self = objc.super(BareMacSidebarSource, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def numberOfRowsInTableView_(self, table):
            return len(self._owner._pages)

        def tableView_viewForTableColumn_row_(self, table, column, row):
            ak = AK()
            cell = table.makeViewWithIdentifier_owner_("BareMacSide", self)
            if cell is None:
                cell = ak.NSTableCellView.alloc().init()
                cell.setIdentifier_("BareMacSide")
                icon = ak.NSImageView.alloc().init()
                icon.setTranslatesAutoresizingMaskIntoConstraints_(False)
                label = ak.NSTextField.labelWithString_("")
                label.setTranslatesAutoresizingMaskIntoConstraints_(False)
                label.setLineBreakMode_(ak.NSLineBreakByTruncatingTail)
                cell.addSubview_(icon)
                cell.addSubview_(label)
                cell.setImageView_(icon)
                cell.setTextField_(label)
                icon.leadingAnchor().constraintEqualToAnchor_constant_(cell.leadingAnchor(), 2.0).setActive_(True)
                icon.centerYAnchor().constraintEqualToAnchor_(cell.centerYAnchor()).setActive_(True)
                icon.widthAnchor().constraintEqualToConstant_(20.0).setActive_(True)
                label.leadingAnchor().constraintEqualToAnchor_constant_(icon.trailingAnchor(), 6.0).setActive_(True)
                label.trailingAnchor().constraintEqualToAnchor_constant_(cell.trailingAnchor(), -2.0).setActive_(True)
                label.centerYAnchor().constraintEqualToAnchor_(cell.centerYAnchor()).setActive_(True)
            page = self._owner._pages[row]
            cell.textField().setStringValue_(page.title)
            image = None
            if page.symbol:
                image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(page.symbol, None)
            cell.imageView().setImage_(image)
            return cell

        def tableViewSelectionDidChange_(self, notification):
            safe_call(self._owner._selection_changed)

    return BareMacSidebarSource


@functools.lru_cache(maxsize=None)
def icon_classes():
    """(collection view class, item class, data source class) for IconGrid."""
    objc = OBJC()
    ak = AK()
    NSObject = FN().NSObject

    class BareMacIconItem(ak.NSCollectionViewItem):
        def loadView(self):
            box = ak.NSBox.alloc().init()
            box.setBoxType_(ak.NSBoxCustom)
            box.setTitlePosition_(ak.NSNoTitle)
            box.setBorderWidth_(0.0)
            box.setCornerRadius_(8.0)
            box.setContentViewMargins_((0.0, 0.0))
            box.setTransparent_(True)
            content = box.contentView()
            icon = ak.NSImageView.alloc().init()
            icon.setTranslatesAutoresizingMaskIntoConstraints_(False)
            icon.setImageScaling_(ak.NSImageScaleProportionallyUpOrDown)
            if hasattr(icon, "setContentTintColor_"):
                icon.setContentTintColor_(ak.NSColor.controlAccentColor())
            label = ak.NSTextField.labelWithString_("")
            label.setTranslatesAutoresizingMaskIntoConstraints_(False)
            label.setAlignment_(ak.NSTextAlignmentCenter)
            label.setLineBreakMode_(ak.NSLineBreakByTruncatingMiddle)
            content.addSubview_(icon)
            content.addSubview_(label)
            self._width = icon.widthAnchor().constraintEqualToConstant_(64.0)
            self._height = icon.heightAnchor().constraintEqualToConstant_(64.0)
            for constraint in (
                self._width,
                self._height,
                icon.topAnchor().constraintEqualToAnchor_constant_(content.topAnchor(), 8.0),
                icon.centerXAnchor().constraintEqualToAnchor_(content.centerXAnchor()),
                label.topAnchor().constraintEqualToAnchor_constant_(icon.bottomAnchor(), 4.0),
                label.leadingAnchor().constraintEqualToAnchor_constant_(content.leadingAnchor(), 4.0),
                label.trailingAnchor().constraintEqualToAnchor_constant_(content.trailingAnchor(), -4.0),
            ):
                constraint.setActive_(True)
            self._box, self._icon, self._label = box, icon, label
            self.setView_(box)
            self.setImageView_(icon)
            self.setTextField_(label)

        def setSelected_(self, flag):
            objc.super(BareMacIconItem, self).setSelected_(flag)
            self._paint(bool(flag))

        @objc.python_method
        def _paint(self, selected):
            if getattr(self, "_box", None) is None:
                return
            self._box.setTransparent_(not selected)
            if selected:
                self._box.setFillColor_(ak.NSColor.selectedContentBackgroundColor())
                self._label.setTextColor_(ak.NSColor.alternateSelectedControlTextColor())
                tint = ak.NSColor.alternateSelectedControlTextColor()  # accent blue would vanish on the accent fill
            else:
                self._label.setTextColor_(ak.NSColor.labelColor())
                tint = ak.NSColor.controlAccentColor()
            if hasattr(self._icon, "setContentTintColor_"):
                self._icon.setContentTintColor_(tint)

        @objc.python_method
        def configure(self, title, image, size):
            self.view()  # makes sure loadView ran
            self._label.setStringValue_(title)
            self._icon.setImage_(image)
            self._width.setConstant_(size)
            self._height.setConstant_(size)
            self._paint(bool(self.isSelected()))

    class BareMacCollectionView(ak.NSCollectionView):
        _double = None

        def mouseDown_(self, event):
            objc.super(BareMacCollectionView, self).mouseDown_(event)
            if event.clickCount() == 2 and self._double is not None:
                safe_call(self._double)

    class BareMacIconSource(NSObject):
        def initWithOwner_(self, owner):
            self = objc.super(BareMacIconSource, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def collectionView_numberOfItemsInSection_(self, view, section):
            return len(self._owner._entries)

        def collectionView_itemForRepresentedObjectAtIndexPath_(self, view, path):
            item = view.makeItemWithIdentifier_forIndexPath_("BareMacIcon", path)
            label, symbol = self._owner._entries[int(path.item())]
            item.configure(label, self._owner._image(symbol), self._owner._icon_size)
            return item

        def collectionView_didSelectItemsAtIndexPaths_(self, view, paths):
            safe_call(self._owner._selection_changed)

        def collectionView_didDeselectItemsAtIndexPaths_(self, view, paths):
            safe_call(self._owner._selection_changed)

    return BareMacCollectionView, BareMacIconItem, BareMacIconSource


@functools.lru_cache(maxsize=None)
def outline_source_class():
    """Data source and delegate for Tree; walks the node objects of its owner."""
    objc = OBJC()
    NSObject = FN().NSObject

    class BareMacOutlineSource(NSObject):
        def initWithOwner_(self, owner):
            self = objc.super(BareMacOutlineSource, self).init()
            if self is None:
                return None
            self._owner = owner
            return self

        def outlineView_numberOfChildrenOfItem_(self, view, item):
            return len(self._owner._roots if item is None else item.children)

        def outlineView_child_ofItem_(self, view, index, item):
            return (self._owner._roots if item is None else item.children)[index]

        def outlineView_isItemExpandable_(self, view, item):
            return bool(item.children)

        def outlineView_viewForTableColumn_item_(self, view, column, item):
            ak = AK()
            cell = view.makeViewWithIdentifier_owner_("BareMacTree", self)
            if cell is None:
                cell = ak.NSTableCellView.alloc().init()
                cell.setIdentifier_("BareMacTree")
                icon = ak.NSImageView.alloc().init()
                icon.setTranslatesAutoresizingMaskIntoConstraints_(False)
                label = ak.NSTextField.labelWithString_("")
                label.setTranslatesAutoresizingMaskIntoConstraints_(False)
                label.setLineBreakMode_(ak.NSLineBreakByTruncatingTail)
                cell.addSubview_(icon)
                cell.addSubview_(label)
                cell.setImageView_(icon)
                cell.setTextField_(label)
                icon.leadingAnchor().constraintEqualToAnchor_constant_(cell.leadingAnchor(), 2.0).setActive_(True)
                icon.centerYAnchor().constraintEqualToAnchor_(cell.centerYAnchor()).setActive_(True)
                icon.widthAnchor().constraintEqualToConstant_(20.0).setActive_(True)
                label.leadingAnchor().constraintEqualToAnchor_constant_(icon.trailingAnchor(), 6.0).setActive_(True)
                label.trailingAnchor().constraintEqualToAnchor_constant_(cell.trailingAnchor(), -2.0).setActive_(True)
                label.centerYAnchor().constraintEqualToAnchor_(cell.centerYAnchor()).setActive_(True)
            cell.textField().setStringValue_(item.text)
            cell.imageView().setImage_(self._owner._image(item.symbol))
            return cell

        def outlineViewSelectionDidChange_(self, notification):
            safe_call(self._owner._selection_changed)

    return BareMacOutlineSource
