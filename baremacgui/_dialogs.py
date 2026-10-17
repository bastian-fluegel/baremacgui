"""Message boxes and file dialogs.

All dialogs are application-modal and block until closed. The `parent`
argument is accepted for API parity with BareWinGUI but not used yet: there
are no window-modal sheets in this version.
"""
from __future__ import annotations

from ._bridge import AK, ensure_app
from ._options import normalize_filetypes

_MODAL_OK = 1  # NSModalResponseOK


def _alert(style_name, text, title, buttons):
    ak = AK()
    ensure_app()
    alert = ak.NSAlert.alloc().init()
    if title:
        alert.setMessageText_(str(title))
        alert.setInformativeText_(str(text))
    else:
        alert.setMessageText_(str(text))
    alert.setAlertStyle_(getattr(ak, style_name))
    for button in buttons:
        alert.addButtonWithTitle_(button)
    return int(alert.runModal())


def show_info(text, title="", parent=None):
    _alert("NSAlertStyleInformational", text, title, ["OK"])


def show_warning(text, title="", parent=None):
    _alert("NSAlertStyleWarning", text, title, ["OK"])


def show_error(text, title="", parent=None):
    _alert("NSAlertStyleCritical", text, title, ["OK"])


def ask_yes_no(text, title="", parent=None):
    """Return True for Yes, False for No."""
    first = int(AK().NSAlertFirstButtonReturn)
    return _alert("NSAlertStyleWarning", text, title, ["Yes", "No"]) == first


def _paths(panel):
    return [str(url.path()) for url in panel.URLs()]


def open_file(title="", filetypes=None, multiple=False):
    """Choose existing file(s). Returns a path (a list if multiple=True) or None."""
    ak = AK()
    ensure_app()
    panel = ak.NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(True)
    panel.setCanChooseDirectories_(False)
    panel.setAllowsMultipleSelection_(bool(multiple))
    if title:
        panel.setMessage_(str(title))
    extensions = normalize_filetypes(filetypes)
    if extensions:
        panel.setAllowedFileTypes_(extensions)  # deprecated by Apple, but still works
    if int(panel.runModal()) != _MODAL_OK:
        return None
    paths = _paths(panel)
    return paths if multiple else paths[0]


def save_file(title="", default_name="", filetypes=None):
    """Choose where to save. Returns a path or None."""
    ak = AK()
    ensure_app()
    panel = ak.NSSavePanel.savePanel()
    if title:
        panel.setMessage_(str(title))
    if default_name:
        panel.setNameFieldStringValue_(str(default_name))
    extensions = normalize_filetypes(filetypes)
    if extensions:
        panel.setAllowedFileTypes_(extensions)
    if int(panel.runModal()) != _MODAL_OK:
        return None
    return str(panel.URL().path())


def choose_folder(title=""):
    """Choose a folder. Returns a path or None."""
    ak = AK()
    ensure_app()
    panel = ak.NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)
    if title:
        panel.setMessage_(str(title))
    if int(panel.runModal()) != _MODAL_OK:
        return None
    return _paths(panel)[0]
