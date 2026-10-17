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


def test_all_names_exist_and_version_is_semver_like():
    import re

    assert re.fullmatch(r"\d+\.\d+\.\d+((a|b|rc)\d+|\.dev\d+)?", baremacgui.__version__)
    for name in baremacgui.__all__:
        assert hasattr(baremacgui, name), name
    assert len(set(baremacgui.__all__)) == len(baremacgui.__all__)


def test_changelog_mentions_current_version():
    import pathlib

    text = (pathlib.Path(__file__).parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{baremacgui.__version__}]" in text


def test_reference_is_up_to_date():
    import pathlib

    tool = pathlib.Path(__file__).parent.parent / "tools" / "make_reference.py"
    result = subprocess.run([sys.executable, str(tool), "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
