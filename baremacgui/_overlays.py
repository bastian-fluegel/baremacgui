"""Sheet (a window attached to a parent window) and Popover (a bubble next to a control)."""
from __future__ import annotations

from . import _core
from ._bridge import AK
from ._layout import Window
from ._options import check_popover_edge, check_window_size


class Sheet(Window):
    """A window that slides down from the top of a parent window and blocks only that window.

        with Sheet(win, size=(360, 160)) as sheet:
            with VBox(padding=20):
                ...
                Button("Close").on_click(sheet.close)
        sheet.show()

    It is built like a Window (one child) but does not appear until show().
    """

    def __init__(self, parent, size=(400, 200), resizable=False):
        if not isinstance(parent, Window):
            raise TypeError("Sheet needs the parent Window")
        super().__init__("", size=size, resizable=resizable, visible=False)
        ak = AK()
        mask = ak.NSWindowStyleMaskTitled | (ak.NSWindowStyleMaskResizable if resizable else 0)
        self.ns.setStyleMask_(mask)
        self._parent = parent
        self._open = False

    def _helper_window(self):
        return True

    @property
    def is_open(self):
        return self._open

    def show(self):
        """Slide the sheet down over the parent window."""
        if self._open:
            return
        self._open = True
        self._parent.ns.beginSheet_completionHandler_(self.ns, None)

    def close(self):
        """Slide the sheet away again."""
        if not self._open:
            return
        self._open = False
        self._parent.ns.endSheet_(self.ns)


class Popover:
    """A small bubble with content, attached to a control. Takes exactly one child.

        with Popover() as info:
            with VBox(padding=12):
                Label("Details")
        info.show(button)

    transient=True (default) closes it on a click anywhere else.
    """

    def __init__(self, transient=True):
        self._transient = bool(transient)
        self._item = None
        self.ns = None

    def accept(self, item):
        if self._item is not None:
            raise ValueError("A Popover takes exactly one child. Wrap several controls in a VBox or HBox.")
        self._item = item

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        if self._item is None:
            raise ValueError("A Popover needs content.")
        ak = AK()
        stack = self._item.view
        controller = ak.NSViewController.alloc().init()
        controller.setView_(stack)
        popover = ak.NSPopover.alloc().init()
        popover.setContentViewController_(controller)
        popover.setBehavior_(
            ak.NSPopoverBehaviorTransient if self._transient else ak.NSPopoverBehaviorApplicationDefined
        )
        popover.setContentSize_(stack.fittingSize())
        self._controller = controller  # keep alive
        self.ns = popover
        return False

    def show(self, anchor, edge="bottom"):
        """Open next to `anchor` (a control, or a Toolbar button). edge: bottom, top, left or right."""
        ak = AK()
        check_popover_edge(edge)
        view = getattr(anchor, "ns", anchor)
        side = {
            "bottom": ak.NSMinYEdge, "top": ak.NSMaxYEdge, "left": ak.NSMinXEdge, "right": ak.NSMaxXEdge,
        }[edge]
        self.ns.showRelativeToRect_ofView_preferredEdge_(view.bounds(), view, side)

    def close(self):
        self.ns.close()

    @property
    def is_open(self):
        return bool(self.ns.isShown())
