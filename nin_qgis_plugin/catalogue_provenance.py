from __future__ import annotations

import configparser
import re
from datetime import datetime, timezone
from pathlib import Path


PLUGIN_METADATA_PATH = Path(__file__).with_name('metadata.txt')
API_VERSION_FILE_PATH = Path(__file__).resolve().parents[1] / 'nin_api_version_info.txt'
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
    version_info_path: Path = API_VERSION_FILE_PATH,
) -> str:
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