"""Event helper: ordered handler lists with the same shape as BareWinGUI.

Controls expose events such as ``on_click``. Handlers are called without
arguments (read the state from the controls)::

    ok = Button("OK", on_click=save)      # as a constructor option
    ok.on_click(save)                     # register another handler
    @ok.on_click                          # as a decorator
    def save(): ...
    ok.on_click = save                    # assignment replaces all handlers
    ok.on_click = None                    # removes all handlers

Pure Python: no AppKit import.
"""
from __future__ import annotations

import traceback


class Event:
    """An ordered list of handlers."""

    __slots__ = ("_handlers",)

    def __init__(self):
        self._handlers = []

    def __call__(self, handler):
        """Register `handler` (also usable as a decorator) and return it."""
        return self.connect(handler)

    def connect(self, handler):
        if not callable(handler):
            raise TypeError(f"an event handler must be callable, got {handler!r}")
        self._handlers.append(handler)
        return handler

    def disconnect(self, handler):
        self._handlers.remove(handler)

    def clear(self):
        self._handlers.clear()

    def emit(self):
        """Call all handlers in registration order.

        An exception in one handler is printed and does not stop the others.
        The app's `on_error` hook (if set) receives it instead of the terminal.
        """
        for handler in list(self._handlers):
            try:
                handler()
            except Exception as exc:  # noqa: BLE001 - a handler must not take the app down
                report_error(exc)

    def __len__(self):
        return len(self._handlers)

    def __bool__(self):
        return True  # an Event is always truthy, even without handlers

    def __repr__(self):
        return f"Event({len(self._handlers)} handlers)"


class event:
    """Descriptor that gives every instance its own Event."""

    def __set_name__(self, owner, name):
        self._key = "_event_" + name
        self.name = name

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        found = obj.__dict__.get(self._key)
        if found is None:
            found = obj.__dict__[self._key] = Event()
        return found

    def __set__(self, obj, value):
        current = self.__get__(obj)
        current.clear()
        if value is not None:
            current.connect(value)


_error_hook = [None]


def set_error_hook(function):
    """Install (or remove with None) the function that receives handler exceptions."""
    _error_hook[0] = function


def report_error(exc):
    """Give an exception to the app's on_error hook, or print it."""
    hook = _error_hook[0]
    if hook is not None:
        try:
            hook(exc)
            return
        except Exception:  # noqa: BLE001 - a broken hook must not hide the original error
            traceback.print_exc()
    traceback.print_exception(type(exc), exc, exc.__traceback__)


def connect_options(obj, options):
    """Register the `on_*=` constructor options of `obj`. Unknown names raise TypeError."""
    for name, handler in options.items():
        if not isinstance(getattr(type(obj), name, None), event):
            raise TypeError(f"{type(obj).__name__} has no event {name!r}")
        if handler is None:
            continue
        if isinstance(handler, (list, tuple)):
            for single in handler:
                getattr(obj, name).connect(single)
        else:
            getattr(obj, name).connect(handler)


def split_options(options):
    """Take the `on_*` entries out of a keyword dict and return them."""
    return {key: options.pop(key) for key in [k for k in options if k.startswith("on_")]}
