"""Window, VBox, HBox and Spacer."""
from __future__ import annotations

from . import _core
from ._bridge import AK, FN, ensure_app, window_class, window_delegate_class
from ._events import connect_options, event, split_options
from ._options import (
    check_align, check_grow, check_justify, event_shortcut, parse_shortcut, check_padding, check_size, check_window_size, check_window_style,
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

    on_resize = event()
    on_destroy = event()

    def __init__(self, title, size=(400, 300), resizable=True, visible=True, style="standard", **options):
        ak = AK()
        ensure_app()
        handlers = split_options(options)
        if options:
            raise TypeError(f"Window got unexpected options: {sorted(options)}")
        self.on_close = handlers.pop("on_close", None)
        connect_options(self, handlers)
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
        self._menubar = None
        self._shortcuts = {}
        self._modal = False
        self._default_button = None
        self._cancel_button = None
        self.ns = window_class().alloc().initWithContentRect_styleMask_backing_defer_(
            FN().NSMakeRect(0, 0, *self._size), style, ak.NSBackingStoreBuffered, False
        )
        self.ns._bmc_owner = self
        # Python owns the reference; without this AppKit over-releases on close.
        self.ns.setReleasedWhenClosed_(False)
        self._delegate = window_delegate_class().alloc().initWithOwner_(self)  # held weakly by the window
        self.ns.setDelegate_(self._delegate)
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

    @property
    def size(self):
        """Content size (width, height) in points."""
        content = self.ns.contentView().frame().size
        return (float(content.width), float(content.height))

    def _should_close(self):
        """Called when the user closes the window. on_close returning False keeps it open."""
        if self.on_close is None:
            return True
        return self.on_close() is not False

    def _will_close(self):
        if self._modal:
            self._modal = False
            AK().NSApplication.sharedApplication().stopModal()
        self.on_destroy.emit()

    def _became_key(self):
        if self._menubar is not None:
            self._menubar.activate()

    def _shortcut_event(self, event):
        key, mods = event_shortcut(event.charactersIgnoringModifiers(), event.keyCode(), event.modifierFlags())
        handler = self._shortcuts.get((key, mods))
        if handler is None:
            return False
        handler.emit()
        return True

    def add_shortcut(self, keys, handler):
        """Call handler() when `keys` ("Cmd+K", "F5", "Escape") is pressed while this window is key."""
        key = parse_shortcut(keys)
        if not callable(handler):
            raise TypeError("handler must be callable")
        if key not in self._shortcuts:
            from ._events import Event

            self._shortcuts[key] = Event()
        self._shortcuts[key].connect(handler)

    @property
    def default_button(self):
        """The button Return clicks (also while typing in a text box)."""
        return self._default_button

    @default_button.setter
    def default_button(self, button):
        if self._default_button is not None:
            self._default_button.ns.setKeyEquivalent_("")
        self._default_button = button
        if button is not None:
            button.ns.setKeyEquivalent_("\r")

    @property
    def cancel_button(self):
        """The button Escape clicks."""
        return self._cancel_button

    @cancel_button.setter
    def cancel_button(self, button):
        if self._cancel_button is not None:
            self._cancel_button.ns.setKeyEquivalent_("")
        self._cancel_button = button
        if button is not None:
            button.ns.setKeyEquivalent_("\x1b")

    def show_modal(self):
        """Show the window and wait until it is closed; other windows of the app are blocked."""
        app = AK().NSApplication.sharedApplication()
        self.ns.center()
        self._modal = True
        self.ns.makeKeyAndOrderFront_(None)
        app.runModalForWindow_(self.ns)
        self._modal = False

    def close(self):
        """Close the window (like the red button: on_close may veto)."""
        self.ns.performClose_(None)

    def destroy(self):
        """Close the window without asking on_close."""
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
            self._became_key()
        return False


class _Box:
    """Common code of VBox and HBox, built on NSStackView.

    padding  space between the box edge and its children
    gap      space between children
    align    cross-axis alignment: start, center, end, or stretch (children fill
             the cross axis: the full width in a VBox, the full height in an HBox)
    justify  where the children sit along the main axis when none of them grows:
             start (default), center, end, or space_between
    grow     flex weight of the box itself inside its parent

    A box packs its children at the start. If none of them has grow > 0, an
    invisible filler absorbs extra space (like flexbox with justify-content:
    flex-start). In a VBox, nested boxes and children with grow > 0 always fill
    the full width.
    """

    KIND = ""

    def __init__(self, padding=0, gap=8, align=None, grow=0, justify="start", **size):
        self.justify = check_justify(justify)
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

        fillers = []
        if items and not growers:
            def new_filler():
                filler = ak.NSView.alloc().init()
                fillers.append(filler)
                return filler

            if self.justify == "start":
                views.append(new_filler())
            elif self.justify == "end":
                views.insert(0, new_filler())
            elif self.justify == "center":
                views.insert(0, new_filler())
                views.append(new_filler())
            elif len(views) > 1:  # space_between
                spaced = []
                for position, view in enumerate(views):
                    if position:
                        spaced.append(new_filler())
                    spaced.append(view)
                views = spaced
            else:
                views.append(new_filler())

        pad = self.padding
        stack = ak.NSStackView.stackViewWithViews_(views)
        stack.setOrientation_(orientation)
        stack.setDistribution_(ak.NSStackViewDistributionFill)
        stack.setSpacing_(self.gap)
        stack.setEdgeInsets_((pad, pad, pad, pad))
        stack.setAlignment_(getattr(ak, _ALIGN_ATTR[(self.KIND, self.align)]))

        for position, filler in enumerate(fillers):
            filler.setContentHuggingPriority_forOrientation_(1, orientation)
            stack.setCustomSpacing_afterView_(0.0, filler)
            before = views[views.index(filler) - 1] if views.index(filler) > 0 else None
            if before is not None:
                stack.setCustomSpacing_afterView_(0.0, before)  # no extra gap next to a filler
        if self.justify == "space_between" and len(fillers) > 0 and len(items) > 1:
            for filler in fillers:  # keep at least the normal gap between neighbours
                _main_anchor(filler, vertical).constraintGreaterThanOrEqualToConstant_(self.gap).setActive_(True)
        for other in fillers[1:]:  # several fillers share the free space equally
            _main_anchor(other, vertical).constraintEqualToAnchor_(_main_anchor(fillers[0], vertical)).setActive_(True)

        for item in growers:
            item.view.setContentHuggingPriority_forOrientation_(1, orientation)
        if growers:
            # Children without grow keep their natural size. Hugging priorities alone did not
            # decide this on a newer macOS (a nested box took the free space instead of the
            # growing row), so cap the main-axis size explicitly, below the 750 default
            # compression resistance and above every hugging priority.
            for item in items:
                if item.grow == 0 and not item.spacer and item.fixed is None:
                    fit = item.view.fittingSize()
                    natural = fit.height if vertical else fit.width
                    if natural > 0:
                        cap = _main_anchor(item.view, vertical).constraintLessThanOrEqualToConstant_(natural)
                        cap.setPriority_(700)
                        cap.setActive_(True)

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
