"""baremacgui: a thin Python layer for native macOS windows on AppKit.

Same API shape as BareWinGUI: windows and controls from short with-blocks,
handlers without arguments, background work handed back with App.invoke.
Importing this package works on any OS; building windows needs macOS and PyObjC.
"""
from ._app import App
from ._containers import GroupBox, Tab, TabControl
from ._controls import Button, CheckBox, ComboBox, Label, SpinBox, TextBox
from ._dialogs import ask_yes_no, choose_folder, open_file, save_file, show_error, show_info, show_warning
from ._layout import HBox, Spacer, VBox, Window

__version__ = "0.0.1.dev0"

__all__ = [
    "App",
    "Window",
    "VBox",
    "HBox",
    "Spacer",
    "Label",
    "TextBox",
    "ComboBox",
    "Button",
    "CheckBox",
    "SpinBox",
    "GroupBox",
    "TabControl",
    "Tab",
    "show_info",
    "show_warning",
    "show_error",
    "ask_yes_no",
    "open_file",
    "save_file",
    "choose_folder",
]
