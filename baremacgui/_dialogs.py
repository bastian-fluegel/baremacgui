"""Message boxes and file dialogs.

Without `parent` a dialog is application-modal and blocks until closed.

With `parent=window` it becomes a sheet on that window and blocks only it.
Two ways to get the answer:
  - give `then=function`: the dialog returns at once and later calls
    function(result) (the dependable way);
  - leave `then` out: the call waits for the answer and returns it, like
    the application-modal version (runs a nested modal loop).
"""
from __future__ import annotations

from ._bridge import AK, ensure_app, safe_call
from ._options import normalize_filetypes

_MODAL_OK = 1  # NSModalResponseOK


def _parent_window(parent, then):
    """The NSWindow of `parent` (None for no parent); `then` needs a parent."""
    if parent is None:
        if then is not None:
            raise ValueError("then= needs parent=: only sheets answer later")
        return None
    window = getattr(parent, "ns", None)
    if window is None or not hasattr(window, "beginSheet_completionHandler_"):
        raise TypeError("parent must be a Window")
    if then is not None and not callable(then):
        raise TypeError("then must be callable")
    return window


def _run_sheet(window, modal_window, begin, then, convert):
    """Run a sheet on `window`. begin(handler) starts it, handler gets the response code."""
    app = AK().NSApplication.sharedApplication()
    answer = []

    def handler(code):
        value = convert(int(code))
        if then is not None:
            safe_call(then, value)
        else:
            answer.append(value)
            app.stopModalWithCode_(int(code))

    begin(handler)
    if then is not None:
        return None
    app.runModalForWindow_(modal_window)
    return answer[0] if answer else None


def _alert(style_name, text, title, buttons, parent=None, then=None, convert=lambda code: code):
    ak = AK()
    ensure_app()
    window = _parent_window(parent, then)
    alert = ak.NSAlert.alloc().init()
    if title:
        alert.setMessageText_(str(title))
        alert.setInformativeText_(str(text))
    else:
        alert.setMessageText_(str(text))
    alert.setAlertStyle_(getattr(ak, style_name))
    for button in buttons:
        alert.addButtonWithTitle_(button)
    if window is None:
        return convert(int(alert.runModal()))
    return _run_sheet(
        window, alert.window(),
        lambda handler: alert.beginSheetModalForWindow_completionHandler_(window, handler),
        then, convert,
    )


def show_info(text, title="", parent=None, then=None):
    _alert("NSAlertStyleInformational", text, title, ["OK"], parent, then, lambda code: None)


def show_warning(text, title="", parent=None, then=None):
    _alert("NSAlertStyleWarning", text, title, ["OK"], parent, then, lambda code: None)


def show_error(text, title="", parent=None, then=None):
    _alert("NSAlertStyleCritical", text, title, ["OK"], parent, then, lambda code: None)


def ask_yes_no(text, title="", parent=None, then=None):
    """Return True for Yes, False for No (with then=..., it is passed to then instead)."""
    first = int(AK().NSAlertFirstButtonReturn)
    return _alert("NSAlertStyleWarning", text, title, ["Yes", "No"], parent, then, lambda code: code == first)


def _paths(panel):
    return [str(url.path()) for url in panel.URLs()]


def _run_panel(panel, parent, then, convert):
    """Run a file panel modally, or as a sheet on `parent`; convert(panel, ok) builds the result."""
    window = _parent_window(parent, then)
    if window is None:
        return convert(panel, int(panel.runModal()) == _MODAL_OK)
    return _run_sheet(
        window, panel,
        lambda handler: panel.beginSheetModalForWindow_completionHandler_(window, handler),
        then, lambda code: convert(panel, code == _MODAL_OK),
    )


def open_file(title="", filetypes=None, multiple=False, parent=None, then=None):
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
    def result(panel, ok):
        if not ok:
            return None
        paths = _paths(panel)
        return paths if multiple else paths[0]

    return _run_panel(panel, parent, then, result)


def save_file(title="", default_name="", filetypes=None, parent=None, then=None):
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
    return _run_panel(panel, parent, then, lambda panel, ok: str(panel.URL().path()) if ok else None)


def choose_folder(title="", parent=None, then=None):
    """Choose a folder. Returns a path or None."""
    ak = AK()
    ensure_app()
    panel = ak.NSOpenPanel.openPanel()
    panel.setCanChooseFiles_(False)
    panel.setCanChooseDirectories_(True)
    panel.setAllowsMultipleSelection_(False)
    if title:
        panel.setMessage_(str(title))
    return _run_panel(panel, parent, then, lambda panel, ok: _paths(panel)[0] if ok else None)
