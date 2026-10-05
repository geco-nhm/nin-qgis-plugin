"""
Draws real mapping data with the symbology, as a map per GeoPackage, to see
how the symbols work on field data. Needs a Python with QGIS:

    python-qgis-ltr.bat symbology_tools/render_test_areas.py [M020]

    symbology/*.gpkg  ->  docs/symbology/testkart_<layer>.png and .pdf

Each GeoPackage holds one polygon layer made by the plugin, with the unit
in 'kode_id_label' as the fid of the row in the attribute table of the
mapping scale. The symbols are the plugin's own (symbology_symbols.py),
with the same half-transparent fill as in a mapping project. A grey
topographic map from Kartverket is drawn below when the network allows.
"""

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qgis.core import (  # noqa: E402
    NULL,
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsCoordinateReferenceSystem,
    QgsFillSymbol,
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

GPKG_PATH = REPO_ROOT / 'symbology'
OUTPUT_PATH = REPO_ROOT / 'docs' / 'symbology'

# Same as the plugin: the fill lets the background map show through
FILL_ALPHA = 128
MAP_SCALE = 5000
EXPORT_DPI = 200

# Kartverket's open grey topographic map, used as backdrop
BACKDROP_URI = (
    'crs=EPSG:25832&dpiMode=7&format=image/png&layers=topograatone&styles=default'
    '&tileMatrixSet=utm32n&url=https://cache.kartverket.no/v1/wmts/1.0.0/WMTSCapabilities.xml'
)



def load_unit_codes(mapping_scale: str) -> dict:
    '''Returns {fid as text: kode_id} from the attribute table of the scale.'''

    csv_path = ATTRIBUTE_TABLES_PATH / f'{mapping_scale}_attribute_table.csv'
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return {row['fid']: row['kode_id'] for row in csv.DictReader(csv_file)}


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


def style_layer(layer: QgsVectorLayer, mapping_scale: str, unit_codes: dict) -> dict:
    '''
    Styles the layer like the plugin does. The renderer classifies on the
    fid in 'kode_id_label' and labels the categories with the unit code.
    Returns {kode_id: feature count} for the units in the layer.
    '''

    styles = load_unit_styles(mapping_scale)
    used = {}
    for feature in layer.getFeatures():
        fid = feature['kode_id_label']
        if fid not in (None, NULL):
            used[str(fid)] = used.get(str(fid), 0) + 1

    categories = []
    for fid, count in sorted(used.items(), key=lambda item: unit_codes.get(item[0], 'ZZZ')):
        kode_id = unit_codes.get(fid)
        if kode_id in styles:
            symbol = create_fill_symbol(styles[kode_id], FILL_ALPHA)
            label = f'{kode_id} ({count})'
        else:
            symbol = QgsFillSymbol.createSimple({'color': f'255,0,0,{FILL_ALPHA}', 'outline_color': 'white'})
            label = f'ukjent fid {fid} ({count})'
        categories.append(QgsRendererCategory(fid, symbol, label))

    categories.append(QgsRendererCategory(
        None, QgsFillSymbol.createSimple({'color': '255,255,255,0', 'outline_color': '#C0392B', 'outline_width': '0.4', 'outline_style': 'dash'}),
        'ikke kartlagt',
    ))
    layer.setRenderer(QgsCategorizedSymbolRenderer('kode_id_label', categories))

    text_buffer = QgsTextBufferSettings()
    text_buffer.setEnabled(True)
    text_buffer.setSize(0.7)
    text_buffer.setColor(QColor(255, 255, 255))

    text_format = QgsTextFormat()
    text_format.setFont(QFont('Arial'))
    text_format.setSize(6)
    text_format.setColor(QColor(0, 0, 0))
    text_format.setBuffer(text_buffer)

    # Label: the unit code without the scale, like the plugin's label
    cases = ''.join(
        f"WHEN \"kode_id_label\" = '{fid}' THEN '{unit_codes[fid].replace('-' + mapping_scale, '')}' "
        for fid in used if fid in unit_codes
    )
    settings = QgsPalLayerSettings()
    settings.fieldName = f"CASE {cases}WHEN \"kode_id_label\" IS NULL THEN 'ikke kartlagt' ELSE 'ukjent' END"
    settings.isExpression = True
    settings.setFormat(text_format)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)

    return {unit_codes.get(fid, f'fid {fid}'): count for fid, count in used.items()}


def backdrop_layer():
    layer = QgsRasterLayer(BACKDROP_URI, 'Kartverket topografisk gråtone', 'wms')
    return layer if layer.isValid() else None


def export_map(project: QgsProject, layer: QgsVectorLayer, backdrop, title: str) -> list:
    '''Exports a layout with map, legend and scale bar. Returns the files written.'''

    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    page = layout.pageCollection().page(0)
    page.setPageSize(QgsLayoutSize(210, 210, QgsUnitTypes.LayoutMillimeters))

    map_item = QgsLayoutItemMap(layout)
    map_item.attemptSetSceneRect(QRectF(8, 12, 110, 192))
    map_item.setFrameEnabled(True)
    map_item.setLayers([layer] + ([backdrop] if backdrop else []))
    map_item.setCrs(layer.crs())
    extent = layer.extent()
    extent.grow(10)
    map_item.zoomToExtent(extent)
    map_item.setScale(MAP_SCALE)
    layout.addLayoutItem(map_item)

    label = QgsLayoutItemLabel(layout)
    label.setText(f'{title} · 1:{MAP_SCALE} · NiN 3.0 kartografi, utkast')
    label.setFont(QFont('Arial', 11))
    label.attemptSetSceneRect(QRectF(8, 3, 196, 8))
    layout.addLayoutItem(label)

    legend = QgsLayoutItemLegend(layout)
    legend.setLinkedMap(map_item)
    legend.setAutoUpdateModel(False)
    legend.setTitle('Kartleggingsenheter')
    legend.setStyleFont(QgsLegendStyle.Title, QFont('Arial', 9))
    legend.setStyleFont(QgsLegendStyle.Subgroup, QFont('Arial', 7))
    legend.setStyleFont(QgsLegendStyle.SymbolLabel, QFont('Arial', 7))
    legend.setSymbolWidth(9)
    legend.setSymbolHeight(5)
    legend.attemptSetSceneRect(QRectF(124, 12, 80, 190))
    root = legend.model().rootGroup()
    root.clear()
    root.addLayer(layer)
    legend.setFrameEnabled(False)
    layout.addLayoutItem(legend)

    scale_bar = QgsLayoutItemScaleBar(layout)
    scale_bar.setLinkedMap(map_item)
    scale_bar.setStyle('Single Box')
    scale_bar.setUnits(QgsUnitTypes.DistanceMeters)
    scale_bar.setNumberOfSegments(2)
    scale_bar.setUnitsPerSegment(100)
    scale_bar.setUnitLabel('m')
    scale_bar.setFont(QFont('Arial', 7))
    scale_bar.attemptMove(QgsLayoutPoint(12, 196, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(scale_bar)

    exporter = QgsLayoutExporter(layout)
    written = []

    image_settings = QgsLayoutExporter.ImageExportSettings()
    image_settings.dpi = EXPORT_DPI
    image_path = OUTPUT_PATH / f'testkart_{layer.name()}.png'
    if exporter.exportToImage(str(image_path), image_settings) == QgsLayoutExporter.Success:
        written.append(image_path)

    pdf_settings = QgsLayoutExporter.PdfExportSettings()
    pdf_settings.dpi = EXPORT_DPI
    pdf_path = OUTPUT_PATH / f'testkart_{layer.name()}.pdf'
    if exporter.exportToPdf(str(pdf_path), pdf_settings) == QgsLayoutExporter.Success:
        written.append(pdf_path)

    return written


def main() -> int:
    '''Execute as standalone script'''

    mapping_scale = sys.argv[1] if len(sys.argv) > 1 else 'M020'

    QgsApplication.setPrefixPath(QgsApplication.prefixPath(), True)
    application = QgsApplication([], False)
    application.initQgis()

    project = QgsProject.instance()
    project.setCrs(QgsCoordinateReferenceSystem('EPSG:25832'))
    unit_codes = load_unit_codes(mapping_scale)

    backdrop = backdrop_layer()
    if backdrop:
        project.addMapLayer(backdrop, False)
        print('Backdrop: Kartverket topografisk gråtone')
    else:
        print('Backdrop: none (Kartverket WMTS not reachable)')

    for layer in polygon_layers():
        used = style_layer(layer, mapping_scale, unit_codes)
        project.addMapLayer(layer, False)
        print(f'{layer.name()}: {layer.featureCount()} polygons, {len(used)} units')
        for path in export_map(project, layer, backdrop, layer.name()):
            print(f'  wrote {path.relative_to(REPO_ROOT)}')

    project_path = OUTPUT_PATH / 'testkart.qgz'
    project.write(str(project_path))
    print(f'Wrote {project_path.relative_to(REPO_ROOT)}')

    application.exitQgis()
    return 0


if __name__ == '__main__':
    sys.exit(main())
