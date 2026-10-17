"""Off macOS, building anything native must fail with a clear message."""
import sys

import pytest

import baremacgui

pytestmark = pytest.mark.skipif(sys.platform == "darwin", reason="only meaningful off macOS")


def test_app_needs_macos():
    with pytest.raises(RuntimeError, match="macOS"):
        baremacgui.App()


def test_window_needs_macos():
    with pytest.raises(RuntimeError, match="macOS"):
        baremacgui.Window("x")


def test_control_outside_window_is_not_a_crash():
    with pytest.raises(RuntimeError):
        baremacgui.Label("x")
