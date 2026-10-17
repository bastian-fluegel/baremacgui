"""The package must import everywhere, without loading AppKit."""
import subprocess
import sys

import baremacgui


def test_public_names_exist():
    for name in baremacgui.__all__:
        assert hasattr(baremacgui, name), name


def test_version_is_set():
    assert baremacgui.__version__


def test_import_does_not_load_appkit():
    code = (
        "import sys, baremacgui\n"
        "assert 'AppKit' not in sys.modules, 'AppKit was imported at import time'\n"
        "assert 'objc' not in sys.modules, 'objc was imported at import time'\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
