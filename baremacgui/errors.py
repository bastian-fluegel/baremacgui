"""Exception types raised by BareMacGUI."""
from __future__ import annotations


class BareMacGUIError(Exception):
    """Base class for all BareMacGUI errors."""


class PlatformError(BareMacGUIError, RuntimeError):
    """Raised when a macOS-only feature is used on another platform or without PyObjC."""


class LayoutError(BareMacGUIError, ValueError):
    """Raised for invalid layout configuration (bad option values, misuse of containers)."""
