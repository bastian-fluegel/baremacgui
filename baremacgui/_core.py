"""The with-block stack and helpers shared by layouts, controls and containers."""
from __future__ import annotations

_stack: list = []


class Item:
    """One child waiting to be placed into its parent container.

    grow    flex weight along the parent's main axis (0 = natural size)
    fixed   fixed main-axis size in points (used by Spacer(size=...))
    fill    in a VBox, stretch to the full width of the box
    spacer  a Spacer: never stretched across the box, never counted as content
    """

    __slots__ = ("view", "grow", "fixed", "fill", "spacer")

    def __init__(self, view, grow=0.0, fixed=None, fill=False, spacer=False):
        self.view = view
        self.grow = grow
        self.fixed = fixed
        self.fill = fill
        self.spacer = spacer


def current():
    if not _stack:
        raise RuntimeError(
            "Create controls inside a `with Window(...)` block "
            "(or inside a VBox, HBox, GroupBox or Tab within it)."
        )
    return _stack[-1]


def push(container):
    _stack.append(container)


def pop(container):
    if not _stack or _stack[-1] is not container:
        raise RuntimeError("with-blocks are nested incorrectly")
    _stack.pop()


def add(view, grow=0.0, fixed=None, fill=False, spacer=False):
    """Hand a finished view to the innermost open container."""
    current().accept(Item(view, grow, fixed, fill, spacer))


def apply_size(view, size):
    """Apply width/height/min_*/max_* (already validated) as Auto Layout constraints."""
    if not size:
        return
    view.setTranslatesAutoresizingMaskIntoConstraints_(False)
    for axis in ("width", "height"):
        anchor = view.widthAnchor() if axis == "width" else view.heightAnchor()
        if axis in size:
            anchor.constraintEqualToConstant_(size[axis]).setActive_(True)
        if "min_" + axis in size:
            anchor.constraintGreaterThanOrEqualToConstant_(size["min_" + axis]).setActive_(True)
        if "max_" + axis in size:
            anchor.constraintLessThanOrEqualToConstant_(size["max_" + axis]).setActive_(True)


def pin(child, parent, inset=0.0):
    """Pin all four edges of `child` to `parent`, `inset` points in."""
    child.setTranslatesAutoresizingMaskIntoConstraints_(False)
    child.leadingAnchor().constraintEqualToAnchor_constant_(parent.leadingAnchor(), inset).setActive_(True)
    child.trailingAnchor().constraintEqualToAnchor_constant_(parent.trailingAnchor(), -inset).setActive_(True)
    child.topAnchor().constraintEqualToAnchor_constant_(parent.topAnchor(), inset).setActive_(True)
    child.bottomAnchor().constraintEqualToAnchor_constant_(parent.bottomAnchor(), -inset).setActive_(True)
