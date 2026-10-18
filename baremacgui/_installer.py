"""Logic of the install creator: what to build, which icons exist, and the build itself.

Everything here except `create_installer` is pure and tested on any OS. The wizard window is in
`_creator.py`; the terminal front end is `python -m baremacgui build` and `python -m baremacgui installer`.
"""
import ast
import difflib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, field, fields

from . import _bundle
from .errors import PlatformError

OUTPUTS = ("app", "zip", "dmg")
SYSTEM_ICON_DIR = "/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources"
SPEC_SUFFIX = ".bmc.json"
_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z.+-]{0,31}$")
_PACKAGE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


@dataclass
class BuildSpec:
    """Everything the creator needs to know. Saved as JSON (`*.bmc.json`) so a build can be repeated."""

    script: str = ""
    name: str = ""
    identifier: str = ""
    version: str = "1.0"
    icon: str = ""  # an .icns or .png file; empty: the plain default icon
    background: bool = False  # menu-bar app without Dock icon
    standalone: bool = True  # False: small launcher bundle that needs this Python (only runs on this Mac)
    include: list = field(default_factory=list)  # extra files or folders the script needs
    packages: list = field(default_factory=list)  # packages to take along completely
    hidden_imports: list = field(default_factory=list)  # modules imported by name at run time
    outputs: list = field(default_factory=lambda: ["dmg"])  # any of app, zip, dmg
    dest: str = "."

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(data) - known)
        if unknown:
            raise ValueError(f"unknown setting(s) in the build file: {', '.join(unknown)}")
        return cls(**data)


def default_name(script):
    return os.path.splitext(os.path.basename(str(script)))[0].replace("_", " ").strip().title()


def check_spec(spec):
    """Validate a BuildSpec and return a normalized copy (absolute paths, defaults filled in)."""
    script = os.path.abspath(str(spec.script))
    if not spec.script or not os.path.isfile(script):
        raise ValueError(f"script not found: {spec.script!r}")
    if not script.endswith(".py"):
        raise ValueError(f"the script must be a .py file, got {spec.script!r}")
    name = _bundle.check_app_name(spec.name or default_name(script))
    identifier = _bundle.check_identifier(spec.identifier or _bundle.default_identifier(name))
    version = str(spec.version or "1.0")
    if not _VERSION.match(version):
        raise ValueError(f"not a usable version: {version!r} (letters, digits, '.', '+', '-')")
    icon = ""
    if spec.icon:
        icon = os.path.abspath(str(spec.icon))
        if not os.path.isfile(icon) or os.path.splitext(icon)[1].lower() not in (".icns", ".png"):
            raise ValueError(f"the icon must be an existing .icns or .png file, got {spec.icon!r}")
    include = []
    for extra in spec.include:
        path = os.path.abspath(str(extra))
        if not os.path.exists(path):
            raise ValueError(f"included path not found: {extra!r}")
        include.append(path)
    for label, values in (("package", spec.packages), ("hidden import", spec.hidden_imports)):
        for value in values:
            if not _PACKAGE.match(str(value)):
                raise ValueError(f"not a usable {label} name: {value!r}")
    outputs = list(dict.fromkeys(spec.outputs))
    if not outputs:
        raise ValueError("choose at least one output (app, zip or dmg)")
    bad = [o for o in outputs if o not in OUTPUTS]
    if bad:
        raise ValueError(f"unknown output {bad[0]!r}: use {', '.join(OUTPUTS)}")
    return BuildSpec(script, name, identifier, version, icon, bool(spec.background), bool(spec.standalone),
                     include, [str(p) for p in spec.packages], [str(m) for m in spec.hidden_imports],
                     outputs, os.path.abspath(str(spec.dest or ".")))


def save_spec(spec, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(spec.to_dict(), handle, indent=2)
        handle.write("\n")


def load_spec(path):
    """Read a build file. Relative paths in it are relative to the file."""
    path = os.path.abspath(str(path))
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"not a build file: {path}")
    spec = BuildSpec.from_dict(data)
    base = os.path.dirname(path)

    def resolve(value):
        return value if not value or os.path.isabs(value) else os.path.normpath(os.path.join(base, value))

    spec.script = resolve(spec.script)
    spec.icon = resolve(spec.icon)
    spec.include = [resolve(p) for p in spec.include]
    spec.dest = resolve(spec.dest)
    return spec


# ---- what a script needs -------------------------------------------------------------------------------

def detect_imports(source):
    """Top-level modules a script imports that are not part of the standard library (and not baremacgui)."""
    tree = ast.parse(source)
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.add(node.module.split(".")[0])
    stdlib = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
    return sorted(found - stdlib - {"baremacgui"})


def is_installed(module):
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


# ---- icons ---------------------------------------------------------------------------------------------

def system_icons(directory=SYSTEM_ICON_DIR):
    """[(name, path)] of the icons macOS ships (CoreTypes), sorted by name. Empty where there are none."""
    try:
        names = os.listdir(directory)
    except OSError:
        return []
    return sorted((os.path.splitext(n)[0], os.path.join(directory, n)) for n in names
                  if n.lower().endswith(".icns") and not n.startswith("."))


def find_system_icon(name, directory=SYSTEM_ICON_DIR):
    """The path of the system icon called `name` (case does not matter). Raises ValueError with suggestions."""
    icons = system_icons(directory)
    lookup = {n.lower(): p for n, p in icons}
    key = str(name).lower()
    if key in lookup:
        return lookup[key]
    if key + "icon" in lookup:
        return lookup[key + "icon"]
    close = difflib.get_close_matches(key, list(lookup), n=5, cutoff=0.5)
    hint = f" Similar: {', '.join(n for n, _ in icons if n.lower() in close)}." if close else ""
    raise ValueError(f"no system icon called {name!r}.{hint}")


def local_icons(folder, limit=2000):
    """[(name, path)] of the .icns and .png files in a folder and its subfolders (two levels deep)."""
    found = []
    base = os.path.abspath(str(folder))
    for root, dirs, files in os.walk(base):
        depth = os.path.relpath(root, base).count(os.sep) + (0 if root == base else 1)
        dirs[:] = [d for d in dirs if not d.startswith(".")] if depth < 2 else []
        for filename in files:
            if filename.lower().endswith((".icns", ".png")) and not filename.startswith("."):
                found.append((os.path.splitext(filename)[0], os.path.join(root, filename)))
    return sorted(found)[:limit]


# ---- packaging -----------------------------------------------------------------------------------------

def output_name(spec, kind):
    return f"{spec.name}.app" if kind == "app" else f"{spec.name}-{spec.version}.{kind}"


def zip_command(app, target):
    return ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", app, target]


def dmg_command(volume_name, folder, target):
    return ["hdiutil", "create", "-volname", volume_name, "-srcfolder", folder, "-ov", "-format", "UDZO", target]


def create_installer(spec, log=None):
    """Build the app from `spec` and package it. Returns the list of files and folders made.

    The app is built standalone (own interpreter, signed ad hoc) unless spec.standalone is False.
    outputs: "app" the bundle itself, "zip" a ZIP made with ditto (keeps the signature), "dmg" a disk image
    with the app and a link to /Applications to drag it to. macOS only.
    """
    spec = check_spec(spec)
    if sys.platform != "darwin":
        raise PlatformError("the install creator builds macOS apps and needs macOS")
    say = log or (lambda line: None)
    os.makedirs(spec.dest, exist_ok=True)
    made = []
    with tempfile.TemporaryDirectory() as stage:
        say(f"Building {spec.name} ...")
        icon = spec.icon or None
        if spec.standalone:
            app = _bundle.build_standalone(spec.script, spec.name, stage, spec.identifier, spec.version, icon,
                                           spec.background, spec.include, spec.hidden_imports, spec.packages, log)
        else:
            say("Light build: the app starts this Python and runs only on this Mac.")
            app = _bundle.build_app(spec.script, spec.name, stage, spec.identifier, spec.version, icon,
                                    spec.background, spec.include)
        for kind in spec.outputs:
            target = os.path.join(spec.dest, output_name(spec, kind))
            say(f"Making {os.path.basename(target)} ...")
            if os.path.isdir(target):
                shutil.rmtree(target)
            elif os.path.exists(target):
                os.remove(target)
            if kind == "app":
                _bundle._run(["ditto", app, target], log)
            elif kind == "zip":
                _bundle._run(zip_command(app, target), log)
            else:
                folder = os.path.join(stage, "disk")
                os.makedirs(folder)
                _bundle._run(["ditto", app, os.path.join(folder, os.path.basename(app))], log)
                os.symlink("/Applications", os.path.join(folder, "Applications"))
                _bundle._run(dmg_command(spec.name, folder, target), log)
                shutil.rmtree(folder)
            made.append(target)
    say("Done.")
    return made
