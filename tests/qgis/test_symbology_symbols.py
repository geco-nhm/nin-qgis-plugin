# coding=utf-8

import unittest

from qgis.core import (
    QgsFillSymbol,
    QgsLinePatternFillSymbolLayer,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsPointPatternFillSymbolLayer,
    QgsSimpleFillSymbolLayer,
    QgsWkbTypes,
)

from nin_qgis_plugin.symbology_styles import load_unit_styles
from nin_qgis_plugin.symbology_symbols import MARKER_SHAPES, create_symbol

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class TestSymbologySymbols(unittest.TestCase):
    def test_every_style_gives_a_polygon_symbol(self):
        for mapping_scale in ('M005', 'M020', 'M050'):
            for kode_id, style in load_unit_styles(mapping_scale).items():
                symbol = create_symbol(style, QgsWkbTypes.PolygonGeometry)
                self.assertIsInstance(symbol, QgsFillSymbol, kode_id)
                expected_layers = 1 + bool(style['hatch']) + len(style['markers'])
                self.assertEqual(symbol.symbolLayerCount(), expected_layers, kode_id)

    def test_layers_of_a_full_symbol(self):
        style = load_unit_styles('M005')['TB01-M005-15']
        symbol = create_symbol(style, QgsWkbTypes.PolygonGeometry, 128)

        fill, hatch, markers = (symbol.symbolLayer(index) for index in range(3))
        self.assertIsInstance(fill, QgsSimpleFillSymbolLayer)
        self.assertEqual(fill.color().alpha(), 128)
        self.assertIsInstance(hatch, QgsLinePatternFillSymbolLayer)
        self.assertEqual(hatch.lineAngle(), 90)
        self.assertEqual(hatch.distance(), 4)
        # Only the fill is transparent
        self.assertEqual(hatch.subSymbol().color().alpha(), 255)
        self.assertIsInstance(markers, QgsPointPatternFillSymbolLayer)
        self.assertEqual(markers.distanceX(), 4)

    def test_points_and_lines_use_the_fill_colour(self):
        style = load_unit_styles('M005')['TB01-M005-15']

        point = create_symbol(style, QgsWkbTypes.PointGeometry)
        line = create_symbol(style, QgsWkbTypes.LineGeometry)

        self.assertIsInstance(point, QgsMarkerSymbol)
        self.assertIsInstance(line, QgsLineSymbol)
        self.assertEqual(point.color().name().upper(), style['fill_hex'])
        self.assertEqual(line.color().name().upper(), style['fill_hex'])

    def test_all_marker_shapes_in_the_tables_are_known(self):
        for mapping_scale in ('M005', 'M020', 'M050'):
            for style in load_unit_styles(mapping_scale).values():
                for marker in style['markers']:
                    self.assertIn(marker['shape'], MARKER_SHAPES)


if __name__ == '__main__':
    unittest.main()
