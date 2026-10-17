"""RadioGroup, DropDown, Slider, ProgressBar, Image, Separator, SearchField and SegmentedControl."""
from __future__ import annotations

from . import _core
from ._bridge import AK, FN, make_target
from ._controls import Control
from ._events import event
from ._options import check_float_range, check_index, check_items, check_ticks, clamp


class RadioGroup(Control):
    """Mutually exclusive choices. vertical=False lays them out in a row."""

    on_change = event()

    def __init__(self, items, selected=0, vertical=True, gap=6, grow=0, **size):
        ak = AK()
        self._items = check_items(items, minimum=2, what="radio items")
        check_index(selected, len(self._items), "selected")
        self._buttons = [
            ak.NSButton.radioButtonWithTitle_target_action_(title, None, None) for title in self._items
        ]
        stack = ak.NSStackView.stackViewWithViews_(self._buttons)
        stack.setOrientation_(
            ak.NSUserInterfaceLayoutOrientationVertical if vertical
            else ak.NSUserInterfaceLayoutOrientationHorizontal
        )
        stack.setSpacing_(float(gap))
        stack.setAlignment_(ak.NSLayoutAttributeLeading if vertical else ak.NSLayoutAttributeCenterY)
        super().__init__(stack, grow, **size)
        # One shared target and one action: that is what makes AppKit treat the buttons as a group.
        target = make_target(self.on_change.emit)
        self._targets["group"] = target
        for button in self._buttons:
            button.setTarget_(target)
            button.setAction_(b"fire:")
        self.index = selected

    @property
    def index(self):
        on = int(AK().NSControlStateValueOn)
        for position, button in enumerate(self._buttons):
            if int(button.state()) == on:
                return position
        return -1

    @index.setter
    def index(self, value):
        check_index(value, len(self._items), "index")
        ak = AK()
        for position, button in enumerate(self._buttons):
            button.setState_(ak.NSControlStateValueOn if position == value else ak.NSControlStateValueOff)

    @property
    def text(self):
        """Label of the selected choice."""
        return self._items[self.index]

    @property
    def enabled(self):
        return all(bool(button.isEnabled()) for button in self._buttons)

    @enabled.setter
    def enabled(self, flag):
        for button in self._buttons:
            button.setEnabled_(bool(flag))



class DropDown(Control):
    """The standard macOS pop-up menu: pick one entry from a list (no typing)."""

    on_change = event()

    def __init__(self, items=(), selected=0, grow=0, **size):
        ak = AK()
        entries = check_items(items)
        ns = ak.NSPopUpButton.alloc().initWithFrame_pullsDown_(FN().NSMakeRect(0, 0, 0, 0), False)
        ns.addItemsWithTitles_(entries)
        if entries and selected is not None:
            check_index(selected, len(entries), "selected")
            ns.selectItemAtIndex_(selected)
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)

    @property
    def text(self):
        title = self.ns.titleOfSelectedItem()
        return "" if title is None else str(title)

    @property
    def index(self):
        """Index of the selected entry, or -1 if the list is empty."""
        return int(self.ns.indexOfSelectedItem())

    @index.setter
    def index(self, value):
        check_index(value, len(self.items), "index")
        self.ns.selectItemAtIndex_(value)

    @property
    def items(self):
        return [str(title) for title in self.ns.itemTitles()]

    @items.setter
    def items(self, values):
        self.ns.removeAllItems()
        self.ns.addItemsWithTitles_(check_items(values))



class Slider(Control):
    """Slider with a float value between minimum and maximum.

    continuous=True calls the handler while dragging, False only on release.
    vertical=True stands the slider upright (give it a height).
    ticks=n draws n tick marks (n >= 2) from minimum to maximum; snap=True lets the knob rest only on
    the marks (BareWinGUI has `ticks` as a bool and `tick_frequency`; here the count is the native way).
    Assigning .value never calls the handler; only user input does.
    """

    on_change = event()

    def __init__(self, value=0, minimum=0, maximum=100, continuous=True, vertical=False, ticks=None, snap=False,
                 grow=0, **size):
        value = check_float_range(value, minimum, maximum)
        ticks = check_ticks(ticks)
        self._min, self._max = float(minimum), float(maximum)
        ns = AK().NSSlider.sliderWithValue_minValue_maxValue_target_action_(
            value, self._min, self._max, None, None
        )
        ns.setContinuous_(bool(continuous))
        if vertical:
            ns.setVertical_(True)
            size.setdefault("min_height", 120)
        else:
            size.setdefault("min_width", 120)
        if ticks is not None:
            ns.setNumberOfTickMarks_(ticks)
            ns.setAllowsTickMarkValuesOnly_(bool(snap))
        elif snap:
            raise ValueError("snap=True needs ticks=")
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)

    @property
    def value(self):
        return float(self.ns.doubleValue())

    @value.setter
    def value(self, number):
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise TypeError(f"Slider value must be a number, got {number!r}")
        self.ns.setDoubleValue_(clamp(float(number), self._min, self._max))



class ProgressBar(Control):
    """Progress bar. indeterminate=True shows the animated "busy" bar instead of a value.

    Call .value from the UI thread only; from a worker use app.invoke(...).
    """

    def __init__(self, value=0, minimum=0, maximum=100, indeterminate=False, grow=0, **size):
        value = check_float_range(value, minimum, maximum)
        ns = AK().NSProgressIndicator.alloc().init()
        ns.setMinValue_(float(minimum))
        ns.setMaxValue_(float(maximum))
        ns.setDoubleValue_(value)
        ns.setIndeterminate_(bool(indeterminate))
        self._min, self._max = float(minimum), float(maximum)
        size.setdefault("min_width", 120)
        super().__init__(ns, grow, **size)
        if indeterminate:
            self.start()

    @property
    def value(self):
        return float(self.ns.doubleValue())

    @value.setter
    def value(self, number):
        if isinstance(number, bool) or not isinstance(number, (int, float)):
            raise TypeError(f"ProgressBar value must be a number, got {number!r}")
        self.ns.setDoubleValue_(clamp(float(number), self._min, self._max))

    @property
    def indeterminate(self):
        return bool(self.ns.isIndeterminate())

    @indeterminate.setter
    def indeterminate(self, flag):
        self.ns.setIndeterminate_(bool(flag))
        self.start() if flag else self.stop()

    def start(self):
        """Run the busy animation (indeterminate bars)."""
        self.ns.startAnimation_(None)

    def stop(self):
        self.ns.stopAnimation_(None)

    @property
    def enabled(self):
        raise TypeError("ProgressBar has no enabled state")

    @enabled.setter
    def enabled(self, flag):
        raise TypeError("ProgressBar has no enabled state")


class Image(Control):
    """A picture from a file (path=...) or a system symbol (symbol="gear", macOS 11+).

    The image keeps its aspect ratio and is scaled into width/height if you give them;
    without them it shows at its natural size. `description` is what VoiceOver reads (say what the
    picture means, e.g. "Warning"); without it a screen reader has nothing to say.
    """

    def __init__(self, path=None, symbol=None, description=None, grow=0, **size):
        if (path is None) == (symbol is None):
            raise ValueError("give exactly one of path or symbol")
        ak = AK()
        if path is not None:
            image = ak.NSImage.alloc().initWithContentsOfFile_(str(path))
            if image is None:
                raise FileNotFoundError(f"cannot load image: {path}")
        else:
            image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(symbol), None)
            if image is None:
                raise ValueError(f"unknown system symbol: {symbol!r}")
        ns = ak.NSImageView.imageViewWithImage_(image)
        ns.setImageScaling_(ak.NSImageScaleProportionallyUpOrDown)
        if description is not None:
            size["accessibility_label"] = str(description)
        super().__init__(ns, grow, **size)


class Separator:
    """A thin horizontal line. Use it in a VBox; it spans the box width."""

    def __init__(self):
        ak = AK()
        box = ak.NSBox.alloc().init()
        box.setBoxType_(ak.NSBoxSeparator)
        _core.apply_size(box, {"height": 1.0})
        self.ns = box
        _core.add(box, 0, fill=True)


class SearchField(Control):
    """The standard search field. on_change fires while typing and on Enter."""

    on_change = event()

    def __init__(self, text="", placeholder="Search", grow=0, **size):
        size.setdefault("min_width", 160.0)
        ns = AK().NSSearchField.alloc().init()
        ns.setStringValue_(str(text))
        ns.setPlaceholderString_(str(placeholder))
        ns.setSendsSearchStringImmediately_(True)
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)

    @property
    def text(self):
        return str(self.ns.stringValue())

    @text.setter
    def text(self, value):
        self.ns.setStringValue_(str(value))



class SegmentedControl(Control):
    """A row of connected buttons where one is selected (Finder's view switcher).

    Give labels in `items`, or SF Symbol names in `symbols` (not both).
    """

    on_change = event()

    def __init__(self, items=None, symbols=None, selected=0, grow=0, **size):
        if (items is None) == (symbols is None):
            raise ValueError("give exactly one of items or symbols")
        ak = AK()
        self._symbols = symbols is not None
        names = check_items(symbols if self._symbols else items, minimum=2, what="segments")
        check_index(selected, len(names), "selected")
        self._items = names
        ns = ak.NSSegmentedControl.alloc().init()
        ns.setSegmentCount_(len(names))
        for position, name in enumerate(names):
            if self._symbols:
                image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
                if image is None:
                    raise ValueError(f"unknown system symbol: {name!r}")
                ns.setImage_forSegment_(image, position)
            else:
                ns.setLabel_forSegment_(name, position)
        ns.setTrackingMode_(ak.NSSegmentSwitchTrackingSelectOne)
        ns.setSelectedSegment_(selected)
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)

    @property
    def index(self):
        return int(self.ns.selectedSegment())

    @index.setter
    def index(self, value):
        check_index(value, len(self._items), "index")
        self.ns.setSelectedSegment_(value)

    @property
    def text(self):
        """Label (or symbol name) of the selected segment."""
        return self._items[self.index]



class Custom(Control):
    """Embed any AppKit view (an NSView) you made yourself.

    The escape hatch for what baremacgui has no control for yet:

        Custom(NSColorWell.alloc().init(), width=44, height=24)

    The view takes part in the layout like any other control; `.ns` is the view.
    """

    def __init__(self, view, grow=0, **size):
        if view is None or not hasattr(view, "setHidden_"):
            raise TypeError("Custom needs an NSView, got %r" % (view,))
        super().__init__(view, grow, **size)
