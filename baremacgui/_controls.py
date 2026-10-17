"""Label, TextBox, ComboBox, Button, CheckBox and SpinBox."""
from __future__ import annotations

from . import _core
from ._bridge import AK, make_target
from ._options import check_grow, check_size, check_spin_range, clamp, parse_int


def _text_of(field):
    """Current text of a field, including an edit that has not been committed yet."""
    editor = field.currentEditor()
    return str(editor.string()) if editor is not None else str(field.stringValue())


class Control:
    """Base class: registers the view with the innermost open container.

    Every control accepts grow (flex weight) and width, height, min_width,
    max_width, min_height, max_height (points).
    """

    def __init__(self, ns, grow=0, **size):
        grow = check_grow(grow)
        size = check_size(size)
        self.ns = ns
        self._targets = {}
        _core.apply_size(ns, size)
        _core.add(ns, grow, fill=grow > 0)

    @property
    def enabled(self):
        return bool(self.ns.isEnabled())

    @enabled.setter
    def enabled(self, value):
        self.ns.setEnabled_(bool(value))

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

    def on_enter(self, handler):
        """Call handler() when Return is pressed (single-line only)."""
        if self.multiline:
            raise TypeError("on_enter() is for single-line TextBox")
        self._bind(self.ns, handler)


class ComboBox(Control):
    """Drop-down list with a text field. editable=False restricts it to the list."""

    def __init__(self, items=(), selected=None, editable=True, grow=0, **size):
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

    def on_change(self, handler):
        """Call handler() when an entry is picked or Return is pressed."""
        self._bind(self.ns, handler)


class Button(Control):
    def __init__(self, title, default=False, symbol=None, grow=0, **size):
        ak = AK()
        ns = ak.NSButton.buttonWithTitle_target_action_(str(title), None, None)
        if symbol is not None:  # SF Symbol, macOS 11+; with an empty title: icon only
            image = ak.NSImage.imageWithSystemSymbolName_accessibilityDescription_(str(symbol), None)
            if image is None:
                raise ValueError(f"unknown system symbol: {symbol!r}")
            ns.setImage_(image)
            if not str(title):
                ns.setImagePosition_(ak.NSImageOnly)
                ns.setBezelStyle_(ak.NSBezelStyleTexturedRounded)
        if default:
            ns.setKeyEquivalent_("\r")
        super().__init__(ns, grow, **size)

    @property
    def title(self):
        return str(self.ns.title())

    @title.setter
    def title(self, value):
        self.ns.setTitle_(str(value))

    def on_click(self, handler):
        """Call handler() on click. Handlers take no arguments."""
        self._bind(self.ns, handler)


class CheckBox(Control):
    def __init__(self, title, checked=False, grow=0, **size):
        ns = AK().NSButton.checkboxWithTitle_target_action_(str(title), None, None)
        super().__init__(ns, grow, **size)
        self.checked = checked

    @property
    def checked(self):
        return int(self.ns.state()) == int(AK().NSControlStateValueOn)

    @checked.setter
    def checked(self, value):
        ak = AK()
        self.ns.setState_(ak.NSControlStateValueOn if value else ak.NSControlStateValueOff)

    def on_change(self, handler):
        """Call handler() when the user toggles the box."""
        self._bind(self.ns, handler)


class SpinBox(Control):
    """Integer field with up/down arrows.

    Assigning .value never calls the on_change handler; only user input does.
    Reading .value also picks up text typed but not yet committed.
    """

    def __init__(self, value=0, minimum=0, maximum=100, step=1, grow=0, **size):
        value = check_spin_range(value, minimum, maximum, step)
        ak = AK()
        self._min, self._max = minimum, maximum
        self._value = value
        self._on_change = None

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
        if self._on_change is not None:
            self._on_change()

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

    def on_change(self, handler):
        """Call handler() when the user changes the number."""
        if not callable(handler):
            raise TypeError("handler must be callable")
        self._on_change = handler
