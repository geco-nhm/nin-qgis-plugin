'''
Compresses the user guide screenshots in user-guide/images.

    pip install Pillow
    python scripts/compress_guide_images.py            -> dry run, prints the plan
    python scripts/compress_guide_images.py --apply    -> rewrites images and .Rmd references

Large, photo-like PNGs (screenshots with aerial imagery) are converted to JPEG,
which is visually identical at a fraction of the size. Small PNGs and PNGs with
transparency stay PNG and are only re-saved losslessly. References in the
user-guide .Rmd files are updated to the new file names.
'''

import argparse
import io
import re
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
GUIDE_DIR = REPO_ROOT / 'user-guide'
IMAGE_DIR = GUIDE_DIR / 'images'

JPEG_QUALITY = 85
# Only convert PNGs above this size, and only if JPEG is at most half the size
MIN_BYTES_FOR_JPEG = 150_000
MAX_JPEG_RATIO = 0.5


def uses_transparency(image: Image.Image) -> bool:
    if image.mode not in ('RGBA', 'LA', 'PA'):
        return 'transparency' in image.info
    return image.getchannel('A').getextrema()[0] < 255


def encode(image: Image.Image, fmt: str, **options) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, fmt, optimize=True, **options)
    return buffer.getvalue()


def plan_image(path: Path):
    '''Returns (new_path, new_bytes), or None when the file should stay as it is.'''
    original_size = path.stat().st_size
    with Image.open(path) as image:
        image.load()
        transparent = uses_transparency(image)
        png_bytes = encode(image, 'PNG')
        if not transparent and original_size >= MIN_BYTES_FOR_JPEG:
            jpeg_bytes = encode(image.convert('RGB'), 'JPEG', quality=JPEG_QUALITY)
            if len(jpeg_bytes) <= MAX_JPEG_RATIO * min(original_size, len(png_bytes)):
                return path.with_suffix('.jpg'), jpeg_bytes
    if len(png_bytes) < original_size:
        return path, png_bytes
    return None


def update_references(renamed: dict, apply: bool) -> int:
    pattern = re.compile(r'images/([A-Za-z0-9_\-]+\.png)')
    changed = 0
    for rmd in sorted(GUIDE_DIR.glob('*.Rmd')):
        text = rmd.read_text(encoding='utf-8')
        new_text, count = pattern.subn(
            lambda m: f'images/{renamed.get(m.group(1), m.group(1))}', text
        )
        if new_text != text:
            changed += sum(1 for m in pattern.finditer(text) if m.group(1) in renamed)
            if apply:
                rmd.write_text(new_text, encoding='utf-8', newline='')
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument('--apply', action='store_true', help='write the changes')
    args = parser.parse_args()

    before = after = 0
    renamed = {}
    for path in sorted(IMAGE_DIR.glob('*.png')):
        size = path.stat().st_size
        before += size
        plan = plan_image(path)
        if plan is None:
            after += size
            continue
        new_path, data = plan
        if new_path != path and new_path.exists():
            raise SystemExit(f'{new_path.name} already exists; rename {path.name} first.')
        after += len(data)
        if new_path != path:
            renamed[path.name] = new_path.name
        if args.apply:
            new_path.write_bytes(data)
            if new_path != path:
                path.unlink()

    references = update_references(renamed, args.apply)
    verb = 'Wrote' if args.apply else 'Would write'
    print(f'{verb}: {len(renamed)} PNG -> JPEG, {references} .Rmd references updated')
    print(f'PNG total {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB')


if __name__ == '__main__':
    main()
