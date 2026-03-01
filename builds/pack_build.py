#!/usr/bin/env python3
"""Package a Kodi build reference directory into a distributable ZIP.

This helper uses the same manifest data produced by ``inspect_build.py`` to
collect all the addon directories (and optionally userdata) and write them
into a single archive.  The resulting ZIP can be deployed to a Kodi box or
extracted as the basis of a new build.

Usage:
    pack_build.py /path/to/reference output.zip [--include-userdata]

The script does not attempt to download anything, it simply archives the
existing files.  For a true "reproducible" build from scratch you could
combine manifest scanning with a downloader that pulls specific versions
from remote repositories.
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def collect_addons(ref: Path):
    addons = []
    addons_dir = ref / "addons"
    if not addons_dir.is_dir():
        return addons
    for entry in sorted(addons_dir.iterdir()):
        if entry.is_dir():
            addons.append(entry)
    return addons


def collect_userdata(ref: Path):
    ud = ref / "userdata"
    return [ud] if ud.is_dir() else []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ref", type=Path, help="root of reference build")
    parser.add_argument(
        "out", 
        type=Path, 
        nargs="?", 
        help="output zip path (defaults to ./{ref_name}.zip)"
    )
    parser.add_argument(
        "--include-userdata",
        action="store_true",
        help="include userdata folder in the archive",
    )
    args = parser.parse_args()

    ref = args.ref.resolve()
    if args.out:
        out = args.out.resolve()
    else:
        out = Path.cwd() / f"{ref.name}.zip"

    todos = collect_addons(ref)
    if args.include_userdata:
        todos += collect_userdata(ref)

    if not todos:
        print("no addons/userdata found, aborting")
        sys.exit(1)

    with ZipFile(out, "w", ZIP_DEFLATED) as zipf:
        for path in todos:
            if path.is_dir():
                for root, dirs, files in os.walk(path):
                    for fn in files:
                        full = Path(root) / fn
                        arcname = full.relative_to(ref)
                        zipf.write(full, arcname)
            else:
                arcname = path.relative_to(ref)
                zipf.write(path, arcname)
    print(f"created {out} containing {len(todos)} items")

if __name__ == "__main__":
    main()
