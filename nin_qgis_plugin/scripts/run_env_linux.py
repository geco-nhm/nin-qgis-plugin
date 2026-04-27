#!/usr/bin/env python
"""Print environment exports for running QGIS-related plugin tasks on Linux."""

from __future__ import annotations

import argparse


DEFAULT_PREFIX = "/usr/local/qgis-2.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("qgis_prefix", nargs="?", default=DEFAULT_PREFIX)
    parser.add_argument(
        "--print-exports",
        action="store_true",
        help="Print only export lines suitable for eval.",
    )
    return parser.parse_args()


def export_lines(prefix: str) -> list[str]:
    return [
        f"export QGIS_PREFIX_PATH={prefix}",
        f"export QGIS_PATH={prefix}",
        f"export LD_LIBRARY_PATH={prefix}/lib",
        (
            "export PYTHONPATH="
            f"{prefix}/share/qgis/python:{prefix}/share/qgis/python/plugins:${{PYTHONPATH}}"
        ),
        "export QGIS_DEBUG=0",
        "export QGIS_LOG_FILE=/tmp/inasafe/realtime/logs/qgis.log",
        f"export PATH={prefix}/bin:${{PATH}}",
    ]


def main() -> int:
    args = parse_args()

    if args.print_exports:
        print("\n".join(export_lines(args.qgis_prefix)))
        return 0

    print(args.qgis_prefix)
    print(f"QGIS PATH: {args.qgis_prefix}")
    print("This helper prints shell exports for a QGIS install path.")
    print()
    print("To use it from bash:")
    print(f'eval "$(python scripts/run_env_linux.py --print-exports {args.qgis_prefix})"')
    print()
    print("Then run plugin tasks, e.g. make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
