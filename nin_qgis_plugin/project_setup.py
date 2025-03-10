'''Adapt project setting for NiN-mapping'''

from pathlib import Path
from typing import Union, Literal, List
import random
import pandas as pd

from qgis.core import (
    QgsDataProvider,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsEditorWidgetSetup,
    QgsFieldConstraints,
    QgsCoordinateReferenceSystem,
    QgsRelation,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsDefaultValue,
    QgsLayerTreeLayer,
    QgsSnappingConfig,  # for snapping settings
    QgsTolerance,       # for snapping tolerance type (pixel or project units)
    Qgis,               # for AvoidIntersectionsMode
    edit
)
from PyQt5.QtGui import QColor, QFont

from .attr_table_settings.value_relations import get_value_relations
from .attr_table_settings.default_values import get_default_values
from .attr_table_settings.field_aliases import get_field_aliases
from .attr_table_settings.edit_form_config import adjust_layer_edit_form


QGS_PROJECT = QgsProject.instance()
# PROJECT_CRS = "EPSG:25833"


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
        proj_crs: str,
        nin_polygons_layer_name: str = "nin_polygons",
    ) -> None:
        '''
        Constructor defining instance variables.
        '''

        self.gpkg_path = gpkg_path
        self.selected_type_id = selected_type_id
        self.selected_hovedtypegrupper = selected_hovedtypegrupper
        self.selected_mapping_scale = selected_mapping_scale
        self.canvas = canvas
        self.proj_crs = proj_crs
        self.nin_polygons_layer_name = nin_polygons_layer_name

    def get_nin_polygons_layer(self):
        '''
        Returns the nin_polygons layer with layer name defined
        in 'self.nin_polygons_layer_name'.
        '''
        return QGS_PROJECT.mapLayersByName(self.nin_polygons_layer_name)[0]

    def load_gpkg_layers(self) -> List[QgsVectorLayer]:
        '''
        Loads all .gpkg layers into current QGIS project.

        Returns list of QgsVectorLayers contained in geopackage.
        '''

        # Accessing layers' tree root
        root = QgsProject.instance().layerTreeRoot()
        
        # Add layer groups
        groupNameList = ['Tabeller']  # May add several group names in the []
        for groupName in groupNameList:
            group = root.addGroup(groupName)
            group.setExpanded(False)   # Collapse the layer group

        layer = QgsVectorLayer(
            str(self.gpkg_path),
            "test",
            "ogr"
        )

        sub_layers = layer.dataProvider().subLayers()
        sub_vlayers = []
        p = 0
        for sub_layer in sub_layers:

            name = sub_layer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
            uri = f"{self.gpkg_path}|layername={name}"

            # Create layer
            sub_vlayer = QgsVectorLayer(uri, name, 'ogr')
            sub_vlayers.append(sub_vlayer)
            
            # Add layer to map
            mygroup = root.findGroup("Tabeller")            # Add the layer to the "Tabeller"-group
            root.findGroup("Tabeller").setItemVisibilityChecked(False)  # Uncheck the Tabeller-group
            if name not in ('nin_polygons','nin_helper_points'):        # Only adding table-layers to this group
                QGS_PROJECT.addMapLayer(sub_vlayer, False)  # Add layer to map (False: don't show layer on top in TOC, but insert the layer at given position p)
                mygroup.insertLayer(p, sub_vlayer)          # place the layer in pth posistion from top of TOC
            else:
                QGS_PROJECT.addMapLayer(sub_vlayer, True)   # Add layer to map
            p = p + 1

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

    def set_layer_field_default_values(
        self,
        field_name: str,
        default_value_expression: str,
        make_field_uneditable: bool = True,
        apply_on_update: bool = False,
        widget_type: str = None,
        widget_config: dict = None,
        constraints: dict = None,
        constraint_description: str = None,
        not_null: bool = False,
        enforce_not_null: bool = False,
    ) -> None:
        #print(f"apply_on_update for {field_name}: {apply_on_update}")
        '''
        Adds QGIS field logic to populate field values automatically when creating
        new features. Optionally toggles "Apply default value on update."
        '''

        # Get layer from project
        layer = self.get_nin_polygons_layer()

        # Find the index of the field
        field_index = layer.fields().indexOf(field_name)

        # Create a QgsDefaultValue object with the expression and
        # set it as the default value for the field
        with edit(layer):

            if default_value_expression:
                default_value_def = QgsDefaultValue(default_value_expression, True)
                default_value_def.setApplyOnUpdate(apply_on_update)  # Directly set applyOnUpdate
                layer.setDefaultValueDefinition(field_index, default_value_def)

            if make_field_uneditable:
                form_config = layer.editFormConfig()
                form_config.setReadOnly(field_index, True)
                layer.setEditFormConfig(form_config)

            # Apply widget settings if defined
            if widget_type:
                widget_setup = QgsEditorWidgetSetup(widget_type, widget_config or {})
                layer.setEditorWidgetSetup(field_index, widget_setup)
            # Apply constraints if defined
            if constraints:
                layer.setConstraintExpression(
                    field_index,
                    constraints,
                    constraint_description or ""
                )
                layer.setFieldConstraint(
                    field_index,
                    QgsFieldConstraints.ConstraintExpression
                )
            # Apply Not Null constraint if specified
            if not_null:
                layer.setFieldConstraint(
                    field_index,
                    QgsFieldConstraints.ConstraintNotNull
                )
           # Enforce Not Null constraint if specified
            if enforce_not_null:
                layer.setFieldConstraint(
                    field_index,
                    QgsFieldConstraints.ConstraintNotNull,
                )
            # Apply the "apply on update" setting
            widget_setup = layer.editorWidgetSetup(field_index)
            config = widget_setup.config()
            #print(f"Previous config for {field_name}: {config}")

            config["applyOnUpdate"] = apply_on_update
            new_widget_setup = QgsEditorWidgetSetup(widget_setup.type(), config)
            layer.setEditorWidgetSetup(field_index, new_widget_setup)

            # Log the updated configuration
            print(f"Updated config for {field_name}: {config}")

    # Function to set the constraints expression for a specified field in a vector layer
    def set_constraints_expression(self, layer, field_name, expression, proj_crs):
        # Get the field index
        field_index = layer.fields().indexFromName(field_name)
        
        if field_index == -1:
            print(f"Field '{field_name}' not found in the layer.")
            return

        # Get the field
        field = layer.fields().field(field_index)

        # https://api.qgis.org/api/classQgsVectorLayer.html
        # ConstraintStrengthSoft = User is warned if constraint is violated but feature can still be accepted. 
        layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression, QgsFieldConstraints.ConstraintStrengthSoft)
        layer.setConstraintExpression(field_index, expression)

        # If decimal degrees, the CRS is transformed to UTM33 N before computing planimetric area
        # If that's the case, the field "area"'s default value must be changed
        if proj_crs=='EPSG:4258':
            default_value = QgsDefaultValue()
            default_value.setExpression("round(area(Transform($geometry,'"+proj_crs+"','EPSG:25833')),1)")
            layer.setDefaultValueDefinition(field_index, default_value)

        # Update the field in the layer
        layer.updateFields()        
        print(f"Constraints expression for field '{field_name}' set to '{expression}'.")

    def field_to_datetime(
        self,
        field_name: str
    ) -> None:
        '''
        Adjusts save and display options for the specified DateTime field.

        From: https://gisunchained.wordpress.com/2019/09/30/configure-editing-form-widgets-using-pyqgis/
        '''
        config = {
            'allow_null': True,
            'calendar_popup': True,
            'display_format': 'yyyy-MM-dd HH:mm:ss',
            'field_format': 'yyyy-MM-dd HH:mm:ss',
            'field_iso_format': False,
        }

        layer = self.get_nin_polygons_layer()

        fields = layer.fields()
        field_idx = fields.indexOf(field_name)
        if field_idx >= 0:
            widget_setup = QgsEditorWidgetSetup('DateTime', config)
            layer.setEditorWidgetSetup(field_idx, widget_setup)

    def set_photo_widget(self, layer):
        '''
        Adjusts the photo widget in registration scheme

        https://gis.stackexchange.com/questions/346363/how-to-set-widget-type-to-attachment
        '''
        FIELD = "photo"

        photo_widget_setup = QgsEditorWidgetSetup(
            'ExternalResource',  # https://qgis.org/pyqgis/3.28/gui/QgsExternalResourceWidget.html
            {
                'FileWidget': True,
                'DocumentViewer': 1,
                # https://qgis.org/pyqgis/3.28/gui/QgsFileWidget.html#qgis.gui.QgsFileWidget
                'RelativeStorage': 1,
                'DefaultRoot': '@project_path',
                'StorageMode': 0,
                'DocumentViewerHeight': 300,
                'DocumentViewerWidth': 300,
                'FileWidgetButton': True,
                'FileWidgetFilter': ''
            })
        index = layer.fields().indexFromName(FIELD)
        layer.setEditorWidgetSetup(index, photo_widget_setup)

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
        Defines the symbology and labels of the nin_polygons layer.
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
        layer = self.get_nin_polygons_layer()

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
            # https://gis.stackexchange.com/questions/469969/using-label-placement-via-pyqgis
            # https://qgis.org/pyqgis/master/gui/Qgis.html#qgis.gui.Qgis.LabelPlacement
            label_settings.placement = Qgis.LabelPlacement.OverPoint

            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 12))
            text_format.setSize(12)
            text_format.setColor(QColor(0, 0, 0))  # Black color for text
            label_settings.setFormat(text_format)

            # ... setting expression as label... if not specified with kode_id_label then labeled with "ikke kartlagt"
            # otherwise the represented value in kode_id_label is shortened to omit the mapping scale (string in the middle between dashes)
            label_settings.fieldName =r"""
            case
            when "kode_id_label" is null and "grunntype_or_klenhet_2" is null then 'ikke kartlagt'
            when "grunntype_or_klenhet_2" is null then 
            regexp_replace(represent_value("kode_id_label"), '-[^-]+-', '-')
            else 
            regexp_replace(represent_value("kode_id_label"), '-[^-]+-', '-') || ' / '|| regexp_replace(represent_value("grunntype_or_klenhet_2"), '^([^-]+)-[^-]+-([^-\\ ]+).+$',  '\\1-\\2')
            end
            """

            label_settings.isExpression = True
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)

            # Refresh layer
            layer.triggerRepaint()

            # Add the layer to the project
            QGS_PROJECT.addMapLayer(layer)

        # Layer is "nin_polygons" hard coded in def_init
        layer.saveStyleToDatabase(layer.name(),"Default style for {}".format(layer.name()),True,"")

    def add_wms_layer(
        self,
        wms_service_url: str,
        wms_layer_names: str,
        wms_style: str,
        wms_crs: str,
        new_qgis_layer_name: str,
        wmts: str,
        zoom_to_extent=True,
    ) -> None:
        '''
        Adds WMS layers from a specified URL to the project instance.
        '''

        # Format the WMS URI
        # wms_uri = f"crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&format=image/png&url={wms_service_url}"
        if wmts == '1':
            wms_uri = f"crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&tileMatrixSet=default028mm&format=image/png&url={wms_service_url}"
        else:
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
            # Index -1 inserts at the bottom
            root.insertChildNode(-1, wms_layer_node)

            if zoom_to_extent:
                self.canvas.setExtent(wms_layer.extent())

            self.canvas.refresh()

    def set_field_aliases(self, aliases: dict) -> None:
        '''
        Sets human-readable aliases for the field names in
        the nin_polygons layer.
        '''

        # Adjust grunntype/kle name based on selected scale
        if self.selected_mapping_scale == 'grunntyper':
            aliases['grunntype_or_klenhet'] = 'Grunntype'
            aliases['grunntype_or_klenhet_2'] = 'Grunntype 2'
            aliases['grunntype_or_klenhet_3'] = 'Grunntype 3'
        else:
            aliases['grunntype_or_klenhet'] = 'Kartleggingsenhet'
            aliases['grunntype_or_klenhet_2'] = 'Kartleggingsenhet 2'
            aliases['grunntype_or_klenhet_3'] = 'Kartleggingsenhet 3'

        # Get layer
        layer = self.get_nin_polygons_layer()

        # Get layer fields
        fields = layer.fields()

        for key, value in aliases.items():
            layer.setFieldAlias(
                index=fields.indexFromName(key),
                aliasString=value
            )

    def set_snap_ovelap(self):
        '''
        Sets the snapping tolerance to 5 meters snapping mode to "Follow Advanced Configuration". 
        Sets enable avoid intersections for the polygon layer
        '''
        # https://qgis.org/pyqgis/master/core/QgsSnappingConfig.html
        # https://qgis.org/pyqgis/master/gui/Qgis.html#qgis.gui.Qgis.SnappingType
        # https://www.qgis.com/api/classQgsSnappingConfig_1_1IndividualLayerSettings.html#details
        # Set the snapping tolerance on polygon (5 meters) on vertex and segments and avoid overlap
        pollyr = self.get_nin_polygons_layer()

        # Create a new snapping config object
        snapping_config = QgsSnappingConfig()
        # Enable snapping
        snapping_config.setEnabled(True)
        # Set to AdvancedConfiguration
        snapping_config.setMode(QgsSnappingConfig.AdvancedConfiguration)
        # Create the individual layer settings
        snap_settings = QgsSnappingConfig.IndividualLayerSettings(
            True,  # Enable snapping
            Qgis.SnappingTypes(Qgis.SnappingType.Vertex |
                               Qgis.SnappingType.Segment),
            # QgsSnappingConfig.SnappingType.VertexAndSegment --> throws a bug in qgis 3.28, see https://github.com/qgis/QGIS/issues/52373
            1.0,  # Tolerance
            QgsTolerance.ProjectUnits,  # Tolerance type
            0.0,  # minScale
            0.0,   # maxScale
        )
        # Apply the individual settings to the layer
        snapping_config.setIndividualLayerSettings(pollyr, snap_settings)
        QGS_PROJECT.setSnappingConfig(
            snapping_config
        )  # Activate the snapping settings

        # Enable topological editing
        # https://qgis.org/pyqgis/master/core/QgsProject.html#qgis.core.QgsProject.setTopologicalEditing
        QGS_PROJECT.setTopologicalEditing(True)

        # Set the snapping mode to "Follow Advanced Configuration" (=2) to avoid overlap on the polygon-layer
        # https://qgis.org/pyqgis/master/core/QgsProject.html#qgis.core.QgsProject.setAvoidIntersectionsMode
        QGS_PROJECT.setAvoidIntersectionsMode(
            Qgis.AvoidIntersectionsMode(2)
        )

        # Enable avoid intersections
        # https://qgis.org/pyqgis/master/core/QgsProject.html#qgis.core.QgsProject.setAvoidIntersectionsLayers
        QGS_PROJECT.setAvoidIntersectionsLayers([pollyr])


def main(
    selected_items: list,
    selected_type_id: str,
    gpkg_path: Union[str, Path],
    canvas,
    proj_crs: str,
    wms_settings: dict,
    selected_mapping_scale="M005",  # ??? Hardkoda? Hva med grunntyper?
) -> None:
    '''Adapt QGIS project settings.'''

    # Pass user selection to create ProjectSetup() instance
    project_setup = ProjectSetup(
        gpkg_path=gpkg_path,
        selected_type_id=selected_type_id,
        selected_hovedtypegrupper=selected_items,
        selected_mapping_scale=selected_mapping_scale,
        canvas=canvas,
        proj_crs=proj_crs,
        nin_polygons_layer_name="nin_polygons",
    )

    # Load all layers from geopackage
    _ = project_setup.load_gpkg_layers()

    # Set default values for type + hovedtype UI choices
    # project_setup.set_project_crs(crs=PROJECT_CRS)
    project_setup.set_project_crs(crs=proj_crs)

    # Adjust datetime format of regdato
    project_setup.field_to_datetime(field_name='regdato')

    project_setup.set_photo_widget(
        layer=project_setup.get_nin_polygons_layer(),
    )

    # Set MMU depending on the chosen mapping scale
    layer_name = "nin_polygons"
    field_name = "area"
    if selected_mapping_scale=="grunntyper":
        expression = "area($geometry)>=1"   # Secure MMU
    elif selected_mapping_scale=="M005":
        expression = "area($geometry)>=500"   # Secure MMU
    elif selected_mapping_scale=="M020":
        expression = "area($geometry)>=2500"  # Secure MMU
    else:
        expression = "area($geometry)>=10000"  # Secure MMU


    # Set default values defined in 'default_values.py'
    for default_value in get_default_values(
        selected_type_id=selected_type_id,
        selected_hovedtypegrupper=selected_items,
    ):
        project_setup.set_layer_field_default_values(
            field_name=default_value["field_name"],
            default_value_expression=default_value["default_value_expression"],
            make_field_uneditable=default_value["make_field_uneditable"],
            apply_on_update=default_value.get("apply_on_update", False),
            widget_type=default_value.get("widget_type", None),
            widget_config=default_value.get("widget_config", None),
            constraints=default_value.get("constraints", None),
            constraint_description=default_value.get("constraint_description", None),
            not_null=default_value.get("not_null", False),
            enforce_not_null=default_value.get("enforce_not_null", False),
            
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

    # Set field aliases
    project_setup.set_field_aliases(
        aliases=get_field_aliases()
    )

    # TEST: Adjust nin polygon edit form
    adjust_layer_edit_form(
        layer=project_setup.get_nin_polygons_layer()
    )

    # Get the layer by name
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    
    # Set the conatraints expression for the specified field
    project_setup.set_constraints_expression(layer, field_name, expression, proj_crs)


    # Add Norway topography WMS raster layer
    if wms_settings['checkBoxNorgeTopo']:
        project_setup.add_wms_layer(
            wms_service_url="https://openwms.statkart.no/skwms1/wms.topo?",
            wms_layer_names='topo',
            wms_style='default',
            wms_crs=proj_crs,
            new_qgis_layer_name="Topografisk norgeskart",
            wmts='0',
            zoom_to_extent=True,
        )

    # Add Norway topography grayscale WMS raster layer
    if wms_settings['checkBoxNorgeTopoGraa']:
        project_setup.add_wms_layer(
            wms_service_url="https://openwms.statkart.no/skwms1/wms.topograatone?",
            wms_layer_names='topograatone',
            wms_style='default',
            wms_crs=proj_crs,
            new_qgis_layer_name="Topografisk norgeskart gråtone",
            wmts='0',
            zoom_to_extent=True,
        )

    # Add "Norway in images" WMTS raster layer
    if wms_settings['checkBoxNiB']:
        project_setup.add_wms_layer(
            wms_service_url="http://opencache.statkart.no/gatekeeper/gk/gk.open_nib_utm33_wmts_v2?",
            wms_layer_names='Nibcache_UTM33_EUREF89_v2',
            wms_style='default',
            wms_crs=proj_crs,
            new_qgis_layer_name="Nibcache_UTM33_EUREF89_v2",
            wmts='1',
            zoom_to_extent=True,
        )

    # Adjust project snapping and overlap options
    project_setup.set_snap_ovelap()

    # Save the project
    project_path = str(Path(gpkg_path).parent / "NiN_kartlegging.qgz")
    QGS_PROJECT.setFileName(project_path)
    QGS_PROJECT.write()
