'''
Builds the plugin zip for upload to plugins.qgis.org (or a GitHub release).

    python build_plugin_zip.py            -> dist/nin_qgis_plugin-<version>.zip

The zip contains a single top-level folder 'nin_qgis_plugin/' with the
runtime files only (no tests, caches or developer tooling), and includes the
plugin-local copy of nin_api_version_info.txt. The version is read from
nin_qgis_plugin/metadata.txt. Plain Python, no dependencies.
'''

import configparser
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PLUGIN_DIR = REPO_ROOT / 'nin_qgis_plugin'
DIST_DIR = REPO_ROOT / 'dist'

# Files and folders (relative to the plugin folder) that must not ship
EXCLUDED_NAMES = {
    '__pycache__', 'test', 'scripts', 'help', 'Makefile', 'pb_tool.cfg',
    'plugin_upload.py', 'pylintrc', 'README.html', 'i18n',
}
EXCLUDED_SUFFIXES = {'.pyc', '.pyo', '.qm~', '.orig'}


def plugin_version() -> str:
    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(PLUGIN_DIR / 'metadata.txt', encoding='utf-8')
    return parser.get('general', 'version').strip()


def is_excluded(path: Path) -> bool:
    relative_parts = path.relative_to(PLUGIN_DIR).parts
    if any(part in EXCLUDED_NAMES for part in relative_parts):
        return True
    return path.suffix in EXCLUDED_SUFFIXES


def main() -> Path:
    version_file = REPO_ROOT / 'nin_api_version_info.txt'
    if version_file.is_file():
        shutil.copyfile(version_file, PLUGIN_DIR / 'nin_api_version_info.txt')
    if not (PLUGIN_DIR / 'nin_api_version_info.txt').is_file():
        raise SystemExit(
            'nin_api_version_info.txt is missing; run '
            'nin-qgis-handling/python/generate_api_version_info.py first.'
        )

    version = plugin_version()
    DIST_DIR.mkdir(exist_ok=True)
    zip_path = DIST_DIR / f'nin_qgis_plugin-{version}.zip'
    if zip_path.exists():
        zip_path.unlink()

    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PLUGIN_DIR.rglob('*')):
            if path.is_dir() or is_excluded(path):
                continue
            archive.write(path, Path('nin_qgis_plugin') / path.relative_to(PLUGIN_DIR))
            count += 1

    size_mb = zip_path.stat().st_size / 1e6
    print(f'Wrote {zip_path} ({count} files, {size_mb:.1f} MB) for version {version}')
    return zip_path


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
