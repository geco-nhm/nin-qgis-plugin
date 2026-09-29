"""
Reads the symbol of every mapping unit from the symbology tables in
'csv/symbology'. No QGIS imports here so the functions can be unit-tested
with plain Python; 'symbology_symbols.py' turns the styles into QGIS symbols.

A unit gets the first of these that exists:

1. its symbol from 'symbology_<scale>.csv' (fill, hatch and markers)
2. the fill colour of its hovedtype ('hovedtype_colours.csv')
3. the fill colour of its hovedtypegruppe ('hovedtypegruppe_colours.csv')
4. a colour derived from its code ('symbology_colors.kode_id_color')
"""

import csv
from pathlib import Path

from .symbology_colors import kode_id_color

CSV_ROOT_PATH = Path(__file__).parent / 'csv'
SYMBOLOGY_PATH = CSV_ROOT_PATH / 'symbology'
ATTRIBUTE_TABLES_PATH = CSV_ROOT_PATH / 'attribute_tables'

OUTLINE_HEX = '#FFFFFF'
MAX_MARKERS = 3

# Prefix of the codes of hovedtypegrupper and hovedtyper of natursystemer
NATURSYSTEM_PREFIX = 'NA-'


def _read_csv_rows(csv_path: Path) -> list:
    if not csv_path.is_file():
        return []
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))


def _fill_colours(file_name: str) -> dict:
    return {
        row['kode_id']: row['fill_hex']
        for row in _read_csv_rows(SYMBOLOGY_PATH / file_name)
    }


def _to_number(text: str):
    return float(text) if text else None


def hovedtype_of(kode_id: str) -> str:
    '''Returns the hovedtype code of a unit code: 'TB01-M005-03' gives 'NA-TB01'.'''

    return NATURSYSTEM_PREFIX + str(kode_id).split('-', maxsplit=1)[0]


def hex_to_rgb(hex_colour: str) -> tuple:
    '''Converts '#RRGGBB' to a (red, green, blue) tuple, each 0-255.'''

    value = hex_colour.lstrip('#')
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def plain_style(kode_id: str, fill_hex: str) -> dict:
    '''Returns a style with a fill colour only.'''

    return {
        'kode_id': kode_id,
        'fill_hex': fill_hex,
        'outline_hex': OUTLINE_HEX,
        'hatch': None,
        'markers': [],
    }


def _style_from_row(row: dict) -> dict:
    style = plain_style(row['kode_id'], row['fill_hex'])
    style['outline_hex'] = row['outline_hex']

    if row['hatch_angle'] != '':
        style['hatch'] = {
            'angle': float(row['hatch_angle']),
            'colour': row['hatch_colour'],
            'style': row['hatch_style'],
            'spacing_mm': float(row['hatch_spacing_mm']),
            'width_mm': float(row['hatch_width_mm']),
        }

    for number in range(1, MAX_MARKERS + 1):
        if row.get(f'marker{number}_shape'):
            style['markers'].append({
                'shape': row[f'marker{number}_shape'],
                'colour': row[f'marker{number}_colour'],
                'size_mm': float(row[f'marker{number}_size_mm']),
                'filled': row[f'marker{number}_filled'] == '1',
                'spacing_mm': _to_number(row['marker_spacing_mm']),
            })

    return style


def load_unit_styles(mapping_scale: str) -> dict:
    '''
    Returns {kode_id: style} for every unit in the attribute table of the
    mapping scale ('M005', 'M020', 'M050' or 'grunntyper'), in table order.
    '''

    symbol_rows = {
        row['kode_id']: row
        for row in _read_csv_rows(SYMBOLOGY_PATH / f'symbology_{mapping_scale}.csv')
    }
    hovedtype_fills = _fill_colours('hovedtype_colours.csv')
    gruppe_fills = _fill_colours('hovedtypegruppe_colours.csv')

    styles = {}
    for row in _read_csv_rows(ATTRIBUTE_TABLES_PATH / f'{mapping_scale}_attribute_table.csv'):
        kode_id = row['kode_id']
        if not kode_id or kode_id in styles:
            continue

        hovedtype = hovedtype_of(kode_id)
        # 'NA-TB01' belongs to hovedtypegruppe 'NA-T'
        hovedtypegruppe = hovedtype[:len(NATURSYSTEM_PREFIX) + 1]

        if kode_id in symbol_rows:
            styles[kode_id] = _style_from_row(symbol_rows[kode_id])
        elif hovedtype in hovedtype_fills and _is_natursystem(row):
            styles[kode_id] = plain_style(kode_id, hovedtype_fills[hovedtype])
        elif hovedtypegruppe in gruppe_fills and _is_natursystem(row):
            styles[kode_id] = plain_style(kode_id, gruppe_fills[hovedtypegruppe])
        else:
            styles[kode_id] = plain_style(kode_id, '#{:02X}{:02X}{:02X}'.format(*kode_id_color(kode_id)))

    return styles


def _is_natursystem(row: dict) -> bool:
    '''
    The start of a code only names a hovedtype or hovedtypegruppe for
    natursystemer; 'TU01' (livsmedium) must not get the colour of 'NA-T'.
    '''

    return '-PE-NA-' in row.get('langkode', '').upper()
