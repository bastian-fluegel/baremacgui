"""`python -m baremacgui ...`: build, icons and installer (the wizard)."""
from __future__ import annotations

import argparse
import subprocess
import sys

from . import _bundle, _installer
from .errors import BareMacGUIError

_ERRORS = (BareMacGUIError, OSError, ValueError, subprocess.CalledProcessError)


def _parser():
    parser = argparse.ArgumentParser(prog="python -m baremacgui", description="BareMacGUI tools")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="build an .app, a ZIP or a disk image from a script (no window needed)")
    build.add_argument("script", nargs="?", help="the script (not needed with --spec)")
    build.add_argument("--spec", help="read all settings from a build file (*.bmc.json)")
    build.add_argument("--save-spec", help="also write the settings to a build file")
    build.add_argument("--name")
    build.add_argument("--dest", default=None, help="folder for the results (default: the current folder)")
    build.add_argument("--identifier")
    build.add_argument("--version", default="1.0")
    icon = build.add_mutually_exclusive_group()
    icon.add_argument("--icon", help=".icns or .png file")
    icon.add_argument("--system-icon", metavar="NAME", help="an icon macOS ships, see: python -m baremacgui icons")
    build.add_argument("--background", action="store_true", help="menu-bar app without Dock icon")
    build.add_argument("--include", action="append", default=[], help="extra file or folder (repeatable)")
    build.add_argument("--package", action="append", default=[], help="take a package along completely (repeatable)")
    build.add_argument("--hidden-import", action="append", default=[], help="module imported by name (repeatable)")
    build.add_argument("--standalone", action="store_true",
                       help="own interpreter inside (needs PyInstaller), signed ad hoc; runs without Python")
    build.add_argument("--dmg", action="store_true", help="also make a disk image (implies --standalone)")
    build.add_argument("--zip", action="store_true", help="also make a ZIP (implies --standalone)")

    icons = sub.add_parser("icons", help="list icons to choose from")
    icons.add_argument("--folder", help="list the .icns and .png files of this folder instead of the system icons")
    icons.add_argument("--filter", default="", help="only names that contain this text")

    wizard = sub.add_parser("installer", help="open the install creator (a window); optional script or build file")
    wizard.add_argument("path", nargs="?")
    return parser


def _spec_from_args(args):
    if args.spec:
        spec = _installer.load_spec(args.spec)
        if args.dest is not None:
            spec.dest = args.dest
        return spec
    if not args.script:
        raise ValueError("give a script or --spec")
    icon = _installer.find_system_icon(args.system_icon) if args.system_icon else (args.icon or "")
    share = args.dmg or args.zip
    outputs = (["app"] if args.standalone or not share else []) + (["dmg"] if args.dmg else []) \
        + (["zip"] if args.zip else [])
    return _installer.BuildSpec(
        script=args.script, name=args.name or "", identifier=args.identifier or "", version=args.version,
        icon=icon, background=args.background, standalone=bool(args.standalone or share), include=args.include,
        packages=args.package, hidden_imports=args.hidden_import, outputs=outputs, dest=args.dest or ".")


def _build(args):
    spec = _spec_from_args(args)
    if args.save_spec:
        _installer.save_spec(spec, args.save_spec)
    if not spec.standalone and not args.spec:  # the plain launcher bundle, as before
        spec = _installer.check_spec(spec)
        print(_bundle.build_app(spec.script, spec.name, spec.dest, spec.identifier, spec.version,
                                spec.icon or None, spec.background, spec.include))
        return 0
    for path in _installer.create_installer(spec, log=lambda line: print(line, file=sys.stderr)):
        print(path)
    return 0


def _icons(args):
    icons = _installer.local_icons(args.folder) if args.folder else _installer.system_icons()
    for name, path in icons:
        if args.filter.lower() in name.lower():
            print(f"{name}\t{path}")
    return 0


def _installer_window(args):
    from ._creator import run

    run(args.path)
    return 0


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        return {"build": _build, "icons": _icons, "installer": _installer_window}[args.command](args)
    except _ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
