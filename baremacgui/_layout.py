"""Window, VBox, HBox and Spacer."""
from __future__ import annotations

from . import _core
from ._bridge import AK, FN, ensure_app
from ._options import (
    check_align, check_grow, check_padding, check_size, check_window_size, check_window_style,
)

_ALIGN_ATTR = {
    ("VBox", "start"): "NSLayoutAttributeLeading",
    ("VBox", "center"): "NSLayoutAttributeCenterX",
    ("VBox", "end"): "NSLayoutAttributeTrailing",
    ("VBox", "stretch"): "NSLayoutAttributeLeading",
    ("HBox", "start"): "NSLayoutAttributeTop",
    ("HBox", "center"): "NSLayoutAttributeCenterY",
    ("HBox", "end"): "NSLayoutAttributeBottom",
    ("HBox", "stretch"): "NSLayoutAttributeTop",
}


class Window:
    """A top-level window. Takes exactly one child, normally a VBox or HBox.

    size is the initial content size in points; the minimum size follows from
    the content. The window shows itself when its with-block ends.

    style="standard"  the usual title bar
    style="sidebar"   System-Settings-like: a Sidebar on the left lists pages, the chosen page
                      shows on the right. The window then holds a `with Sidebar():` block
                      and nothing else.
    style="unified"   Finder-like: no title text, a transparent title bar, and the
                      content starts below it. Put controls in the title bar with a
                      `with Toolbar():` block directly inside the window.
    """

    def __init__(self, title, size=(400, 300), resizable=True, visible=True, style="standard"):
        ak = AK()
        ensure_app()
        self.style = check_window_style(style)
        self._toolbar = None
        self._sidebar = None
        self._size = check_window_size(size)
        self._visible = bool(visible)
        self._item = None
        style = (
            ak.NSWindowStyleMaskTitled
            | ak.NSWindowStyleMaskClosable
            | ak.NSWindowStyleMaskMiniaturizable
        )
        if resizable:
            style |= ak.NSWindowStyleMaskResizable
        if self.style in ("unified", "sidebar"):
            style |= ak.NSWindowStyleMaskFullSizeContentView
        self.ns = ak.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            FN().NSMakeRect(0, 0, *self._size), style, ak.NSBackingStoreBuffered, False
        )
        # Python owns the reference; without this AppKit over-releases on close.
        self.ns.setReleasedWhenClosed_(False)
        self.ns.setTitle_(str(title))
        if self.style in ("unified", "sidebar"):
            self.ns.setTitlebarAppearsTransparent_(True)
        if self.style == "unified":
            self.ns.setTitleVisibility_(ak.NSWindowTitleHidden)
            if hasattr(self.ns, "setToolbarStyle_"):  # macOS 11+
                self.ns.setToolbarStyle_(ak.NSWindowToolbarStyleUnified)

    @property
    def title(self):
        return str(self.ns.title())

    @title.setter
    def title(self, value):
        self.ns.setTitle_(str(value))

    def close(self):
        self.ns.close()

    def accept(self, item):
        if self.style == "sidebar":
            raise ValueError("A sidebar window holds only a `with Sidebar():` block.")
        if self._item is not None:
            raise ValueError("A Window takes exactly one child. Wrap several controls in a VBox or HBox.")
        self._item = item

    def __enter__(self):
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        if self.style == "sidebar":
            if self._sidebar is None:
                raise ValueError('Window(style="sidebar") needs a `with Sidebar():` block.')
        elif self._item is not None:
            stack = self._item.view
            fit = stack.fittingSize()  # minimum window size follows from the content
            extra = 0.0
            if self.style == "unified":
                # The content view reaches under the title bar/toolbar; the stack is pinned
                # below it (contentLayoutGuide), so the window must be that much taller.
                container = AK().NSView.alloc().init()
                container.addSubview_(stack)
                self.ns.setContentView_(container)
                stack.setTranslatesAutoresizingMaskIntoConstraints_(False)
                guide = self.ns.contentLayoutGuide()
                stack.topAnchor().constraintEqualToAnchor_(guide.topAnchor()).setActive_(True)
                stack.leadingAnchor().constraintEqualToAnchor_(container.leadingAnchor()).setActive_(True)
                stack.trailingAnchor().constraintEqualToAnchor_(container.trailingAnchor()).setActive_(True)
                stack.bottomAnchor().constraintEqualToAnchor_(container.bottomAnchor()).setActive_(True)
                layout = self.ns.contentLayoutRect()
                extra = float(self.ns.contentView().frame().size.height - layout.size.height)
                if extra <= 0:
                    extra = 52.0 if self._toolbar is not None else 28.0
            else:
                self.ns.setContentView_(stack)
            self.ns.setContentMinSize_((fit.width, fit.height + extra))
            self.ns.setContentSize_(
                (max(self._size[0], fit.width), max(self._size[1], fit.height + extra))
            )
        self.ns.center()
        if self._visible:
            self.ns.makeKeyAndOrderFront_(None)
        return False


class _Box:
    """Common code of VBox and HBox, built on NSStackView.

    padding  space between the box edge and its children
    gap      space between children
    align    cross-axis alignment: start, center, end, or stretch (children fill
             the cross axis: the full width in a VBox, the full height in an HBox)
    grow     flex weight of the box itself inside its parent

    A box packs its children at the start. If none of them has grow > 0, an
    invisible filler absorbs extra space (like flexbox with justify-content:
    flex-start). In a VBox, nested boxes and children with grow > 0 always fill
    the full width.
    """

    KIND = ""

    def __init__(self, padding=0, gap=8, align=None, grow=0, **size):
        self.padding = check_padding(padding)
        self.gap = check_padding(gap)
        self.align = check_align(self.KIND, align)
        self.grow = check_grow(grow)
        self._size = check_size(size)
        self._items = []
        self.ns = None  # the NSStackView, available after the with-block

    def accept(self, item):
        self._items.append(item)

    def __enter__(self):
        _core.current()  # fail early with a clear message when used outside a Window
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        ak = AK()
        vertical = self.KIND == "VBox"
        orientation = (
            ak.NSUserInterfaceLayoutOrientationVertical
            if vertical
            else ak.NSUserInterfaceLayoutOrientationHorizontal
        )
        items = self._items
        views = [item.view for item in items]
        growers = [item for item in items if item.grow > 0]

        filler = None
        if items and not growers:
            filler = ak.NSView.alloc().init()
            views.append(filler)

        pad = self.padding
        stack = ak.NSStackView.stackViewWithViews_(views)
        stack.setOrientation_(orientation)
        stack.setDistribution_(ak.NSStackViewDistributionFill)
        stack.setSpacing_(self.gap)
        stack.setEdgeInsets_((pad, pad, pad, pad))
        stack.setAlignment_(getattr(ak, _ALIGN_ATTR[(self.KIND, self.align)]))

        if filler is not None:
            stack.setCustomSpacing_afterView_(0.0, items[-1].view)  # no extra gap before the filler
            filler.setContentHuggingPriority_forOrientation_(1, orientation)

        for item in growers:
            item.view.setContentHuggingPriority_forOrientation_(1, orientation)
        if len(growers) > 1:
            # Share extra space by weight. Priority 500 stays below the
            # compression resistance (750) so intrinsic minimum sizes still win.
            first = growers[0]
            for other in growers[1:]:
                constraint = _main_anchor(other.view, vertical).constraintEqualToAnchor_multiplier_(
                    _main_anchor(first.view, vertical), other.grow / first.grow
                )
                constraint.setPriority_(500)
                constraint.setActive_(True)

        for item in items:
            if item.fixed is not None:
                _main_anchor(item.view, vertical).constraintEqualToConstant_(item.fixed).setActive_(True)

        if vertical:
            for item in items:
                if item.spacer:
                    continue
                if self.align == "stretch" or item.fill:
                    item.view.widthAnchor().constraintEqualToAnchor_constant_(
                        stack.widthAnchor(), -2.0 * pad
                    ).setActive_(True)
        elif self.align == "stretch":
            for item in items:
                if item.spacer:
                    continue
                item.view.heightAnchor().constraintEqualToAnchor_constant_(
                    stack.heightAnchor(), -2.0 * pad
                ).setActive_(True)

        # Children that fill the cross axis must not resist being stretched there: a scroll view
        # reports an intrinsic size on newer macOS, and with the default priority 250 it would
        # keep its row small while another row took the free space.
        cross = 0 if vertical else 1
        for item in items:
            if item.spacer:
                continue
            if (vertical and (self.align == "stretch" or item.fill)) or (not vertical and self.align == "stretch"):
                item.view.setContentHuggingPriority_forOrientation_(1, cross)

        _core.apply_size(stack, self._size)
        self.ns = stack
        _core.add(stack, self.grow, fill=True)
        return False


def _main_anchor(view, vertical):
    return view.heightAnchor() if vertical else view.widthAnchor()


class VBox(_Box):
    """Stack children top to bottom."""

    KIND = "VBox"


class HBox(_Box):
    """Stack children left to right."""

    KIND = "HBox"


class Spacer:
    """Flexible space (default) or a fixed gap.

    Spacer()          absorbs free space, e.g. to push buttons to the right
    Spacer(grow=2)    takes twice the share of a Spacer()
    Spacer(size=24)   a fixed gap of 24 points along the box's main axis
    """

    def __init__(self, grow=None, size=None):
        if grow is not None and size is not None:
            raise ValueError("Spacer takes either grow or size, not both")
        fixed = None
        if size is not None:
            fixed = check_padding(size)
            weight = 0.0
        else:
            weight = check_grow(1 if grow is None else grow)
        view = AK().NSView.alloc().init()
        self.ns = view
        _core.add(view, weight, fixed=fixed, spacer=True)
