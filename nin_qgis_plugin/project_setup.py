'''Adapt project setting for NiN-mapping'''

from pathlib import Path
from typing import Union, Literal, List
import random
import pandas as pd
import os
from qgis.core import (
    QgsDataProvider, 
    QgsVectorLayer, 
    QgsProject,
    QgsEditorWidgetSetup, 
    QgsCoordinateReferenceSystem,
    QgsRelation, 
    QgsCategorizedSymbolRenderer, 
    QgsRendererCategory, 
    QgsSymbol, 
    QgsApplication,
    QgsProject,
    QgsVectorFileWriter,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QMessageBox,
)


def load_gpkg_layers(gpkg_path: Union[str, Path]) -> List[QgsVectorLayer]:
    '''
    Loads all .gpkg layers into current QGIS project.

    Returns list of QgsVectorLayers contained in geopackage.
    '''

    layer = QgsVectorLayer(
        str(gpkg_path),
        "test",
        "ogr"
    )

    sub_layers = layer.dataProvider().subLayers()
    sub_vlayers = []

    for sub_layer in sub_layers:

        name = sub_layer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
        uri = f"{gpkg_path}|layername={name}"

        # Create layer
        sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
        sub_vlayers.append(sub_vlayer)

        # Add layer to map
        QgsProject.instance().addMapLayer(sub_vlayer)

    return sub_vlayers


def field_to_value_relation(
    primary_attribute_table_layer: QgsVectorLayer,  # E.g.: nin_polygons_layer
    forgein_attribute_table_layer: QgsVectorLayer,  # E.g.: hovedtyper_layer
    primary_key_field_name: str,  # E.g.: 'hovedtype'
    foreign_key_field_name: str,  # E.g.: 'fid'
    foreign_field_to_display: str,  # E.g.: 'navn'
    filter_expression: str,  # E.g.: '''"typer_fkey" = current_value('type')'''
) -> bool:
    '''
    Configures the QGIS widget to display only relevant subtypes in
    the hierarchichal NiN relationships when assigning polygon attributes
    (type -> hovedtypegruppe -> hovedtype -> etc.).

    https://gisunchained.wordpress.com/2019/09/30/configure-editing-form-widgets-using-pyqgis/

    params:
    filter_expression: QGIS filter expression as a string. Field names in double quotes, strings in single quotes.
    '''

    # foreign_fields = forgein_attribute_table_layer.fields()

    config = {
        'AllowMulti': False,
        'AllowNull': True,
        'FilterExpression': filter_expression,  # QgsExpression()?
        'Key': foreign_key_field_name,
        'Layer': forgein_attribute_table_layer.id(),  # Foreign key layer by ID
        'NofColumns': 1,
        'OrderByValue': True,
        'UseCompleter': False,
        'Value': foreign_field_to_display,
    }

    try:
        primary_fields = primary_attribute_table_layer.fields()
        field_idx = primary_fields.indexOf(primary_key_field_name)
        widget_setup = QgsEditorWidgetSetup('ValueRelation', config)

        primary_attribute_table_layer.setEditorWidgetSetup(
            field_idx,
            widget_setup
        )

        return True

    except Exception as exception:
        raise exception


def set_relation(
    parent_layer: QgsVectorLayer,
    child_layer: QgsVectorLayer,
    relation_name: str,
    child_fkey_field_name: str,
    parent_pkey_field_name: str,
    relation_id: str,
    relation_strength: Literal["comp", "asso"],
) -> QgsVectorLayer:
    '''
    Defines field relationships in layers.

    Template from Anne's code.
    '''

    rel = QgsRelation()

    rel.setName(relation_name)  # name of relation
    rel.setReferencedLayer(parent_layer.id())  # parent layer
    rel.setReferencingLayer(child_layer.id())  # child layer
    rel.addFieldPair(
        # first element are the field names of the foreign key
        referencingField=child_fkey_field_name,
        referencedField=parent_pkey_field_name,
    )
    # id of relation
    rel.setId(relation_id)

    # strength of relation
    if relation_strength == "comp":
        rel.setStrength(QgsRelation.Composition)
    elif relation_strength == "asso":
        rel.setStrength(QgsRelation.Association)
    else:
        raise ValueError(
            f"relation_strength='{relation_strength}' not supported! "
            + "Must be 'comp' or 'asso'."
        )

    # add this realtion to the project
    QgsProject.instance().relationManager().addRelation(rel)

def main(
    selected_items: list,
    selected_type_id: str,
    gpkg_path: Union[str, Path],
    selected_mapping_scale="M005",
) -> None:
    '''Adapt QGIS project settings.'''

    if not selected_items:
        QMessageBox.information(
            None,
            "No hovedtypegrupper selected!",
            "Please select the 'hovedtypegrupper' you want to map."
        )
        return

    # passing the selected "Type" from the UI
    if not selected_type_id:
        QMessageBox.information(
            None,
            "No type selected!",
            "Please select the 'type' you want to map."
        )
        return

    # Get the project instance
    project = QgsProject.instance()

    # Define name and path of existing geopackage
    # TODO: Remove after testing!
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name

    # Declare a SpatialReference
    # PostGIS SRID 25833 is allocated for ETRS89 UTM-zone 33N
    crs = QgsCoordinateReferenceSystem.fromEpsgId(25833)
    if crs.isValid():
        project.setCrs(crs)
    else:
        print("Invalid CRS!")

    # Load all layers from geopackage
    _ = load_gpkg_layers(gpkg_path)

    if selected_items:
        selected_kode_ids = [f"'{item['kode_id']}'" for item in selected_items]
        # passing the selected "Hovedtypegrupper" from the UI
        additional_filter = \
            f'"kode_id" IN ({", ".join(map(str, selected_kode_ids))})'
            
    #selected_type_id = "'" + selected_type_id + "'"

    relations_to_set = (
        {
            "primary_attribute_table_layer": QgsProject.instance().mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QgsProject.instance().mapLayersByName('typer')[0],
            "primary_key_field_name": "type",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f""""kode_id" = '{selected_type_id}'""",
        },
        {
            "primary_attribute_table_layer": QgsProject.instance().mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QgsProject.instance().mapLayersByName('hovedtypegrupper')[0],
            "primary_key_field_name": "hovedtypegruppe",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f'''"typer_fkey" = current_value('type') AND {additional_filter}''' if additional_filter else '''"typer_fkey" = current_value('type')''',
        },
        {
            "primary_attribute_table_layer": QgsProject.instance().mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QgsProject.instance().mapLayersByName('hovedtyper')[0],
            "primary_key_field_name": "hovedtype",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe')''',
        },
        {
            "primary_attribute_table_layer": QgsProject.instance().mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QgsProject.instance().mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype')''',
        },
        {
            "primary_attribute_table_layer": QgsProject.instance().mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QgsProject.instance().mapLayersByName(f"var_{selected_mapping_scale}")[0],
            "primary_key_field_name": "variabler",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "display_str",
            "filter_expression": '''"grunntype_or_kle_fkey" = current_value('grunntype_or_klenhet')''',
        },
    )

    for rel in relations_to_set:

        field_to_value_relation(
            primary_attribute_table_layer=rel["primary_attribute_table_layer"],
            forgein_attribute_table_layer=rel["forgein_attribute_table_layer"],
            primary_key_field_name=rel["primary_key_field_name"],
            foreign_key_field_name=rel["foreign_key_field_name"],
            foreign_field_to_display=rel["foreign_field_to_display"],
            filter_expression=rel["filter_expression"],
        )

    # Here we set the random color categorized symbology for each 'kode_id' of the mapping units and label also with 'kode_id'
    # Load the attribute table
    attribute_table_path = f'csv/attribute_tables/{selected_mapping_scale}_attribute_table.csv'
    attribute_table = pd.read_csv(attribute_table_path)

    # Function to generate random color
    def random_color():
        return [random.randint(0, 255) for _ in range(3)]

    # Load the layer
    layer = QgsProject.instance().mapLayersByName('nin_polygons')[0] #QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", layer_name, "ogr")
    if not layer.isValid():
        print(f"Failed to load layer nin_polygons")
    else:
        print(f"Layer nin_polygons loaded successfully")

        # Prepare categorized symbology
        categories = []
        unique_values = attribute_table['kode_id'].unique()

        for value in unique_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            color = random_color()
            symbol.setColor(QColor(color[0], color[1], color[2]))
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer('kode_id', categories)
        layer.setRenderer(renderer)

        # Set up labeling
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = 'kode_id'
        label_settings.placement = QgsPalLayerSettings.OverPoint
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        text_format.setColor(QColor(0, 0, 0))  # Black color for text

        label_settings.setFormat(text_format)
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabelsEnabled(True)
        layer.setLabeling(labeling)
        layer.triggerRepaint()

        # Add the layer to the project
        project = QgsProject.instance()
        project.addMapLayer(layer)

