"""
Prints the HTML overviews in docs/symbology to PDF with a Chromium browser
(Microsoft Edge or Google Chrome) in headless mode:

    python symbology_tools/print_overviews.py

    docs/symbology/<name>.html -> docs/symbology/<name>.pdf

The page size, orientation, margins and page numbers come from the @page
rules in each HTML file. Each page is printed with its own temporary
browser profile, because a headless browser that shares a profile with
another running instance can exit without printing. The browser writes
the PDF after the launcher has returned, so the script waits for it.
"""

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_PATH = REPO_ROOT / 'docs' / 'symbology'

PAGES = ('fargeoversikt', 'symboloversikt', 'symboloversikt_forslag_B')

BROWSER_CANDIDATES = (
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'msedge', 'google-chrome', 'chromium', 'chromium-browser',
)

TIMEOUT_SECONDS = 180


def find_browser() -> str:
    for candidate in BROWSER_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    raise SystemExit('No Edge or Chrome found; open the HTML files and print them from the browser.')


def wait_for_file(path: Path) -> bool:
    '''Waits until the file exists and has stopped growing.'''

    deadline = time.monotonic() + TIMEOUT_SECONDS
    last_size = -1
    while time.monotonic() < deadline:
        if path.is_file():
            size = path.stat().st_size
            if size > 0 and size == last_size:
                return True
            last_size = size
        time.sleep(1)
    return False


def main() -> int:
    '''Execute as standalone script'''

    browser = find_browser()
    failed = []

    for name in PAGES:
        html_path = DOCS_PATH / f'{name}.html'
        pdf_path = DOCS_PATH / f'{name}.pdf'
        pdf_path.unlink(missing_ok=True)

        with tempfile.TemporaryDirectory(prefix='nin_print_', ignore_cleanup_errors=True) as profile:
            subprocess.run([
                browser, '--headless=new', '--disable-gpu', f'--user-data-dir={profile}',
                '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}', html_path.as_uri(),
            ], check=False, capture_output=True)

            if wait_for_file(pdf_path):
                print(f'Wrote {pdf_path.relative_to(REPO_ROOT)}')
            else:
                failed.append(name)
                print(f'No PDF for {name} after {TIMEOUT_SECONDS} s')

    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
