"""The .app builder is pure standard library, so it is tested everywhere; running a built bundle is macOS only."""
import os
import plistlib
import struct
import subprocess
import sys
import zlib

import pytest

from baremacgui import _bundle as b


def png_file(path, size=4):
    """A minimal valid PNG (solid red), written without any imaging library."""
    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    row = b"\x00" + b"\xff\x00\x00" * size
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b""))
    path.write_bytes(data)
    return str(path)


def test_names_and_identifiers():
    assert b.check_app_name("  My Notes ") == "My Notes"
    for bad in ("", "a/b", "x:y", ".hidden", "n" * 65):
        with pytest.raises(ValueError):
            b.check_app_name(bad)
    assert b.default_identifier("My Notes!") == "local.baremacgui.my-notes"
    assert b.check_identifier("com.example.notes") == "com.example.notes"
    for bad in ("notes", "com..x", "com.exa mple.x", 5):
        with pytest.raises(ValueError):
            b.check_identifier(bad)


def test_info_plist_and_launcher_text():
    info = b.info_plist("Notes", "com.example.notes", "2.1", "AppIcon.icns", background=True)
    assert info["CFBundleName"] == "Notes" and info["CFBundleIconFile"] == "AppIcon.icns" and info["LSUIElement"] is True
    assert "LSUIElement" not in b.info_plist("Notes", "com.example.notes")
    text = b.launcher_script("/opt/my py/bin/python", "my script.py", "AppIcon.icns", "O'Neil")
    assert text.startswith("#!/bin/sh\n")
    assert "exec '/opt/my py/bin/python' 'my script.py' \"$@\"" in text
    assert "BAREMACGUI_APP_NAME='O'\"'\"'Neil'" in text and "BAREMACGUI_ICON" in text


def test_build_app_structure(tmp_path):
    script = tmp_path / "my_tool.py"
    script.write_text("print('hi')\n")
    data = tmp_path / "data"
    data.mkdir()
    (data / "a.txt").write_text("x")
    out = tmp_path / "out"
    out.mkdir()
    app = b.build_app(script, dest=out, include=[data], version="3")
    assert app.endswith("My Tool.app")
    with open(os.path.join(app, "Contents", "Info.plist"), "rb") as handle:
        info = plistlib.load(handle)
    assert info["CFBundleName"] == "My Tool" and info["CFBundleVersion"] == "3"
    assert info["CFBundleIdentifier"] == "local.baremacgui.my-tool"
    launcher = os.path.join(app, "Contents", "MacOS", info["CFBundleExecutable"])
    assert os.access(launcher, os.X_OK)
    assert os.path.isfile(os.path.join(app, "Contents", "Resources", "my_tool.py"))
    assert os.path.isfile(os.path.join(app, "Contents", "Resources", "data", "a.txt"))
    again = b.build_app(script, dest=out)  # replaces the old bundle
    assert again == app


def test_build_app_rejects_bad_input(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("")
    with pytest.raises(FileNotFoundError):
        b.build_app(tmp_path / "missing.py")
    with pytest.raises(FileNotFoundError):
        b.build_app(script, dest=tmp_path, icon=tmp_path / "none.icns")
    (tmp_path / "icon.gif").write_bytes(b"x")
    with pytest.raises(ValueError):
        b.build_app(script, dest=tmp_path, icon=tmp_path / "icon.gif")
    with pytest.raises(FileNotFoundError):
        b.build_app(script, dest=tmp_path, include=[tmp_path / "nothing"])
    with pytest.raises(ValueError):
        b.build_app(script, dest=tmp_path, identifier="bad")


def test_command_line(tmp_path, capsys):
    script = tmp_path / "tool.py"
    script.write_text("")
    assert b.main(["build", str(script), "--dest", str(tmp_path), "--name", "Tool X", "--background"]) == 0
    assert capsys.readouterr().out.strip().endswith("Tool X.app")
    assert b.main(["build", str(tmp_path / "nope.py")]) == 1


@pytest.mark.skipif(sys.platform != "darwin", reason="runs the launcher with PyObjC")
def test_built_app_runs_and_hands_over_name_and_icon(tmp_path):
    script = tmp_path / "probe.py"
    script.write_text(
        "import os, sys\n"
        "from baremacgui import App\n"
        "app = App(menu=False)\n"
        "size = app.ns.applicationIconImage().size()\n"
        "open(sys.argv[1], 'w').write(f'{app.name}|{os.getcwd()}|{int(size.width)}')\n"
    )
    app = b.build_app(script, name="Probe Tool", dest=tmp_path, icon=png_file(tmp_path / "i.png"))
    marker = tmp_path / "marker.txt"
    subprocess.run([os.path.join(app, "Contents", "MacOS", "launcher"), str(marker)], check=True, timeout=60,
                   env={**os.environ, "PYTHONPATH": os.pathsep.join(p for p in sys.path if p)})
    name, cwd, width = marker.read_text().split("|")
    assert name == "Probe Tool"
    assert os.path.realpath(cwd) == os.path.realpath(os.path.join(app, "Contents", "Resources"))
    assert int(width) > 0


@pytest.mark.skipif(sys.platform == "darwin", reason="the error is for other systems")
def test_png_icon_needs_macos(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("")
    with pytest.raises(RuntimeError):  # PlatformError
        b.build_app(script, dest=tmp_path, icon=png_file(tmp_path / "i.png"))


def test_default_icon_png_is_a_valid_rounded_square(tmp_path):
    target = tmp_path / "icon.png"
    b.default_icon_png(str(target), size=256)
    data = target.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height, depth, color = struct.unpack(">IIBB", data[16:26])
    assert (width, height, depth, color) == (256, 256, 8, 6)
    start = data.index(b"IDAT") + 4
    raw = zlib.decompress(data[start:data.index(b"IEND") - 8])
    stride = 256 * 4 + 1

    def pixel(x, y):
        offset = y * stride + 1 + x * 4
        return tuple(raw[offset:offset + 4])

    assert pixel(0, 0)[3] == 0  # the corner is transparent
    assert pixel(128, 40)[3] == 255 and pixel(128, 90) != pixel(128, 40)  # body, then the window
