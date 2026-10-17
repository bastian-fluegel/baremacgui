"""baremacgui: a thin Python layer for native macOS windows on AppKit.

Same API shape as BareWinGUI: windows and controls from short with-blocks,
handlers without arguments, background work handed back with App.invoke.
Importing this package works on any OS; building windows needs macOS and PyObjC.
"""
from ._app import App
from ._collections import IconGrid, Tree
from ._containers import GroupBox, Tab, TabControl
from ._controls import Button, CheckBox, ComboBox, Label, SpinBox, TextBox
from ._dialogs import ask_yes_no, choose_folder, open_file, save_file, show_error, show_info, show_warning
from ._layout import HBox, Spacer, VBox, Window
from ._overlays import Popover, Sheet
from ._sidebar import Page, Sidebar
from ._table import ListBox, Table
from ._toolbar import Toolbar
from ._widgets import Custom, DropDown, Image, ProgressBar, RadioGroup, SearchField, SegmentedControl, Separator, Slider

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
    "DropDown",
    "Button",
    "CheckBox",
    "RadioGroup",
    "SpinBox",
    "Slider",
    "ProgressBar",
    "Image",
    "Separator",
    "SearchField",
    "SegmentedControl",
    "Toolbar",
    "IconGrid",
    "Tree",
    "Custom",
    "Sheet",
    "Popover",
    "Sidebar",
    "Page",
    "ListBox",
    "Table",
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
