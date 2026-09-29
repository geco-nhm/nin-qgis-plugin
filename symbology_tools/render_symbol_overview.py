"""
Renders the symbols of all mapping units to a standalone HTML overview
(Norwegian):

    python symbology_tools/render_symbol_overview.py
    -> docs/symbology/symboloversikt.html

Each hovedtype is shown as a table with one column per mapping scale. A
unit stands to the right of the unit it belongs to at the coarser scale,
so the aggregation between scales can be read directly.

Symbols are drawn as inline SVG from the same tables the QGIS styles are
made from. No external dependencies.
"""

import html
import sys
from math import cos, pi, sin
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from symbology_tools.palette import (  # noqa: E402
    INCLUDED_HOVEDTYPEGRUPPER, MAPPING_SCALES, REPO_ROOT, load_hovedtype_colours,
    load_hovedtypegruppe_colours, load_mapped_hovedtyper,
)
from symbology_tools.patterns import (  # noqa: E402
    ANGLE_INTERMEDIAER, ANGLE_KALKFATTIG, ANGLE_KALKRIK, ANGLE_NEUTRAL,
    DEFAULT_HATCH_COLOUR, DRYNESS_COLOURS, HATCH_SPACING_MM, HATCH_WIDTH_MM,
    MARKER_SPACING_MM, MARKER_STROKE_WIDTH_MM, STROKE_SHAPES, build_symbology,
    load_hovedtype_patterns, load_variable_rules, validate_symbology,
)
from symbology_tools.render_palette_overview import SCALE_LABELS, short_code  # noqa: E402

OUTPUT_PATH = REPO_ROOT / 'docs' / 'symbology' / 'symboloversikt.html'

# Screen pixels per millimetre in the overview. Symbols are drawn larger
# than in print so that they can be studied.
PIXELS_PER_MM = 4.0
SWATCH_WIDTH_MM = 26
SWATCH_HEIGHT_MM = 12

# Finest scale last: the table reads from coarse (left) to fine (right)
COLUMN_SCALES = tuple(reversed(MAPPING_SCALES))

DASH_PATTERNS_MM = {
    'solid': '',
    'dashed': '2.4 1.2',
    'dotted': '0.5 1.1',
}

# Where in the repeating cell each marker layer is placed, in parts of the cell
MARKER_OFFSETS = ((0.25, 0.25), (0.75, 0.75), (0.75, 0.25))

MARKER_STROKE_COLOUR = '#3A3A3A'

PAGE_STYLE = '''
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 32px 16px 64px; background: #F6F5F1; color: #1F2421;
    font: 14px/1.45 "Segoe UI", system-ui, -apple-system, sans-serif;
  }
  main { max-width: 1280px; margin: 0 auto; }
  h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; }
  h2 { font-size: 20px; margin: 48px 0 4px; }
  h3 { font-size: 16px; margin: 0; }
  p { margin: 0 0 12px; max-width: 76ch; }
  .lead { color: #4A524D; }
  .card { margin-top: 20px; padding: 16px; background: #fff; border: 1px solid #DDDBD2; border-radius: 6px; }
  .card-head { display: flex; gap: 12px; align-items: center; margin-bottom: 10px; }
  .chip { width: 40px; height: 22px; border-radius: 3px; box-shadow: 0 0 0 1px #C9C7BE; flex: none; }
  .note { color: #4A524D; font-size: 13px; margin: 0 0 10px; }
  .table-wrap { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; min-width: 900px; table-layout: fixed; }
  th { text-align: left; font-weight: 600; font-size: 12px; color: #4A524D; padding: 4px 8px; border-bottom: 1px solid #DDDBD2; }
  td { padding: 6px 8px; vertical-align: top; border-bottom: 1px solid #EEEDE7; border-left: 1px solid #EEEDE7; }
  td:first-child { border-left: 0; }
  .unit { display: flex; gap: 10px; align-items: flex-start; }
  .unit svg { flex: none; border-radius: 2px; box-shadow: 0 0 0 1px #C9C7BE; }
  .code { font-weight: 600; font-size: 12px; white-space: nowrap; }
  .name { font-size: 12.5px; line-height: 1.3; }
  .why { font-size: 11.5px; line-height: 1.3; color: #5A625D; margin-top: 2px; }
  .legend { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px 20px; }
  .legend .unit { align-items: center; }
  .legend .code { white-space: normal; }
  .missing { color: #8A8F8B; font-size: 12px; }
  @media print { body { background: #fff; } .card { break-inside: avoid; } }
'''


def px(millimetres: float) -> str:
    return f'{millimetres * PIXELS_PER_MM:.2f}'.rstrip('0').rstrip('.')


def marker_svg(marker: dict, centre_x: float, centre_y: float) -> str:
    '''Returns the SVG of one marker centred on a point (millimetres).'''

    shape, size, colour = marker['shape'], marker['size_mm'], marker['colour']
    half = size / 2
    stroke_width = px(MARKER_STROKE_WIDTH_MM)

    if shape in STROKE_SHAPES or not marker['filled']:
        paint = f'fill="none" stroke="{colour}" stroke-width="{px(max(MARKER_STROKE_WIDTH_MM, size * 0.18))}"'
    elif colour.upper() == '#FFFFFF':
        paint = f'fill="{colour}" stroke="{MARKER_STROKE_COLOUR}" stroke-width="{stroke_width}"'
    else:
        paint = f'fill="{colour}"'

    def points(*pairs) -> str:
        return ' '.join(f'{px(centre_x + x)},{px(centre_y + y)}' for x, y in pairs)

    if shape in ('circle', 'ring'):
        return f'<circle cx="{px(centre_x)}" cy="{px(centre_y)}" r="{px(half)}" {paint}/>'
    if shape == 'square':
        return (
            f'<rect x="{px(centre_x - half)}" y="{px(centre_y - half)}" '
            f'width="{px(size)}" height="{px(size)}" {paint}/>'
        )
    if shape == 'triangle':
        return f'<polygon points="{points((0, -half), (half, half), (-half, half))}" {paint}/>'
    if shape == 'diamond':
        return f'<polygon points="{points((0, -half), (half, 0), (0, half), (-half, 0))}" {paint}/>'
    if shape == 'star':
        star = []
        for index in range(10):
            radius = half if index % 2 == 0 else half * 0.42
            # Points of a five-pointed star, first point up
            angle = -pi / 2 + index * pi / 5
            star.append((radius * cos(angle), radius * sin(angle)))
        return f'<polygon points="{points(*star)}" {paint}/>'
    if shape == 'arrowhead':
        return f'<polyline points="{points((-half, -half), (half, 0), (-half, half))}" {paint} stroke-linejoin="round"/>'
    if shape == 'line':
        return f'<polyline points="{points((-half, 0), (half, 0))}" {paint}/>'
    if shape == 'cross':
        return (
            f'<path d="M{px(centre_x - half)} {px(centre_y)}H{px(centre_x + half)}'
            f'M{px(centre_x)} {px(centre_y - half)}V{px(centre_y + half)}" {paint}/>'
        )
    if shape == 'cross2':
        return (
            f'<path d="M{px(centre_x - half)} {px(centre_y - half)}L{px(centre_x + half)} {px(centre_y + half)}'
            f'M{px(centre_x - half)} {px(centre_y + half)}L{px(centre_x + half)} {px(centre_y - half)}" {paint}/>'
        )

    raise ValueError(f"Unknown marker shape: {shape}")


def symbol_svg(symbol: dict, element_id: str) -> str:
    '''Returns the symbol drawn as a swatch.'''

    width, height = px(SWATCH_WIDTH_MM), px(SWATCH_HEIGHT_MM)
    definitions, layers = [], []

    if symbol['hatch_angle'] is not None:
        spacing = px(HATCH_SPACING_MM)
        dash = DASH_PATTERNS_MM[symbol['hatch_style']]
        dash_attribute = ''
        if dash:
            dash_attribute = ' stroke-dasharray="' + ' '.join(px(float(part)) for part in dash.split()) + '"'
        # SVG rotates clockwise, the angles are counter-clockwise
        definitions.append(
            f'<pattern id="{element_id}h" width="{px(12 * HATCH_SPACING_MM)}" height="{spacing}" '
            f'patternUnits="userSpaceOnUse" patternTransform="rotate({-symbol["hatch_angle"]})">'
            f'<line x1="0" y1="{px(HATCH_SPACING_MM / 2)}" x2="{px(12 * HATCH_SPACING_MM)}" '
            f'y2="{px(HATCH_SPACING_MM / 2)}" stroke="{symbol["hatch_colour"]}" '
            f'stroke-width="{px(HATCH_WIDTH_MM)}"{dash_attribute}/></pattern>'
        )
        layers.append(f'<rect width="{width}" height="{height}" fill="url(#{element_id}h)"/>')

    for number, marker in enumerate(symbol['markers']):
        offset_x, offset_y = MARKER_OFFSETS[number]
        definitions.append(
            f'<pattern id="{element_id}m{number}" width="{px(MARKER_SPACING_MM)}" '
            f'height="{px(MARKER_SPACING_MM)}" patternUnits="userSpaceOnUse">'
            f'{marker_svg(marker, MARKER_SPACING_MM * offset_x, MARKER_SPACING_MM * offset_y)}</pattern>'
        )
        layers.append(f'<rect width="{width}" height="{height}" fill="url(#{element_id}m{number})"/>')

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{html.escape(symbol["kode_id"])}">'
        f'<defs>{"".join(definitions)}</defs>'
        f'<rect width="{width}" height="{height}" fill="{symbol["fill_hex"]}"/>'
        f'{"".join(layers)}</svg>'
    )


def unit_cell(symbol: dict, rowspan: int, element_id: str) -> str:
    explanation = '. '.join(symbol['explanation'])
    why = f'<div class="why">{html.escape(explanation)}</div>' if explanation else ''
    # 'TB01-M005-03' is shown as 'TB01-03'; the column tells the scale
    code = f"{symbol['kode_id'].split('-')[0]}-{symbol['kode_id'].split('-')[-1]}"

    return (
        f'<td rowspan="{rowspan}"><div class="unit">{symbol_svg(symbol, element_id)}'
        f'<div><div class="code">{html.escape(code)}</div>'
        f'<div class="name">{html.escape(symbol["navn"])}</div>{why}</div></div></td>'
    )


def empty_cell(rowspan: int) -> str:
    return f'<td rowspan="{rowspan}"><span class="missing">Ingen enhet i katalogen</span></td>'


def build_tree(symbols_by_scale: dict) -> list:
    '''
    Returns the units of one hovedtype as a tree from coarse to fine:
    [(coarse symbol or None, [(middle symbol or None, [fine symbols])])].
    '''

    coarse_scale, middle_scale, fine_scale = COLUMN_SCALES

    fine_by_parent, middle_by_parent = {}, {}
    for symbol in symbols_by_scale[fine_scale]:
        fine_by_parent.setdefault(symbol['parent_kode_id'], []).append(symbol)
    for symbol in symbols_by_scale[middle_scale]:
        middle_by_parent.setdefault(symbol['parent_kode_id'], []).append(symbol)

    tree = [
        (coarse, [
            (middle, fine_by_parent.pop(middle['kode_id'], []))
            for middle in middle_by_parent.pop(coarse['kode_id'], [])
        ])
        for coarse in symbols_by_scale[coarse_scale]
    ]

    # Units that the catalogue does not link to a coarser unit
    orphans = [
        (middle, fine_by_parent.pop(middle['kode_id'], []))
        for middles in middle_by_parent.values() for middle in middles
    ]
    orphans += [(None, fines) for fines in fine_by_parent.values()]
    if orphans:
        tree.append((None, orphans))

    return tree


def render_hovedtype(kode_id: str, colour: dict, symbols_by_scale: dict, emblem: dict, counter: list) -> str:
    rows = []

    def next_id() -> str:
        counter[0] += 1
        return f's{counter[0]}'

    for coarse, middles in build_tree(symbols_by_scale):
        coarse_rows = sum(max(len(fines), 1) for _, fines in middles) or 1
        coarse_cell = unit_cell(coarse, coarse_rows, next_id()) if coarse else empty_cell(coarse_rows)

        if not middles:
            rows.append(f'<tr>{coarse_cell}{empty_cell(1)}{empty_cell(1)}</tr>')
            continue

        for middle, fines in middles:
            middle_rows = max(len(fines), 1)
            middle_cell = unit_cell(middle, middle_rows, next_id()) if middle else empty_cell(middle_rows)
            fine_cells = [unit_cell(fine, 1, next_id()) for fine in fines] or [empty_cell(1)]

            for fine_cell in fine_cells:
                rows.append(f'<tr>{coarse_cell}{middle_cell}{fine_cell}</tr>')
                coarse_cell = middle_cell = ''

    headers = ''.join(
        f'<th>{SCALE_LABELS[scale]} · {len(symbols_by_scale[scale])} enheter</th>'
        for scale in COLUMN_SCALES
    )
    note = f'<p class="note">Gjelder alle enheter: {html.escape(emblem["betydning"])}.</p>' if emblem else ''

    return (
        '<section class="card">'
        f'<div class="card-head"><span class="chip" style="background:{colour["fill_hex"]}"></span>'
        f'<h3>{short_code(kode_id)} {html.escape(colour["navn"])}</h3></div>'
        f'{note}'
        f'<div class="table-wrap"><table><tr>{headers}</tr>{"".join(rows)}</table></div>'
        '</section>'
    )


def render_legend(counter: list) -> str:
    '''Returns the key to the rules, drawn with the same code as the symbols.'''

    fill = '#F1EFE6'

    def sample(name: str, text: str, **parts) -> str:
        counter[0] += 1
        symbol = {
            'kode_id': name, 'fill_hex': fill, 'hatch_angle': None, 'hatch_colour': DEFAULT_HATCH_COLOUR,
            'hatch_style': 'solid', 'markers': [],
        }
        symbol.update(parts)
        return (
            f'<div class="unit">{symbol_svg(symbol, f"k{counter[0]}")}'
            f'<div><div class="code">{html.escape(name)}</div><div class="name">{html.escape(text)}</div></div></div>'
        )

    hatch = [
        sample('Skrå skravur', 'Kalkfattig', hatch_angle=ANGLE_KALKFATTIG),
        sample('Vannrett skravur', 'Intermediær', hatch_angle=ANGLE_INTERMEDIAER),
        sample('Loddrett skravur', 'Kalkrik', hatch_angle=ANGLE_KALKRIK),
        sample('Skravur mot venstre', 'Skravuren sier ikke noe om kalkinnhold', hatch_angle=ANGLE_NEUTRAL),
        sample('Blå skravur', 'Frisk eller sjelden tørrlagt; vannpåvirket', hatch_angle=ANGLE_KALKFATTIG, hatch_colour=DRYNESS_COLOURS[0]),
        sample('Grå skravur', 'Noe tørkeutsatt', hatch_angle=ANGLE_KALKFATTIG, hatch_colour=DRYNESS_COLOURS[1]),
        sample('Oransje skravur', 'Tørkeutsatt', hatch_angle=ANGLE_KALKFATTIG, hatch_colour=DRYNESS_COLOURS[2]),
        sample('Mørk rød skravur', 'Svært tørkeutsatt', hatch_angle=ANGLE_KALKFATTIG, hatch_colour=DRYNESS_COLOURS[3]),
        sample('Stiplet eller prikket', 'Skiller to enheter som ellers ville fått likt symbol', hatch_angle=ANGLE_KALKFATTIG, hatch_style='dashed'),
    ]

    markers, seen = [], set()
    for rule in load_variable_rules().values():
        key = (rule['shape'], rule['colour_hex'], rule['betydning'])
        if rule['element'] != 'marker' or key in seen:
            continue
        seen.add(key)
        title, _, text = rule['betydning'].partition(': ')
        markers.append(sample(title, text, markers=[{
            'shape': rule['shape'], 'colour': rule['colour_hex'], 'size_mm': 1.6,
            'filled': rule['shape'] not in STROKE_SHAPES,
        }]))

    for emblem in load_hovedtype_patterns().values():
        key = emblem['betydning'].partition(': ')[0]
        if emblem['element'] != 'marker' or key in seen or emblem['colour_hex'] == '#1F5FBF':
            continue
        seen.add(key)
        markers.append(sample(key, 'Skog i våtmark og sterkt endret skogsmark', markers=[{
            'shape': emblem['shape'], 'colour': emblem['colour_hex'], 'size_mm': 1.0, 'filled': True,
        }]))

    return (
        '<h2>Tegnforklaring</h2>'
        '<p class="lead">De samme reglene gjelder i alle hovedtyper og i alle målestokker. '
        'Større symbol betyr mer av egenskapen. Laveste trinn har ikke symbol.</p>'
        f'<section class="card"><h3>Skravur</h3><div class="legend" style="margin-top:10px">{"".join(hatch)}</div></section>'
        f'<section class="card"><h3>Symboler</h3><div class="legend" style="margin-top:10px">{"".join(markers)}</div></section>'
    )


def render_page(symbology: dict) -> str:
    colours = load_hovedtype_colours()
    gruppe_colours = load_hovedtypegruppe_colours()
    mapped_hovedtyper = load_mapped_hovedtyper()
    emblems = load_hovedtype_patterns()
    counter = [0]

    by_hovedtype = {}
    for scale, symbols in symbology.items():
        for symbol in symbols:
            by_hovedtype.setdefault(symbol['hovedtype'], {s: [] for s in MAPPING_SCALES})[scale].append(symbol)

    sections = [render_legend(counter)]
    for hovedtypegruppe in INCLUDED_HOVEDTYPEGRUPPER:
        sections.append(
            f'<h2>{short_code(hovedtypegruppe)} '
            f'{html.escape(gruppe_colours[hovedtypegruppe]["navn"])}</h2>'
        )
        for kode_id, colour in colours.items():
            if mapped_hovedtyper[kode_id]['hovedtypegruppe'] == hovedtypegruppe:
                sections.append(
                    render_hovedtype(kode_id, colour, by_hovedtype[kode_id], emblems.get(kode_id), counter)
                )

    totals = ', '.join(f'{len(symbology[scale])} i {SCALE_LABELS[scale]}' for scale in MAPPING_SCALES)

    return (
        '<!DOCTYPE html>\n<html lang="nb">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>NiN 3.0 symboloversikt</title>\n'
        f'<style>{PAGE_STYLE}</style>\n</head>\n<body>\n<main>\n'
        '<h1>NiN 3.0 kartografi: symboler for kartleggingsenheter</h1>\n'
        f'<p class="lead">Fastmarkssystemer og våtmarkssystemer: {totals}. Fyllfargen viser '
        'hovedtypen. Skravur og symboler viser kartleggingsenheten og er beregnet fra '
        'miljøvariablene som definerer enheten.</p>\n'
        '<p class="lead">Hver tabell leses fra venstre mot høyre: en enhet i 1:50 000 deles i '
        'enhetene til høyre for den i 1:20 000, som igjen deles i 1:5 000. En egenskap tegnes '
        'bare i de målestokkene der den skiller enheter i hovedtypen. Derfor er symbolene '
        'enklest i 1:50 000. Symbolene er tegnet forstørret.</p>\n'
        f'{"".join(sections)}\n'
        '</main>\n</body>\n</html>\n'
    )


def main() -> int:
    '''Execute as standalone script'''

    symbology = build_symbology()
    problems = validate_symbology(symbology)
    if problems:
        print("The symbology is not valid, nothing was rendered:")
        for problem in problems:
            print(f"  {problem}")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_page(symbology), encoding='utf-8', newline='\n')
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
