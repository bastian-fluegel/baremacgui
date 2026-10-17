"""Label, TextBox, ComboBox, Button, CheckBox and SpinBox."""
from __future__ import annotations

from . import _core
from ._bridge import AK, FN, make_target
from ._events import connect_options, event, split_options
from ._options import check_grow, check_size, check_spin_range, clamp, parse_int


def _text_of(field):
    """Current text of a field, including an edit that has not been committed yet."""
    editor = field.currentEditor()
    return str(editor.string()) if editor is not None else str(field.stringValue())


class Control:
    """Base class: registers the view with the innermost open container.

    Every control accepts grow (flex weight) and width, height, min_width,
    max_width, min_height, max_height (points), tooltip (the yellow hint on hover) and
    accessibility_label (what VoiceOver reads; give it to every control that shows no text of its own,
    such as an icon button, an Image or a Slider).
    """

    def __init__(self, ns, grow=0, **size):
        handlers = split_options(size)
        tooltip = size.pop("tooltip", None)
        label = size.pop("accessibility_label", None)
        grow = check_grow(grow)
        size = check_size(size)
        self.ns = ns
        self._targets = {}
        self._muted = getattr(self, "_muted", False)
        _core.apply_size(ns, size)
        _core.add(ns, grow, fill=grow > 0)
        connect_options(self, handlers)
        if tooltip is not None:
            self.tooltip = tooltip
        if label is not None:
            self.accessibility_label = label

    @property
    def tooltip(self):
        """The hint shown when the pointer rests on the control, or None."""
        value = self.ns.toolTip()
        return None if value is None else str(value)

    @tooltip.setter
    def tooltip(self, text):
        self.ns.setToolTip_(None if text is None else str(text))

    @property
    def accessibility_label(self):
        """The text VoiceOver reads for this control, or None (then AppKit uses the visible title)."""
        value = self._menu_view().accessibilityLabel()
        return None if value is None else str(value)

    @accessibility_label.setter
    def accessibility_label(self, text):
        self._menu_view().setAccessibilityLabel_(None if text is None else str(text))

    @property
    def enabled(self):
        return bool(self.ns.isEnabled())

    @enabled.setter
    def enabled(self, value):
        self.ns.setEnabled_(bool(value))

    @property
    def visible(self):
        """False hides the control; a box closes the gap it leaves."""
        return not bool(self.ns.isHidden())

    @visible.setter
    def visible(self, value):
        self.ns.setHidden_(not value)

    @property
    def context_menu(self):
        """A ContextMenu shown on right-click (Control-click), or None."""
        return getattr(self, "_context_menu", None)

    @context_menu.setter
    def context_menu(self, menu):
        self._context_menu = menu
        self._menu_view().setMenu_(None if menu is None else menu.ns)

    def _menu_view(self):
        """The view that receives the right-click (the inner view for scroll-view based controls)."""
        return self.ns

    def _bind(self, ns, handler):
        """Route the action of `ns` to `handler` (a function without arguments)."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        target = make_target(handler)
        self._targets[id(ns)] = target  # NSControl keeps its target only weakly
        ns.setTarget_(target)
        ns.setAction_(b"fire:")


class Label(Control):
    def __init__(self, text="", grow=0, **size):
        super().__init__(AK().NSTextField.labelWithString_(str(text)), grow, **size)

    @property
    def text(self):
        return str(self.ns.stringValue())

    @text.setter
    def text(self, value):
        self.ns.setStringValue_(str(value))


class TextBox(Control):
    """Single-line field, or a scrollable multi-line view (multiline=True).

    password=True gives a secure single-line field. placeholder is single-line
    only. The multi-line view uses a monospaced font and turns off smart
    quotes, dashes and spelling correction, which get in the way in tools.
    """

    on_enter = event()
    on_change = event()

    def __init__(self, text="", multiline=False, readonly=False, password=False,
                 placeholder="", grow=0, **size):
        ak = AK()
        self.multiline = bool(multiline)
        self._readonly = bool(readonly)
        self._tv = None
        if self.multiline:
            if password or placeholder:
                raise TypeError("password and placeholder are only for single-line TextBox")
            ns = ak.NSTextView.scrollableTextView()  # an NSScrollView
            tv = ns.documentView()
            tv.setEditable_(not self._readonly)
            tv.setRichText_(False)
            tv.setAutomaticQuoteSubstitutionEnabled_(False)
            tv.setAutomaticDashSubstitutionEnabled_(False)
            tv.setAutomaticSpellingCorrectionEnabled_(False)
            tv.setFont_(ak.NSFont.monospacedSystemFontOfSize_weight_(12, ak.NSFontWeightRegular))
            tv.setString_(str(text))
            self._tv = tv
            size.setdefault("min_height", 120)
            size.setdefault("min_width", 240)
        else:
            if password:
                ns = ak.NSSecureTextField.alloc().init()
                ns.setStringValue_(str(text))
            else:
                ns = ak.NSTextField.textFieldWithString_(str(text))
            ns.setEditable_(not self._readonly)
            if placeholder:
                ns.setPlaceholderString_(str(placeholder))
        super().__init__(ns, grow, **size)
        if not self.multiline:
            self._bind(ns, self.on_enter.emit)  # Return in a single-line field
        self._watch_typing(self._tv if self.multiline else ns)

    def _menu_view(self):
        return self._tv if self.multiline else self.ns

    def _watch_typing(self, view):
        """Call on_change on every edit of the user (not for changes made from code)."""
        name = "NSTextDidChangeNotification" if self.multiline else "NSControlTextDidChangeNotification"
        target = make_target(self.on_change.emit)
        self._targets["typing"] = target  # the notification center does not keep its observer alive
        FN().NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            target, b"fire:", name, view
        )

    @property
    def text(self):
        return str(self._tv.string()) if self.multiline else _text_of(self.ns)

    @text.setter
    def text(self, value):
        if self.multiline:
            self._tv.setString_(str(value))
        else:
            self.ns.setStringValue_(str(value))

    def append(self, text):
        """Add text at the end and scroll to it (multi-line only)."""
        if not self.multiline:
            raise TypeError("append() needs a multiline TextBox")
        self._tv.textStorage().mutableString().appendString_(str(text))
        self._tv.scrollToEndOfDocument_(None)

    @property
    def readonly(self):
        return self._readonly

    @readonly.setter
    def readonly(self, value):
        self._readonly = bool(value)
        (self._tv or self.ns).setEditable_(not self._readonly)

    @property
    def enabled(self):
        if self.multiline:
            return bool(self._tv.isSelectable())
        return bool(self.ns.isEnabled())

    @enabled.setter
    def enabled(self, value):
        if self.multiline:
            self._tv.setSelectable_(bool(value))
            self._tv.setEditable_(bool(value) and not self._readonly)
        else:
            self.ns.setEnabled_(bool(value))


class ComboBox(Control):
    """Drop-down list with a text field. By default the user can only pick from the list;
    editable=True lets them type their own text as well."""

    on_change = event()

    def __init__(self, items=(), selected=None, editable=False, grow=0, **size):
        ns = AK().NSComboBox.alloc().init()
        items = [str(item) for item in items]
        ns.addItemsWithObjectValues_(items)
        ns.setEditable_(bool(editable))
        if selected is not None:
            if not 0 <= selected < len(items):
                raise ValueError(f"selected index {selected} is outside the {len(items)} items")
            ns.selectItemAtIndex_(selected)
            ns.setStringValue_(items[selected])
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)

    @property
    def text(self):
        return _text_of(self.ns)

    @text.setter
    def text(self, value):
        self.ns.setStringValue_(str(value))

    @property
    def index(self):
        """Index of the selected list entry, or -1 for custom text."""
        return int(self.ns.indexOfSelectedItem())

    @index.setter
    def index(self, value):
        items = self.items
        if not 0 <= value < len(items):
            raise ValueError(f"index {value} is outside the {len(items)} items")
        self.ns.selectItemAtIndex_(value)
        self.ns.setStringValue_(items[value])

    @property
    def items(self):
        return [str(item) for item in self.ns.objectValues()]

    @items.setter
    def items(self, values):
        self.ns.removeAllItems()
        self.ns.addItemsWithObjectValues_([str(value) for value in values])


class Button(Control):
    on_click = event()

    def __init__(self, text, default=False, symbol=None, grow=0, **size):
        ak = AK()
        ns = ak.NSButton.buttonWithTitle_target_action_(str(text), None, None)
        if symbol is not None:  # SF Symbol, macOS 11+; with an empty title: icon only
            image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(symbol), None)
            if image is None:
                raise ValueError(f"unknown system symbol: {symbol!r}")
            ns.setImage_(image)
            if not str(text):
                ns.setImagePosition_(ak.NSImageOnly)
                ns.setBezelStyle_(ak.NSBezelStyleTexturedRounded)
        if default:
            ns.setKeyEquivalent_("\r")
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_click.emit)

    @property
    def text(self):
        return str(self.ns.title())

    @text.setter
    def text(self, value):
        self.ns.setTitle_(str(value))


class CheckBox(Control):
    on_change = event()

    def __init__(self, text, checked=False, grow=0, **size):
        ns = AK().NSButton.checkboxWithTitle_target_action_(str(text), None, None)
        super().__init__(ns, grow, **size)
        self._bind(ns, self.on_change.emit)
        self.checked = checked

    @property
    def checked(self):
        return int(self.ns.state()) == int(AK().NSControlStateValueOn)

    @checked.setter
    def checked(self, value):
        ak = AK()
        self.ns.setState_(ak.NSControlStateValueOn if value else ak.NSControlStateValueOff)


class SpinBox(Control):
    """Integer field with up/down arrows.

    Assigning .value never calls the on_change handler; only user input does.
    Reading .value also picks up text typed but not yet committed.
    """

    on_change = event()

    def __init__(self, value=0, minimum=0, maximum=100, step=1, grow=0, **size):
        value = check_spin_range(value, minimum, maximum, step)
        ak = AK()
        self._min, self._max = minimum, maximum
        self._value = value

        field = ak.NSTextField.textFieldWithString_(str(value))
        field.setAlignment_(ak.NSTextAlignmentRight)
        field.setTranslatesAutoresizingMaskIntoConstraints_(False)
        field.widthAnchor().constraintEqualToConstant_(60.0).setActive_(True)

        stepper = ak.NSStepper.alloc().init()
        stepper.setMinValue_(minimum)
        stepper.setMaxValue_(maximum)
        stepper.setIncrement_(step)
        stepper.setValueWraps_(False)
        stepper.setIntegerValue_(value)

        row = ak.NSStackView.stackViewWithViews_([field, stepper])
        row.setOrientation_(ak.NSUserInterfaceLayoutOrientationHorizontal)
        row.setSpacing_(4.0)
        row.setAlignment_(ak.NSLayoutAttributeCenterY)

        self._field, self._stepper = field, stepper
        super().__init__(row, grow, **size)
        self._bind(field, self._from_field)
        self._bind(stepper, self._from_stepper)

    def _set(self, value):
        self._value = clamp(value, self._min, self._max)
        self._field.setStringValue_(str(self._value))
        self._stepper.setIntegerValue_(self._value)

    def _fire(self):
        self.on_change.emit()

    def _from_field(self):
        parsed = parse_int(_text_of(self._field))
        self._set(self._value if parsed is None else parsed)
        self._fire()

    def _from_stepper(self):
        self._set(int(self._stepper.integerValue()))
        self._fire()

    @property
    def value(self):
        parsed = parse_int(_text_of(self._field))
        return self._value if parsed is None else clamp(parsed, self._min, self._max)

    @value.setter
    def value(self, number):
        if isinstance(number, bool) or not isinstance(number, int):
            raise TypeError(f"SpinBox value must be an int, got {number!r}")
        self._set(number)

    @property
    def enabled(self):
        return bool(self._field.isEnabled())

    @enabled.setter
    def enabled(self, flag):
        self._field.setEnabled_(bool(flag))
        self._stepper.setEnabled_(bool(flag))
