"""
Renders the symbology colours to a standalone HTML overview (Norwegian):

    python symbology_tools/render_palette_overview.py
    -> docs/symbology/fargeoversikt.html

The page follows the type hierarchy: hovedtypegrupper first, then the
hovedtyper of each group. It has no external dependencies, so it can be
opened from disk, printed or sent by e-mail.
"""

import html
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from symbology_tools.colour import hex_to_rgb, rgb_to_oklch  # noqa: E402
from symbology_tools.palette import (  # noqa: E402
    DOMINANT_HOVEDTYPER, INCLUDED_HOVEDTYPEGRUPPER, MAPPING_SCALES, OUTLINE_HEX,
    REPO_ROOT, load_colour_families, load_hovedtype_colours,
    load_hovedtypegruppe_colours, load_mapped_hovedtyper,
    load_mapped_hovedtypegrupper, load_reserved_colours, validate_palette,
)

OUTPUT_PATH = REPO_ROOT / 'docs' / 'symbology' / 'fargeoversikt.html'

SCALE_LABELS = {
    'M005': '1:5 000',
    'M020': '1:20 000',
    'M050': '1:50 000',
}

# Label colour on top of a swatch switches to white below this lightness
DARK_FILL_LIGHTNESS = 0.62

PAGE_STYLE = '''
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 32px 16px 64px; background: #F6F5F1; color: #1F2421;
    font: 15px/1.5 "Segoe UI", system-ui, -apple-system, sans-serif;
  }
  main { max-width: 1080px; margin: 0 auto; }
  h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; }
  h2 { font-size: 20px; margin: 48px 0 4px; }
  h3 { font-size: 16px; margin: 0; }
  p { margin: 0 0 12px; max-width: 72ch; }
  .lead { color: #4A524D; }
  .mosaic { display: flex; flex-wrap: wrap; margin: 16px 0 0; background: #8A8F8B; padding: 1px; gap: 0; }
  .mosaic span {
    flex: 1 0 56px; height: 44px; font-size: 11px; font-weight: 600;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid ''' + OUTLINE_HEX + ''';
  }
  .card { margin-top: 28px; padding: 16px; background: #fff; border: 1px solid #DDDBD2; border-radius: 6px; }
  .card-head { display: flex; flex-wrap: wrap; gap: 4px 16px; align-items: baseline; }
  .tone { color: #4A524D; font-size: 13px; }
  .reason { color: #4A524D; font-size: 13px; margin: 2px 0 12px; }
  .table-wrap { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; min-width: 760px; font-size: 14px; table-layout: fixed; }
  th:nth-child(1) { width: 96px; }
  th:nth-child(2) { width: 64px; }
  th:nth-child(4) { width: 84px; }
  th:nth-child(5) { width: 120px; }
  th:nth-child(n+6) { width: 84px; }
  th { text-align: left; font-weight: 600; font-size: 12px; color: #4A524D; padding: 4px 12px 4px 0; border-bottom: 1px solid #DDDBD2; }
  td { padding: 5px 12px 5px 0; border-bottom: 1px solid #EEEDE7; vertical-align: middle; }
  tr:last-child td { border-bottom: 0; }
  .swatch { width: 72px; height: 28px; border-radius: 3px; box-shadow: 0 0 0 1px #C9C7BE; }
  .code { font-weight: 600; white-space: nowrap; }
  .tag { font-size: 11px; font-weight: 600; color: #4A524D; border: 1px solid #C9C7BE; border-radius: 3px; padding: 0 5px; margin-left: 8px; white-space: nowrap; }
  .hex, td.num { font-family: Consolas, "Cascadia Mono", monospace; font-size: 13px; white-space: nowrap; }
  .num { text-align: right; }
  .reserved { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; margin-top: 12px; font-size: 13px; color: #4A524D; }
  .reserved div { display: flex; gap: 8px; align-items: center; }
  .reserved .swatch { width: 40px; height: 20px; }
  @media print { body { background: #fff; } .card { break-inside: avoid; } }
'''


def short_code(kode_id: str) -> str:
    '''Returns the code without the 'NA-' prefix, e.g. 'TB01'.'''

    return kode_id.removeprefix('NA-')


def text_colour(fill_hex: str) -> str:
    lightness = rgb_to_oklch(hex_to_rgb(fill_hex))[0]
    return '#FFFFFF' if lightness < DARK_FILL_LIGHTNESS else '#1F2421'


def rgb_text(fill_hex: str) -> str:
    return ', '.join(str(channel) for channel in hex_to_rgb(fill_hex))


def scale_headers() -> str:
    return ''.join(f'<th class="num">{SCALE_LABELS[scale]}</th>' for scale in MAPPING_SCALES)


def count_cells(unit_counts: dict) -> str:
    return ''.join(f'<td class="num">{unit_counts[scale]}</td>' for scale in MAPPING_SCALES)


def render_hovedtypegrupper() -> str:
    gruppe_colours = load_hovedtypegruppe_colours()
    mapped_grupper = load_mapped_hovedtypegrupper()

    rows = []
    for kode_id, row in gruppe_colours.items():
        info = mapped_grupper[kode_id]
        tag = '' if kode_id in INCLUDED_HOVEDTYPEGRUPPER else '<span class="tag">kun gruppefarge</span>'
        rows.append(
            '<tr>'
            f'<td><div class="swatch" style="background:{row["fill_hex"]}"></div></td>'
            f'<td class="code">{short_code(kode_id)}</td>'
            f'<td>{html.escape(row["navn"])} · {len(info["hovedtyper"])} hovedtyper{tag}</td>'
            f'<td class="hex">{row["fill_hex"]}</td>'
            f'<td class="hex">{rgb_text(row["fill_hex"])}</td>'
            f'{count_cells(info["unit_counts"])}'
            '</tr>'
        )

    return (
        '<h2>Hovedtypegrupper</h2>'
        '<p class="lead">Hver hovedtypegruppe har en grunnfarge. For fastmark og '
        'våtmark har hver hovedtype sin egen farge. De andre gruppene tegnes '
        'foreløpig med grunnfargen for alle kartleggingsenheter.</p>'
        '<section class="card"><div class="table-wrap"><table>'
        '<tr><th>Farge</th><th>Kode</th><th>Hovedtypegruppe</th><th>Hex</th><th>RGB</th>'
        f'{scale_headers()}</tr>'
        f'{"".join(rows)}'
        '</table></div></section>'
    )


def render_mosaic(colours: dict) -> str:
    cells = [
        f'<span style="background:{row["fill_hex"]};color:{text_colour(row["fill_hex"])}" '
        f'title="{html.escape(kode_id + " " + row["navn"])}">{short_code(kode_id)}</span>'
        for kode_id, row in colours.items()
    ]
    return '<div class="mosaic">' + ''.join(cells) + '</div>'


def render_family(family_key: str, family: dict, members: list, mapped_hovedtyper: dict) -> str:
    rows = []
    for kode_id, row in members:
        tag = '<span class="tag">arealmessig dominerende</span>' if kode_id in DOMINANT_HOVEDTYPER else ''
        rows.append(
            '<tr>'
            f'<td><div class="swatch" style="background:{row["fill_hex"]}"></div></td>'
            f'<td class="code">{short_code(kode_id)}</td>'
            f'<td>{html.escape(row["navn"])}{tag}</td>'
            f'<td class="hex">{row["fill_hex"]}</td>'
            f'<td class="hex">{rgb_text(row["fill_hex"])}</td>'
            f'{count_cells(mapped_hovedtyper[kode_id]["unit_counts"])}'
            '</tr>'
        )

    reserved = ''.join(
        f'<div><span class="swatch" style="background:{row["fill_hex"]}"></span>'
        f'<span class="hex">{row["fill_hex"]}</span></div>'
        for row in load_reserved_colours() if row['colour_family'] == family_key
    )

    return (
        '<section class="card">'
        '<div class="card-head">'
        f'<h3>{html.escape(family["navn"])}</h3>'
        f'<span class="tone">{html.escape(family["fargetone"])} · {len(members)} hovedtyper</span>'
        '</div>'
        f'<p class="reason">{html.escape(family["begrunnelse"])}.</p>'
        '<div class="table-wrap"><table>'
        '<tr><th>Farge</th><th>Kode</th><th>Hovedtype</th><th>Hex</th><th>RGB</th>'
        f'{scale_headers()}</tr>'
        f'{"".join(rows)}'
        '</table></div>'
        f'<div class="reserved">Holdt av til nye hovedtyper: {reserved}</div>'
        '</section>'
    )


def render_page() -> str:
    families = load_colour_families()
    colours = load_hovedtype_colours()
    gruppe_colours = load_hovedtypegruppe_colours()
    mapped_hovedtyper = load_mapped_hovedtyper()

    sections = [render_hovedtypegrupper()]

    for hovedtypegruppe in INCLUDED_HOVEDTYPEGRUPPER:
        gruppe_name = gruppe_colours[hovedtypegruppe]['navn']
        hovedtype_colours = {
            kode_id: row for kode_id, row in colours.items()
            if mapped_hovedtyper[kode_id]['hovedtypegruppe'] == hovedtypegruppe
        }
        totals = ' · '.join(
            f'{sum(mapped_hovedtyper[kode_id]["unit_counts"][scale] for kode_id in hovedtype_colours)} '
            f'enheter i {SCALE_LABELS[scale]}'
            for scale in MAPPING_SCALES
        )

        sections.append(
            f'<h2>{short_code(hovedtypegruppe)} {html.escape(gruppe_name)}</h2>'
            f'<p class="lead">{len(hovedtype_colours)} hovedtyper · {totals}</p>'
        )
        sections.append(render_mosaic(hovedtype_colours))

        for family_key, family in families.items():
            members = [
                (kode_id, row) for kode_id, row in hovedtype_colours.items()
                if row['colour_family'] == family_key
            ]
            if members:
                sections.append(render_family(family_key, family, members, mapped_hovedtyper))

    return (
        '<!DOCTYPE html>\n<html lang="nb">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>NiN 3.0 fargeoversikt</title>\n'
        f'<style>{PAGE_STYLE}</style>\n</head>\n<body>\n<main>\n'
        '<h1>NiN 3.0 kartografi: farger</h1>\n'
        '<p class="lead">Hver hovedtype har én fyllfarge, og den er lik i alle tre '
        'målestokker. Beslektede hovedtyper har farger fra samme fargefamilie. '
        'Klar grønn er forbeholdt skogsmark. Kartleggingsenhetene innen en '
        'hovedtype skilles med skravur, symboler og påskrift, ikke med farge.</p>\n'
        '<p class="lead">Alle figurer har tynt, hvitt omriss. Tallene til høyre '
        'viser antall kartleggingsenheter per målestokk.</p>\n'
        f'{"".join(sections)}\n'
        '</main>\n</body>\n</html>\n'
    )


def main() -> int:
    '''Execute as standalone script'''

    problems = validate_palette()
    if problems:
        print("The palette is not valid, nothing was rendered:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_page(), encoding='utf-8', newline='\n')
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
