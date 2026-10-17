"""A System-Settings-style window: a sidebar of pages on the left, the chosen page on the right."""
from baremacgui import (
    App, CheckBox, DropDown, Label, Page, RadioGroup, Sidebar, Slider, Spacer, VBox, Window,
)

app = App("Settings")

with Window("Settings", size=(720, 480), style="sidebar"):
    with Sidebar(selected=0, width=200) as sidebar:
        with Page("General", symbol="gearshape"):
            with VBox(padding=24, gap=12):
                Label("General")
                CheckBox("Open at login", checked=True)
                CheckBox("Check for updates automatically")
                Label("Default browser")
                DropDown(["Safari", "Firefox", "Chrome"])
        with Page("Appearance", symbol="paintbrush"):
            with VBox(padding=24, gap=12):
                Label("Appearance")
                RadioGroup(["Light", "Dark", "Automatic"], selected=2)
                Label("Text size")
                Slider(50, width=200)
        with Page("Notifications", symbol="bell"):
            with VBox(padding=24, gap=12):
                Label("Notifications")
                CheckBox("Allow notifications", checked=True)
                CheckBox("Play sound")
        with Page("About", symbol="info.circle"):
            with VBox(padding=24, gap=12):
                Label("baremacgui")
                Label("A thin Python layer for native macOS windows.")

sidebar.on_change(lambda: print("page:", sidebar.text))
app.run()
