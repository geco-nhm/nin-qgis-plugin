'''Adapt project setting for NiN-mapping'''

from pathlib import Path
from typing import Union, Literal, List
import random
import pandas as pd
import os

from qgis.core import (
    QgsDataProvider,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsEditorWidgetSetup,
    QgsCoordinateReferenceSystem,
    QgsRelation,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol,
    QgsProject,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsDefaultValue,
    QgsLayerTreeLayer,
    QgsSnappingConfig,  # for snapping settings
    QgsTolerance,       # for snapping tolerance type (pixel or project units)
    edit
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QMessageBox,
)

# Import functions from other py-files in the attr_table_field_setings-folder
from .attr_table_field_setings.value_relations import get_value_relations
from .attr_table_field_setings.default_values import get_default_values


QGS_PROJECT = QgsProject.instance()
PROJECT_CRS = "EPSG:25833"


class ProjectSetup:
    '''
    Helper class to adjust the QGIS project options.
    '''

    def __init__(
        self,
        gpkg_path: Union[str, Path],
        selected_type_id: str,
        selected_hovedtypegrupper: List[str],
        selected_mapping_scale: str,
        canvas,
        nin_polygons_layer_name: str = "nin_polygons",
    ) -> None:
        '''Constructor with shared variables'''

        self.gpkg_path = gpkg_path
        self.selected_type_id = selected_type_id
        self.selected_hovedtypegrupper = selected_hovedtypegrupper
        self.selected_mapping_scale = selected_mapping_scale
        self.canvas = canvas
        self.nin_polygons_layer_name = nin_polygons_layer_name

    def load_gpkg_layers(self) -> List[QgsVectorLayer]:
        '''
        Loads all .gpkg layers into current QGIS project.

        Returns list of QgsVectorLayers contained in geopackage.
        '''

        layer = QgsVectorLayer(
            str(self.gpkg_path),
            "test",
            "ogr"
        )

        sub_layers = layer.dataProvider().subLayers()
        sub_vlayers = []

        for sub_layer in sub_layers:

            name = sub_layer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
            uri = f"{self.gpkg_path}|layername={name}"

            # Create layer
            sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
            sub_vlayers.append(sub_vlayer)

            # Add layer to map
            QgsProject.instance().addMapLayer(sub_vlayer)

        return sub_vlayers

    def field_to_value_relation(
        self,
        primary_attribute_table_layer: QgsVectorLayer,  # E.g.: nin_polygons_layer
        forgein_attribute_table_layer: QgsVectorLayer,  # E.g.: hovedtyper_layer
        primary_key_field_name: str,  # E.g.: 'hovedtype'
        foreign_key_field_name: str,  # E.g.: 'fid'
        foreign_field_to_display: str,  # E.g.: 'navn'
        filter_expression: str,  # E.g.: '''"typer_fkey" = current_value('type')'''
        allow_multi_selection: bool = False,
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
            'AllowMulti': allow_multi_selection,
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
        self,
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
        QGS_PROJECT.relationManager().addRelation(rel)

    def set_layer_field_default_values(
        self,
        layer_name: str,
        field_name: str,
        default_value_expression: str,
        make_field_uneditable: bool = True,
    ) -> None:
        '''
        Adds QGIS field logic to populate field values automatically when creating
        new features.
        '''

        # Get layer from project
        layer = QGS_PROJECT.mapLayersByName(layer_name)[0]

        # Find the index of the field
        field_index = layer.fields().indexOf(field_name)

        # Create a QgsDefaultValue object with the expression and set it as the default value for the field
        with edit(layer):

            if default_value_expression:
                layer.setDefaultValueDefinition(
                    field_index,
                    QgsDefaultValue(default_value_expression, True),
                )

            if make_field_uneditable:
                form_config = layer.editFormConfig()
                form_config.setReadOnly(field_index, True)
                layer.setEditFormConfig(form_config)

    def field_to_datetime(self, layer_name: str, field_name: str) -> None:
        '''
        Adjusts save and display options in desired DateTime field.

        From: https://gisunchained.wordpress.com/2019/09/30/configure-editing-form-widgets-using-pyqgis/
        '''
        config = {
            'allow_null': True,
            'calendar_popup': True,
            'display_format': 'yyyy-MM-dd HH:mm:ss',
            'field_format': 'yyyy-MM-dd HH:mm:ss',
            'field_iso_format': False,
        }

        layer = QGS_PROJECT.mapLayersByName(layer_name)[0]

        fields = layer.fields()
        field_idx = fields.indexOf(field_name)
        if field_idx >= 0:
            widget_setup = QgsEditorWidgetSetup('DateTime', config)
            layer.setEditorWidgetSetup(field_idx, widget_setup)

    def set_project_crs(self, crs: Union[int, str]) -> None:
        '''Sets the project CRS'''

        # Create QgsCoordinateReferenceSystem instance based on data type
        if isinstance(crs, int):
            proj_crs = QgsCoordinateReferenceSystem.fromEpsgId(crs)
        elif isinstance(crs, str):
            proj_crs = QgsCoordinateReferenceSystem(crs)
        else:
            raise ValueError(f"'crs' must be string or int! Was: {type(crs)}.")

        # Set to project
        if proj_crs.isValid():
            QGS_PROJECT.setCrs(proj_crs)
        else:
            raise ValueError(f"Invalid crs given: {crs}")

    def set_nin_polygons_styling(self) -> None:
        '''
        Defines the symbology of the nin_polygons layer.
        '''

        # Here we set the random color categorized symbology for each 'kode_id' of
        # the mapping units and label also with 'kode_id'
        # Load the attribute table
        attribute_table_path = Path(__file__).parent / 'csv' / \
            'attribute_tables' / \
            f"{self.selected_mapping_scale}_attribute_table.csv"

        attribute_table = pd.read_csv(
            attribute_table_path,
            index_col=False,
            encoding="utf-8",
        )

        # Function to generate random color
        def random_color():
            # Adding 128 as the alpha value for semi-transparency
            return [random.randint(0, 255) for _ in range(3)] + [128]

        # Load the layer
        layer = QGS_PROJECT.mapLayersByName(self.nin_polygons_layer_name)[0]

        if not layer.isValid():
            print(f"Failed to load layer {self.nin_polygons_layer_name}")
        else:
            # Prepare categorized symbology
            categories = []
            unique_values = attribute_table['kode_id'].unique()

            for value in unique_values:
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                color = random_color()
                # Use the RGB + Alpha values
                symbol.setColor(QColor(color[0], color[1], color[2], color[3]))
                category = QgsRendererCategory(value, symbol, str(value))
                categories.append(category)

            # Add a default category for all other strings
            default_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            # Red color with semi-transparency
            default_symbol.setColor(QColor(255, 0, 0, 128))
            default_category = QgsRendererCategory(
                None, default_symbol, "Other")
            categories.append(default_category)

            renderer = QgsCategorizedSymbolRenderer(
                'represent_value("kode_id_label")',
                categories
            )

            layer.setRenderer(renderer)

            # Set up labeling
            label_settings = QgsPalLayerSettings()

            label_settings.placement = QgsPalLayerSettings.OverPoint
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(12)
            text_format.setColor(QColor(0, 0, 0))  # Black color for text
            label_settings.setFormat(text_format)

            # This feels so wrong... setting expression as field name...
            label_settings.fieldName = """regexp_replace( represent_value("kode_id_label"), '-[^-]+-', '-')"""
            # ...and say its an expression ¯\_(ツ)_/¯
            label_settings.isExpression = True
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)

            # Refresh layer
            layer.triggerRepaint()

            # Add the layer to the project
            QGS_PROJECT.addMapLayer(layer)

    def add_wms_layer(
        self,
        wms_service_url: str,
        wms_layer_names: str,
        wms_style: str,
        wms_crs: str,
        new_qgis_layer_name: str,
        zoom_to_extent=True,
    ) -> None:
        '''
        Adds WMS layers from a specified URL to the project instance.
        '''

        # Format the WMS URI
        wms_uri = f"crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&format=image/png&url={wms_service_url}"

        # Create a new raster layer using the WMS URI
        wms_layer = QgsRasterLayer(
            wms_uri,
            f'{new_qgis_layer_name}',
            'wms',
        )

        # Check if the layer is valid
        if not wms_layer.isValid():
            print(
                f"WMS layer '{new_qgis_layer_name}' failed to load! "
                + "Make sure the provided URI information is correct!"
            )
        else:
            # Add the layer to the QGIS project
            # Add the WMS layer to the project (it will be added to the top)
            # The second parameter set to False prevents auto-add
            QGS_PROJECT.addMapLayer(wms_layer, False)

            # Get the root (top-level) node of the layer tree
            root = QGS_PROJECT.layerTreeRoot()

            # Create a new layer tree node for the added WMS layer
            wms_layer_node = QgsLayerTreeLayer(wms_layer)

            # Insert the new layer's node at the bottom of the layer tree
            # Index 0 inserts at the bottom
            root.insertChildNode(-1, wms_layer_node)

            if zoom_to_extent:
                self.canvas.setExtent(wms_layer.extent())

            self.canvas.refresh()


def main(
    selected_items: list,
    selected_type_id: str,
    gpkg_path: Union[str, Path],
    canvas,
    wms_settings: dict,
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

    # Define name and path of existing geopackage
    # TODO: Remove after testing!
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name

    project_setup = ProjectSetup(
        gpkg_path=gpkg_path,
        selected_type_id=selected_type_id,
        selected_hovedtypegrupper=selected_items,
        selected_mapping_scale=selected_mapping_scale,
        canvas=canvas,
        nin_polygons_layer_name="nin_polygons",
    )

    # Load all layers from geopackage
    _ = project_setup.load_gpkg_layers()

    # Set default values for type + hovedtype UI choices
    project_setup.set_project_crs(crs=PROJECT_CRS)

    # Adjust datetime format of regdato
    project_setup.field_to_datetime(
        layer_name='nin_polygons',
        field_name='regdato'
    )

    # Set default values defined in 'default_values.py'
    for default_value in get_default_values(
        selected_type_id=selected_type_id,
        selected_hovedtypegrupper=selected_items,
    ):
        project_setup.set_layer_field_default_values(
            layer_name=default_value["layer_name"],
            field_name=default_value["field_name"],
            default_value_expression=default_value["default_value_expression"],
            make_field_uneditable=default_value["make_field_uneditable"],
        )

    # Set value relations defined in 'value_relations.py'
    for rel in get_value_relations(
        selected_type_id=selected_type_id,
        selected_mapping_scale=selected_mapping_scale,
        selected_items=selected_items,
    ):
        project_setup.field_to_value_relation(
            primary_attribute_table_layer=rel["primary_attribute_table_layer"],
            forgein_attribute_table_layer=rel["forgein_attribute_table_layer"],
            primary_key_field_name=rel["primary_key_field_name"],
            foreign_key_field_name=rel["foreign_key_field_name"],
            foreign_field_to_display=rel["foreign_field_to_display"],
            filter_expression=rel["filter_expression"],
            allow_multi_selection=rel["allow_multi"],
        )

    # Adjust styling
    project_setup.set_nin_polygons_styling()

    # Add Norway topography WMS raster layer
    if wms_settings['checkBoxNorgeTopo']:
        project_setup.add_wms_layer(
            wms_service_url="https://openwms.statkart.no/skwms1/wms.topo?",
            wms_layer_names='topo',
            wms_style='default',
            wms_crs=PROJECT_CRS,
            new_qgis_layer_name="Topografisk norgeskart",
            zoom_to_extent=True,
        )

    # Add Norway topography grayscale WMS raster layer
    if wms_settings['checkBoxNorgeTopoGraa']:
        project_setup.add_wms_layer(
            wms_service_url="https://openwms.statkart.no/skwms1/wms.topograatone?",
            wms_layer_names='topograatone',
            wms_style='default',
            wms_crs=PROJECT_CRS,
            new_qgis_layer_name="Topografisk norgeskart gråtone",
            zoom_to_extent=True,
        )

    # Add "Norway in images" WMTS raster layer NOT WORKING!?!
    if wms_settings['checkBoxNiB']:
        project_setup.add_wms_layer(
            wms_service_url="http://opencache.statkart.no/gatekeeper/gk/gk.open_nib_utm33_wmts_v2?",
            wms_layer_names='Nibcache_UTM33_EUREF89_v2',
            wms_style='default',
            wms_crs=PROJECT_CRS,
            new_qgis_layer_name="Nibcache_UTM33_EUREF89_v2",
            zoom_to_extent=True,
        )

    # https://qgis.org/pyqgis/master/core/QgsSnappingConfig.html
    # https://qgis.org/pyqgis/master/gui/Qgis.html#qgis.gui.Qgis.SnappingType
    # https://www.qgis.com/api/classQgsSnappingConfig_1_1IndividualLayerSettings.html#details
    # Set the snapping tolerance on polygon (5 meters) on vertex and segments and avvoid overlapp
    pollyr = QgsProject.instance().mapLayersByName(
        'nin_polygons')[0]  # Set the polygon layer
    # Create a new snapping config object
    snapping_config = QgsSnappingConfig()
    # Enable snapping
    snapping_config.setEnabled(True)
    # Set to AdvancedConfiguration
    snapping_config.setMode(QgsSnappingConfig.AdvancedConfiguration)
    # Create the individual layer settings
    snap_settings = QgsSnappingConfig.IndividualLayerSettings(
        True,  # Enable snapping
        QgsSnappingConfig.VertexFlag | QgsSnappingConfig.SegmentFlag,  # Snapping type flags
        5,  # Tolerance
        QgsTolerance.ProjectUnits  # Tolerance type
    )
    # Apply the individual settings to the layer
    snapping_config.setIndividualLayerSettings(pollyr, snap_settings)
    QgsProject.instance().setSnappingConfig(
        snapping_config)          # Activate the snapping settings

    # Enable topological editing
    # https://qgis.org/pyqgis/master/core/QgsProject.html#qgis.core.QgsProject.setTopologicalEditing
    QgsProject.instance().setTopologicalEditing(True)

    # Enable avoid intersections
    # https://qgis.org/pyqgis/master/core/QgsProject.html#qgis.core.QgsProject.setAvoidIntersectionsLayers
    QgsProject.instance().setAvoidIntersectionsLayers([pollyr])
