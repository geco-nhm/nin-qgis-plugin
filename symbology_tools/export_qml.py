"""
Exports the symbology as QGIS style files and draws a test map of every
symbol with the QGIS renderer. Needs a Python with QGIS:

    python-qgis-ltr.bat symbology_tools/export_qml.py

    -> symbology/qml/NiN3_M005.qml, NiN3_M020.qml, NiN3_M050.qml
    -> docs/symbology/qgis_M005.png, qgis_M020.png, qgis_M050.png

The style files are for polygon layers with the unit code (for example
'TB01-M005-03') in the field 'kode_id'. The symbols are built by the same
code that the plugin uses, so the test map shows what users will see.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from qgis.core import (  # noqa: E402
    QgsApplication,
    QgsCategorizedSymbolRenderer,
    QgsFeature,
    QgsGeometry,
    QgsMapRendererSequentialJob,
    QgsMapSettings,
    QgsPalLayerSettings,
    QgsRectangle,
    QgsRendererCategory,
    QgsTextBufferSettings,
    QgsTextFormat,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling,
)
from qgis.PyQt.QtCore import QSize  # noqa: E402
from qgis.PyQt.QtGui import QColor, QFont  # noqa: E402

from nin_qgis_plugin.symbology_styles import load_unit_styles  # noqa: E402
from nin_qgis_plugin.symbology_symbols import create_fill_symbol  # noqa: E402

MAPPING_SCALES = ('M005', 'M020', 'M050')

QML_PATH = REPO_ROOT / 'symbology' / 'qml'
IMAGE_PATH = REPO_ROOT / 'docs' / 'symbology'

CODE_FIELD = 'kode_id'

# Test map: one rectangle per unit, in a grid. Sizes in metres on the ground
# and the map is drawn at 1:1000, so 30 m is 30 mm on the map.
TEST_MAP_SCALE = 1000
TEST_MAP_DPI = 150
CELL_WIDTH_M = 34
CELL_HEIGHT_M = 22
CELL_GAP_M = 3
COLUMNS = 12


def create_layer(styles: dict) -> QgsVectorLayer:
    '''Returns a memory layer with one rectangle per unit, styled by code.'''

    layer = QgsVectorLayer(f'Polygon?crs=EPSG:25833&field={CODE_FIELD}:string(30)', 'nin', 'memory')

    features = []
    for index, kode_id in enumerate(styles):
        column, row = index % COLUMNS, index // COLUMNS
        x_min = column * (CELL_WIDTH_M + CELL_GAP_M)
        y_max = -row * (CELL_HEIGHT_M + CELL_GAP_M)

        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromRect(
            QgsRectangle(x_min, y_max - CELL_HEIGHT_M, x_min + CELL_WIDTH_M, y_max)
        ))
        feature.setAttribute(CODE_FIELD, kode_id)
        features.append(feature)

    layer.dataProvider().addFeatures(features)
    layer.updateExtents()

    layer.setRenderer(QgsCategorizedSymbolRenderer(CODE_FIELD, [
        QgsRendererCategory(kode_id, create_fill_symbol(style), kode_id)
        for kode_id, style in styles.items()
    ]))

    return layer


def add_labels(layer: QgsVectorLayer) -> None:
    '''Labels the rectangles of the test map with the short code.'''

    text_buffer = QgsTextBufferSettings()
    text_buffer.setEnabled(True)
    text_buffer.setSize(0.8)
    text_buffer.setColor(QColor(255, 255, 255))

    text_format = QgsTextFormat()
    text_format.setFont(QFont('Arial'))
    text_format.setSize(7)
    text_format.setColor(QColor(0, 0, 0))
    text_format.setBuffer(text_buffer)

    settings = QgsPalLayerSettings()
    settings.fieldName = f"regexp_replace(\"{CODE_FIELD}\", '-[^-]+-', '-')"
    settings.isExpression = True
    settings.setFormat(text_format)

    layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
    layer.setLabelsEnabled(True)


def render_test_map(layer: QgsVectorLayer, image_path: Path) -> None:
    extent = layer.extent()
    extent.grow(CELL_GAP_M)

    # Pixels per metre on the ground when the map is drawn at the test scale
    pixels_per_metre = TEST_MAP_DPI / 25.4 * 1000 / TEST_MAP_SCALE

    settings = QgsMapSettings()
    settings.setLayers([layer])
    settings.setDestinationCrs(layer.crs())
    settings.setOutputDpi(TEST_MAP_DPI)
    settings.setBackgroundColor(QColor(255, 255, 255))
    settings.setExtent(extent)
    settings.setOutputSize(QSize(
        round(extent.width() * pixels_per_metre),
        round(extent.height() * pixels_per_metre),
    ))

    job = QgsMapRendererSequentialJob(settings)
    job.start()
    job.waitForFinished()
    job.renderedImage().save(str(image_path))


def main() -> int:
    '''Execute as standalone script'''

    QgsApplication.setPrefixPath(QgsApplication.prefixPath(), True)
    application = QgsApplication([], False)
    application.initQgis()

    QML_PATH.mkdir(parents=True, exist_ok=True)

    for scale in MAPPING_SCALES:
        styles = load_unit_styles(scale)
        layer = create_layer(styles)

        qml_path = QML_PATH / f'NiN3_{scale}.qml'
        message, success = layer.saveNamedStyle(str(qml_path))
        if not success:
            print(f"Could not write {qml_path}: {message}")
            return 1
        print(f"Wrote {qml_path.relative_to(REPO_ROOT)} ({len(styles)} units)")

        # The test map shows land and wetland, which have symbols of their own
        drawn = {
            kode_id: styles[kode_id] for kode_id in sorted(styles)
            if kode_id.startswith(('T', 'V'))
        }
        test_layer = create_layer(drawn)
        add_labels(test_layer)
        image_path = IMAGE_PATH / f'qgis_{scale}.png'
        render_test_map(test_layer, image_path)
        print(f"Wrote {image_path.relative_to(REPO_ROOT)} ({len(drawn)} units)")

    application.exitQgis()
    return 0


if __name__ == '__main__':
    sys.exit(main())
