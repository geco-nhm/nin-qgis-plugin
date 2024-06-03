'''Creates an empty geopackage (.gpkg) with vectors and attribute tables for NiN-mapping'''
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Any, Union
import pandas as pd
import numpy as np

from qgis.core import (
    QgsApplication, QgsFields,
    QgsField, QgsWkbTypes, QgsVectorFileWriter,
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext, QgsVectorLayer,
    QgsFeatureRequest, QgsDataProvider, QgsFeature,
    QgsRelation, edit
)
from qgis.PyQt.QtCore import QVariant

ATTRIBUTE_TABLES_PATH = Path(__file__).parent / 'csv' / 'attribute_tables'
FIELD_DEFINITIONS_CSV_PATH = Path(__file__).parent / 'csv' / 'layer_fields_meta'


def get_qvariant(qvariant: str) -> Any:
    '''
    Returns QVariant object for corresponding short-hand strings.
    Raises an error if provided string does not match a supported Qvariant type.
    '''

    if qvariant == 'Int':
        return QVariant.Int
    if qvariant == 'String':
        return QVariant.String
    if qvariant == 'Date':
        return QVariant.Date
    if qvariant == 'Double':
        return QVariant.Double
    if qvariant == 'DateTime':
        return QVariant.DateTime
    if qvariant == 'Bool':
        return QVariant.Bool
    raise ValueError("Qvariant Type not supported!")


def create_empty_gpkg(
    gpkg_save_path: Union[str, Path],
    crs: str,
) -> None:
    '''
    Creates an empty geopackage (.gpkg file) with a specified geometry and crs.

    TODO: legacy code, can be fully replaced with write_layer_to_gpkg_file()!
    '''

    # Set QgsVectorFileWriter options
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.fileEncoding = "UTF-8"

    # Create an empty GeoPackage
    _writer = QgsVectorFileWriter.create(
        str(gpkg_save_path),
        QgsFields(),  # No fields yet
        QgsWkbTypes.NoGeometry,  # No geometry for the empty gpkg
        QgsCoordinateReferenceSystem(crs),  # Specify the CRS
        QgsCoordinateTransformContext(),
        options,
    )  # Format

    # Release the file writer to flush changes to disk
    del _writer


def create_empty_layer(
    layer_name: str,
    geometry: Union[str, None],
    crs: Union[str, None] = 'epsg:25833',
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
    Creates or extends a geopackage file with a specified layer.

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

    print(f"Writing layer to '{gpkg_out_path}'")

    QgsVectorFileWriter.writeAsVectorFormatV3(
        layer=layer,
        fileName=str(gpkg_out_path),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )


def copy_layer(gpkg_path: str, layer_name: str) -> QgsVectorLayer:
    '''
    Duplicates a layer loaded in memory.

    https://gis.stackexchange.com/questions/205947/duplicating-layer-in-memory-using-pyqgis
    '''

    previous_layer = QgsVectorLayer(
        str(gpkg_path),
        layer_name,
        "ogr"
    )  # Open existing gpkg-file fuglepunkter with the one layer fuglepunkter
    previous_layer.selectAll()  # select all features in fuglepunkter layer
    new_layer = previous_layer.materialize(
        QgsFeatureRequest().setFilterFids(
            previous_layer.selectedFeatureIds()
        )
    )  # create a new layer from selected features
    previous_layer.removeSelection()  # remove selection in the original layer

    return new_layer


def add_layer_attributes_from_file(
    attribute_csv_file_path: str,
    layer: QgsVectorLayer,
) -> QgsVectorLayer:
    '''
    Adds attributes defined in csv file to a QgsVectorLayer.

    https://gis.stackexchange.com/questions/262549/pyqgis-adding-fields-to-a-feature-layer
    '''

    attribute_df = pd.read_csv(
        attribute_csv_file_path,
        delimiter=",",  # comma delimited
        header=0,  # Column names stored in row 0
    )

    data_provider = layer.dataProvider()

    for _, row in attribute_df.iterrows():

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
    Hallo.

    https://gis.stackexchange.com/questions/330269/adding-values-to-field-using-pyqgis
    '''

    # Read csv
    attribute_df = pd.read_csv(
        csv_path,
        index_col=False,
        delimiter=",",  # comma delimited
        header=0,  # Column names stored in row 0
    ).infer_objects()

    with edit(layer):
        # Add new features
        for _ in range(attribute_df.shape[0]):
            layer.addFeature(QgsFeature(layer.fields()))

    with edit(layer):

        # Loop through dataframe rows
        for idx, feature in enumerate(layer.getFeatures()):

            for col_name in attribute_df.columns:
                field_idx = layer.fields().lookupField(col_name)
                new_value = attribute_df.loc[idx, col_name]

                # TODO: this is hacking around the fact that layer.changeAttributeValue()
                # cannot deal with numpy data types from pandas. Need a more sustainable
                # solution!
                
                if pd.isnull(new_value):
                    new_value = None
                elif isinstance(new_value, np.int64):
                    new_value = int(new_value)
                elif isinstance(new_value, np.float64):
                    new_value = float(new_value)

                layer.changeAttributeValue(
                    feature.id(), field_idx, new_value
                )

    return layer


def create_table_from_csv(
    csv_path: str,
    gpkg_path: str,
    layer_name: str,
) -> None:
    '''
    Creates a vector format Table from a csv.

    https://gis.stackexchange.com/questions/364211/importing-csv-table-to-geopackage-with-pyqgis-using-csv-file-name
    '''

    table = QgsVectorLayer(csv_path, "csv", 'delimitedtext')
    opt = QgsVectorFileWriter.SaveVectorOptions()
    opt.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
    opt.layerName = layer_name
    opt.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    tw = QgsVectorFileWriter.writeAsVectorFormatV3(
        table,
        gpkg_path,
        QgsCoordinateTransformContext(),
        opt
    )

    del tw


def set_style(layer: str, lname: str) -> None:
    '''
    Sets styles defined in a .qml file. TODO.

    https://gis.stackexchange.com/questions/276743/saving-styles-for-all-layers-using-pyqgis-sld-qml-databases
    '''

    # lyr = QgsVectorLayer(layer,lname,"ogr")
    # name = lyr.name()
    # lyr.loadNamedStyle('S:/.../qml/'+lname+'.qml')
    # lyr.saveStyleToDatabase(name,'style '+lname,True,'')
    pass

def main(selected_mapping_scale: str, gpkg_path: Union[str, Path]) -> None:
    '''Creates new NiN-conforming gpkg based on definitions in csv file.
        Passing variable from mapping scale selection in the UI
    '''

    # Define name and path of new geopackage
    # NEXT IS OVERWRITING gpkg_path FOR TESTING, REMOVE IN THE END
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name
    if gpkg_path.is_file():  # If gpkg-file already exists, raise Error
        os.remove(gpkg_path)
        # raise ValueError(f"{gpkg_path} already exists! Use a different name to avoid data loss.")

    # Define paths to attribute csvs
    nin_polygons_meta_csv_path = FIELD_DEFINITIONS_CSV_PATH \
        / 'nin_polygons_meta.csv'

    # Define CRS string (EPSG:25833 -> ETRS89 / UTM zone 33N)
    crs = "epsg:25833"

    # Create NiN multipolygon layer
    print(
        f"Creating NiN multipolygon layer with attributes defined in {nin_polygons_meta_csv_path}."
    )
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

    print("Written nin polygon layer to .gpkg file.")

    # Add helper point layer for testing
    helper_point_layer = create_empty_layer(
        layer_name='nin_helper_points',
        geometry='multipoint',
        crs=crs,
        data_provider='memory',
    )

    with edit(helper_point_layer):
        provider = helper_point_layer.dataProvider()
        provider.addAttributes([QgsField("Comment", QVariant.String)])
        helper_point_layer.updateFields()

    write_layer_to_gpkg_file(
        gpkg_out_path=gpkg_path,
        layer=helper_point_layer,
        extend_existing=True,
    )

    # Remove vector layers from memory
    del nin_polygons_layer, helper_point_layer

    # Create attribute tables! MAKE SURE .CSV FILES EXIST AND ARE NAMED CORRECTLY
    
    # TODO: Here we need to fetch info from the plugin selection!
    
    table_names = ('typer', 'hovedtypegrupper', 'hovedtyper', selected_mapping_scale)

    for name in table_names:

        table_layer = create_empty_layer(
            layer_name=name,
            geometry=None,
            crs=None,
            data_provider='memory',
        )
        # Add fields to attribute table
        table_layer = add_layer_attributes_from_file(
            attribute_csv_file_path=FIELD_DEFINITIONS_CSV_PATH / f'{name}_meta.csv',
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
