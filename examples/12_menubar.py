"""A menu-bar app: no Dock icon, a clock in the menu bar, a menu with a few actions.

Quit it from its own menu. (Run from a terminal it shows up as a Python process.)
"""
import datetime as dt

from baremacgui import App, MenuItem, MenuSeparator, StatusItem, Timer, show_info


def clock_text(now):
    """'14:05' for the menu bar."""
    return now.strftime("%H:%M")


app = App("Clock", background=True)

with StatusItem(clock_text(dt.datetime.now()), symbol="clock") as item:
    greet = MenuItem("Say hello")
    seconds = MenuItem("Show seconds", checkable=True)
    MenuSeparator()
    quit_item = MenuItem("Quit", shortcut="Cmd+Q")


def tick():
    now = dt.datetime.now()
    item.title = now.strftime("%H:%M:%S") if seconds.checked else clock_text(now)


greet.on_click(lambda: show_info("Hello from the menu bar.", "Clock"))
quit_item.on_click(app.quit)
ticker = Timer(1.0, tick)

if __name__ == "__main__":
    app.run()
