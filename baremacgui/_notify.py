"""System notifications (Notification Center banners)."""
from __future__ import annotations

import subprocess
import sys

from .errors import PlatformError

_SCRIPT = (
    "on run argv\n"
    "  if (item 4 of argv) is \"\" then\n"
    "    display notification (item 1 of argv) with title (item 2 of argv) subtitle (item 3 of argv)\n"
    "  else\n"
    "    display notification (item 1 of argv) with title (item 2 of argv) subtitle (item 3 of argv) "
    "sound name (item 4 of argv)\n"
    "  end if\n"
    "end run"
)


def notification_command(text, title="", subtitle="", sound=None):
    """The osascript command line for a notification (pure, so it is tested on every OS)."""
    if not isinstance(text, str) or not text:
        raise ValueError("a notification needs a text")
    return ["osascript", "-e", _SCRIPT, str(text), str(title or ""), str(subtitle or ""), str(sound or "")]


def notify(text, title="", subtitle="", sound=None):
    """Show a banner in Notification Center and return at once.

    title, subtitle  optional lines above the text
    sound            name of a system sound, e.g. "Glass" or "Ping" (None for silence)

    Works from a plain script: it asks the system's `osascript` to post it, so no bundle or
    entitlement is needed. The banner is attributed to Script Editor, not to your app, and it only
    shows if notifications are allowed for Script Editor in System Settings. Text is passed as
    arguments, never pasted into the script, so quotes in it are safe.

    Native counterpart: UNUserNotificationCenter (needs a signed .app bundle; not used here).
    """
    command = notification_command(text, title, subtitle, sound)
    if sys.platform != "darwin":
        raise PlatformError(f"notify only runs on macOS (this is {sys.platform}).")
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
