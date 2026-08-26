from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any
from typing import Iterable


def _is_missing(value: Any) -> bool:
    return value is None or value == '' or (
        isinstance(value, float) and math.isnan(value)
    )


def _normalize_identity_value(value: Any) -> str:
    if _is_missing(value):
        return ''

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def build_identity_key(
    row: dict[str, Any],
    identity_columns: Iterable[str],
) -> tuple[str, ...]:
    return tuple(
        _normalize_identity_value(row.get(column))
        for column in identity_columns
    )


def _validate_unique_identities(
    rows: Iterable[dict[str, Any]],
    identity_columns: tuple[str, ...],
    table_name: str,
) -> None:
    seen_identities: dict[tuple[str, ...], int] = {}

    for row_index, row in enumerate(rows):
        identity_key = build_identity_key(row, identity_columns)
        if identity_key in seen_identities:
            raise ValueError(
                f'Duplicate identity for {table_name} using {identity_columns}: '
                f'{identity_key!r} at rows {seen_identities[identity_key]} and {row_index}'
            )
        seen_identities[identity_key] = row_index


def assign_append_only_fids(
    rows: list[dict[str, Any]],
    identity_columns: tuple[str, ...],
    existing_csv_path: Path,
    table_name: str,
) -> list[int]:
    _validate_unique_identities(rows, identity_columns, table_name)

    existing_rows: list[dict[str, Any]] = []
    if existing_csv_path.is_file():
        with open(existing_csv_path, newline='', encoding='utf-8') as csv_file:
            existing_rows = list(csv.DictReader(csv_file))
        _validate_unique_identities(existing_rows, identity_columns, table_name)

    existing_fid_map: dict[tuple[str, ...], int] = {}
    max_existing_fid = -1

    for row in existing_rows:
        fid_value = int(_normalize_identity_value(row.get('fid')))
        max_existing_fid = max(max_existing_fid, fid_value)
        existing_fid_map[build_identity_key(row, identity_columns)] = fid_value

    next_fid = max_existing_fid + 1
    assigned_fids: list[int] = []

    for row in rows:
        identity_key = build_identity_key(row, identity_columns)
        if identity_key in existing_fid_map:
            assigned_fids.append(existing_fid_map[identity_key])
            continue

        existing_fid_map[identity_key] = next_fid
        assigned_fids.append(next_fid)
        next_fid += 1

    return assigned_fids