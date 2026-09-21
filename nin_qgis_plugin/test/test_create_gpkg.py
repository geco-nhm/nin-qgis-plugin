# coding=utf-8

import re
import sqlite3
import tempfile
import unittest
from pathlib import Path

from nin_qgis_plugin.catalogue_provenance import read_nin_kode_api_sha
from nin_qgis_plugin.catalogue_provenance import read_plugin_version
from nin_qgis_plugin.create_gpkg import main as create_gpkg

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class TestCreateGpkg(unittest.TestCase):
    def test_creates_catalogue_provenance_table(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
            gpkg_path = Path(tmp_dir) / 'nin_catalogue.gpkg'

            create_gpkg(
                selected_mapping_scale='M005',
                gpkg_path=gpkg_path,
                proj_crs='EPSG:25833',
            )

            self.assertTrue(gpkg_path.exists())

            with sqlite3.connect(gpkg_path) as conn:
                table_names = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }
                self.assertIn('catalogue_provenance', table_names)

                columns = [
                    row[1]
                    for row in conn.execute(
                        'PRAGMA table_info(catalogue_provenance)'
                    ).fetchall()
                ]
                self.assertEqual(
                    columns,
                    ['fid', 'plugin_version', 'nin_kode_api_sha', 'generated_at'],
                )

                rows = conn.execute(
                    'SELECT plugin_version, nin_kode_api_sha, generated_at '
                    'FROM catalogue_provenance'
                ).fetchall()

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0], read_plugin_version())
            self.assertEqual(rows[0][1], read_nin_kode_api_sha())
            self.assertRegex(
                rows[0][2],
                re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'),
            )


if __name__ == '__main__':
    unittest.main()