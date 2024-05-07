'''Creates a NiN-conforming empty geopackage (.gpkg)'''
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Any
import pandas as pd

from qgis.core import (
    QgsApplication, QgsFields,
    QgsField, QgsWkbTypes, QgsVectorFileWriter,
    QgsProject, QgsCoordinateReferenceSystem,
    QgsCoordinateTransformContext, QgsVectorLayer,
    QgsFeatureRequest, QgsDataProvider
)
from qgis.PyQt.QtCore import QVariant

def set_qvariant(qvariant: str) -> Any:
    '''Returns QVariant object for corresponding short-hand strings'''

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


def create_gpkg_from_layer(
    gpkg_path: str,
    layer_name: str,
    geometry: QgsWkbTypes,
    crs: str,
    fields: QgsFields,
    overwrite_layer: bool = False,
) -> bool:
    '''
    Creates an empty geopackage object with an empty layer of predifined attributes.

    https://gis.stackexchange.com/questions/417916/creating-empty-layers-in-a-geopackage-using-pyqgis
    '''

    # To add a layer to an existing GPKG file, pass 'append' as True
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name

    if overwrite_layer:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

    writer = QgsVectorFileWriter.create(
        fileName=str(gpkg_path),
        fields=fields,
        geometryType=geometry,
        srs=QgsCoordinateReferenceSystem(crs),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )

    del writer

    return True


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

    writer = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer=layer,
        fileName=str(gpkg_path),
        transformContext=QgsCoordinateTransformContext(),
        options=options,
    )

    del writer

    return True


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
    data_provider: QgsDataProvider,
    lyr: QgsVectorLayer,
) -> QgsVectorLayer:
    '''
    Adds attributes defined in csv file to a QGis vector layer.

    https://gis.stackexchange.com/questions/262549/pyqgis-adding-fields-to-a-feature-layer
    '''

    attribute_df = pd.read_csv(
        attribute_csv_file_path,
        delimiter=";",
        header=0,
    )

    for _, row in attribute_df.iterrows():
        # Extract and cast attribute metadata
        attribute_name = str(row['name'])
        attribute_length = int(row['length'])
        attribute_precision = int(row['precision'])
        attribute_type = str(row['type'])

        try:
            data_provider.addAttributes(
                [QgsField(
                    attribute_name,
                    set_qvariant(attribute_type),
                    '',
                    attribute_length,
                    attribute_precision,
                )]
            )  # add field to layer
            lyr.updateFields()  # update vector layer from the datasource

        except Exception as exception:
            print(
				f"Could not create attribute {attribute_name} from {attribute_csv_file_path}."
			)
            raise exception

    print(attribute_df)

    return lyr


# https://gis.stackexchange.com/questions/364211/importing-csv-table-to-geopackage-with-pyqgis-using-csv-file-name
def create_table_from_csv(
    csv_path: str,
    gpkg_path: str,
    layer_name: str,
) -> None:
    '''Creates a vector format Table from a csv.'''

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

    # Define path to attribute csv
    nin_attributes_csv_path = Path(__file__).parent / 'bird_attributes_test.csv'

    print(f"Creating empty layer with attributes from {nin_attributes_csv_path}.")

    # Create new layer in memory
    layer_name = 'NiN-observations'
    crs = 'epsg:25833'
    layer = QgsVectorLayer(f'multipoint?crs={crs}', layer_name, 'memory')  # points for testing
    QgsProject.instance().addMapLayer(layer)
    data_provider = layer.dataProvider()

    # Add attributes to empty polygon layer
    layer = add_layer_attributes_from_file(
        attribute_csv_file_path=nin_attributes_csv_path,
        data_provider=data_provider,
        lyr=layer,
    )

    # the NEW gpkg to be created
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name
    if gpkg_path.is_file():  # If gpkg-file already exists, delete it
        os.remove(gpkg_path)

    create_empty_gpkg(
        gpkg_path=gpkg_path,
        layer_name=layer_name,
        geometry=QgsWkbTypes.PointZ,
        crs=crs,
        fields=QgsFields(),
        append=False,
    )  # Ikke inkl. True når FØRSTE lag lages

    print("Done testing.")

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
