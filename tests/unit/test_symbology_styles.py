"""Tests for the styles the plugin reads from the symbology tables."""

import csv
from pathlib import Path

import pytest

from nin_qgis_plugin.symbology_colors import kode_id_color
from nin_qgis_plugin.symbology_styles import hex_to_rgb, hovedtype_of, load_unit_styles

ATTRIBUTE_TABLES_PATH = (
    Path(__file__).parents[2] / "nin_qgis_plugin" / "csv" / "attribute_tables"
)
MAPPING_SCALES = ["M005", "M020", "M050", "grunntyper"]


def _kode_ids(mapping_scale):
    csv_path = ATTRIBUTE_TABLES_PATH / f"{mapping_scale}_attribute_table.csv"
    with open(csv_path, newline="", encoding="utf-8") as csv_file:
        return [row["kode_id"] for row in csv.DictReader(csv_file) if row["kode_id"]]


def test_hovedtype_of():
    assert hovedtype_of("TB01-M005-03") == "NA-TB01"
    assert hovedtype_of("TB01-03") == "NA-TB01"


@pytest.mark.parametrize("mapping_scale", MAPPING_SCALES)
def test_every_unit_has_a_style(mapping_scale):
    styles = load_unit_styles(mapping_scale)
    assert set(styles) == set(_kode_ids(mapping_scale))

    for style in styles.values():
        assert all(0 <= channel <= 255 for channel in hex_to_rgb(style["fill_hex"]))
        assert len(style["markers"]) <= 3


def test_land_unit_has_a_full_symbol():
    style = load_unit_styles("M005")["TB01-M005-15"]
    assert style["fill_hex"] == "#8ACA8B"
    assert style["hatch"]["angle"] == 90
    assert style["hatch"]["spacing_mm"] == 4
    assert [marker["shape"] for marker in style["markers"]] == ["ring", "circle"]


def test_water_unit_has_the_colour_of_its_hovedtypegruppe():
    styles = load_unit_styles("M005")
    assert styles["LA01-M005-01"]["fill_hex"] == "#7BAED9"
    assert styles["LA01-M005-01"]["hatch"] is None


def test_grunntype_has_the_colour_of_its_hovedtype():
    styles = load_unit_styles("grunntyper")
    assert styles["TB01-01"]["fill_hex"] == load_unit_styles("M005")["TB01-M005-01"]["fill_hex"]


def test_type_outside_natursystem_falls_back_to_the_code_colour():
    '''TU01 is a livsmedium; its first letter must not give it the colour of NA-T.'''

    style = load_unit_styles("grunntyper")["TU01-01"]
    assert hex_to_rgb(style["fill_hex"]) == kode_id_color("TU01-01")
