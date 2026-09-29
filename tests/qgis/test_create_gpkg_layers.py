# coding=utf-8
"""Tests that create_gpkg writes the classified mapping layers (polygons, points, lines)."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from nin_qgis_plugin.create_gpkg import main as create_gpkg
from nin_qgis_plugin.create_gpkg import HELPER_POINT_LAYER_NAME, mapping_layer_names

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()

SCALE = 'M005'
LAYER_NAMES = mapping_layer_names(SCALE)

COMMON_FIELDS = {
    'fid', 'regdato', 'type', 'hovedtypegruppe', 'hovedtype',
    'grunntype_or_klenhet', 'variabler', 'kode_id_label', 'photo',
}


class TestCreateGpkgLayers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.gpkg_path = Path(cls.tmp_dir.name) / 'nin_test.gpkg'
        create_gpkg(
            selected_mapping_scale=SCALE,
            gpkg_path=cls.gpkg_path,
            proj_crs='EPSG:25833',
        )

    @classmethod
    def tearDownClass(cls):
        cls.tmp_dir.cleanup()

    def _columns(self, conn, table_name):
        return {
            row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")')
        }

    def test_layer_names_carry_the_mapping_scale_suffix(self):
        self.assertEqual(LAYER_NAMES['nin_polygons'], 'nin_polygons_M005')
        self.assertEqual(LAYER_NAMES['nin_points'], 'nin_points_M005')
        self.assertEqual(LAYER_NAMES['nin_lines'], 'nin_lines_M005')
        self.assertEqual(
            mapping_layer_names('grunntyper')['nin_polygons'], 'nin_polygons_grunntyper'
        )

    def test_mapping_layers_have_expected_geometry(self):
        self.assertTrue(self.gpkg_path.exists())

        with sqlite3.connect(self.gpkg_path) as conn:
            geometry_types = dict(conn.execute(
                'SELECT table_name, geometry_type_name FROM gpkg_geometry_columns'
            ).fetchall())

        self.assertEqual(geometry_types[LAYER_NAMES['nin_polygons']], 'MULTIPOLYGON')
        self.assertEqual(geometry_types[LAYER_NAMES['nin_points']], 'POINT')
        self.assertEqual(geometry_types[LAYER_NAMES['nin_lines']], 'LINESTRING')
        self.assertIn(HELPER_POINT_LAYER_NAME, geometry_types)
        # No unsuffixed mapping layers left behind
        self.assertNotIn('nin_polygons', geometry_types)

    def test_point_and_line_layers_have_single_type_fields(self):
        with sqlite3.connect(self.gpkg_path) as conn:
            polygon_columns = self._columns(conn, LAYER_NAMES['nin_polygons'])
            point_columns = self._columns(conn, LAYER_NAMES['nin_points'])
            line_columns = self._columns(conn, LAYER_NAMES['nin_lines'])

        for columns in (polygon_columns, point_columns, line_columns):
            self.assertTrue(COMMON_FIELDS <= columns, columns)

        # Points and lines are single-type: no mosaic / Type 2/3 fields
        for column in ('area', 'andel_kle_1', 'sammensatt', 'mosaikk',
                       'hovedtypegruppe_2', 'grunntype_or_klenhet_3'):
            self.assertIn(column, polygon_columns)
            self.assertNotIn(column, point_columns)
            self.assertNotIn(column, line_columns)

        self.assertIn('kommentar', point_columns)
        self.assertIn('kommentar', line_columns)
        self.assertNotIn('kommentar', polygon_columns)

        # Only lines get a length field
        self.assertIn('lengde', line_columns)
        self.assertNotIn('lengde', point_columns)
        self.assertNotIn('lengde', polygon_columns)


if __name__ == '__main__':
    unittest.main()
