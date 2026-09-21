"""
Deterministic symbology colours for NiN mapping units.

Every mapping unit ('kode_id') gets a colour derived from a hash of its code,
so the same unit has the same colour in every project, on every computer and
across catalogue regenerations (issues #62 and #75). No QGIS imports here so
the function can be unit-tested with plain Python.
"""

import colorsys
import hashlib

# Saturation and value ranges keep colours visible on top of topographic
# background maps: no greys, no near-black, no near-white.
_MIN_SATURATION = 0.55
_MAX_SATURATION = 0.90
_MIN_VALUE = 0.60
_MAX_VALUE = 0.95


def kode_id_color(kode_id: str) -> tuple[int, int, int]:
    '''
    Returns a deterministic (red, green, blue) tuple, each 0-255, for a
    mapping unit code such as 'TK01-M005-19'.

    The hue comes from the first two bytes of the SHA-1 of the code,
    saturation and value from the next two, so codes that differ only in
    the last digit still get clearly different colours.
    '''

    digest = hashlib.sha1(str(kode_id).encode('utf-8')).digest()

    hue = int.from_bytes(digest[0:2], 'big') / 65535.0
    saturation = _MIN_SATURATION + (digest[2] / 255.0) * (_MAX_SATURATION - _MIN_SATURATION)
    value = _MIN_VALUE + (digest[3] / 255.0) * (_MAX_VALUE - _MIN_VALUE)

    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)

    return (round(red * 255), round(green * 255), round(blue * 255))
