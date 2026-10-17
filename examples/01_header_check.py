"""Security-header checker: a small real tool built with baremacgui.

Needs nothing beyond the standard library. If `certifi` is installed
(pip install certifi) its CA list is used, which python.org builds of Python
need when "Install Certificates.command" has not been run.
"""
import ssl
import threading
import urllib.error
import urllib.request

from baremacgui import App, Button, ComboBox, HBox, Label, TextBox, VBox, Window

try:
    import certifi
except ImportError:
    certifi = None

CHECKED = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]


def fetch(target):
    """Return (final_url, status, headers) of a GET request. Runs in a worker thread."""
    target = target.strip()
    if "://" not in target:
        target = "https://" + target
    if not target.lower().startswith(("http://", "https://")):
        raise ValueError("only http and https are supported")
    context = ssl.create_default_context(cafile=certifi.where() if certifi else None)
    request = urllib.request.Request(target, headers={"User-Agent": "baremacgui-example/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=8, context=context) as response:
            return response.geturl(), response.status, response.headers
    except urllib.error.HTTPError as error:  # error pages still carry headers
        return error.url, error.code, error.headers


def report(url, status, headers):
    csp = headers.get("Content-Security-Policy")
    lines = [f"URL     {url}", f"Status  {status}", f"Server  {headers.get('Server') or '(not sent)'}", ""]
    present = 0
    for name in CHECKED:
        value = headers.get(name)
        note = ""
        if name == "X-Frame-Options" and not value and csp and "frame-ancestors" in csp.lower():
            value, note = "-", "  (covered by CSP frame-ancestors)"
        if value:
            present += 1
            lines.append(f"OK       {name}{note}" if note else f"OK       {name}: {value}")
        else:
            lines.append(f"MISSING  {name}")
    lines += ["", f"{present} of {len(CHECKED)} present"]
    if csp:
        lines += ["", "Content-Security-Policy"]
        lines += [f"  {directive.strip()}" for directive in csp.split(";") if directive.strip()]
    return "\n".join(lines)


app = App("Header Check")

with Window("Header Check", size=(560, 460)):
    with VBox(padding=16, gap=10):
        with HBox(gap=8):
            Label("Host")
            host = ComboBox(["github.com", "pypi.org", "mozilla.org", "example.com"], selected=0, grow=1)
            go = Button("Check", default=True)
        output = TextBox(multiline=True, readonly=True, grow=1)


def show(text):
    output.text = text
    go.enabled = True


def work(target):  # worker thread: never touch controls from here
    try:
        text = report(*fetch(target))
    except Exception as error:  # noqa: BLE001 - shown to the user
        text = f"Error: {error}"
    app.invoke(show, text)


def start():
    go.enabled = False
    output.text = "Checking ..."
    threading.Thread(target=work, args=(host.text,), daemon=True).start()


go.on_click(start)
app.run()
