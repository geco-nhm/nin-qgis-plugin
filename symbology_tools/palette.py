"""
Loads and checks the fill colours of the NiN 3.0 symbology.

The colours are hand-curated in 'nin_qgis_plugin/csv/symbology/':

    hovedtypegruppe_colours.csv   base colour of the seven hovedtypegrupper
    hovedtype_colours.csv         one fill per hovedtype with mapping units
    reserved_colours.csv          free colours held back for future hovedtyper
    subtype_colours.csv           shades of a hovedtype fill per value of one
                                  variable (TG01 per løsmassetype)
    colour_families.csv           the families and why they have their hue

These files are the single source of truth: nothing is derived from a
formula at runtime, so adding a hovedtype never changes the colour of an
existing one. A new hovedtype takes a reserved colour of its family.

The rules checked here come from the review of the NiN 2 cartography
(see docs/symbology/README.md).

Run as a script to print a check report:

    python symbology_tools/palette.py
"""

import csv
import itertools
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from symbology_tools.colour import (  # noqa: E402
    CVD_MATRICES, colour_difference, hex_to_rgb, rgb_to_oklch, simulate_cvd,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_ROOT_PATH = REPO_ROOT / 'nin_qgis_plugin' / 'csv'
SYMBOLOGY_PATH = CSV_ROOT_PATH / 'symbology'
ATTRIBUTE_TABLES_PATH = CSV_ROOT_PATH / 'attribute_tables'

MAPPING_SCALES = ('M005', 'M020', 'M050')

# Hovedtypegrupper with a colour per hovedtype (decision 2026-09-29: land and
# wetland first). The other groups are drawn with their group colour.
INCLUDED_HOVEDTYPEGRUPPER = ('NA-T', 'NA-V')

# All polygons have the same thin white outline. Outline colour is not used
# to carry information, because it is hard to read in the map.
OUTLINE_HEX = '#FFFFFF'

# Smallest allowed OKLab distance between two fills.
# About 0.02 is a just noticeable difference.
MIN_COLOUR_DIFFERENCE = 0.03

# The 'normal' hovedtyper cover most of the mapped area and must stand out
# from every other fill.
DOMINANT_HOVEDTYPER = (
    'NA-TA01', 'NA-TA02', 'NA-TA03', 'NA-TA04', 'NA-TB01', 'NA-VA01', 'NA-VB01',
)
MIN_DOMINANT_COLOUR_DIFFERENCE = 0.045

# Forest and open mountain vegetation must never be confused
MIN_FOREST_MOUNTAIN_DIFFERENCE = 0.08

# Clear green is reserved for forest: other families stay out of this hue
# range (OKLCH degrees) unless the colour is nearly grey.
GREEN_HUE_RANGE = (110, 180)
GREEN_MIN_CHROMA = 0.045
GREEN_FAMILIES = ('skog', 'vatmarksskog')

# Fills must stay light enough for dark overlay patterns and labels to read,
# and dark enough to stand out from a white map background.
MIN_LIGHTNESS = 0.50
MAX_LIGHTNESS = 0.96


def read_csv_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))


def load_colour_families() -> dict:
    '''Returns {colour_family: row} from colour_families.csv.'''

    return {
        row['colour_family']: row
        for row in read_csv_rows(SYMBOLOGY_PATH / 'colour_families.csv')
    }


def load_hovedtypegruppe_colours() -> dict:
    '''Returns {hovedtypegruppe kode_id: row} from hovedtypegruppe_colours.csv.'''

    return {
        row['kode_id']: row
        for row in read_csv_rows(SYMBOLOGY_PATH / 'hovedtypegruppe_colours.csv')
    }


def load_hovedtype_colours() -> dict:
    '''Returns {hovedtype kode_id: row} from hovedtype_colours.csv.'''

    return {
        row['kode_id']: row
        for row in read_csv_rows(SYMBOLOGY_PATH / 'hovedtype_colours.csv')
    }


def load_reserved_colours() -> list[dict]:
    '''Returns the rows of reserved_colours.csv.'''

    return read_csv_rows(SYMBOLOGY_PATH / 'reserved_colours.csv')


def load_subtype_colours() -> dict:
    '''
    Returns {hovedtype: {'variable': var_kode_id, 'colours': {value: row}}}
    from subtype_colours.csv.
    '''

    subtypes = {}
    for row in read_csv_rows(SYMBOLOGY_PATH / 'subtype_colours.csv'):
        subtype = subtypes.setdefault(row['hovedtype'], {'variable': row['var_kode_id'], 'colours': {}})
        subtype['colours'][row['value']] = row
    return subtypes


def load_mapped_hovedtypegrupper() -> dict:
    '''
    Returns {hovedtypegruppe kode_id: info} for every hovedtypegruppe that
    has mapping units. 'info' holds the name, the number of hovedtyper and
    the number of mapping units per scale.
    '''

    hovedtypegrupper = {
        row['fid']: row
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtypegrupper_attribute_table.csv')
    }
    hovedtype_to_gruppe = {
        row['fid']: hovedtypegrupper[row['hovedtypegrupper_fkey']]
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtyper_attribute_table.csv')
    }

    mapped = {}
    for scale in MAPPING_SCALES:
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / f'{scale}_attribute_table.csv'):
            gruppe = hovedtype_to_gruppe[row['hovedtyper_fkey']]
            info = mapped.setdefault(gruppe['kode_id'], {
                'navn': gruppe['navn'].removeprefix(gruppe['kode_id']).strip(),
                'hovedtyper': set(),
                'unit_counts': dict.fromkeys(MAPPING_SCALES, 0),
            })
            info['hovedtyper'].add(row['hovedtyper_fkey'])
            info['unit_counts'][scale] += 1

    return mapped


def load_mapped_hovedtyper() -> dict:
    '''
    Returns {hovedtype kode_id: info} for every hovedtype of the included
    hovedtypegrupper that has mapping units. 'info' holds the name, the
    hovedtypegruppe and the number of mapping units per scale.
    '''

    hovedtypegrupper = {
        row['fid']: row['kode_id']
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtypegrupper_attribute_table.csv')
    }

    unit_counts = {}
    for scale in MAPPING_SCALES:
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / f'{scale}_attribute_table.csv'):
            counts = unit_counts.setdefault(row['hovedtyper_fkey'], dict.fromkeys(MAPPING_SCALES, 0))
            counts[scale] += 1

    mapped_hovedtyper = {}
    for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtyper_attribute_table.csv'):
        hovedtypegruppe = hovedtypegrupper[row['hovedtypegrupper_fkey']]
        if row['fid'] not in unit_counts or hovedtypegruppe not in INCLUDED_HOVEDTYPEGRUPPER:
            continue

        mapped_hovedtyper[row['kode_id']] = {
            # 'navn' is stored as '<kode_id> <name>'
            'navn': row['navn'].removeprefix(row['kode_id']).strip(),
            'hovedtypegruppe': hovedtypegruppe,
            'unit_counts': unit_counts[row['fid']],
        }

    return mapped_hovedtyper


def all_fills() -> dict:
    '''
    Returns {label: (colour_family, fill_hex)} for every fill that can end
    up in a map or is held in reserve: the hovedtyper, their subtype shades,
    the reserved colours and the group colour of the hovedtypegrupper
    without hovedtype colours.
    '''

    colours = load_hovedtype_colours()
    fills = {
        kode_id: (row['colour_family'], row['fill_hex'])
        for kode_id, row in colours.items()
    }

    # A shade equal to the fill of its own hovedtype is not a new colour
    for hovedtype, subtype in load_subtype_colours().items():
        for value, row in subtype['colours'].items():
            if row['fill_hex'].upper() != colours[hovedtype]['fill_hex'].upper():
                fills[f"{hovedtype} {subtype['variable']}={value}"] = (
                    colours[hovedtype]['colour_family'], row['fill_hex']
                )

    family_counts = {}
    for row in load_reserved_colours():
        family = row['colour_family']
        family_counts[family] = family_counts.get(family, 0) + 1
        fills[f'reserved {family} {family_counts[family]}'] = (family, row['fill_hex'])

    for kode_id, row in load_hovedtypegruppe_colours().items():
        if kode_id not in INCLUDED_HOVEDTYPEGRUPPER:
            fills[f'group {kode_id}'] = ('', row['fill_hex'])

    return fills


def closest_pairs(fills: dict, deficiency: str = '') -> list[tuple]:
    '''
    Returns (difference, label_1, label_2) for all pairs of fills, most
    similar first. With 'deficiency' the colours are compared as seen with
    that colour vision deficiency.
    '''

    rgb_values = {}
    for label, (_, fill_hex) in fills.items():
        rgb = hex_to_rgb(fill_hex)
        rgb_values[label] = simulate_cvd(rgb, deficiency) if deficiency else rgb

    return sorted(
        (colour_difference(rgb_1, rgb_2), label_1, label_2)
        for (label_1, rgb_1), (label_2, rgb_2)
        in itertools.combinations(rgb_values.items(), 2)
    )


def _validate_coverage(problems: list) -> None:
    families = load_colour_families()
    colours = load_hovedtype_colours()
    mapped_hovedtyper = load_mapped_hovedtyper()

    for kode_id in sorted(set(mapped_hovedtyper) - set(colours)):
        problems.append(f"{kode_id} {mapped_hovedtyper[kode_id]['navn']}: has mapping units but no colour")

    for kode_id in sorted(set(colours) - set(mapped_hovedtyper)):
        problems.append(f"{kode_id}: has a colour but is not a hovedtype with mapping units")

    for kode_id, row in colours.items():
        if kode_id in mapped_hovedtyper and row['navn'] != mapped_hovedtyper[kode_id]['navn']:
            problems.append(f"{kode_id}: name '{row['navn']}' differs from the catalogue '{mapped_hovedtyper[kode_id]['navn']}'")

    used_families = {row['colour_family'] for row in colours.values()}
    reserved_families = {row['colour_family'] for row in load_reserved_colours()}

    for family in sorted(set(families) - used_families):
        problems.append(f"colour family '{family}' has no hovedtyper")

    for family in sorted(set(families) - reserved_families):
        problems.append(f"colour family '{family}' has no reserved colour")

    gruppe_colours = load_hovedtypegruppe_colours()
    mapped_grupper = load_mapped_hovedtypegrupper()

    for kode_id in sorted(set(mapped_grupper) ^ set(gruppe_colours)):
        problems.append(f"{kode_id}: hovedtypegrupper with mapping units and group colours do not match")


def _validate_single_fills(fills: dict, problems: list) -> bool:
    '''Checks each fill on its own. Returns False when a colour is unreadable.'''

    families = load_colour_families()
    all_colours_readable = True

    fills = dict(fills)
    for kode_id, row in load_hovedtypegruppe_colours().items():
        fills.setdefault(f'group {kode_id}', ('', row['fill_hex']))

    for label, (family, fill_hex) in fills.items():
        if family and family not in families:
            problems.append(f"{label}: unknown colour family '{family}'")

        try:
            lightness, chroma, hue = rgb_to_oklch(hex_to_rgb(fill_hex))
        except ValueError as error:
            problems.append(f"{label}: {error}")
            all_colours_readable = False
            continue

        # Snow and ice is drawn nearly white on purpose
        max_lightness = 1.0 if label == 'group NA-I' else MAX_LIGHTNESS
        if not MIN_LIGHTNESS <= lightness <= max_lightness:
            problems.append(
                f"{label}: lightness {lightness:.2f} of {fill_hex} is outside "
                f"{MIN_LIGHTNESS}-{max_lightness}"
            )

        is_green = GREEN_HUE_RANGE[0] < hue < GREEN_HUE_RANGE[1] and chroma > GREEN_MIN_CHROMA
        if family and family not in GREEN_FAMILIES and is_green:
            problems.append(f"{label}: {fill_hex} is green (hue {hue:.0f}), which is reserved for forest")

    return all_colours_readable


def _validate_differences(fills: dict, problems: list) -> None:
    for difference, label_1, label_2 in closest_pairs(fills):
        if difference >= MIN_DOMINANT_COLOUR_DIFFERENCE:
            break

        is_dominant = label_1 in DOMINANT_HOVEDTYPER or label_2 in DOMINANT_HOVEDTYPER
        limit = MIN_DOMINANT_COLOUR_DIFFERENCE if is_dominant else MIN_COLOUR_DIFFERENCE
        if difference < limit:
            problems.append(f"{label_1} and {label_2}: colours differ by {difference:.3f}, less than {limit}")

    for kode_id, (family, fill_hex) in fills.items():
        if family != 'skog':
            continue
        for other_kode_id in ('NA-TA03', 'NA-TA04'):
            difference = colour_difference(hex_to_rgb(fill_hex), hex_to_rgb(fills[other_kode_id][1]))
            if difference < MIN_FOREST_MOUNTAIN_DIFFERENCE:
                problems.append(
                    f"{kode_id} (forest) and {other_kode_id} (mountain): colours differ by "
                    f"{difference:.3f}, less than {MIN_FOREST_MOUNTAIN_DIFFERENCE}"
                )


def validate_palette() -> list[str]:
    '''Returns a list of problems; empty when the palette is valid.'''

    problems = []
    fills = all_fills()

    _validate_coverage(problems)
    if _validate_single_fills(fills, problems) and not problems:
        _validate_differences(fills, problems)

    return problems


def main() -> int:
    '''Execute as standalone script'''

    fills = all_fills()
    problems = validate_palette()

    print(
        f"{len(load_hovedtype_colours())} hovedtype colours and "
        f"{len(load_reserved_colours())} reserved colours in "
        f"{len(load_colour_families())} families"
    )

    print("\nMost similar pairs:")
    for difference, label_1, label_2 in closest_pairs(fills)[:5]:
        print(f"  {difference:.3f}  {label_1}  {label_2}")

    # Reported, not enforced: this many fills cannot all stay apart for every
    # kind of colour vision, which is why units also carry a pattern and a label.
    hovedtype_fills = {label: fill for label, fill in fills.items() if label.startswith('NA-')}
    print("\nHovedtype pairs that become hard to tell apart (difference < 0.02) with:")
    for deficiency in CVD_MATRICES:
        count = sum(1 for pair in closest_pairs(hovedtype_fills, deficiency) if pair[0] < 0.02)
        print(f"  {deficiency}: {count}")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for problem in problems:
            print(f"  {problem}")
        return 1

    print("\nPalette is valid.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
