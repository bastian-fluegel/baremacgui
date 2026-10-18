"""Pure logic of the install creator (specs, icons, import detection, terminal front end): runs everywhere."""
import json
import sys

import pytest

from baremacgui import _cli, _installer as inst


@pytest.fixture
def script(tmp_path):
    path = tmp_path / "my_tool.py"
    path.write_text("import os\nimport certifi\nfrom requests.auth import HTTPBasicAuth\nfrom baremacgui import App\n")
    return path


def test_check_spec_fills_defaults(script, tmp_path):
    spec = inst.check_spec(inst.BuildSpec(script=str(script), dest=str(tmp_path)))
    assert spec.name == "My Tool" and spec.identifier == "local.baremacgui.my-tool" and spec.outputs == ["dmg"]
    assert spec.script == str(script) and spec.standalone is True


def test_check_spec_rejects_bad_input(script, tmp_path):
    def bad(**changes):
        with pytest.raises(ValueError):
            inst.check_spec(inst.BuildSpec(script=str(script), **changes))

    with pytest.raises(ValueError):
        inst.check_spec(inst.BuildSpec(script=str(tmp_path / "missing.py")))
    (tmp_path / "notes.txt").write_text("x")
    with pytest.raises(ValueError):
        inst.check_spec(inst.BuildSpec(script=str(tmp_path / "notes.txt")))
    bad(name="a/b")
    bad(identifier="nodots")
    bad(version="1 0")
    bad(icon=str(tmp_path / "none.png"))
    bad(include=[str(tmp_path / "nothing")])
    bad(packages=["bad name"])
    bad(hidden_imports=["x;y"])
    bad(outputs=[])
    bad(outputs=["exe"])


def test_spec_file_round_trip_and_relative_paths(script, tmp_path):
    spec = inst.BuildSpec(script="my_tool.py", name="Tool", outputs=["zip", "dmg"], dest="out", include=["data"])
    target = tmp_path / ("tool" + inst.SPEC_SUFFIX)
    inst.save_spec(spec, target)
    loaded = inst.load_spec(target)
    assert loaded.script == str(tmp_path / "my_tool.py") and loaded.dest == str(tmp_path / "out")
    assert loaded.include == [str(tmp_path / "data")] and loaded.outputs == ["zip", "dmg"]
    target.write_text(json.dumps({"script": "x.py", "colour": "red"}))
    with pytest.raises(ValueError):
        inst.load_spec(target)
    target.write_text("[1]")
    with pytest.raises(ValueError):
        inst.load_spec(target)


def test_detect_imports_skips_stdlib_and_baremacgui():
    source = "import os, sys\nimport numpy as np\nfrom PIL import Image\nfrom . import sibling\nfrom baremacgui import App\n"
    assert inst.detect_imports(source) == ["PIL", "numpy"]
    assert inst.detect_imports("print(1)") == []
    assert inst.is_installed("json") and not inst.is_installed("surely_not_a_module_xyz")


def test_system_and_local_icons(tmp_path):
    (tmp_path / "FolderIcon.icns").write_bytes(b"x")
    (tmp_path / "GenericApplicationIcon.icns").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("x")
    names = [n for n, _ in inst.system_icons(str(tmp_path))]
    assert names == ["FolderIcon", "GenericApplicationIcon"]
    assert inst.system_icons(str(tmp_path / "nope")) == []
    assert inst.find_system_icon("foldericon", str(tmp_path)).endswith("FolderIcon.icns")
    assert inst.find_system_icon("Folder", str(tmp_path)).endswith("FolderIcon.icns")
    try:
        inst.find_system_icon("Fodler", str(tmp_path))
    except ValueError as error:
        assert "no system icon called 'Fodler'" in str(error) and "FolderIcon" in str(error)
    else:
        raise AssertionError("expected ValueError")
    sub = tmp_path / "pack" / "one" / "two" / "three"
    sub.mkdir(parents=True)
    (tmp_path / "pack" / "a.png").write_bytes(b"x")
    (tmp_path / "pack" / "one" / "two" / "b.icns").write_bytes(b"x")
    (sub / "too_deep.png").write_bytes(b"x")
    found = [n for n, _ in inst.local_icons(str(tmp_path / "pack"))]
    assert found == ["a", "b"]


def test_output_names_and_commands(script):
    spec = inst.check_spec(inst.BuildSpec(script=str(script), name="Tool", version="2.1"))
    assert inst.output_name(spec, "app") == "Tool.app"
    assert inst.output_name(spec, "dmg") == "Tool-2.1.dmg" and inst.output_name(spec, "zip") == "Tool-2.1.zip"
    assert inst.zip_command("/a/T.app", "/o/T.zip")[:5] == ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent"]
    command = inst.dmg_command("Tool", "/stage", "/o/T.dmg")
    assert command[:2] == ["hdiutil", "create"] and command[command.index("-volname") + 1] == "Tool"
    assert command[-1] == "/o/T.dmg"


@pytest.mark.skipif(sys.platform == "darwin", reason="the error is for other systems")
def test_create_installer_needs_macos(script, tmp_path):
    with pytest.raises(RuntimeError):
        inst.create_installer(inst.BuildSpec(script=str(script), dest=str(tmp_path)))


def test_terminal_builds_the_right_spec(script, tmp_path):
    args = _cli._parser().parse_args(["build", str(script), "--dmg", "--zip", "--package", "certifi",
                                      "--hidden-import", "pkg.mod", "--include", str(tmp_path), "--name", "T",
                                      "--dest", str(tmp_path)])
    spec = _cli._spec_from_args(args)
    assert spec.outputs == ["dmg", "zip"] and spec.standalone and spec.packages == ["certifi"]
    assert spec.hidden_imports == ["pkg.mod"] and spec.name == "T"
    args = _cli._parser().parse_args(["build", str(script), "--standalone"])
    assert _cli._spec_from_args(args).outputs == ["app"]
    args = _cli._parser().parse_args(["build", str(script)])
    plain = _cli._spec_from_args(args)
    assert plain.standalone is False and plain.outputs == ["app"]


def test_terminal_spec_file_save_and_errors(script, tmp_path, capsys):
    target = tmp_path / "saved.bmc.json"
    assert _cli.main(["build", str(script), "--dest", str(tmp_path), "--save-spec", str(target), "--name", "Saved"]) == 0
    assert inst.load_spec(target).name == "Saved"
    assert _cli.main(["build", "--spec", str(tmp_path / "missing.json")]) == 1
    assert _cli.main(["build"]) == 1
    assert _cli.main(["build", str(script), "--system-icon", "NoSuchIconAnywhere"]) == 1
    assert "no system icon" in capsys.readouterr().err
    assert _cli.main(["icons", "--folder", str(tmp_path)]) == 0
