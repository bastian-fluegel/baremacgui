"""BareMacGUI (import name: baremacgui): a thin Python layer for native macOS windows on AppKit.

The API shape follows BareWinGUI, the author's Windows library: windows and controls from short with-blocks,
handlers without arguments, background work handed back with App.invoke.
Importing this package works on any OS; building windows needs macOS and PyObjC.
"""
from ._app import App
from .errors import BareMacGUIError, LayoutError, PlatformError
from ._bundle import build_app
from ._collections import IconGrid, Tree
from ._containers import GroupBox, Tab, TabControl
from ._controls import Button, CheckBox, ComboBox, Label, SpinBox, TextBox
from ._drop import DropZone
from ._events import Event
from ._dialogs import ask_ok_cancel, ask_yes_no, pick_folder, input_box, open_file, save_file, show_error, show_info, show_warning
from ._menus import ContextMenu, Menu, MenuBar, MenuItem, MenuSeparator
from ._panels import FontChoice, choose_color, choose_font
from ._pickers import DatePicker, TimePicker
from ._timer import Timer
from ._layout import HBox, Spacer, VBox, Window
from ._overlays import Popover, Sheet
from ._sidebar import Page, Sidebar
from ._settings import Settings
from ._system import ColorWell, Clipboard, Switch, clipboard
from ._split import SplitView
from ._statusitem import StatusItem
from ._table import ListBox, Table
from ._toolbar import Toolbar
from ._widgets import Custom, DropDown, Image, ProgressBar, RadioGroup, SearchField, SegmentedControl, Separator, Slider

__version__ = "0.1.0a1"

__all__ = [
    "BareMacGUIError",
    "PlatformError",
    "LayoutError",
    "Event",
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
    "SplitView",
    "GroupBox",
    "TabControl",
    "Tab",
    "MenuBar",
    "Menu",
    "MenuItem",
    "MenuSeparator",
    "ContextMenu",
    "StatusItem",
    "Timer",
    "Switch",
    "DropZone",
    "ColorWell",
    "Clipboard",
    "clipboard",
    "Settings",
    "build_app",
    "DatePicker",
    "TimePicker",
    "input_box",
    "ask_ok_cancel",
    "show_info",
    "show_warning",
    "show_error",
    "ask_yes_no",
    "open_file",
    "save_file",
    "pick_folder",
    "choose_color",
    "choose_font",
    "FontChoice",
]
