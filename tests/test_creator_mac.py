"""The install creator window: built hidden, driven by calling its handlers (no clicks, no event loop)."""
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="needs macOS and PyObjC")


@pytest.fixture
def make_wizard(tmp_path):
    from baremacgui import _core
    from baremacgui._creator import build

    _core._stack.clear()
    script = tmp_path / "my_tool.py"
    script.write_text("import os\nimport certifi\nfrom baremacgui import App\n")

    def make(path=None):
        return build(path=path if path is not None else str(script), window_args={"visible": False})

    yield make
    _core._stack.clear()


def test_wizard_starts_on_the_first_step_with_a_guessed_name(make_wizard):
    wizard = make_wizard()
    assert wizard.state.step == 0 and wizard.title.text == "Your app"
    assert wizard.name.text == "My Tool" and wizard.nxt.enabled and not wizard.back.enabled
    assert [page.visible for page in wizard.pages] == [True, False, False, False]


def test_wizard_blocks_next_until_the_script_exists(make_wizard):
    wizard = make_wizard(path="")
    assert not wizard.nxt.enabled and "script" in wizard.problem.text.lower()
    wizard.script.text = "/nonexistent/x.py"
    wizard.script_changed()
    assert not wizard.nxt.enabled and wizard.problem.text


def test_wizard_walks_through_the_steps(make_wizard):
    wizard = make_wizard()
    wizard.go_next()
    assert wizard.state.step == 1 and wizard.back.enabled
    wizard.go_next()
    assert wizard.state.step == 2 and "certifi" in wizard.found.text
    wizard.go_next()
    assert wizard.state.step == 3 and wizard.nxt.text == "Build"
    assert [page.visible for page in wizard.pages] == [False, False, False, True]
    wizard.go_back()
    assert wizard.state.step == 2 and wizard.nxt.text == "Next"


def test_wizard_system_icons_show_in_the_list_and_preview(make_wizard):
    from baremacgui import _installer

    wizard = make_wizard()
    assert wizard.current_icon() == "" and not wizard.icon_list.visible
    wizard.icon_source.index = 3
    wizard.icon_source_changed()
    icons = _installer.system_icons()
    assert icons and wizard.icon_list.visible and wizard.icon_list.items == [n for n, _ in icons]
    wizard.icon_list.index = 0
    wizard.show_icon()
    assert wizard.current_icon() == icons[0][1] and wizard.preview.path == icons[0][1]
    wizard.icon_filter.text = icons[0][0][:4]
    wizard.filter_icons()
    assert icons[0][0] in wizard.icon_list.items
    wizard.icon_source.index = 0
    wizard.icon_source_changed()
    assert wizard.current_icon() == "" and wizard.preview.path is None


def test_wizard_spec_follows_the_controls(make_wizard, tmp_path):
    wizard = make_wizard()
    wizard.version.text = "2.0"
    wizard.background.checked = True
    wizard.make_zip.checked = True
    wizard.packages.text = "certifi\n\n requests "
    wizard.include_list.items = [str(tmp_path)]
    spec = wizard.spec()
    assert spec.version == "2.0" and spec.background and spec.outputs == ["dmg", "zip"]
    assert spec.packages == ["certifi", "requests"] and spec.include == [str(tmp_path)]
    wizard.make_dmg.checked = wizard.make_zip.checked = wizard.make_app.checked = False
    wizard.state.step = 3
    wizard.refresh()
    assert not wizard.nxt.enabled and "output" in wizard.problem.text


def test_wizard_loads_a_build_file(make_wizard, tmp_path):
    from baremacgui import _installer

    spec = _installer.BuildSpec(script=str(tmp_path / "my_tool.py"), name="Saved Name", outputs=["zip"])
    target = tmp_path / ("a" + _installer.SPEC_SUFFIX)
    _installer.save_spec(spec, target)
    wizard = make_wizard(path=str(target))
    assert wizard.name.text == "Saved Name" and wizard.make_zip.checked and not wizard.make_dmg.checked


def test_image_path_can_change_and_box_can_hide(tmp_path):
    from baremacgui import Image, VBox, Window, _core
    from baremacgui._installer import system_icons

    _core._stack.clear()
    with Window("t", visible=False):
        with VBox() as outer:
            with VBox() as inner:
                image = Image(symbol="doc", width=32, height=32)
    icon = system_icons()[0][1]
    image.path = icon
    assert image.path == icon
    image.path = None
    assert image.path is None
    with pytest.raises(FileNotFoundError):
        image.path = "/nonexistent/x.png"
    inner.visible = False
    assert not inner.visible and outer.visible
    inner.visible = True
    assert inner.visible
    _core._stack.clear()
