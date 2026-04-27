#!/usr/bin/env python
"""Compile Qt translation source files (.ts) into .qm files."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("lrelease", help="Path or command for Qt lrelease tool")
    parser.add_argument("locales", nargs="+", help="Locale codes to compile")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    for locale in args.locales:
        ts_file = Path("i18n") / f"{locale}.ts"
        print(f"Processing: {ts_file.name}")
        subprocess.run([args.lrelease, str(ts_file)], check=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
