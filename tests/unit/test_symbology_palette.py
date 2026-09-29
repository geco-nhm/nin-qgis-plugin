"""Tests for the hovedtype fill colours of the NiN 3.0 symbology."""

import pytest

from symbology_tools.colour import (
    colour_difference, hex_to_rgb, oklch_to_rgb, rgb_to_hex, rgb_to_oklch, simulate_cvd,
)
from symbology_tools.palette import (
    GREEN_FAMILIES, all_fills, load_colour_families, load_hovedtype_colours,
    load_hovedtypegruppe_colours, load_mapped_hovedtyper,
    load_mapped_hovedtypegrupper, load_reserved_colours, validate_palette,
)


def test_hex_round_trip():
    assert hex_to_rgb("#8FC990") == (143, 201, 144)
    assert rgb_to_hex((143, 201, 144)) == "#8FC990"


def test_invalid_hex_is_rejected():
    with pytest.raises(ValueError):
        hex_to_rgb("#8FC9")


@pytest.mark.parametrize("rgb", [(143, 201, 144), (0, 0, 0), (255, 255, 255), (252, 231, 101)])
def test_oklch_round_trip(rgb):
    assert oklch_to_rgb(*rgb_to_oklch(rgb)) == rgb


def test_oklch_reference_values():
    # White and black are the end points of the lightness axis
    assert rgb_to_oklch((255, 255, 255))[0] == pytest.approx(1.0, abs=1e-3)
    assert rgb_to_oklch((0, 0, 0))[0] == pytest.approx(0.0, abs=1e-3)
    # Pure sRGB red, from the OKLab reference implementation
    lightness, chroma, hue = rgb_to_oklch((255, 0, 0))
    assert lightness == pytest.approx(0.628, abs=1e-3)
    assert chroma == pytest.approx(0.2577, abs=1e-3)
    assert hue == pytest.approx(29.23, abs=0.1)


def test_out_of_gamut_colour_is_rejected():
    with pytest.raises(ValueError):
        oklch_to_rgb(0.82, 0.30, 55)


def test_colour_difference():
    assert colour_difference((10, 20, 30), (10, 20, 30)) == 0
    assert colour_difference((0, 0, 0), (255, 255, 255)) == pytest.approx(1.0, abs=1e-3)


def test_cvd_simulation_keeps_greys_and_merges_red_and_green():
    assert simulate_cvd((128, 128, 128), "deuteranopia") == (128, 128, 128)
    red, green = (200, 80, 60), (110, 140, 60)
    assert colour_difference(
        simulate_cvd(red, "deuteranopia"), simulate_cvd(green, "deuteranopia")
    ) < colour_difference(red, green)


def test_palette_is_valid():
    assert validate_palette() == []


def test_every_mapped_hovedtype_has_a_colour():
    assert set(load_hovedtype_colours()) == set(load_mapped_hovedtyper())


def test_every_mapped_hovedtypegruppe_has_a_colour():
    assert set(load_hovedtypegruppe_colours()) == set(load_mapped_hovedtypegrupper())


def test_every_family_has_a_reserved_colour():
    reserved_families = {row["colour_family"] for row in load_reserved_colours()}
    assert reserved_families == set(load_colour_families())


def _oklch(fill_hex):
    return rgb_to_oklch(hex_to_rgb(fill_hex))


def test_established_colours():
    '''Forest is green, semi-natural meadow yellow, mire purple.'''

    colours = load_hovedtype_colours()

    def hue(kode_id):
        return _oklch(colours[kode_id]["fill_hex"])[2]

    assert 130 <= hue("NA-TB01") <= 160
    assert 90 <= hue("NA-TK01") <= 110
    assert 285 <= hue("NA-VA01") <= 315


def test_green_is_reserved_for_forest():
    for label, (family, fill_hex) in all_fills().items():
        if not family or family in GREEN_FAMILIES:
            continue
        _, chroma, hue = _oklch(fill_hex)
        assert not (110 < hue < 180 and chroma > 0.045), f"{label} {fill_hex} is green"


def test_forest_and_mountain_are_clearly_different():
    colours = load_hovedtype_colours()
    forest = hex_to_rgb(colours["NA-TB01"]["fill_hex"])
    for kode_id in ("NA-TA03", "NA-TA04"):
        assert colour_difference(forest, hex_to_rgb(colours[kode_id]["fill_hex"])) >= 0.08


def test_snowbed_is_nearly_white():
    lightness, chroma, _ = _oklch(load_hovedtype_colours()["NA-TC08"]["fill_hex"])
    assert lightness >= 0.90 and chroma <= 0.04


def test_jordvannsmyr_is_stronger_than_nedbormyr():
    '''The richer, more productive mire has the stronger colour.'''

    colours = load_hovedtype_colours()
    jordvannsmyr = _oklch(colours["NA-VA01"]["fill_hex"])
    nedborsmyr = _oklch(colours["NA-VC01"]["fill_hex"])
    assert jordvannsmyr[0] < nedborsmyr[0] and jordvannsmyr[1] > nedborsmyr[1]
