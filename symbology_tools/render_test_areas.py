"""
Draws real mapping data with the symbology and evaluates how the symbols
work on it. Needs a Python with QGIS:

    python-qgis-ltr.bat symbology_tools/render_test_areas.py [--variant A]

    symbology/*.gpkg  ->  docs/symbology/testkart_<scale>.png and .pdf      all areas, at the mapping scale
                          docs/symbology/testkart_<scale>_omrade_<n>.png    one area each, enlarged

Each GeoPackage holds one polygon layer made by the plugin, with the unit
in 'kode_id_label' as the fid of the row in the attribute table of the
mapping scale. The mapping scale is read from the data: it is the scale
whose units belong to the hovedtype stored on each polygon. All layers
are drawn together in one map at the mapping scale, and each area again
on its own page, enlarged (DETAIL_SCALE). The symbols are the plugin's
own, for the mapping scale, with the plugin's fill opacity; only the map
is enlarged. A grey topographic map from Kartverket is
drawn below when the network allows.
"""

import argparse
import os
import csv
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qgis.core import (  # noqa: E402
    NULL,
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFillSymbol,
    QgsGeometry,
    QgsLayoutExporter,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemMap,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsLegendStyle,
    QgsPalLayerSettings,
    QgsPrintLayout,
    QgsProject,
    QgsProviderRegistry,
    QgsRasterLayer,
    QgsRendererCategory,
    QgsSingleSymbolRenderer,
    QgsSpatialIndex,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import QRectF  # noqa: E402
from qgis.PyQt.QtGui import QColor, QFont  # noqa: E402

from nin_qgis_plugin.symbology_styles import ATTRIBUTE_TABLES_PATH, load_unit_styles  # noqa: E402
from nin_qgis_plugin.symbology_symbols import create_fill_symbol  # noqa: E402
from symbology_tools.patterns import DEFAULT_VARIANT, OUTPUT_PATHS, VARIANTS  # noqa: E402

GPKG_PATH = REPO_ROOT / 'symbology'
OUTPUT_PATH = REPO_ROOT / 'docs' / 'symbology'

MAPPING_SCALES = {'M005': 5000, 'M020': 20000, 'M050': 50000}

# Scale of the enlarged map of each area
DETAIL_SCALE = 7500

VARIANT_TEXTS = {
    'A': 'utkast A (erstattet av B)',
    'B': 'utkast B (brukes i programtillegget)',
}
FILE_SUFFIXES = {'A': '_utkast_A', 'B': ''}

# Same as the plugin (project_setup.POLYGON_FILL_ALPHA): 65 % opaque fill
FILL_ALPHA = round(0.65 * 255)
EXPORT_DPI = 300

# Size of one pattern cell in millimetres on the map; a polygon narrower
# than two cells cannot show its pattern
PATTERN_CELL_MM = 4.0

# Kartverket's open grey topographic map, used as backdrop
BACKDROP_URI = (
    'crs=EPSG:25832&dpiMode=7&format=image/png&layers=topograatone&styles=default'
    '&tileMatrixSet=utm32n&url=https://cache.kartverket.no/v1/wmts/1.0.0/WMTSCapabilities.xml'
)

UNKNOWN_COLOUR = '#FF4040'


def read_attribute_table(mapping_scale: str) -> dict:
    '''Returns {fid as text: row} from the attribute table of the scale.'''

    csv_path = ATTRIBUTE_TABLES_PATH / f'{mapping_scale}_attribute_table.csv'
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return {row['fid']: row for row in csv.DictReader(csv_file)}


def polygon_layers() -> list:
    '''Returns the polygon layer of every GeoPackage in symbology/.'''

    layers = []
    metadata = QgsProviderRegistry.instance().providerMetadata('ogr')
    for gpkg in sorted(GPKG_PATH.glob('*.gpkg')):
        for sublayer in metadata.querySublayers(str(gpkg)):
            layer = QgsVectorLayer(f'{gpkg}|layername={sublayer.name()}', sublayer.name(), 'ogr')
            if layer.isValid() and layer.geometryType() == 2:  # polygons
                layers.append(layer)
    return layers


def detect_mapping_scale(layers: list) -> tuple:
    '''
    Returns (scale, {scale: matching polygons}). A polygon matches a scale
    when its 'kode_id_label' is a unit of that scale that belongs to the
    hovedtype stored on the polygon. The fids alone are ambiguous, because
    every scale table starts at fid 0.
    '''

    matches = Counter()
    for scale in MAPPING_SCALES:
        table = read_attribute_table(scale)
        for layer in layers:
            for feature in layer.getFeatures():
                row = table.get(str(feature['kode_id_label']))
                if row and row['hovedtyper_fkey'] == str(feature['hovedtype']):
                    matches[scale] += 1

    return matches.most_common(1)[0][0], dict(matches)


def merged_layer(layers: list) -> QgsVectorLayer:
    '''Copies the polygons of all layers into one memory layer.'''

    merged = QgsVectorLayer(
        'MultiPolygon?crs=EPSG:25832&field=kode_id_label:string(10)&field=omrade:string(40)',
        'NiN-kartlegging', 'memory',
    )
    features = []
    for layer in layers:
        for source in layer.getFeatures():
            feature = QgsFeature(merged.fields())
            feature.setGeometry(source.geometry())
            value = source['kode_id_label']
            feature['kode_id_label'] = None if value in (None, NULL) else str(value)
            feature['omrade'] = layer.name()
            features.append(feature)
    merged.dataProvider().addFeatures(features)
    merged.updateExtents()
    return merged


def area_frames(layers: list) -> QgsVectorLayer:
    '''Returns the extent of each mapped area, drawn as a dashed frame.'''

    frames = QgsVectorLayer('Polygon?crs=EPSG:25832&field=navn:string(40)', 'Kartlagte områder', 'memory')
    features = []
    for layer in layers:
        feature = QgsFeature(frames.fields())
        feature.setGeometry(QgsGeometry.fromRect(layer.extent()))
        # 'omrade_2_polygoner' -> 'Område 2'
        feature['navn'] = 'Område ' + layer.name().split('_')[1]
        features.append(feature)
    frames.dataProvider().addFeatures(features)
    frames.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({
        'color': '0,0,0,0', 'outline_color': '#3A3A3A', 'outline_width': '0.3', 'outline_style': 'dash',
    })))
    frames.setLabeling(QgsVectorLayerSimpleLabeling(_label_settings('"navn"', 7, bold=True)))
    frames.setLabelsEnabled(True)
    return frames


def _label_settings(expression: str, size: float, bold: bool = False) -> QgsPalLayerSettings:
    text_buffer = QgsTextBufferSettings()
    text_buffer.setEnabled(True)
    text_buffer.setSize(0.6)
    text_buffer.setColor(QColor(255, 255, 255))

    font = QFont('Arial')
    font.setBold(bold)
    text_format = QgsTextFormat()
    text_format.setFont(font)
    text_format.setSize(size)
    text_format.setColor(QColor(0, 0, 0))
    text_format.setBuffer(text_buffer)

    settings = QgsPalLayerSettings()
    settings.fieldName = expression
    settings.isExpression = True
    settings.setFormat(text_format)
    return settings


def style_layer(layer: QgsVectorLayer, mapping_scale: str, styles: dict) -> dict:
    '''
    Styles the layer like the plugin does: one symbol per unit, labelled
    with the unit code without the scale. Returns {fid: feature count}.
    '''

    table = read_attribute_table(mapping_scale)
    used = Counter(
        feature['kode_id_label'] for feature in layer.getFeatures()
        if feature['kode_id_label'] not in (None, NULL)
    )

    categories = []
    for fid, count in sorted(used.items(), key=lambda item: table.get(item[0], {}).get('kode_id', 'ZZZ')):
        row = table.get(fid)
        if row and row['kode_id'] in styles:
            symbol = create_fill_symbol(styles[row['kode_id']], FILL_ALPHA)
            name = row['navn'].removeprefix(row['kode_id']).strip()
            if len(name) > 38:
                name = name[:36].rstrip() + '…'
            label = f"{row['kode_id']}  {name} ({count})"
        else:
            symbol = QgsFillSymbol.createSimple({'color': UNKNOWN_COLOUR, 'outline_color': 'white'})
            label = f'Enhet {fid} finnes ikke i katalogen ({count})'
        categories.append(QgsRendererCategory(fid, symbol, label))

    categories.append(QgsRendererCategory(
        None,
        QgsFillSymbol.createSimple({
            'color': '255,255,255,0', 'outline_color': '#C0392B', 'outline_width': '0.3', 'outline_style': 'dash',
        }),
        'Ikke kartlagt',
    ))
    layer.setRenderer(QgsCategorizedSymbolRenderer('kode_id_label', categories))

    # 'TH01-M020-01' -> 'TH01-01', as the plugin labels the polygons
    cases = ''.join(
        f"WHEN \"kode_id_label\" = '{fid}' THEN '{table[fid]['kode_id'].replace('-' + mapping_scale, '')}' "
        for fid in used if fid in table
    )
    layer.setLabeling(QgsVectorLayerSimpleLabeling(_label_settings(f'CASE {cases}ELSE NULL END', 5)))
    layer.setLabelsEnabled(True)

    return dict(used)


def backdrop_layer():
    layer = QgsRasterLayer(BACKDROP_URI, 'Kartverket topografisk gråtone', 'wms')
    return layer if layer.isValid() else None


def export_map(project, layers: list, legend_layer, mapping_scale: str, variant: str,
               display_scale: int = 0, area_name: str = '', file_stem: str = '') -> list:
    '''
    Exports an A4 landscape layout with map, legend and scale bar. Without
    'display_scale' the map is drawn at the mapping scale.
    '''

    scale = MAPPING_SCALES[mapping_scale]
    display_scale = display_scale or scale
    variant_text = VARIANT_TEXTS[variant]

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.pageCollection().page(0).setPageSize(QgsLayoutSize(297, 210, QgsUnitTypes.LayoutMillimeters))

    map_item = QgsLayoutItemMap(layout)
    frame_height = 112 if display_scale == scale else 172
    map_item.attemptSetSceneRect(QRectF(10, 22, 112, frame_height))
    map_item.setFrameEnabled(True)
    map_item.setLayers(layers)
    map_item.setCrs(QgsCoordinateReferenceSystem('EPSG:25832'))
    map_item.zoomToExtent(legend_layer.extent())
    map_item.setScale(display_scale)
    layout.addLayoutItem(map_item)

    title = QgsLayoutItemLabel(layout)
    title.setText(f'NiN 3.0 kartografi, {variant_text}' + (f' · {area_name}' if area_name else ''))
    title.setFont(QFont('Arial', 13))
    title.attemptSetSceneRect(QRectF(10, 6, 277, 7))
    layout.addLayoutItem(title)

    subtitle = QgsLayoutItemLabel(layout)
    drawn = (
        f'kartet er tegnet i 1:{scale:,}' if display_scale == scale
        else f'forstørret utsnitt i 1:{display_scale:,} med symbolene for 1:{scale:,}'
    )
    subtitle.setText(
        f'Kartlagt i målestokk 1:{scale:,} (kartleggingsenheter {mapping_scale}) · '
        f'{drawn} · fyll 65 % dekkende'.replace(',', ' ')
    )
    subtitle.setFont(QFont('Arial', 8))
    subtitle.attemptSetSceneRect(QRectF(10, 13, 277, 5))
    layout.addLayoutItem(subtitle)

    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.setAutoUpdateModel(False)
    legend.setTitle(f'Kartleggingsenheter {mapping_scale}')
    legend.setStyleFont(QgsLegendStyle.Title, QFont('Arial', 9))
    legend.setStyleFont(QgsLegendStyle.Subgroup, QFont('Arial', 1))
    legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont('Arial', 6))
    legend.setSymbolWidth(9)
    legend.setSymbolHeight(5)
    legend.setColumnCount(2)
    # Only the units that are visible in the map
    legend.setLegendFilterByMapEnabled(True)
    legend.setSplitLayer(True)
    legend.setEqualColumnWidth(True)
    legend.attemptSetSceneRect(QRectF(130, 22, 160, 175))
    root = legend.model().rootGroup()
    root.clear()
    node = root.addLayer(legend_layer)
    node.setCustomProperty('legend/title-style', 'hidden')
    legend.setFrameEnabled(False)
    layout.addLayoutItem(legend)

    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setLinkedMap(map_item)
    scale_bar.setStyle('Single Box')
    scale_bar.setUnits(QgsUnitTypes.DistanceMeters)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setUnitsPerSegment(250 if display_scale >= 20000 else 100)
    scale_bar.setUnitLabel('m')
    scale_bar.setFont(QFont('Arial', 7))
    scale_bar.attemptMove(QgsLayoutPoint(130, 182 if display_scale != scale else 138, QgsUnitTypes.LayoutMillimeters)
                          if display_scale != scale else QgsLayoutPoint(10, 138, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_bar)

    note = QgsLayoutItemLabel(layout)
    note.setText('Bakgrunn: Kartverket, topografisk gråtone. Stiplet ramme: kartlagt område.')
    note.setFont(QFont('Arial', 6))
    if display_scale == scale:
        note.attemptSetSceneRect(QRectF(10, 150, 112, 10))
    else:
        note.attemptSetSceneRect(QRectF(130, 196, 160, 5))
    layout.addLayoutItem(note)

    exporter = QgsLayoutExporter(layout)
    file_stem = file_stem or f'testkart_{mapping_scale}{FILE_SUFFIXES[variant]}'
    written = []

    image_settings = QgsLayoutExporter.ImageExportSettings()
    image_settings.dpi = EXPORT_DPI
    image_path = OUTPUT_PATH / f'{file_stem}.png'
    if exporter.exportToImage(str(image_path), image_settings) == QgsLayoutExporter.Success:
        written.append(image_path)

    pdf_settings = QgsLayoutExporter.PdfExportSettings()
    pdf_settings.dpi = EXPORT_DPI
    pdf_path = OUTPUT_PATH / f'{file_stem}.pdf'
    if exporter.exportToPdf(str(pdf_path), pdf_settings) == QgsLayoutExporter.Success:
        written.append(pdf_path)

    return written


def _symbol_signature(style: dict) -> tuple:
    hatch = style['hatch']
    return (
        style['fill_hex'],
        (hatch['angle'], hatch['colour'], hatch['style']) if hatch else None,
        tuple((m['shape'], m['colour'], m['size_mm'], m['filled']) for m in style['markers']),
    )


def _difference(style_1: dict, style_2: dict) -> str:
    '''Names the parts in which two symbols differ.'''

    signature_1, signature_2 = _symbol_signature(style_1), _symbol_signature(style_2)
    hatch_1, hatch_2 = signature_1[1] or (None,) * 3, signature_2[1] or (None,) * 3
    parts = []
    if signature_1[0] != signature_2[0]:
        parts.append('fyll')
    if hatch_1[0] != hatch_2[0]:
        parts.append('skravurvinkel')
    elif hatch_1 != hatch_2:
        parts.append('skravurfarge eller -type')
    if signature_1[2] != signature_2[2]:
        parts.append('symbol')
    return ' + '.join(parts) or 'likt'


def evaluate(layer: QgsVectorLayer, mapping_scale: str, styles: dict) -> None:
    '''Prints how the symbols separate neighbours and how much of the map is patterned.'''

    table = read_attribute_table(mapping_scale)
    min_width_m = 2 * PATTERN_CELL_MM / 1000 * MAPPING_SCALES[mapping_scale]

    features = {feature.id(): feature for feature in layer.getFeatures()}
    index = QgsSpatialIndex(layer.getFeatures())

    def style_of(feature):
        row = table.get(feature['kode_id_label'])
        return styles.get(row['kode_id']) if row else None

    pairs, same_fill = Counter(), Counter()
    area = Counter()
    narrow = 0
    for fid, feature in features.items():
        style = style_of(feature)
        if style is None:
            continue
        geometry = feature.geometry()
        box = geometry.boundingBox()
        has_pattern = bool(style['hatch'] or style['markers'])
        area['all'] += geometry.area()
        area['hatch'] += geometry.area() if style['hatch'] else 0
        area['pattern'] += geometry.area() if has_pattern else 0
        if has_pattern and min(box.width(), box.height()) < min_width_m:
            narrow += 1

        for other_id in index.intersects(box):
            other = features[other_id]
            other_style = style_of(other)
            if other_id <= fid or other_style is None or other['kode_id_label'] == feature['kode_id_label']:
                continue
            if not geometry.touches(other.geometry()) and not geometry.intersects(other.geometry()):
                continue
            pairs[_difference(style, other_style)] += 1
            if style['fill_hex'] == other_style['fill_hex']:
                codes = sorted((style['kode_id'], other_style['kode_id']))
                same_fill[(codes[0], codes[1], _difference(style, other_style))] += 1

    print(f'  Neighbour pairs of different units ({sum(pairs.values())}), by what separates the symbols:')
    for difference, count in pairs.most_common():
        print(f'    {count:4d}  {difference}')
    print('  Neighbours with the same fill:')
    for (code_1, code_2, difference), count in same_fill.most_common():
        print(f'    {count:4d}  {code_1} | {code_2}: {difference}')
    print(f"  Area with hatch: {area['hatch'] / area['all']:.0%}, with any pattern: {area['pattern'] / area['all']:.0%}")
    print(f'  Polygons with a pattern but narrower than {min_width_m:.0f} m (two pattern cells): {narrow}')


def main() -> int:
    '''Execute as standalone script'''

    parser = argparse.ArgumentParser(description='Draws the test areas with the symbology.')
    parser.add_argument('--variant', choices=VARIANTS, default=DEFAULT_VARIANT)
    variant = parser.parse_args().variant

    QgsApplication.setPrefixPath(QgsApplication.prefixPath(), True)
    application = QgsApplication([], False)
    application.initQgis()

    project = QgsProject.instance()
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:25832'))

    source_layers = polygon_layers()
    mapping_scale, matches = detect_mapping_scale(source_layers)
    print(f'Mapping scale read from the data: {mapping_scale} (matching polygons per scale: {matches})')

    styles = load_unit_styles(mapping_scale, OUTPUT_PATHS[variant])
    layer = merged_layer(source_layers)
    used = style_layer(layer, mapping_scale, styles)
    frames = area_frames(source_layers)
    print(f'{layer.featureCount()} polygons in {len(source_layers)} areas, {len(used)} units')

    layers = [frames, layer]
    backdrop = backdrop_layer()
    if backdrop:
        layers.append(backdrop)
        print('Backdrop: Kartverket topografisk gråtone')
    else:
        print('Backdrop: none (Kartverket WMTS not reachable)')
    for map_layer in layers:
        project.addMapLayer(map_layer, False)

    for path in export_map(project, layers, layer, mapping_scale, variant):
        print(f'Wrote {path.relative_to(REPO_ROOT)}')

    evaluate(layer, mapping_scale, styles)

    # One enlarged map per area
    for source in source_layers:
        number = source.name().split('_')[1]
        area_layer = merged_layer([source])
        style_layer(area_layer, mapping_scale, styles)
        area_frame = area_frames([source])
        area_layers = [area_frame, area_layer] + layers[2:]
        for map_layer in (area_frame, area_layer):
            project.addMapLayer(map_layer, False)
        for path in export_map(
            project, area_layers, area_layer, mapping_scale, variant,
            display_scale=DETAIL_SCALE, area_name=f'Område {number}',
            file_stem=f'testkart_{mapping_scale}{FILE_SUFFIXES[variant]}_omrade_{number}',
        ):
            print(f'Wrote {path.relative_to(REPO_ROOT)}')

    # Release the layers before QGIS shuts down, or the interpreter crashes on exit
    project.clear()

    application.exitQgis()
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.stdout.flush()
    # QGIS can crash in its own teardown after a layout export; all output
    # is written at this point, so leave without running the teardown
    os._exit(exit_code)
