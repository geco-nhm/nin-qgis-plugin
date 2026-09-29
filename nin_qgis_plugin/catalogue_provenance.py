from __future__ import annotations

import configparser
import re
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_METADATA_PATH = Path(__file__).with_name('metadata.txt')
# The version file is generated into the plugin folder so it ships in the
# plugin zip (an installed plugin has no repository root above it).
API_VERSION_FILE_CANDIDATES = (
    Path(__file__).with_name('nin_api_version_info.txt'),
)
API_VERSION_FILE_PATH = API_VERSION_FILE_CANDIDATES[0]
UNKNOWN_API_SHA = 'unknown'
CATALOGUE_PROVENANCE_TABLE_NAME = 'catalogue_provenance'


def read_plugin_version(metadata_path: Path = PLUGIN_METADATA_PATH) -> str:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(metadata_path, encoding='utf-8')

    if not parser.has_section('general'):
        raise ValueError(f'Missing [general] section in {metadata_path}')

    plugin_version = parser.get('general', 'version', fallback='').strip()
    if not plugin_version:
        raise ValueError(f'Missing plugin version in {metadata_path}')

    return plugin_version


def read_nin_kode_api_sha(
    version_info_path: Path | None = None,
) -> str:
    '''
    Returns the nin-kode-api commit SHA recorded in nin_api_version_info.txt.
    Without an explicit path, the file in the plugin folder is used.
    When no file exists (should not happen for a
    packaged plugin, but must never break project creation), 'unknown' is
    returned so the provenance table still records the plugin version.
    '''

    if version_info_path is None:
        version_info_path = next(
            (candidate for candidate in API_VERSION_FILE_CANDIDATES if candidate.is_file()),
            None,
        )
        if version_info_path is None:
            return UNKNOWN_API_SHA

    for line in version_info_path.read_text(encoding='utf-8').splitlines():
        if 'latest commit:' not in line:
            continue

        api_sha = line.split('latest commit:', maxsplit=1)[-1].strip().lower()
        if not re.fullmatch(r'[0-9a-f]{40}', api_sha):
            raise ValueError(
                f'Invalid nin-kode-api SHA in {version_info_path}: {api_sha}'
            )
        return api_sha

    raise ValueError(f'No nin-kode-api SHA found in {version_info_path}')


def build_catalogue_provenance(
    generated_at: datetime | None = None,
) -> dict[str, str]:
    timestamp = generated_at or datetime.now(timezone.utc)
    timestamp_str = timestamp.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    return {
        'plugin_version': read_plugin_version(),
        'nin_kode_api_sha': read_nin_kode_api_sha(),
        'generated_at': timestamp_str,
    }