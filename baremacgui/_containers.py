"""GroupBox, TabControl and Tab."""
from __future__ import annotations

from . import _core
from ._bridge import AK
from ._options import check_grow, check_padding, check_size


class GroupBox:
    """A titled frame around exactly one child (normally a VBox or HBox)."""

    def __init__(self, title, padding=8, grow=0, **size):
        self.title = str(title)
        self.padding = check_padding(padding)
        self.grow = check_grow(grow)
        self._size = check_size(size)
        self._item = None
        self.ns = None

    def accept(self, item):
        if self._item is not None:
            raise ValueError("A GroupBox takes exactly one child. Wrap several controls in a VBox or HBox.")
        self._item = item

    def __enter__(self):
        _core.current()
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        ak = AK()
        box = ak.NSBox.alloc().init()
        box.setTitle_(self.title)
        box.setContentViewMargins_((self.padding, self.padding))
        if self._item is not None:
            child = self._item.view
            fit = child.fittingSize()  # measure before the child moves into the box
            content = box.contentView()
            content.addSubview_(child)
            _core.pin(child, content)
            # The box does not derive its own size from the child, so ask for enough room.
            box.setTranslatesAutoresizingMaskIntoConstraints_(False)
            box.widthAnchor().constraintGreaterThanOrEqualToConstant_(fit.width + 2 * self.padding + 12).setActive_(True)
            box.heightAnchor().constraintGreaterThanOrEqualToConstant_(fit.height + 2 * self.padding + 28).setActive_(True)
        _core.apply_size(box, self._size)
        self.ns = box
        _core.add(box, self.grow, fill=True)
        return False


class TabControl:
    """Tabs. Use Tab(...) blocks inside it:

        with TabControl(grow=1):
            with Tab("General"):
                with VBox(): ...
    """

    def __init__(self, padding=12, grow=1, **size):
        self.padding = check_padding(padding)
        self.grow = check_grow(grow)
        self._size = check_size(size)
        self._pages = []
        self.ns = None

    def accept(self, item):
        raise ValueError("Put controls inside a Tab(...) block within the TabControl.")

    def add_page(self, title, item):
        self._pages.append((title, item))

    def __enter__(self):
        _core.current()
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        ak = AK()
        pad = self.padding
        tabs = ak.NSTabView.alloc().init()
        widest = tallest = 0.0
        for index, (title, item) in enumerate(self._pages):
            container = ak.NSView.alloc().init()  # plain view: the tab view sets its frame itself
            if item is not None:
                child = item.view
                fit = child.fittingSize()
                widest, tallest = max(widest, fit.width), max(tallest, fit.height)
                container.addSubview_(child)
                _core.pin(child, container, pad)
            entry = ak.NSTabViewItem.alloc().initWithIdentifier_(str(index))
            entry.setLabel_(title)
            entry.setView_(container)
            tabs.addTabViewItem_(entry)
        # Rough allowance for the tab strip and the frame; the tab view has no intrinsic size.
        tabs.setTranslatesAutoresizingMaskIntoConstraints_(False)
        tabs.widthAnchor().constraintGreaterThanOrEqualToConstant_(widest + 2 * pad + 24).setActive_(True)
        tabs.heightAnchor().constraintGreaterThanOrEqualToConstant_(tallest + 2 * pad + 48).setActive_(True)
        _core.apply_size(tabs, self._size)
        self.ns = tabs
        _core.add(tabs, self.grow, fill=True)
        return False

    @property
    def selected(self):
        """Index of the visible tab."""
        return int(self.ns.indexOfTabViewItem_(self.ns.selectedTabViewItem()))

    @selected.setter
    def selected(self, index):
        self.ns.selectTabViewItemAtIndex_(index)


class Tab:
    """One page of a TabControl; takes exactly one child (normally a VBox or HBox)."""

    def __init__(self, title):
        self.title = str(title)
        self._item = None
        self._parent = None

    def accept(self, item):
        if self._item is not None:
            raise ValueError("A Tab takes exactly one child. Wrap several controls in a VBox or HBox.")
        self._item = item

    def __enter__(self):
        parent = _core.current()
        if not isinstance(parent, TabControl):
            raise RuntimeError("Tab(...) must be used directly inside a TabControl block.")
        self._parent = parent
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        self._parent.add_page(self.title, self._item)
        return False
