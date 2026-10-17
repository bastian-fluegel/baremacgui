"""Settings: remember values between runs, in the standard macOS preferences (NSUserDefaults)."""
from __future__ import annotations

from ._bridge import FN
from ._options import check_setting_key, check_setting_value, plain_value


class Settings:
    """A small persistent dictionary.

        prefs = Settings("my-tool", defaults={"theme": "System", "recent": 10})
        prefs["theme"]                 # "System" until something else was stored
        prefs["recent"] = 20           # written to ~/Library/Preferences/baremacgui.my-tool.plist
        del prefs["recent"]            # back to the default

    Values may be bool, int, float, str and lists or dicts of those (what a property list holds).
    `name` becomes the preferences domain "baremacgui.<name>". A packaged .app would normally use
    its own bundle identifier instead; pass `domain="com.example.app"` for that.

    Native counterpart: NSUserDefaults (a custom suite). Difference: the domain is not the
    script's bundle, because a plain Python process has none of its own.
    """

    def __init__(self, name=None, defaults=None, domain=None):
        if (name is None) == (domain is None):
            raise ValueError("give exactly one of name or domain")
        self.domain = str(domain) if domain else f"baremacgui.{check_setting_key(name)}"
        self._defaults = {check_setting_key(k): check_setting_value(v) for k, v in (defaults or {}).items()}
        self._ns = FN().NSUserDefaults.alloc().initWithSuiteName_(self.domain)

    def __getitem__(self, key):
        check_setting_key(key)
        stored = self._ns.objectForKey_(key)
        if stored is None:
            if key in self._defaults:
                return self._defaults[key]
            raise KeyError(key)
        return plain_value(stored)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key, value):
        self._ns.setObject_forKey_(check_setting_value(value), check_setting_key(key))

    def __delitem__(self, key):
        self._ns.removeObjectForKey_(check_setting_key(key))

    def __contains__(self, key):
        return self.get(key, _MISSING) is not _MISSING

    def keys(self):
        """Names of all stored values and defaults."""
        stored = {str(k) for k in (self._ns.persistentDomainForName_(self.domain) or {})}
        return sorted(stored | set(self._defaults))

    def to_dict(self):
        return {key: self[key] for key in self.keys()}

    def clear(self):
        """Forget everything stored (defaults stay)."""
        self._ns.removePersistentDomainForName_(self.domain)

    def save(self):
        """Write to disk now. Done automatically in the background; call it before a hard exit."""
        self._ns.synchronize()


_MISSING = object()
