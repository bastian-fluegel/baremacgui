"""The install creator that ships with BareMacGUI: a wizard that turns a script into an app, ZIP or disk image.

It is built with BareMacGUI itself (baremacgui/_creator.py). From the terminal: python -m baremacgui build --help
"""
from baremacgui import App
from baremacgui._creator import build

app = App("Install Creator")
wizard = build(app)

if __name__ == "__main__":
    app.run()
