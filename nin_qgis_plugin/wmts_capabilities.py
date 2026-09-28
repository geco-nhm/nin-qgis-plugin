"""
Reads the parameters QGIS needs for a WMTS layer (layer, style, format,
tile matrix set) from a WMTS GetCapabilities document, the way the QGIS
connection dialog does, instead of guessing them. No QGIS imports so it
can be unit-tested with plain Python.
"""

import re
import xml.etree.ElementTree as ElementTree
from typing import Optional

WMTS_NS = '{http://www.opengis.net/wmts/1.0}'
OWS_NS = '{http://www.opengis.net/ows/1.1}'

PREFERRED_FORMATS = ('image/png', 'image/jpgpng', 'image/jpeg', 'image/jpg')


class WmtsCapabilitiesError(ValueError):
    '''Raised with a Norwegian, user-facing message.'''


def _text(element, path: str) -> str:
    found = element.find(path)
    return (found.text or '').strip() if found is not None and found.text else ''


def _epsg_code(crs: str) -> str:
    '''EPSG:25832 / urn:ogc:def:crs:EPSG::25832 / urn:ogc:def:crs:EPSG:6.18:3:25832 -> '25832'.'''
    match = re.search(r'EPSG:+(?:[\d.]+:)*(\d+)\s*$', str(crs).strip(), re.IGNORECASE)
    return match.group(1) if match else ''


def select_wmts_layer_parameters(
    capabilities_xml: bytes,
    layer_identifier: str,
    crs: str,
    preferred_formats=PREFERRED_FORMATS,
) -> dict:
    '''
    Returns {'layer', 'style', 'format', 'tile_matrix_set', 'tile_matrix_set_crs'}
    for the given layer and CRS (e.g. 'EPSG:25832').

    layer: exact identifier match, else the single layer offered, else a
           case-insensitive substring match.
    style: the one marked isDefault, else the first.
    format: first of preferred_formats offered, else the first offered.
    tile matrix set: the linked set whose SupportedCRS has the same EPSG
           code as crs; if none matches and only one set is linked, that one.
    Raises WmtsCapabilitiesError when something cannot be resolved.
    '''

    try:
        root = ElementTree.fromstring(capabilities_xml)
    except ElementTree.ParseError as exception:
        raise WmtsCapabilitiesError(
            f'Tjenestebeskrivelsen (GetCapabilities) kunne ikke leses: {exception}'
        ) from exception

    layers = root.findall(f'{WMTS_NS}Contents/{WMTS_NS}Layer')
    if not layers:
        raise WmtsCapabilitiesError('Tjenestebeskrivelsen inneholder ingen kartlag.')

    identifiers = [_text(layer, f'{OWS_NS}Identifier') for layer in layers]
    layer = None
    if layer_identifier in identifiers:
        layer = layers[identifiers.index(layer_identifier)]
    elif len(layers) == 1:
        layer = layers[0]
    else:
        wanted = layer_identifier.lower()
        for candidate, identifier in zip(layers, identifiers):
            if wanted in identifier.lower() or identifier.lower() in wanted:
                layer = candidate
                break
    if layer is None:
        raise WmtsCapabilitiesError(
            f"Kartlaget '{layer_identifier}' finnes ikke i tjenesten. "
            f"Tilgjengelige kartlag: {', '.join(identifiers)}"
        )

    styles = layer.findall(f'{WMTS_NS}Style')
    style = ''
    for candidate in styles:
        if (candidate.get('isDefault') or '').lower() == 'true':
            style = _text(candidate, f'{OWS_NS}Identifier')
            break
    if not style and styles:
        style = _text(styles[0], f'{OWS_NS}Identifier')
    if not style:
        style = 'default'

    formats = [(element.text or '').strip() for element in layer.findall(f'{WMTS_NS}Format')]
    formats = [value for value in formats if value]
    image_format = next((value for value in preferred_formats if value in formats), '')
    if not image_format:
        image_format = formats[0] if formats else 'image/png'

    linked_sets = [
        _text(link, f'{WMTS_NS}TileMatrixSet')
        for link in layer.findall(f'{WMTS_NS}TileMatrixSetLink')
    ]
    linked_sets = [value for value in linked_sets if value]
    set_crs = {}
    for tile_matrix_set in root.findall(f'{WMTS_NS}Contents/{WMTS_NS}TileMatrixSet'):
        set_crs[_text(tile_matrix_set, f'{OWS_NS}Identifier')] = _text(
            tile_matrix_set, f'{OWS_NS}SupportedCRS'
        )

    wanted_epsg = _epsg_code(crs)
    tile_matrix_set: Optional[str] = next(
        (name for name in linked_sets if _epsg_code(set_crs.get(name, '')) == wanted_epsg),
        None,
    )
    if tile_matrix_set is None and len(linked_sets) == 1:
        tile_matrix_set = linked_sets[0]
    if tile_matrix_set is None:
        offered = ', '.join(f"{name} ({set_crs.get(name, '?')})" for name in linked_sets) or 'ingen'
        raise WmtsCapabilitiesError(
            f"Tjenesten tilbyr ikke kartlaget '{layer_identifier}' i koordinatsystemet {crs}. "
            f"Tilgjengelige flisrutenett: {offered}"
        )

    return {
        'layer': _text(layer, f'{OWS_NS}Identifier') or layer_identifier,
        'style': style,
        'format': image_format,
        'tile_matrix_set': tile_matrix_set,
        'tile_matrix_set_crs': set_crs.get(tile_matrix_set, ''),
    }
