'''Creates an empty geopackage (.gpkg) with vectors and attribute tables for NiN-mapping'''
# -*- coding: utf-8 -*-

import csv
import os
from pathlib import Path
from typing import Any, Union

from qgis.core import (
    QgsField, QgsVectorFileWriter,
    QgsCoordinateTransformContext, QgsVectorLayer,
    QgsFeature, edit
)
from qgis.PyQt.QtCore import QVariant

try:
    from qgis.PyQt.QtCore import QMetaType
    _FIELD_TYPES = {
        'Int': QMetaType.Type.Int,
        'String': QMetaType.Type.QString,
        'Date': QMetaType.Type.QDate,
        'Double': QMetaType.Type.Double,
        'DateTime': QMetaType.Type.QDateTime,
        'Bool': QMetaType.Type.Bool,
    }
except (ImportError, AttributeError):
    _FIELD_TYPES = {
        'Int': QVariant.Int,
        'String': QVariant.String,
        'Date': QVariant.Date,
        'Double': QVariant.Double,
        'DateTime': QVariant.DateTime,
        'Bool': QVariant.Bool,
    }

ATTRIBUTE_TABLES_PATH = Path(__file__).parent / 'csv' / \
    'attribute_tables'
FIELD_DEFINITIONS_CSV_PATH = Path(__file__).parent / \
    'csv' / 'layer_fields_meta'


def _read_csv_rows(csv_path: Union[str, Path]) -> list[dict[str, str]]:
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        return list(csv.DictReader(csv_file))


def _normalize_attribute_value(value: Any) -> Any:
    if value == '':
        return None

    if isinstance(value, str):
        stripped_value = value.strip()
        if stripped_value.lower() in {'true', 'false'}:
            return stripped_value.lower() == 'true'
        return stripped_value

    return value


def get_qvariant(qvariant: str) -> Any:
    '''
    Returns QVariant object for corresponding short-hand strings.
    Raises an error if provided string does not match a supported QVariant type.
    '''

    if qvariant not in _FIELD_TYPES:
        raise ValueError(f"QVariant type '{qvariant}' not supported!")
    return _FIELD_TYPES[qvariant]


def create_empty_layer(
    layer_name: str,
    geometry: Union[str, None],
    # crs: Union[str, None] = 'epsg:25833',
    crs: str,
    data_provider: str = 'memory',
) -> QgsVectorLayer:
    '''
    Creates and returns a layer (in memory by default).

    Geometry needs to be one of: ('point', 'linestring', 'polygon', 'multipoint', 'multilinestring', 'multipolygon')
    or None for geometry-less features (e.g, attribute tables).

    https://gis.stackexchange.com/questions/183692/creating-geometry-less-memory-layer-using-pyqgis
    '''

    layer = QgsVectorLayer(
        path=f'{geometry}?crs={crs}&index=yes' if geometry else 'None',
        baseName=layer_name,
        providerLib=data_provider,
        options=QgsVectorLayer.LayerOptions(),
    )

    return layer


def write_layer_to_gpkg_file(
    gpkg_out_path: Union[str, Path],
    layer: QgsVectorLayer,
    extend_existing: bool = True,
) -> None:
    '''
    Creates or extends a geopackage file with a provided layer.

    https://gis.stackexchange.com/questions/417916/creating-empty-layers-in-a-geopackage-using-pyqgis
    '''

    # Set QgsVectorFileWriter options
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = layer.name()
    options.driverName = "GPKG"
    options.fileEncoding = "UTF-8"
    options.layerOptions = ['ENCODING=UTF-8']

    # Add to existing gpkg?
    if extend_existing:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

    # Printing for debugging
    #  print(f"Writing layer to '{gpkg_out_path}'")

    QgsVectorFileWriter.writeAsVectorFormatV3(
        layer=layer,
        fileName=str(gpkg_out_path),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )


def add_layer_attributes_from_file(
    attribute_csv_file_path: str,
    layer: QgsVectorLayer,
) -> QgsVectorLayer:
    '''
    Adds new fields with meta info defined in csv file
    to an empty QgsVectorLayer.

    attribute_csv_file_path: path to .csv file containing field meta
    information (see files for required format).
    layer: QgsVectorLayer where fields will be added.

    https://gis.stackexchange.com/questions/262549/pyqgis-adding-fields-to-a-feature-layer
    '''

    attribute_rows = _read_csv_rows(attribute_csv_file_path)

    data_provider = layer.dataProvider()

    for row in attribute_rows:

        # Extract and cast attribute metadata
        attribute_name = str(row['name'])
        attribute_length = int(row['length'])
        attribute_precision = int(row['precision'])
        attribute_type = str(row['type'])

        try:
            data_provider.addAttributes(
                [QgsField(
                    name=attribute_name,
                    type=get_qvariant(attribute_type),
                    # Field type (e.g., char, varchar, text, int, serial, double) -> not needed for now
                    typeName='',
                    len=attribute_length,
                    prec=attribute_precision,
                )]
            )  # add field to layer
            layer.updateFields()  # update vector layer from the datasource

        except Exception as exception:
            print(
                f"Could not create attribute {attribute_name} from {attribute_csv_file_path}. Check the csv for correct formatting!"
            )
            raise exception

    return layer


def add_attribute_values_from_csv(
    layer: QgsVectorLayer,
    csv_path: Union[str, Path],
) -> QgsVectorLayer:
    '''
    Reads attributes defined in a .csv table and adds them
    to a geometry-less vector layer (to store as attribute
    table in the geopackage).

    layer: empty QgsVectorLayer that has the same field names as column names in .csv table.
    csv_path: path to the corresponding .csv file.

    https://gis.stackexchange.com/questions/330269/adding-values-to-field-using-pyqgis
    '''

    attribute_rows = _read_csv_rows(csv_path)
    field_names = [field.name() for field in layer.fields()]

    with edit(layer):
        # Add new features
        for _ in attribute_rows:
            layer.addFeature(QgsFeature(layer.fields()))

    with edit(layer):

        # Loop through dataframe rows
        for idx, feature in enumerate(layer.getFeatures()):
            row = attribute_rows[idx]

            for col_name in field_names:
                field_idx = layer.fields().lookupField(col_name)
                new_value = _normalize_attribute_value(row.get(col_name, ''))

                layer.changeAttributeValue(
                    feature.id(), field_idx, new_value
                )

    return layer


def main(
    selected_mapping_scale: str,
    gpkg_path: Union[str, Path],
    proj_crs: str,
) -> None:
    '''
    Creates new geopackage (.gpkg) based on definitions in csv file.
    Passing variable from mapping scale selection in the UI.
    '''

    # If gpkg-file already exists, remove it (previously confirmed by user)
    if gpkg_path.is_file():
        os.remove(gpkg_path)

    # Define paths to attribute csvs
    nin_polygons_meta_csv_path = FIELD_DEFINITIONS_CSV_PATH \
        / 'nin_polygons_meta.csv'

    # Define CRS string (EPSG:25833 -> ETRS89 / UTM zone 33N)
    # crs = "epsg:25833"
    crs = proj_crs

    # Create NiN multipolygon layer
    # print(
    #    f"Creating NiN multipolygon layer with attributes defined in {nin_polygons_meta_csv_path}."
    # )
    nin_polygons_layer = create_empty_layer(
        layer_name='nin_polygons',
        geometry='multipolygon',
        crs=crs,
        data_provider='memory',
    )

    # Add attributes to nin polygon layer from csv file
    nin_polygons_layer = add_layer_attributes_from_file(
        attribute_csv_file_path=nin_polygons_meta_csv_path,
        layer=nin_polygons_layer,
    )

    # Save to created geopackage
    write_layer_to_gpkg_file(
        gpkg_out_path=gpkg_path,
        layer=nin_polygons_layer,
        extend_existing=False,  # Create new .gpkg here!
    )

    # print("Written nin polygon layer to .gpkg file.")

    # Add helper point layer
    helper_point_layer = create_empty_layer(
        layer_name='nin_helper_points',
        geometry='multipoint',
        crs=crs,
        data_provider='memory',
    )

    with edit(helper_point_layer):
        provider = helper_point_layer.dataProvider()
        provider.addAttributes([QgsField("Comment", _FIELD_TYPES['String'])])
        helper_point_layer.updateFields()

    write_layer_to_gpkg_file(
        gpkg_out_path=gpkg_path,
        layer=helper_point_layer,
        extend_existing=True,
    )

    # Remove vector layers from memory
    del nin_polygons_layer, helper_point_layer

    # Create attribute tables! MAKE SURE .CSV FILES EXIST AND ARE NAMED CORRECTLY
    table_names = (
        'typer',
        'hovedtypegrupper',
        'hovedtyper',
        selected_mapping_scale,
        f"var_{selected_mapping_scale}"
    )

    for name in table_names:

        table_layer = create_empty_layer(
            layer_name=name,
            geometry=None,
            crs=None,
            data_provider='memory',
        )
        # Add fields to attribute table
        table_layer = add_layer_attributes_from_file(
            attribute_csv_file_path=(
                FIELD_DEFINITIONS_CSV_PATH / f'{name}_meta.csv'
            ),
            layer=table_layer,
        )
        # Populate attribute table
        table_layer = add_attribute_values_from_csv(
            layer=table_layer,
            csv_path=ATTRIBUTE_TABLES_PATH / f'{name}_attribute_table.csv',
        )
        # Write to .gpkg
        write_layer_to_gpkg_file(
            gpkg_out_path=gpkg_path,
            layer=table_layer,
            extend_existing=True,
        )

        del table_layer

    print(
        f"Created new .gpkg file in '{gpkg_path}'."
    )
