"""Tests for the symbols of the mapping units of the NiN 3.0 symbology."""

import csv

import pytest

from symbology_tools.colour import hex_to_rgb, rgb_to_oklch
from symbology_tools.palette import ATTRIBUTE_TABLES_PATH, MAPPING_SCALES, SYMBOLOGY_PATH
from symbology_tools.patterns import (
    ANGLE_INTERMEDIAER, ANGLE_KALKFATTIG, ANGLE_KALKRIK, DRYNESS_COLOURS, MAX_MARKERS,
    MIN_PATTERN_CONTRAST, OUTPUT_COLUMNS, build_symbology, catalogue_gaps,
    dryness_class, ensure_contrast, kalk_angle, load_hovedtype_patterns,
    load_variable_rules, marker_variant, symbol_signature, symbol_to_row,
    validate_symbology, value_colour, value_midpoint, value_span,
)


@pytest.fixture(scope="module")
def symbology():
    return build_symbology()


def _symbol(symbology, scale, kode_id):
    return next(symbol for symbol in symbology[scale] if symbol["kode_id"] == kode_id)


def test_value_midpoint_and_span():
    assert value_midpoint("b,c,d") == 3
    assert value_midpoint("0,a") == 0.5
    assert value_span("b,c,d") == 3
    assert value_span("A") == 1


def test_kalk_angle():
    assert kalk_angle("a,b") == ANGLE_KALKFATTIG
    assert kalk_angle("d,e,f") == ANGLE_INTERMEDIAER
    assert kalk_angle("g,h,i") == ANGLE_KALKRIK
    # A unit that covers the whole gradient says nothing about kalkinnhold
    assert kalk_angle("a,b,c,d,e,f,g,h,i") is None


def test_dryness_class_goes_from_moist_to_dry():
    extent = (1, 8)
    classes = [dryness_class(values, extent) for values in ("a,b", "c,d", "e,f", "g,h")]
    assert classes == [0, 1, 2, 3]


def test_marker_variant():
    assert marker_variant("circle", 1) == (1.0, True)
    assert marker_variant("circle", 3) == (2.2, True)
    # After the filled sizes come the open ones
    assert marker_variant("circle", 4) == (1.0, False)
    # A shape without an inside only has sizes
    assert marker_variant("cross", 1) == (1.0, False)
    assert marker_variant("cross", 4) is None


def test_value_colour():
    rule = {"value_colours": "A=#111111;D=#2E7D32"}
    assert value_colour(rule, "D") == "#2E7D32"
    # A range that includes '0' is undifferentiated
    assert value_colour(rule, "0,A") == ""
    assert value_colour({"value_colours": ""}, "D") is None


@pytest.mark.parametrize("fill_hex", ["#8ACA8B", "#EDEBFF", "#747071"])
def test_ensure_contrast(fill_hex):
    fill_lightness = rgb_to_oklch(hex_to_rgb(fill_hex))[0]
    for colour in DRYNESS_COLOURS + ("#EDEBFF", "#C9A400"):
        adjusted = ensure_contrast(colour, fill_hex)
        lightness = rgb_to_oklch(hex_to_rgb(adjusted))[0]
        assert abs(lightness - fill_lightness) >= MIN_PATTERN_CONTRAST - 0.01


def test_rules_use_known_elements():
    for rule in load_variable_rules().values():
        assert rule["element"] in ("hatch_angle", "hatch_colour", "marker")
        assert bool(rule["shape"]) == (rule["element"] == "marker")
    for emblem in load_hovedtype_patterns().values():
        assert emblem["element"] in ("hatch_colour", "marker")


def test_symbology_is_valid(symbology):
    assert validate_symbology(symbology) == []


@pytest.mark.parametrize("scale", MAPPING_SCALES)
def test_every_unit_has_a_unique_symbol(symbology, scale):
    symbols = symbology[scale]
    assert len({symbol_signature(symbol) for symbol in symbols}) == len(symbols)
    assert all(len(symbol["markers"]) <= MAX_MARKERS for symbol in symbols)


@pytest.mark.parametrize("scale", MAPPING_SCALES)
def test_written_tables_are_up_to_date(symbology, scale):
    '''The CSV tables in the plugin must match what the rules produce.'''

    with open(SYMBOLOGY_PATH / f"symbology_{scale}.csv", newline="", encoding="utf-8") as csv_file:
        written = list(csv.DictReader(csv_file))

    expected = [
        {column: str(value) for column, value in symbol_to_row(symbol).items()}
        for symbol in symbology[scale]
    ]
    assert list(written[0]) == list(OUTPUT_COLUMNS)
    assert written == expected, "Run: python symbology_tools/patterns.py"


@pytest.mark.parametrize("scale", MAPPING_SCALES)
def test_table_covers_the_catalogue(symbology, scale):
    with open(ATTRIBUTE_TABLES_PATH / f"{scale}_attribute_table.csv", newline="", encoding="utf-8") as csv_file:
        catalogue = {
            row["kode_id"] for row in csv.DictReader(csv_file)
            if row["kode_id"].startswith(("T", "V"))
        }
    assert {symbol["kode_id"] for symbol in symbology[scale]} == catalogue


def test_coarser_scales_have_simpler_symbols(symbology):
    def mean_layers(scale):
        symbols = symbology[scale]
        layers = sum(len(s["markers"]) + (s["hatch_angle"] is not None) for s in symbols)
        return layers / len(symbols)

    assert mean_layers("M050") < mean_layers("M020") < mean_layers("M005")


def test_forest_example(symbology):
    '''Kalkinnhold sets the angle; drought and moisture appear at finer scales.'''

    kalkskog = _symbol(symbology, "M050", "TB01-M050-02")
    assert kalkskog["hatch_angle"] == ANGLE_KALKRIK
    assert kalkskog["markers"] == []

    hogstaudeskog = _symbol(symbology, "M005", "TB01-M005-15")
    assert hogstaudeskog["hatch_angle"] == ANGLE_KALKRIK
    assert hogstaudeskog["hatch_colour"] == DRYNESS_COLOURS[0]
    assert [marker["shape"] for marker in hogstaudeskog["markers"]] == ["circle"]


def test_units_follow_their_parent_to_the_coarsest_scale(symbology):
    lavskog = _symbol(symbology, "M005", "TB01-M005-10")
    parent = _symbol(symbology, "M020", lavskog["parent_kode_id"])
    assert parent["kode_id"] == "TB01-M020-04"
    assert parent["parent_kode_id"] == "TB01-M050-01"


def test_wetland_forest_has_green_circles(symbology):
    for symbol in symbology["M005"]:
        if symbol["hovedtype"] in ("NA-VB01", "NA-VF01", "NA-VF02", "NA-VI01"):
            first = symbol["markers"][0]
            assert first["shape"] == "circle"
            hue = rgb_to_oklch(hex_to_rgb(first["colour"]))[2]
            assert 130 <= hue <= 160


def test_known_catalogue_gaps(symbology):
    gaps = {symbol["kode_id"] for symbols in catalogue_gaps(symbology).values() for symbol in symbols}
    assert gaps == {"TA01-M005-23", "TC02-M005-04"}
