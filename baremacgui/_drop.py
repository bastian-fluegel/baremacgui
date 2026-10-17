"""DropZone: a place where files can be dropped from Finder."""
from __future__ import annotations

from ._bridge import AK, drop_zone_class
from ._controls import Control
from ._events import event
from ._options import check_extensions, filter_dropped


class DropZone(Control):
    """A framed area that accepts files dragged from Finder (native NSDraggingDestination).

        zone = DropZone("Drop images here", extensions=["png", "jpg"], on_drop=lambda: print(zone.paths))

    `extensions` limits the accepted files (None accepts everything, folders included);
    multiple=False accepts exactly one item per drop. While the pointer is over the zone with items
    it would not accept, macOS shows the usual "not allowed" cursor; accepted items highlight the frame.
    `paths` holds the files of the last accepted drop. on_drop fires once per accepted drop.

    Native NSBox has no dashed border; the frame is a plain line (the look of a native custom box).
    """

    on_drop = event()

    def __init__(self, text="Drop files here", extensions=None, multiple=True, grow=0, **size):
        ak = AK()
        self.extensions = check_extensions(extensions)
        self.multiple = bool(multiple)
        self.paths = []
        ns = drop_zone_class().alloc().init()
        ns.setBoxType_(ak.NSBoxCustom)
        ns.setTitlePosition_(ak.NSNoTitle)
        ns.setBorderWidth_(1.5)
        ns.setCornerRadius_(10.0)
        ns.setContentViewMargins_((12.0, 12.0))
        ns._bmc_owner = self
        self._label = ak.NSTextField.labelWithString_(str(text))
        self._label.setAlignment_(ak.NSTextAlignmentCenter)
        self._label.setTextColor_(ak.NSColor.secondaryLabelColor())
        self._label.setTranslatesAutoresizingMaskIntoConstraints_(False)
        content = ns.contentView()
        content.addSubview_(self._label)
        for attribute in (ak.NSLayoutAttributeCenterX, ak.NSLayoutAttributeCenterY):
            ak.NSLayoutConstraint.constraintWithItem_attribute_relatedBy_toItem_attribute_multiplier_constant_(
                self._label, attribute, ak.NSLayoutRelationEqual, content, attribute, 1.0, 0.0).setActive_(True)
        ns.registerForDraggedTypes_([ak.NSPasteboardTypeFileURL])
        size.setdefault("min_height", 80)
        super().__init__(ns, grow, **size)
        self._highlight(False)

    @property
    def text(self):
        return str(self._label.stringValue())

    @text.setter
    def text(self, value):
        self._label.setStringValue_(str(value))

    def _can_accept(self, paths):
        return bool(filter_dropped(paths, self.extensions, self.multiple))

    def _highlight(self, on):
        ak = AK()
        accent = ak.NSColor.controlAccentColor()
        self.ns.setBorderColor_(accent if on else ak.NSColor.separatorColor())
        self.ns.setFillColor_(accent.colorWithAlphaComponent_(0.12) if on else ak.NSColor.clearColor())

    def _drop(self, paths):
        accepted = filter_dropped(paths, self.extensions, self.multiple)
        if not accepted:
            return False
        self.paths = accepted
        self.on_drop.emit()
        return True
