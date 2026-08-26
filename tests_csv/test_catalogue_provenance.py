from datetime import datetime, timezone

from nin_qgis_plugin.catalogue_provenance import build_catalogue_provenance
from nin_qgis_plugin.catalogue_provenance import read_nin_kode_api_sha
from nin_qgis_plugin.catalogue_provenance import read_plugin_version


def test_read_plugin_version_from_metadata():
    assert read_plugin_version() == '0.4'


def test_read_nin_kode_api_sha_from_version_file():
    api_sha = read_nin_kode_api_sha()

    assert len(api_sha) == 40
    assert api_sha == 'b68054a64030efc093c9a75905f14fd58722905c'


def test_build_catalogue_provenance_formats_generation_timestamp():
    provenance = build_catalogue_provenance(
        generated_at=datetime(2026, 8, 26, 12, 34, 56, tzinfo=timezone.utc)
    )

    assert provenance == {
        'plugin_version': '0.4',
        'nin_kode_api_sha': 'b68054a64030efc093c9a75905f14fd58722905c',
        'generated_at': '2026-08-26T12:34:56Z',
    }