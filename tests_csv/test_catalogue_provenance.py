import configparser
from datetime import datetime, timezone
from pathlib import Path

from nin_qgis_plugin.catalogue_provenance import API_VERSION_FILE_CANDIDATES
from nin_qgis_plugin.catalogue_provenance import UNKNOWN_API_SHA
from nin_qgis_plugin.catalogue_provenance import build_catalogue_provenance
from nin_qgis_plugin.catalogue_provenance import read_nin_kode_api_sha
from nin_qgis_plugin.catalogue_provenance import read_plugin_version

REPO_ROOT = Path(__file__).parents[1]
PLUGIN_DIR = REPO_ROOT / 'nin_qgis_plugin'


def _metadata_version() -> str:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(PLUGIN_DIR / 'metadata.txt', encoding='utf-8')
    return parser.get('general', 'version').strip()


def test_read_plugin_version_from_metadata():
    assert read_plugin_version() == _metadata_version()


def test_read_nin_kode_api_sha_from_version_file():
    api_sha = read_nin_kode_api_sha()

    assert len(api_sha) == 40
    assert all(character in '0123456789abcdef' for character in api_sha)


def test_plugin_local_version_file_ships_and_matches_repo_root():
    # An installed plugin has no repository root above it, so the copy inside
    # the plugin folder is what users get; it must exist and be identical.
    plugin_copy = PLUGIN_DIR / 'nin_api_version_info.txt'
    root_file = REPO_ROOT / 'nin_api_version_info.txt'
    assert plugin_copy.is_file(), 'run generate_api_version_info.py to create the plugin copy'
    assert plugin_copy.read_text(encoding='utf-8') == root_file.read_text(encoding='utf-8')
    assert API_VERSION_FILE_CANDIDATES[0] == plugin_copy


def test_missing_version_file_gives_unknown_instead_of_crashing(tmp_path, monkeypatch):
    # Neither the plugin-local nor the repo-root copy exists: project creation
    # must still work, with the SHA recorded as 'unknown'
    from nin_qgis_plugin import catalogue_provenance

    monkeypatch.setattr(
        catalogue_provenance,
        'API_VERSION_FILE_CANDIDATES',
        (tmp_path / 'missing_a.txt', tmp_path / 'missing_b.txt'),
    )
    assert catalogue_provenance.read_nin_kode_api_sha() == UNKNOWN_API_SHA
    assert catalogue_provenance.build_catalogue_provenance()['nin_kode_api_sha'] == UNKNOWN_API_SHA


def test_build_catalogue_provenance_formats_generation_timestamp():
    provenance = build_catalogue_provenance(
        generated_at=datetime(2026, 8, 26, 12, 34, 56, tzinfo=timezone.utc)
    )

    assert provenance['plugin_version'] == _metadata_version()
    assert provenance['nin_kode_api_sha'] == read_nin_kode_api_sha()
    assert provenance['generated_at'] == '2026-08-26T12:34:56Z'
