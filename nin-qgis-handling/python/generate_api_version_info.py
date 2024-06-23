'''
Generates the file "nin_api_version_info.txt" in the project root.
As different table generation components are currently handled in
different files, this script needs to be executed manually after
tables were updated.
'''

from pathlib import Path
import subprocess
from datetime import datetime
import textwrap

VERSION_INFO_FILE_PATH = Path(__file__).parents[2] / 'nin_api_version_info.txt'


def main() -> None:
    '''Run as standalone script.'''

    # If file exists, delete
    if VERSION_INFO_FILE_PATH.is_file():
        VERSION_INFO_FILE_PATH.unlink()

    # Retrieve current NiN Kode API github HEAD SHA
    kode_api_git_sha = str(subprocess.check_output(
        args=[
            'git',
            'ls-remote',
            'https://github.com/Artsdatabanken/nin-kode-api.git',
            'HEAD'
        ],
        text=True,
        encoding='utf-8',
    ))

    # Open version text file
    with open(VERSION_INFO_FILE_PATH, mode="w", encoding="utf-8") as version_file:
        version_file.write(textwrap.dedent(
            f"""\
            NinKode API version information, retrieved when the NiN QGIS plugin csv tables were created.
            Note: this file is manually created by running
            './nin-qgis-handling/python/generate_api_version_info.py'.

            ----

            nin-kode-api (https://github.com/Artsdatabanken/nin-kode-api.git) latest commit: {kode_api_git_sha.strip().split()[0]}
            date: {datetime.now().strftime('%Y/%m/%d, %H:%M:%S')}"""
        ))

    print(f"Successfully created {VERSION_INFO_FILE_PATH}!")


if __name__ == "__main__":
    main()
