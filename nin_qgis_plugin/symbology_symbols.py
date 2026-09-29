"""
Turns the styles of 'symbology_styles.py' into QGIS symbols: a fill with
hatch and marker patterns for polygons, and a marker or line in the fill
colour for points and lines.
"""

from qgis.core import (
    Qgis,
    QgsFillSymbol,
    QgsLinePatternFillSymbolLayer,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPointPatternFillSymbolLayer,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
    QgsSymbol,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor

from .symbology_styles import hex_to_rgb

OUTLINE_WIDTH_MM = 0.26
MARKER_STROKE_WIDTH_MM = 0.25
# Stroke of white markers, which would otherwise not show on light fills
MARKER_STROKE_COLOUR = '#3A3A3A'

# Dash and gap lengths in millimetres
DASH_PATTERNS_MM = {
    'dashed': [2.4, 1.2],
    'dotted': [0.5, 1.1],
}

# Where in the repeating cell each marker pattern is placed, in parts of the
# cell, so that the patterns of one symbol do not cover each other
MARKER_OFFSETS = ((0.25, 0.25), (0.75, 0.75), (0.75, 0.25))

# Size of point markers and width of lines in the points and lines layers
POINT_SIZE_MM = 3.0
LINE_WIDTH_MM = 0.8

# (QGIS marker shape, rotation in degrees)
MARKER_SHAPES = {
    'circle': (Qgis.MarkerShape.Circle, 0),
    'ring': (Qgis.MarkerShape.Circle, 0),
    'square': (Qgis.MarkerShape.Square, 0),
    'triangle': (Qgis.MarkerShape.Triangle, 0),
    'diamond': (Qgis.MarkerShape.Diamond, 0),
    'star': (Qgis.MarkerShape.Star, 0),
    'cross': (Qgis.MarkerShape.Cross, 0),
    'cross2': (Qgis.MarkerShape.Cross2, 0),
    # The QGIS line marker is vertical and the arrow head points right
    'line': (Qgis.MarkerShape.Line, 90),
    'arrowhead': (Qgis.MarkerShape.ArrowHead, 0),
}

# Shapes that are drawn with a stroke only
STROKE_SHAPES = ('ring', 'cross', 'cross2', 'line', 'arrowhead')


def to_qcolor(hex_colour: str, alpha: int = 255) -> QColor:
    red, green, blue = hex_to_rgb(hex_colour)
    return QColor(red, green, blue, alpha)


def _hatch_layer(hatch: dict) -> QgsLinePatternFillSymbolLayer:
    line_layer = QgsSimpleLineSymbolLayer(to_qcolor(hatch['colour']), hatch['width_mm'])
    line_layer.setPenCapStyle(Qt.PenCapStyle.FlatCap)

    if hatch['style'] in DASH_PATTERNS_MM:
        line_layer.setUseCustomDashPattern(True)
        line_layer.setCustomDashVector(DASH_PATTERNS_MM[hatch['style']])

    line_symbol = QgsLineSymbol()
    line_symbol.changeSymbolLayer(0, line_layer)

    hatch_layer = QgsLinePatternFillSymbolLayer()
    # Degrees counter-clockwise from horizontal: 45 is '/'
    hatch_layer.setLineAngle(hatch['angle'])
    hatch_layer.setDistance(hatch['spacing_mm'])
    hatch_layer.setSubSymbol(line_symbol)

    return hatch_layer


def _marker_symbol_layer(marker: dict) -> QgsSimpleMarkerSymbolLayer:
    shape, rotation = MARKER_SHAPES[marker['shape']]
    colour = to_qcolor(marker['colour'])

    marker_layer = QgsSimpleMarkerSymbolLayer(shape, marker['size_mm'], rotation)

    if marker['shape'] in STROKE_SHAPES or not marker['filled']:
        marker_layer.setColor(QColor(0, 0, 0, 0))
        marker_layer.setStrokeColor(colour)
        marker_layer.setStrokeWidth(max(MARKER_STROKE_WIDTH_MM, marker['size_mm'] * 0.18))
    elif marker['colour'].upper() == '#FFFFFF':
        marker_layer.setColor(colour)
        marker_layer.setStrokeColor(to_qcolor(MARKER_STROKE_COLOUR))
        marker_layer.setStrokeWidth(MARKER_STROKE_WIDTH_MM)
    else:
        marker_layer.setColor(colour)
        marker_layer.setStrokeStyle(Qt.PenStyle.NoPen)

    return marker_layer


def _marker_pattern_layer(marker: dict, number: int) -> QgsPointPatternFillSymbolLayer:
    marker_symbol = QgsMarkerSymbol()
    marker_symbol.changeSymbolLayer(0, _marker_symbol_layer(marker))

    spacing = marker['spacing_mm']
    offset_x, offset_y = MARKER_OFFSETS[number]

    pattern_layer = QgsPointPatternFillSymbolLayer()
    pattern_layer.setDistanceX(spacing)
    pattern_layer.setDistanceY(spacing)
    pattern_layer.setOffsetX(spacing * offset_x)
    pattern_layer.setOffsetY(spacing * offset_y)
    pattern_layer.setSubSymbol(marker_symbol)

    return pattern_layer


def create_fill_symbol(style: dict, fill_alpha: int = 255) -> QgsFillSymbol:
    '''
    Returns the polygon symbol of a style. 'fill_alpha' (0-255) makes only
    the fill colour transparent, so that a background map shows through
    while hatch and markers stay clear.
    '''

    fill_layer = QgsSimpleFillSymbolLayer(
        to_qcolor(style['fill_hex'], fill_alpha),
        Qt.BrushStyle.SolidPattern,
        to_qcolor(style['outline_hex']),
        Qt.PenStyle.SolidLine,
        OUTLINE_WIDTH_MM,
    )

    symbol = QgsFillSymbol()
    symbol.changeSymbolLayer(0, fill_layer)

    if style['hatch']:
        symbol.appendSymbolLayer(_hatch_layer(style['hatch']))

    for number, marker in enumerate(style['markers']):
        symbol.appendSymbolLayer(_marker_pattern_layer(marker, number))

    return symbol


def create_marker_symbol(style: dict) -> QgsMarkerSymbol:
    '''Returns the point symbol of a style: a circle in the fill colour.'''

    marker_layer = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.Circle, POINT_SIZE_MM)
    marker_layer.setColor(to_qcolor(style['fill_hex']))
    marker_layer.setStrokeColor(to_qcolor(MARKER_STROKE_COLOUR))
    marker_layer.setStrokeWidth(MARKER_STROKE_WIDTH_MM)

    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, marker_layer)

    return symbol


def create_line_symbol(style: dict) -> QgsLineSymbol:
    '''Returns the line symbol of a style: a line in the fill colour.'''

    symbol = QgsLineSymbol()
    symbol.changeSymbolLayer(
        0, QgsSimpleLineSymbolLayer(to_qcolor(style['fill_hex']), LINE_WIDTH_MM)
    )

    return symbol


def create_symbol(style: dict, geometry_type, fill_alpha: int = 255) -> QgsSymbol:
    '''Returns the symbol of a style for a polygon, line or point layer.'''

    default_symbol = QgsSymbol.defaultSymbol(geometry_type)

    if isinstance(default_symbol, QgsMarkerSymbol):
        return create_marker_symbol(style)
    if isinstance(default_symbol, QgsLineSymbol):
        return create_line_symbol(style)
    return create_fill_symbol(style, fill_alpha)
