"""
Colour maths for the symbology tools: sRGB <-> OKLab/OKLCH, colour
difference and colour vision deficiency simulation. Plain Python.

OKLab (Ottosson 2020) is used because equal distances in it look about
equally different to the eye, which hex or HSV distances do not.
"""

import math

# Linear-RGB matrices for simulating colour vision deficiency
# (Viénot, Brettel & Mollon 1999; tritanopia from Machado et al. 2009)
CVD_MATRICES = {
    'protanopia': (
        (0.11238, 0.88762, 0.00000),
        (0.11238, 0.88762, 0.00000),
        (0.00401, -0.00401, 1.00000),
    ),
    'deuteranopia': (
        (0.29275, 0.70725, 0.00000),
        (0.29275, 0.70725, 0.00000),
        (-0.02234, 0.02234, 1.00000),
    ),
    'tritanopia': (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}


def hex_to_rgb(hex_colour: str) -> tuple[int, int, int]:
    '''Converts '#RRGGBB' to a (red, green, blue) tuple, each 0-255.'''

    value = hex_colour.strip().lstrip('#')
    if len(value) != 6:
        raise ValueError(f"Expected '#RRGGBB', got: {hex_colour!r}")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    '''Converts a (red, green, blue) tuple, each 0-255, to '#RRGGBB'.'''

    return '#{:02X}{:02X}{:02X}'.format(*rgb)


def _srgb_to_linear(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(channel: float) -> float:
    if channel <= 0.0031308:
        return channel * 12.92
    return 1.055 * (channel ** (1 / 2.4)) - 0.055


def _cube_root(value: float) -> float:
    return math.copysign(abs(value) ** (1 / 3), value)


def _linear_rgb_to_oklab(red: float, green: float, blue: float) -> tuple[float, float, float]:
    long = _cube_root(0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue)
    medium = _cube_root(0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue)
    short = _cube_root(0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue)

    return (
        0.2104542553 * long + 0.7936177850 * medium - 0.0040720468 * short,
        1.9779984951 * long - 2.4285922050 * medium + 0.4505937099 * short,
        0.0259040371 * long + 0.7827717662 * medium - 0.8086757660 * short,
    )


def rgb_to_oklab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    '''Converts sRGB (0-255) to OKLab (L 0-1, a, b).'''

    return _linear_rgb_to_oklab(*(_srgb_to_linear(c / 255) for c in rgb))


def rgb_to_oklch(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    '''Converts sRGB (0-255) to OKLCH (lightness 0-1, chroma, hue in degrees).'''

    lightness, a, b = rgb_to_oklab(rgb)
    return (lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360)


def oklch_to_rgb(lightness: float, chroma: float, hue: float) -> tuple[int, int, int]:
    '''
    Converts OKLCH to sRGB (0-255). Raises ValueError when the colour
    cannot be shown in sRGB, so an out-of-gamut colour is never silently
    clipped into a different one.
    '''

    a = chroma * math.cos(math.radians(hue))
    b = chroma * math.sin(math.radians(hue))

    long = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3
    medium = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3
    short = (lightness - 0.0894841775 * a - 1.2914855480 * b) ** 3

    linear = (
        4.0767416621 * long - 3.3077115913 * medium + 0.2309699292 * short,
        -1.2684380046 * long + 2.6097574011 * medium - 0.3413193965 * short,
        -0.0041960863 * long - 0.7034186147 * medium + 1.7076147010 * short,
    )

    tolerance = 0.002
    if any(c < -tolerance or c > 1 + tolerance for c in linear):
        raise ValueError(f"OKLCH({lightness}, {chroma}, {hue}) is outside the sRGB gamut")

    return tuple(round(_linear_to_srgb(min(max(c, 0.0), 1.0)) * 255) for c in linear)


def colour_difference(rgb_1: tuple[int, int, int], rgb_2: tuple[int, int, int]) -> float:
    '''
    Returns the OKLab distance between two sRGB colours. About 0.02 is a
    just noticeable difference for colours side by side.
    '''

    return math.dist(rgb_to_oklab(rgb_1), rgb_to_oklab(rgb_2))


def simulate_cvd(rgb: tuple[int, int, int], deficiency: str) -> tuple[int, int, int]:
    '''
    Returns the colour as seen with a colour vision deficiency
    ('protanopia', 'deuteranopia' or 'tritanopia').
    '''

    matrix = CVD_MATRICES[deficiency]
    linear = [_srgb_to_linear(c / 255) for c in rgb]

    simulated = (
        sum(weight * channel for weight, channel in zip(row, linear))
        for row in matrix
    )

    return tuple(round(_linear_to_srgb(min(max(c, 0.0), 1.0)) * 255) for c in simulated)
