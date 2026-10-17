"""SplitView: panes with draggable dividers."""
from __future__ import annotations

from . import _core
from ._bridge import AK
from ._options import check_fixed_panes, check_grow, check_size, check_split


class SplitView:
    """Two or more panes separated by draggable dividers (native NSSplitView).

        with SplitView(fixed=[0], min_pane=160, autosave="main-split", grow=1) as split:
            with VBox(padding=8): ...      # pane 0
            with VBox(padding=8): ...      # pane 1

    orientation  "horizontal": panes side by side (default); "vertical": stacked
    min_pane     smallest size of a pane in points; the user cannot drag below it
    fixed        pane indexes that keep their size when the window grows; the others take the space
    divider      "thin" (default), "thick" or "pane"
    autosave     a name: the divider positions are remembered between runs

    Each child (normally a VBox or HBox) is one pane. `split.set_position(0, 220)` moves a divider
    from code (points from the start edge). Differences from native: panes cannot collapse by
    dragging past the minimum, and panes cannot be added after the with-block.
    """

    def __init__(self, orientation="horizontal", min_pane=120, fixed=(), divider="thin", autosave=None,
                 grow=1, **size):
        self.orientation, self.divider = check_split(orientation, divider)
        self.min_pane = float(check_size({"width": min_pane})["width"])
        self._fixed = tuple(fixed)
        self.autosave = None if autosave is None else str(autosave)
        self.grow = check_grow(grow)
        self._size = check_size(size)
        self._items = []
        self.ns = None

    def accept(self, item):
        self._items.append(item)

    def __enter__(self):
        _core.current()
        _core.push(self)
        return self

    def __exit__(self, exc_type, exc, tb):
        _core.pop(self)
        if exc_type is not None:
            return False
        if len(self._items) < 2:
            raise ValueError("A SplitView needs at least two panes.")
        fixed = check_fixed_panes(self._fixed, len(self._items))
        ak = AK()
        split = ak.NSSplitView.alloc().init()
        horizontal = self.orientation == "horizontal"
        split.setVertical_(horizontal)  # NSSplitView "vertical" means vertical divider lines
        split.setDividerStyle_({
            "thin": ak.NSSplitViewDividerStyleThin,
            "thick": ak.NSSplitViewDividerStyleThick,
            "pane": ak.NSSplitViewDividerStylePaneSplitter,
        }[self.divider])
        for position, item in enumerate(self._items):
            view = item.view
            view.setTranslatesAutoresizingMaskIntoConstraints_(False)
            split.addArrangedSubview_(view)
            anchor = view.widthAnchor() if horizontal else view.heightAnchor()
            anchor.constraintGreaterThanOrEqualToConstant_(self.min_pane).setActive_(True)
            # Higher holding priority = this pane resists being resized when the window changes.
            split.setHoldingPriority_forSubviewAtIndex_(260 if position in fixed else 250, position)
        if self.autosave:
            split.setAutosaveName_(self.autosave)
        _core.apply_size(split, self._size)
        self.ns = split
        _core.add(split, self.grow, fill=True)
        return False

    @property
    def count(self):
        return len(self._items)

    def set_position(self, divider_index, points):
        """Move a divider (0 = between the first two panes) to `points` from the start edge."""
        if isinstance(divider_index, bool) or not isinstance(divider_index, int) or not 0 <= divider_index < self.count - 1:
            raise ValueError(f"divider {divider_index!r} does not exist")
        self.ns.setPosition_ofDividerAtIndex_(float(points), divider_index)

    def position(self, divider_index):
        """Size of the panes before a divider in points (where the divider sits)."""
        if isinstance(divider_index, bool) or not isinstance(divider_index, int) or not 0 <= divider_index < self.count - 1:
            raise ValueError(f"divider {divider_index!r} does not exist")
        total = 0.0
        for view in list(self.ns.arrangedSubviews())[: divider_index + 1]:
            size = view.frame().size
            total += float(size.width if self.orientation == "horizontal" else size.height)
        return total + divider_index * float(self.ns.dividerThickness())
