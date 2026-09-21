"""Tests for the deterministic mapping unit colours (issues #62 and #75)."""

import csv
from pathlib import Path

import pytest

from nin_qgis_plugin.symbology_colors import kode_id_color

ATTRIBUTE_TABLES_PATH = (
    Path(__file__).parents[1] / "nin_qgis_plugin" / "csv" / "attribute_tables"
)
MAPPING_SCALE_TABLES = ["M005", "M020", "M050", "grunntyper"]


def _kode_ids(table_name):
    csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return [row["kode_id"] for row in csv.DictReader(csv_file) if row["kode_id"]]


def test_color_is_deterministic():
    assert kode_id_color("TK01-M005-19") == kode_id_color("TK01-M005-19")
    # Pinned value: changing the hashing scheme changes every project's colours
    assert kode_id_color("TK01-M005-19") == (225, 36, 130)


def test_color_components_are_valid_rgb():
    for kode_id in ("TK01-M005-19", "NA-VC02", "", "æøå"):
        color = kode_id_color(kode_id)
        assert len(color) == 3
        assert all(isinstance(c, int) and 0 <= c <= 255 for c in color)


def test_similar_codes_get_different_colors():
    assert kode_id_color("TK01-M005-19") != kode_id_color("TK01-M005-18")
    assert kode_id_color("TK01-M005-19") != kode_id_color("TK01-M020-19")


@pytest.mark.parametrize("table_name", MAPPING_SCALE_TABLES)
def test_mapping_units_get_distinct_colors(table_name):
    kode_ids = _kode_ids(table_name)
    colors = {kode_id: kode_id_color(kode_id) for kode_id in kode_ids}
    unique_ratio = len(set(colors.values())) / len(colors)
    assert unique_ratio >= 0.99, (
        f"{table_name}: only {unique_ratio:.1%} of {len(colors)} units have a unique colour"
    )
