'''Creates an empty geopackage (.gpkg) with vectors and attribute tables for NiN-mapping'''
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Any, Union
import pandas as pd

from qgis.core import (
    QgsApplication, QgsFields,
    QgsField, QgsWkbTypes, QgsVectorFileWriter,
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext, QgsVectorLayer,
    QgsFeatureRequest, QgsDataProvider
)
from qgis.PyQt.QtCore import QVariant

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

    Geometry needs to be one of: ('point', 'linestring', 'polygon', 'multipoint', 'multilinestring', 'multipolygon') or None.

    If crs is None, a layer with no geometry (for tables) is created.
    https://gis.stackexchange.com/questions/183692/creating-geometry-less-memory-layer-using-pyqgis
    '''

    layer = QgsVectorLayer(
        path=f'{geometry}?crs={crs}&index=yes' if geometry else 'None',
        baseName=layer_name,
        providerLib=data_provider,
        options=QgsVectorLayer.LayerOptions(),
    )

    return layer

    """
    # Constructor
    # QgsVectorLayer(path: str = '', baseName: str = '', providerLib: str = '', options: QgsVectorLayer.LayerOptions = QgsVectorLayer.LayerOptions())
    layer = QgsVectorLayer(
        path="",
        baseName="",
        providerLib="",
        options=QgsVectorLayer.LayerOptions(),
    )

    # QgsFeature(fields: QgsFields, id: int = FID_NULL) Constructor for QgsFeature

    # Create new layer in memory
    layer_name = 'vegreg'
    crs = 'epsg:25833'
    layer = QgsVectorLayer(f'multipoint?crs={crs}', layer_name, 'memory')  # points for testing
    QgsProject.instance().addMapLayer(layer)
    geom = QgsWkbTypes.NoGeometry
    crs = ''
    fields = QgsFields()
    fields.append(QgsField("delomr", QVariant.String, '', 1, 0))            # a-f
    fields.append(QgsField("vegtype", QVariant.String, '', 50, 0))          # delområdets vegetasjonstype
    fields.append(QgsField("pdekning", QVariant.Int, '', 3, 0))			    # aktuell vegetasjonsdekkeandel
    fields.append(QgsField("vr_id", QVariant.String, '', 38, 0))            # Relasjon mellom NYE punkter i vv_vegtype med vegtypedekning
    """


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
    #options.layerName = new_layer_name

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


    #if writer_result == QgsVectorFileWriter.NoError:
    #    print("Success!")
    #else:
    #    print(error_message)

    """
    file_writer = QgsVectorFileWriter.create(
        fileName=str(gpkg_out_path),
        fields=layer.fields(),
        geometryType=layer.wkbType(),
        srs=layer.crs(),  #QgsCoordinateReferenceSystem(crs),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )
    """
"""
def create_gpkg_from_layer(
    layer_name: str,
    layer: QgsVectorLayer,
    gpkg_path: str,
    append: bool = False,
) -> bool:
    '''
    Creates a new geopackage (.gpkg) file with a NiN-compliant vector layer.

    https://gis.stackexchange.com/questions/435772/pyqgis-qgsvectorfilewriter-writeasvectorformatv3-export-z-dimension-not-workin
    '''

    # To add a layer to an existing GPKG file, pass 'append' as True
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name

    if append:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

    writer_result, error_message = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer=layer,
        fileName=str(gpkg_path),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )

    if writer_result == QgsVectorFileWriter.NoError:
        print ("Success!")
    else:
        print (error_message)

    return True
"""

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
    )  #create a new layer from selected features
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
        delimiter=";",
        header=0,
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
                    typeName='',  # Field type (e.g., char, varchar, text, int, serial, double) -> not needed for now
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

    print(attribute_df)

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
    Sets styles defined in a .qml file.

    https://gis.stackexchange.com/questions/276743/saving-styles-for-all-layers-using-pyqgis-sld-qml-databases
    '''

    #lyr = QgsVectorLayer(layer,lname,"ogr")
    #name = lyr.name()
    #lyr.loadNamedStyle('S:/.../qml/'+lname+'.qml')
    #lyr.saveStyleToDatabase(name,'style '+lname,True,'')
    pass


def main() -> None:
    '''Creates new NiN-conforming gpkg based on definitions in csv file.'''

    # # All spatial layers and non-spatial tables are saved in the same geopackage-file fugleregistrering.gpkg
    # gpkg_pkt = "S:/.../gpkg/fuglepunkter.gpkg"  # existing gpkg with 1162 fuglepunkter, fields flatenr and pnr exists

    ###### Hvis man skal kopiere et lag i en gpkg-fil #####
    # # Åpner fuglepunkter.gpkg, kopierer alle punkter til nytt layer fugleobs, legger til egenskaper og lagrer i NY gpkg-fil: fugleregistrering.gpkg.
    # # data provider is the connection to the underlying file or db that holds the geospatial information to be displayed
    # newlyr = copy_layer(gpkg_pkt,"fuglepunkter")  # make a copy of the fuglepunkter layer
    # pr = newlyr.dataProvider()  # you access the real datasource behind your layer
    # nl = add_layer_attributes_from_file("S:\\Forvaltning\\Geomatikk\\abni\\fugler\\egenskaper\\egenskaper_fugleobs.csv", pr, newlyr)  # add fields from csv-file to this copy
    # create_gpkg_layer("fugleobs", nl, gpkg_reg)  # Save as new layer fugleobs, geometry type and crs inherited from original point-layer
    #####

    # Define name and path of new geopackage
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name
    if gpkg_path.is_file():  # If gpkg-file already exists, raise Error
        os.remove(gpkg_path)
        #raise ValueError(f"{gpkg_path} already exists! Define a different one to avoid data loss.")

    # Define path to attribute csv
    nin_attributes_csv_path = Path(__file__).parent / 'bird_attributes_test.csv'

    # Define CRS string (EPSG:25833 -> ETRS89 / UTM zone 33N)
    crs = 'epsg:25833'

    # Create empty geopackage
    print(f"Creating empty geopackage in {gpkg_path}.")
    create_empty_gpkg(
        gpkg_save_path=gpkg_path,
        crs=crs,
    )

    # Create NiN multipolygon layer
    print(f"Creating NiN multipolygon layer with attributes defined in {nin_attributes_csv_path}.")
    nin_polygons_layer = create_empty_layer(
        layer_name='nin_polygons',
        geometry='multipolygon',
        crs=crs,
        data_provider='memory',
    )

    #QgsProject.instance().addMapLayer(layer)

    # Add attributes to nin polygon layer from csv file
    nin_polygons_layer = add_layer_attributes_from_file(
        attribute_csv_file_path=nin_attributes_csv_path,
        layer=nin_polygons_layer,
    )

    # Save to created geopackage
    write_layer_to_gpkg_file(
        gpkg_out_path=gpkg_path,
        layer=nin_polygons_layer,
        extend_existing=True,
    )

    print("Written nin polygon layer to gpkg. Now add another one for testing.")

    helper_point_layer = create_empty_layer(
        layer_name='nin_helper_points',
        geometry='multipoint',
        crs=crs,
        data_provider='memory',
    )

    # Get the data provider of the layer
    helper_point_layer.startEditing()
    provider = helper_point_layer.dataProvider()
    provider.addAttributes([QgsField("Comment", QVariant.String)])
    helper_point_layer.updateFields()
    helper_point_layer.commitChanges()

    write_layer_to_gpkg_file(
        gpkg_out_path=gpkg_path,
        layer=helper_point_layer,
        extend_existing=True,
    )

    # Remove layers from memory
    del nin_polygons_layer, helper_point_layer


    '''
    # Add a cvs-file as a table in the gpkg
    # Layer 3 fugleartsliste
    csv = "file:///S:\\...\\fugler\\egenskaper\\fugleartsliste.csv?delimiter=;"
    lyrname = 'fugleartsliste'
    create_table_from_csv(csv, gpkg_reg, lyrname)

    # Layer 4 vegetasjonstypeliste
    csv = "file:///S:\\...\\fugler\\egenskaper\\vegetasjonstypeliste.csv?delimiter=;"
    lyrname = 'vegetasjonstypeliste'
    create_table_from_csv(csv, gpkg_reg, lyrname)

    # Create tables and add to gpkg
    # Layer 5 vegtypedekning (lagre vegtype med tilhørednde prosentdekning)
    layer_name = "vegreg"
    geom = QgsWkbTypes.NoGeometry
    crs = ''
    fields = QgsFields()
    fields.append(QgsField("delomr", QVariant.String, '', 1, 0))            # a-f
    fields.append(QgsField("vegtype", QVariant.String, '', 50, 0))          # delområdets vegetasjonstype
    fields.append(QgsField("pdekning", QVariant.Int, '', 3, 0))			    # aktuell vegetasjonsdekkeandel
    fields.append(QgsField("vr_id", QVariant.String, '', 38, 0))            # Relasjon mellom NYE punkter i vv_vegtype med vegtypedekning
    create_empty_gpkg(gpkg_reg, layer_name, geom, crs, fields, True)  # create the layer, is added to the same gpkg

    # Layer 6 fuglereg (lagrer art, ant, avst, delomr m.m.)
    layer_name = "fuglereg"
    geom = QgsWkbTypes.NoGeometry
    crs = ''
    fields = QgsFields()
    fields.append(QgsField("art", QVariant.String, '', 50, 0))              # fugleart (norsk - latin)
    fields.append(QgsField("art_annen", QVariant.String, '', 50, 0))        # hvis fugleart mangler i opprinnelige liste
    fields.append(QgsField("ant", QVariant.Int, '', 3, 0))                  # antall hekkende par, hvis 999 skal flokk angis
    fields.append(QgsField("flokk", QVariant.Int, '', 3, 0))                # antall individer hvis flokk
    fields.append(QgsField("avst", QVariant.Int, '', 1, 0))                 # 1,2 eller 3 (innafor/utafor 50 m fra punkt eller mellom punkter)
    fields.append(QgsField("delomr", QVariant.String, '', 1, 0))            # innhold bestemmes av delområder angitt i vegreg
    fields.append(QgsField("fr_id", QVariant.String, '', 38, 0))            # relasjon mellom NYE punkter i fugleartsdekning med fugleobs
    create_empty_gpkg(gpkg_reg, layer_name, geom, crs, fields, True)  # create the layer, is added to the same gpkg 
    # Load qml and save style in geopackage.
    # Layer fugleobs gets style set when QGIS-project is created (see create_project.py) due to the project relations dependency
    set_style('fugleregistrering.gpkg|layername=fuglereg',"fuglereg")
    set_style('fugleregistrering.gpkg|layername=vegreg',"vegreg")
    '''

if __name__ == "__main__":
    main()
