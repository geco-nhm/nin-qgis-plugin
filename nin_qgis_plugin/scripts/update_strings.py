#!/usr/bin/env python
"""Update Qt translation .ts files if plugin sources changed."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("locales", nargs="+", help="Locale codes to update")
    return parser.parse_args()


def source_files() -> list[Path]:
    return [
        path
        for path in Path(".").rglob("*")
        if path.is_file() and path.suffix in {".py", ".ui"}
    ]


def newest_mtime(paths: list[Path]) -> float:
    if not paths:
        return 0.0
    return max(path.stat().st_mtime for path in paths)


def should_update(locales: list[str], changed_ts: float) -> bool:
    for locale in locales:
        ts_path = Path("i18n") / f"{locale}.ts"
        if not ts_path.exists():
            ts_path.touch()
            return True
        if changed_ts > ts_path.stat().st_mtime:
            return True
    return False


def main() -> int:
    args = parse_args()
    python_files = source_files()
    changed_ts = newest_mtime(python_files)

    if should_update(args.locales, changed_ts):
        file_list = [str(path) for path in python_files]
        print(" ".join(file_list))
        print("Please provide translations by editing the translation files below:")

        for locale in args.locales:
            ts_path = Path("i18n") / f"{locale}.ts"
            print(str(ts_path))
            subprocess.run(
                ["pylupdate4", "-noobsolete", *file_list, "-ts", str(ts_path)],
                check=True,
            )
    else:
        print("No need to edit any translation files (.ts) because no python files")
        print("has been updated since the last update translation.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
