"""A settings window: tabs, group box, combo box, check boxes, spin box, button row."""
from baremacgui import (
    App, Button, CheckBox, ComboBox, GroupBox, HBox, Label, SpinBox, Spacer, Tab, TabControl, VBox,
    Window, show_info,
)

app = App("Settings")

with Window("Settings", size=(460, 380)) as win:
    with VBox(padding=16, gap=12):
        with TabControl(grow=1):
            with Tab("General"):
                with VBox(gap=12):
                    with GroupBox("Appearance"):
                        with VBox(padding=4, gap=8):
                            with HBox(gap=8):
                                Label("Theme")
                                theme = ComboBox(["System", "Light", "Dark"], selected=0, editable=False)
                            mono_icons = CheckBox("Use monochrome icons")
                    with HBox(gap=8):
                        Label("Recent items")
                        recent = SpinBox(10, minimum=0, maximum=50)
            with Tab("Advanced"):
                with VBox(gap=10):
                    logging = CheckBox("Enable logging", checked=True)
                    with HBox(gap=8):
                        Label("Keep logs for (days)")
                        days = SpinBox(7, minimum=1, maximum=90)
        with HBox(gap=8):
            Spacer()
            cancel = Button("Cancel")
            save = Button("Save", default=True)


def on_save():
    show_info(
        f"Theme: {theme.text}\nMonochrome icons: {mono_icons.checked}\nRecent items: {recent.value}\n"
        f"Logging: {logging.checked}\nKeep logs: {days.value} days",
        "Settings",
        parent=win,
    )


logging.on_change(lambda: setattr(days, "enabled", logging.checked))
save.on_click(on_save)
cancel.on_click(win.close)
app.run()
