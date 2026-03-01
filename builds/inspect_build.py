#!/usr/bin/env python3
"""Inspect a Kodi build reference directory and print out a manifest.

The script scans the addons and userdata folders and reports information
that can be used to reproduce the build.

Usage:
    inspect_build.py /path/to/reference

Output includes:
  * addon id, name, version, type (script/video/skin/etc), dependencies
  * userdata directories present

Future enhancements could generate a zip or a Dockerfile to rebuild a
similar environment.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_addon(addon_dir: Path):
    xml_path = addon_dir / "addon.xml"
    if not xml_path.exists():
        return None
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f"failed to parse {xml_path}: {e}")
        return None
    root = tree.getroot()
    info = {
        "id": root.attrib.get("id"),
        "version": root.attrib.get("version"),
        "name": root.attrib.get("name"),
        "provider": root.attrib.get("provider-name"),
        "type": root.attrib.get("type", ""),
        "requires": [],
    }
    req = root.find("requires")
    if req is not None:
        for imp in req.findall("import"):
            info["requires"].append(
                {
                    "addon": imp.attrib.get("addon"),
                    "version": imp.attrib.get("version"),
                }
            )
    return info


def main(base: Path):
    addons_dir = base / "addons"
    userdata_dir = base / "userdata"

    if not addons_dir.is_dir():
        print(f"{addons_dir} is not a directory")
        return

    manifest = []
    for entry in sorted(addons_dir.iterdir()):
        if entry.is_dir():
            info = parse_addon(entry)
            if info:
                manifest.append(info)
    # sort by id
    manifest.sort(key=lambda x: x.get("id") or "")

    print("Detected addons:")
    for a in manifest:
        print(f"- {a['id']} {a['version']} ({a['name']})")
        if a["requires"]:
            deps = ", ".join(r["addon"] + ("@" + r["version"] if r.get("version") else "") for r in a["requires"])
            print(f"    depends on: {deps}")
    print()

    if userdata_dir.is_dir():
        print("Userdata folders:")
        for entry in sorted(userdata_dir.iterdir()):
            print(f"- {entry.name}")
    else:
        print("No userdata directory found")

    # could dump to JSON, YAML, etc.

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: inspect_build.py /path/to/reference")
        sys.exit(1)
    main(Path(sys.argv[1]))
