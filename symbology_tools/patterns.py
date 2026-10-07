"""
Builds the symbol of every mapping unit (kartleggingsenhet) at the three
mapping scales and writes them to

    nin_qgis_plugin/csv/symbology/symbology_M005.csv, _M020.csv, _M050.csv

    python symbology_tools/patterns.py              (variant A, used by the plugin)
    python symbology_tools/patterns.py --variant B  (proposal, see VARIANTS)

A symbol has three parts:

    fill      the colour of the hovedtype (see palette.py), same at all scales;
              a few hovedtyper use a shade per value of one variable
              ('subtype_colours.csv'), for example TG01 per løsmassetype
    hatch     parallel lines; angle and colour carry meaning
    markers   up to three repeated markers; shape, colour and size carry meaning

The symbol is computed from the variables that define the unit
('var_M005/M020/M050' tables), using the rules in 'variable_rules.csv' and
'hovedtype_patterns.csv'. Nothing is drawn by hand.

Aggregation between scales: the same rules are used at every scale, and a
variable is drawn only where it separates units of the same hovedtype at
that scale. Coarse scales have fewer separating variables, so their symbols
have fewer parts.
"""

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from symbology_tools.colour import (  # noqa: E402
    hex_to_rgb, oklch_to_rgb, rgb_to_hex, rgb_to_oklch,
)
from symbology_tools.palette import (  # noqa: E402
    ATTRIBUTE_TABLES_PATH, INCLUDED_HOVEDTYPEGRUPPER, MAPPING_SCALES, OUTLINE_HEX,
    REPO_ROOT, SYMBOLOGY_PATH, load_hovedtype_colours, load_subtype_colours, read_csv_rows,
)

# Variant A is the symbology the plugin uses. Variant B is a proposal:
# kalkfattig is the unhatched baseline, and drought is drawn with coloured
# circles instead of hatch colour, so that it shows also without a hatch.
VARIANTS = ('A', 'B')
OUTPUT_PATHS = {
    'A': SYMBOLOGY_PATH,
    'B': REPO_ROOT / 'symbology' / 'forslag_B',
}

# All sizes are millimetres on paper or screen, independent of map scale
HATCH_SPACING_MM = 4.0
HATCH_WIDTH_MM = 0.25
MARKER_SPACING_MM = 4.0
MARKER_SIZES_MM = (1.0, 1.6, 2.2)
MARKER_STROKE_WIDTH_MM = 0.25

# Three clearly different hatch angles carry kalkinnhold. Degrees counter-
# clockwise from horizontal, so 45 is '/', 0 is '-' and 90 is '|'.
ANGLE_KALKFATTIG = 45
ANGLE_INTERMEDIAER = 0
ANGLE_KALKRIK = 90
# Used when a hatch is needed but says nothing about kalkinnhold: '\'
ANGLE_NEUTRAL = 135

# Steps of LM-KA are a (1) to i (9). A unit is classed by the middle of its range.
KALK_BREAKS = (3.5, 6.5)
# A unit that spans this many steps or more covers the whole gradient: no angle
KALK_FULL_SPAN = 7

DEFAULT_HATCH_COLOUR = '#3A3A3A'
# From moist to dry. Blue always means water, so a unit is blue only when
# its whole range lies in the moist quarter of the scale.
DRYNESS_COLOURS = ('#1F5FBF', '#5A5A5A', '#C45F00', '#8E1B1B')
DRYNESS_LABELS = ('blå', 'grå', 'oransje', 'mørk rød')
DRYNESS_BLUE_MAX_POSITION = 0.25
# A unit that spans this share of the scale or more says nothing about
# dryness and keeps the neutral hatch colour
DRYNESS_FULL_SPAN = 2 / 3

HATCH_STYLES = ('solid', 'dashed', 'dotted')
# Dashed means myrkant, so only dotted is used to tell units apart
TIE_BREAK_HATCH_STYLES = ('solid', 'dotted')
# Variant B: drought class 1 (grey, the commonest) is the baseline without circle
DRYNESS_BASELINE_CLASS = 1

# Shapes without an inside: they cannot be drawn open or filled
STROKE_SHAPES = ('line', 'cross', 'cross2', 'ring')

# Markers for variables without a rule of their own, and for telling apart
# units that the rules leave with the same symbol
GENERIC_SHAPES = ('arrowhead', 'star', 'cross', 'triangle', 'diamond', 'square', 'cross2', 'line')
GENERIC_COLOUR = '#4A4A4A'

# Norwegian names of the marker shapes, for the explanation of each symbol
SHAPE_NAMES = {
    'circle': 'sirkel', 'ring': 'ring', 'square': 'firkant', 'triangle': 'trekant',
    'diamond': 'rute', 'star': 'stjerne', 'cross': 'plusstegn', 'cross2': 'kryss',
    'line': 'strek', 'arrowhead': 'vinkel',
}

# Most symbols have none or one marker; three is the ceiling
MAX_MARKERS = 3

# Smallest lightness difference (OKLCH) between a pattern colour and the fill
MIN_PATTERN_CONTRAST = 0.22

# Order of the steps of the ordinal scales. 'y' and 'z' are special end steps.
STEP_ORDER = '0abcdefghijklmnopqrstuvwxyz'

OUTPUT_COLUMNS = (
    'kode_id', 'navn', 'hovedtype', 'parent_kode_id', 'fill_hex', 'outline_hex',
    'hatch_angle', 'hatch_colour', 'hatch_style', 'hatch_spacing_mm', 'hatch_width_mm',
    'marker1_shape', 'marker1_colour', 'marker1_size_mm', 'marker1_filled',
    'marker2_shape', 'marker2_colour', 'marker2_size_mm', 'marker2_filled',
    'marker3_shape', 'marker3_colour', 'marker3_size_mm', 'marker3_filled',
    'marker_spacing_mm', 'forklaring',
)


def step_index(step: str) -> int:
    '''Returns the position of a step on its scale ('0' is 0, 'a' or 'A' is 1).'''

    return STEP_ORDER.index(step.lower())


def value_midpoint(values: str) -> float:
    '''Returns the middle of a range of steps such as 'b,c,d'.'''

    indices = [step_index(step) for step in values.split(',')]
    return (min(indices) + max(indices)) / 2


def value_span(values: str) -> int:
    '''Returns the number of steps a range such as 'b,c,d' covers.'''

    indices = [step_index(step) for step in values.split(',')]
    return max(indices) - min(indices) + 1


def ensure_contrast(colour_hex: str, fill_hex: str) -> str:
    '''
    Returns the colour, made darker or lighter when needed so that it can
    be seen on top of the fill. Hue is kept.
    '''

    lightness, chroma, hue = rgb_to_oklch(hex_to_rgb(colour_hex))
    fill_lightness = rgb_to_oklch(hex_to_rgb(fill_hex))[0]

    if abs(lightness - fill_lightness) >= MIN_PATTERN_CONTRAST:
        return colour_hex.upper()

    # Go away from the fill, in the direction the colour already leans,
    # unless that side has no room left
    target = fill_lightness - MIN_PATTERN_CONTRAST
    if lightness > fill_lightness and fill_lightness + MIN_PATTERN_CONTRAST <= 1.0:
        target = fill_lightness + MIN_PATTERN_CONTRAST

    while chroma >= 0:
        try:
            return rgb_to_hex(oklch_to_rgb(target, chroma, hue))
        except ValueError:
            chroma -= 0.005

    return rgb_to_hex(oklch_to_rgb(target, 0, 0))


def load_variable_rules() -> dict:
    '''Returns {var_kode_id: row} from variable_rules.csv, in priority order.'''

    return {
        row['var_kode_id']: row
        for row in read_csv_rows(SYMBOLOGY_PATH / 'variable_rules.csv')
    }


def load_hovedtype_patterns() -> dict:
    '''Returns {hovedtype kode_id: row} from hovedtype_patterns.csv.'''

    return {
        row['kode_id']: row
        for row in read_csv_rows(SYMBOLOGY_PATH / 'hovedtype_patterns.csv')
    }


def load_units() -> dict:
    '''
    Returns {hovedtype kode_id: {scale: [unit, ...]}} for the hovedtyper
    that have a colour. A unit is a dict with 'kode_id', 'navn',
    'parent_kode_id' and 'variables' ({var_kode_id: 'a,b,c'}).
    '''

    hovedtypegrupper = {
        row['fid']: row['kode_id']
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtypegrupper_attribute_table.csv')
    }
    hovedtyper = {
        row['fid']: row['kode_id']
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'hovedtyper_attribute_table.csv')
        if hovedtypegrupper[row['hovedtypegrupper_fkey']] in INCLUDED_HOVEDTYPEGRUPPER
    }
    parents = load_parents()

    units = {}
    for scale in MAPPING_SCALES:
        variables = {}
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / f'var_{scale}_attribute_table.csv'):
            variables.setdefault(row['grunntype_or_kle_fkey'], {})[row['var_kode_id']] = row['values']

        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / f'{scale}_attribute_table.csv'):
            if row['hovedtyper_fkey'] not in hovedtyper:
                continue

            hovedtype = hovedtyper[row['hovedtyper_fkey']]
            units.setdefault(hovedtype, {s: [] for s in MAPPING_SCALES})[scale].append({
                'kode_id': row['kode_id'],
                'navn': row['navn'].removeprefix(row['kode_id']).strip(),
                'parent_kode_id': parents.get(row['kode_id'], ''),
                'variables': variables.get(row['fid'], {}),
            })

    for scales in units.values():
        for scale_units in scales.values():
            scale_units.sort(key=lambda unit: unit['kode_id'])

    return units


def load_parents() -> dict:
    '''
    Returns {unit kode_id: kode_id of the unit it belongs to at the next
    coarser scale}. The link goes through the grunntyper, which name their
    unit at every scale. A unit whose grunntyper belong to two coarser
    units gets the one that holds most of its grunntyper.
    '''

    votes = {}
    for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'grunntyper_attribute_table.csv'):
        for child_scale, parent_scale in (('m005', 'm020'), ('m020', 'm050')):
            child = row[f'kartleggingsenhet_{child_scale}_fkey']
            parent = row[f'kartleggingsenhet_{parent_scale}_fkey']
            if child and parent:
                votes.setdefault(child, Counter())[parent] += 1

    return {
        # Ties go to the lowest code so the result does not depend on row order
        child: min(counter, key=lambda parent: (-counter[parent], parent))
        for child, counter in votes.items()
    }


def varying_variables(scale_units: list) -> set:
    '''Returns the variables that do not have the same value in every unit.'''

    all_variables = set().union(*(unit['variables'] for unit in scale_units))
    return {
        variable for variable in all_variables
        if len({unit['variables'].get(variable) for unit in scale_units}) > 1
    }


def within_lower_half(values: str, extent: tuple) -> bool:
    '''True when a range of steps lies entirely in the lower half of the variable.'''

    low, high = extent
    return max(step_index(step) for step in values.split(',')) <= (low + high) / 2


def includes_lowest_step(values: str, extent: tuple) -> bool:
    '''True when a range of steps includes the lowest step of the variable.'''

    return min(step_index(step) for step in values.split(',')) <= extent[0]


def value_ranks(scales: dict, extents: dict) -> dict:
    '''
    Returns {var_kode_id: {values: rank}} over the units of one hovedtype
    at all scales, so that a value has the same rank at every scale.

    Rank 0 means 'nothing to show': the range includes the lowest step of
    the variable, so the unit may be without the property. The other
    values get rank 1, 2, ... from low to high.
    '''

    distinct_values = {}
    for scale_units in scales.values():
        for unit in scale_units:
            for variable, values in unit['variables'].items():
                distinct_values.setdefault(variable, set()).add(values)

    ranks = {}
    for variable, value_set in distinct_values.items():
        extent = extents.get(variable, (0, 0))
        ranks[variable] = {}
        ranked = sorted(
            (values for values in value_set if not includes_lowest_step(values, extent)),
            key=lambda values: (value_midpoint(values), value_span(values), values),
        )
        for values in value_set:
            ranks[variable][values] = ranked.index(values) + 1 if values in ranked else 0

    return ranks


def variable_extents() -> dict:
    '''
    Returns {var_kode_id: (lowest, highest step index)} over all grunntyper,
    so that classes and ranks mean the same in every hovedtype. The special
    end steps 'y' and 'z' are left out.
    '''

    extents = {}
    for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / 'var_grunntyper_attribute_table.csv'):
        variable = row['var_kode_id']
        indices = [step_index(step) for step in row['values'].split(',') if step not in ('y', 'z')]
        if indices:
            low, high = extents.get(variable, (min(indices), max(indices)))
            extents[variable] = (min(low, *indices), max(high, *indices))

    return extents


def kalk_angle(values: str, variant: str = 'A'):
    '''
    Returns the hatch angle for a range of LM-KA steps, or None. In variant
    B kalkfattig is the baseline and has no hatch.
    '''

    if value_span(values) >= KALK_FULL_SPAN:
        return None

    midpoint = value_midpoint(values)
    if midpoint <= KALK_BREAKS[0]:
        return None if variant == 'B' else ANGLE_KALKFATTIG
    if midpoint <= KALK_BREAKS[1]:
        return ANGLE_INTERMEDIAER
    return ANGLE_KALKRIK


def dryness_class(values: str, extent: tuple):
    '''
    Returns 0 (moist) to 3 (dry) for a range of steps of a dryness
    variable, or None when the range covers most of the scale.
    '''

    low, high = extent
    if value_span(values) >= DRYNESS_FULL_SPAN * (high - low + 1):
        return None

    indices = [step_index(step) for step in values.split(',')]
    highest_position = (max(indices) - low) / (high - low)
    if highest_position <= DRYNESS_BLUE_MAX_POSITION:
        return 0

    midpoint_position = (value_midpoint(values) - low) / (high - low)
    return max(1, min(int(midpoint_position * len(DRYNESS_COLOURS)), len(DRYNESS_COLOURS) - 1))


def marker_variant(shape: str, rank: int):
    '''
    Returns (size_mm, filled) for the rank of a value, or None when the
    shape has no more variants. Rank 1 is the smallest marker.
    '''

    sizes = len(MARKER_SIZES_MM)
    if rank <= sizes:
        return (MARKER_SIZES_MM[rank - 1], shape not in STROKE_SHAPES)
    if rank <= 2 * sizes and shape not in STROKE_SHAPES:
        return (MARKER_SIZES_MM[rank - sizes - 1], False)
    return None


def value_colour(rule: dict, values: str):
    '''
    Returns the colour a rule gives to a nominal value, or None when the
    rule has no colours per value. Returns '' when the value is drawn
    without a marker: a range that includes '0' is undifferentiated.
    '''

    if not rule.get('value_colours'):
        return None

    colours = dict(pair.split('=') for pair in rule['value_colours'].split(';'))
    steps = values.split(',')
    if '0' in steps:
        return ''
    return colours.get(steps[len(steps) // 2], '')


def resolve_colour(colour: str, fills: dict) -> str:
    '''Resolves 'fill:<hovedtype>' to the fill colour of that hovedtype.'''

    if colour.startswith('fill:'):
        return fills[colour.removeprefix('fill:')]['fill_hex']
    return colour


def build_symbol(unit: dict, hovedtype: str, varying: set, ranks: dict, context: dict) -> dict:
    '''Builds the symbol of one unit from the rules. Ties are broken later.'''

    rules, extents, fills = context['rules'], context['extents'], context['fills']
    variant = context['variant']
    emblem = context['hovedtype_patterns'].get(hovedtype)
    fill_hex = fills[hovedtype]['fill_hex']
    variables = unit['variables']
    explanation = []

    # A shade of the fill per value of one variable, when the unit has one value
    subtype = context['subtypes'].get(hovedtype)
    if subtype and variables.get(subtype['variable']) in subtype['colours']:
        row = subtype['colours'][variables[subtype['variable']]]
        fill_hex = row['fill_hex']
        explanation.append(f"{row['navn']}: egen nyanse av fyllfargen")

    symbol = {
        'kode_id': unit['kode_id'],
        'navn': unit['navn'],
        'hovedtype': hovedtype,
        'parent_kode_id': unit['parent_kode_id'],
        'fill_hex': fill_hex,
        'outline_hex': OUTLINE_HEX,
        'hatch_angle': None,
        'hatch_colour': None,
        'hatch_style': None,
        'hatch_style_fixed': False,
        'markers': [],
        'explanation': explanation,
    }

    if emblem and emblem['element'] == 'marker':
        symbol['markers'].append({
            'shape': emblem['shape'],
            'colour': ensure_contrast(resolve_colour(emblem['colour_hex'], fills), fill_hex),
            'size_mm': MARKER_SIZES_MM[0],
            'filled': True,
        })
        symbol['explanation'].append(emblem['betydning'])

    if 'LM-KA' in varying and 'LM-KA' in variables:
        symbol['hatch_angle'] = kalk_angle(variables['LM-KA'], variant)
        if symbol['hatch_angle'] is not None:
            label = {ANGLE_KALKFATTIG: 'skrå', ANGLE_INTERMEDIAER: 'vannrett', ANGLE_KALKRIK: 'loddrett'}
            symbol['explanation'].append(
                f"Kalkinnhold {variables['LM-KA']}: {label[symbol['hatch_angle']]} skravur"
            )
        elif variant == 'B' and value_span(variables['LM-KA']) < KALK_FULL_SPAN:
            symbol['explanation'].append(f"Kalkinnhold {variables['LM-KA']}: kalkfattig, ingen skravur")

    if emblem and emblem['element'] == 'hatch_colour':
        symbol['hatch_colour'] = resolve_colour(emblem['colour_hex'], fills)
        symbol['explanation'].append(emblem['betydning'])
    else:
        for variable, rule in rules.items():
            if rule['element'] == 'hatch_colour' and variable in varying and variable in variables:
                dryness = dryness_class(variables[variable], extents[variable])
                if dryness is not None and variant == 'A':
                    symbol['hatch_colour'] = DRYNESS_COLOURS[dryness]
                    symbol['explanation'].append(
                        f"{rule['navn']} {variables[variable]}: {DRYNESS_LABELS[dryness]} skravur"
                    )
                elif dryness is not None and dryness != DRYNESS_BASELINE_CLASS:
                    # Variant B: a circle in the drought colour; the grey class has none
                    symbol['markers'].append({
                        'shape': 'circle',
                        'colour': ensure_contrast(DRYNESS_COLOURS[dryness], fill_hex),
                        'size_mm': MARKER_SIZES_MM[0],
                        'filled': True,
                    })
                    symbol['explanation'].append(
                        f"{rule['navn']} {variables[variable]}: {DRYNESS_LABELS[dryness]} sirkel"
                    )
                break

    for variable, rule in rules.items():
        if rule['element'] == 'hatch_style' and variable in varying and variable in variables:
            # A range entirely in the lower half (for example myrkant) is
            # dashed; the upper half and ranges over both halves are solid
            dashed = within_lower_half(variables[variable], extents[variable])
            has_hatch = symbol['hatch_angle'] is not None or symbol['hatch_colour']
            # Variant B: myrflate without a hatch stays without one (baseline)
            if dashed or has_hatch or variant == 'A':
                symbol['hatch_style'] = HATCH_STYLES[1] if dashed else HATCH_STYLES[0]
                symbol['hatch_style_fixed'] = True
                symbol['explanation'].append(
                    f"{rule['navn']} {variables[variable]}: {'stiplet' if dashed else 'heltrukken'} skravur"
                )
            break

    if (symbol['hatch_colour'] or symbol['hatch_style_fixed']) and symbol['hatch_angle'] is None:
        symbol['hatch_angle'] = ANGLE_NEUTRAL
    if symbol['hatch_angle'] is not None:
        symbol['hatch_colour'] = ensure_contrast(symbol['hatch_colour'] or DEFAULT_HATCH_COLOUR, fill_hex)
        symbol['hatch_style'] = symbol['hatch_style'] or HATCH_STYLES[0]

    add_variable_markers(symbol, variables, varying, ranks, context)

    return symbol


def add_variable_markers(symbol: dict, variables: dict, varying: set, ranks: dict, context: dict) -> None:
    '''Adds the markers of the varying variables, in the order of the rules.'''

    rules = context['rules']
    generic_shapes = context['generic_shapes']
    subtype = context['subtypes'].get(symbol['hovedtype'])
    # The variable that sets the shade of the fill is not drawn again
    fill_variable = subtype['variable'] if subtype else None

    marker_variables = [
        variable for variable, rule in rules.items()
        if rule['element'] == 'marker' and variable in varying
    ]
    # Variables without a rule come last, in a fixed order
    marker_variables += sorted(
        variable for variable in varying if variable not in rules and variable != fill_variable
    )

    for variable in marker_variables:
        if len(symbol['markers']) >= MAX_MARKERS or variable not in variables:
            continue

        rank = ranks[variable][variables[variable]]

        if variable in rules:
            shape, colour = rules[variable]['shape'], rules[variable]['colour_hex']
            name = rules[variable]['navn']
        else:
            shape, colour = generic_shapes[variable], GENERIC_COLOUR
            name = context['variable_names'].get(variable, variable)

        nominal_colour = value_colour(rules.get(variable, {}), variables[variable])
        if nominal_colour is None:
            # Ordinal: the lowest value has no marker, higher values a larger one
            variant = marker_variant(shape, rank) if rank else None
        else:
            # Nominal: the value decides the colour
            colour = resolve_colour(nominal_colour, context['fills'])
            variant = (MARKER_SIZES_MM[1], True) if nominal_colour else None

        if variant is None:
            continue

        # White markers keep their colour; their dark stroke makes them visible
        if colour.upper() != '#FFFFFF':
            colour = ensure_contrast(colour, symbol['fill_hex'])

        if any(marker['shape'] == shape and marker['colour'] == colour for marker in symbol['markers']):
            continue

        symbol['markers'].append({
            'shape': shape, 'colour': colour, 'size_mm': variant[0], 'filled': variant[1],
        })
        symbol['explanation'].append(f"{name} {variables[variable]}: {SHAPE_NAMES[shape]} {variant[0]} mm")


def symbol_signature(symbol: dict) -> tuple:
    '''Returns everything that is drawn, for comparing symbols.'''

    return (
        symbol['fill_hex'], symbol['hatch_angle'], symbol['hatch_colour'], symbol['hatch_style'],
        tuple(
            (marker['shape'], marker['colour'], marker['size_mm'], marker['filled'])
            for marker in symbol['markers']
        ),
    )


def break_ties(symbols: list, units: dict) -> None:
    '''
    Makes symbols that are still equal different. Equal symbols are put in
    the order of their variables and code; the first keeps its symbol, the
    next one gets a dotted hatch, the next ones a neutral marker. Dashed is
    not used here, because it means myrkant.
    '''

    groups = {}
    for symbol in symbols:
        groups.setdefault(symbol_signature(symbol), []).append(symbol)

    used_shapes = {marker['shape'] for symbol in symbols for marker in symbol['markers']}
    free_shapes = [shape for shape in GENERIC_SHAPES if shape not in used_shapes] or list(GENERIC_SHAPES)

    for group in groups.values():
        if len(group) < 2:
            continue

        group.sort(key=lambda symbol: (
            sorted(
                (variable, value_midpoint(values))
                for variable, values in units[symbol['kode_id']]['variables'].items()
            ),
            symbol['kode_id'],
        ))

        has_hatch = group[0]['hatch_angle'] is not None and not group[0]['hatch_style_fixed']
        has_room = len(group[0]['markers']) < MAX_MARKERS
        styles = TIE_BREAK_HATCH_STYLES if has_hatch else (None,)

        variants = [(style, None) for style in styles]
        if has_room:
            variants += [
                (style, (shape, size))
                for size in MARKER_SIZES_MM[:2] for shape in free_shapes for style in styles
            ]

        for symbol, (style, tag) in zip(group, variants):
            if style and style != HATCH_STYLES[0]:
                symbol['hatch_style'] = style
                symbol['explanation'].append(f"Skilles fra naboenhet med {_style_name(style)} skravur")
            if tag:
                symbol['markers'].append({
                    'shape': tag[0],
                    'colour': ensure_contrast(GENERIC_COLOUR, symbol['fill_hex']),
                    'size_mm': tag[1],
                    'filled': tag[0] not in STROKE_SHAPES,
                })
                symbol['explanation'].append(f"Skilles fra naboenhet med symbol: {SHAPE_NAMES[tag[0]]} {tag[1]} mm")


def _style_name(style: str) -> str:
    return {'dashed': 'stiplet', 'dotted': 'prikket'}[style]


def build_context(variant: str = 'A') -> dict:
    variable_names = {}
    for scale in MAPPING_SCALES:
        for row in read_csv_rows(ATTRIBUTE_TABLES_PATH / f'var_{scale}_attribute_table.csv'):
            variable_names[row['var_kode_id']] = row['var_name']

    rules = load_variable_rules()
    used_shapes = {rule['shape'] for rule in rules.values() if rule['shape']}
    free_shapes = [shape for shape in GENERIC_SHAPES if shape not in used_shapes] or list(GENERIC_SHAPES)
    fill_variables = {subtype['variable'] for subtype in load_subtype_colours().values()}
    unruled = sorted(
        variable for variable in variable_names
        if variable not in rules and variable not in fill_variables
    )

    return {
        'variant': variant,
        'rules': rules,
        'subtypes': load_subtype_colours(),
        'hovedtype_patterns': load_hovedtype_patterns(),
        'extents': variable_extents(),
        'fills': load_hovedtype_colours(),
        'variable_names': variable_names,
        # A variable without a rule has the same shape in every hovedtype
        'generic_shapes': {
            variable: free_shapes[index % len(free_shapes)]
            for index, variable in enumerate(unruled)
        },
    }


def build_symbology(variant: str = 'A') -> dict:
    '''Returns {scale: [symbol, ...]} for all units, sorted by code.'''

    context = build_context(variant)
    symbology = {scale: [] for scale in MAPPING_SCALES}

    for hovedtype, scales in sorted(load_units().items()):
        ranks = value_ranks(scales, context['extents'])

        for scale, scale_units in scales.items():
            varying = varying_variables(scale_units)
            symbols = [
                build_symbol(unit, hovedtype, varying, ranks, context)
                for unit in scale_units
            ]
            break_ties(symbols, {unit['kode_id']: unit for unit in scale_units})
            symbology[scale].extend(symbols)

    return symbology


def catalogue_gaps(symbology: dict) -> dict:
    '''
    Returns {scale: [symbol, ...]} for the units that the catalogue does
    not link to any unit at the next coarser scale. These are gaps in the
    NiN catalogue, not in the symbology.
    '''

    return {
        scale: [symbol for symbol in symbols if not symbol['parent_kode_id']]
        for scale, symbols in symbology.items() if scale != MAPPING_SCALES[-1]
    }


def validate_symbology(symbology: dict) -> list[str]:
    '''Returns a list of problems; empty when the symbology is valid.'''

    problems = []
    gaps = {symbol['kode_id'] for symbols in catalogue_gaps(symbology).values() for symbol in symbols}

    for scale, symbols in symbology.items():
        seen = {}
        for symbol in symbols:
            signature = symbol_signature(symbol)
            if signature in seen:
                problems.append(f"{scale}: {symbol['kode_id']} has the same symbol as {seen[signature]}")
            seen[signature] = symbol['kode_id']

            if len(symbol['markers']) > MAX_MARKERS:
                problems.append(f"{scale}: {symbol['kode_id']} has more than {MAX_MARKERS} markers")

            fill_lightness = rgb_to_oklch(hex_to_rgb(symbol['fill_hex']))[0]
            colours = [marker['colour'] for marker in symbol['markers'] if marker['colour'] != '#FFFFFF']
            if symbol['hatch_colour']:
                colours.append(symbol['hatch_colour'])
            for colour in colours:
                contrast = abs(rgb_to_oklch(hex_to_rgb(colour))[0] - fill_lightness)
                if contrast < MIN_PATTERN_CONTRAST - 0.01:
                    problems.append(
                        f"{scale}: {symbol['kode_id']} pattern colour {colour} has contrast "
                        f"{contrast:.2f} against the fill, less than {MIN_PATTERN_CONTRAST}"
                    )

        codes = {symbol['kode_id'] for symbol in symbols}
        coarser = MAPPING_SCALES[MAPPING_SCALES.index(scale) + 1:][:1]
        if coarser:
            parent_codes = {symbol['kode_id'] for symbol in symbology[coarser[0]]}
            for symbol in symbols:
                if symbol['parent_kode_id'] not in parent_codes and symbol['kode_id'] not in gaps:
                    problems.append(f"{scale}: {symbol['kode_id']} has no unit at {coarser[0]}")
        if len(codes) != len(symbols):
            problems.append(f"{scale}: duplicate codes")

    return problems


def symbol_to_row(symbol: dict) -> dict:
    row = {
        column: symbol.get(column, '')
        for column in ('kode_id', 'navn', 'hovedtype', 'parent_kode_id', 'fill_hex', 'outline_hex')
    }

    has_hatch = symbol['hatch_angle'] is not None
    row.update({
        'hatch_angle': symbol['hatch_angle'] if has_hatch else '',
        'hatch_colour': symbol['hatch_colour'] if has_hatch else '',
        'hatch_style': symbol['hatch_style'] if has_hatch else '',
        'hatch_spacing_mm': HATCH_SPACING_MM if has_hatch else '',
        'hatch_width_mm': HATCH_WIDTH_MM if has_hatch else '',
        'marker_spacing_mm': MARKER_SPACING_MM if symbol['markers'] else '',
        'forklaring': '; '.join(symbol['explanation']),
    })

    for number in range(1, MAX_MARKERS + 1):
        marker = symbol['markers'][number - 1] if number <= len(symbol['markers']) else None
        row.update({
            f'marker{number}_shape': marker['shape'] if marker else '',
            f'marker{number}_colour': marker['colour'] if marker else '',
            f'marker{number}_size_mm': marker['size_mm'] if marker else '',
            f'marker{number}_filled': int(marker['filled']) if marker else '',
        })

    return row


def write_symbology(symbology: dict, output_path: Path = SYMBOLOGY_PATH) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    for scale, symbols in symbology.items():
        csv_path = output_path / f'symbology_{scale}.csv'
        with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_COLUMNS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(symbol_to_row(symbol) for symbol in symbols)


def main() -> int:
    '''Execute as standalone script'''

    parser = argparse.ArgumentParser(description='Builds the symbol tables.')
    parser.add_argument('--variant', choices=VARIANTS, default='A')
    variant = parser.parse_args().variant

    symbology = build_symbology(variant)
    problems = validate_symbology(symbology)

    for scale, symbols in symbology.items():
        hatched = sum(1 for symbol in symbols if symbol['hatch_angle'] is not None)
        plain = sum(1 for symbol in symbols if symbol['hatch_angle'] is None and not symbol['markers'])
        three = sum(1 for symbol in symbols if len(symbol['markers']) == MAX_MARKERS)
        tie_broken = sum(1 for symbol in symbols if any('Skilles' in part for part in symbol['explanation']))
        print(
            f"{scale}: {len(symbols)} units, {hatched} with hatch, {plain} with fill only, "
            f"{three} with {MAX_MARKERS} markers, {tie_broken} told apart by tie-break"
        )

    for symbols in catalogue_gaps(symbology).values():
        for symbol in symbols:
            print(f"Catalogue gap: {symbol['kode_id']} {symbol['navn']} has no unit at the next coarser scale")

    if problems:
        print(f"\n{len(problems)} problem(s), nothing was written:")
        for problem in problems[:40]:
            print(f"  {problem}")
        return 1

    write_symbology(symbology, OUTPUT_PATHS[variant])
    print(f"\nWrote variant {variant} symbology tables to {OUTPUT_PATHS[variant]}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
