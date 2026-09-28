'''Adapt project setting for NiN-mapping'''

import csv
import os
from pathlib import Path
from typing import Union, List
from urllib.parse import quote_plus

from qgis.core import (
    QgsDataProvider,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsProject,
    QgsEditorWidgetSetup,
    QgsFieldConstraints,
    QgsCoordinateReferenceSystem,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsSymbol,
    QgsMarkerSymbol,
    QgsLineSymbol,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling,
    QgsDefaultValue,
    QgsLayerTreeLayer,
    QgsSnappingConfig,  # for snapping settings
    QgsTolerance,       # for snapping tolerance type (pixel or project units)
    Qgis,               # for AvoidIntersectionsMode
    QgsMessageLog,
    QgsBlockingNetworkRequest,
    QgsApplication,
    QgsAuthMethodConfig,
    edit
)
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtNetwork import QNetworkRequest

from .nib_access import classify_nib_capabilities_response
from .wmts_capabilities import WmtsCapabilitiesError, select_wmts_layer_parameters

from .attr_table_settings.value_relations import get_value_relations
from .attr_table_settings.default_values import get_default_values
from .attr_table_settings.field_aliases import get_field_aliases
from .attr_table_settings.edit_form_config import adjust_layer_edit_form
from .attr_table_settings.edit_form_config import POLYGON_LAYOUT, SIMPLE_LAYOUT
from .create_gpkg import (
    HELPER_POINT_LAYER_NAME,
    POLYGON_LAYER_BASE_NAME,
    mapping_layer_name,
    mapping_layer_names,
)
from .symbology_colors import kode_id_color


QGS_PROJECT = QgsProject.instance()
# PROJECT_CRS = "EPSG:25833"

# Label expression for nin_polygons: if not specified with kode_id_label then
# labeled with "ikke kartlagt", otherwise the represented value in kode_id_label
# is shortened to omit the mapping scale (string in the middle between dashes).
# A second type (mosaic/composite polygon) is appended after ' / '.
POLYGON_LABEL_EXPRESSION = r"""
            CASE
                WHEN "type" IN (1,2,3,4,5) THEN
                    regexp_substr(represent_value("hovedtype"), '^[A-Z]+-[A-Z0-9]+')
                WHEN "kode_id_label" IS NULL AND "grunntype_or_klenhet_2" IS NULL THEN
                    'ikke kartlagt'
                WHEN "grunntype_or_klenhet_2" IS NULL THEN
                    regexp_replace(represent_value("kode_id_label"), '-[^-]+-', '-')
                ELSE
                    regexp_replace(represent_value("kode_id_label"), '-[^-]+-', '-') || ' / ' || regexp_replace(represent_value("grunntype_or_klenhet_2"), '^([A-Z0-9]+)-(?:[A-Z0-9]+-)?([A-Z0-9]+).*$', '\\1-\\2')
            END
            """
# Regexp explanation:
# ^([A-Z0-9]+)-
# Captures the first part (e.g., TK01).
# (?:[A-Z0-9]+-)?
# Matches (but does not capture) an optional middle part (e.g., M005-).
# ([A-Z0-9]+)
# Captures the third part (e.g., 19).
# .*$
# Matches and removes everything after the third part (optional descriptive text).
# '\\1-\\2'
# Keeps only the first and third parts, removing the middle part and anything extra at the end.

# Label expression for nin_points and nin_lines (single type, no Type 2/3 fields).
SIMPLE_LABEL_EXPRESSION = r"""
            CASE
                WHEN "type" IN (1,2,3,4,5) THEN
                    regexp_substr(represent_value("hovedtype"), '^[A-Z]+-[A-Z0-9]+')
                WHEN "kode_id_label" IS NULL THEN
                    'ikke kartlagt'
                ELSE
                    regexp_replace(represent_value("kode_id_label"), '-[^-]+-', '-')
            END
            """


def _read_csv_column(csv_path: Union[str, Path], column_name: str) -> list[str]:
    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        return [row[column_name] for row in reader if row.get(column_name)]


def _utm_zone_from_crs(crs: str) -> str:
    crs_digits = ''.join(character for character in str(crs) if character.isdigit())
    if len(crs_digits) < 2:
        raise ValueError(f"Could not derive UTM zone from CRS: {crs}")

    return crs_digits[-2:]


def _encode_uri_value(value: str) -> str:
    '''
    Encodes a value for use inside a QGIS provider URI (e.g. the 'url=' part
    of a WMS/WMTS URI). Mirrors QgsDataSourceUri::encodedUri(), which escapes
    only '&' and '=' (verified against QGIS 3.40: '%' is passed through and
    only '%26' / '%3D' are decoded), so full percent-encoding via
    urllib.parse.quote would NOT be decoded and must not be used here.
    '''

    return value.replace('&', '%26').replace('=', '%3D')


def _enum_member(owner, enum_name: str, member: str):
    '''Qt5/Qt6 compatible enum lookup: owner.member or owner.EnumName.member.'''
    scoped = getattr(owner, enum_name, None)
    if scoped is not None and hasattr(scoped, member):
        return getattr(scoped, member)
    return getattr(owner, member)


def fetch_url(url: str, authcfg: str = '') -> tuple:
    '''
    Blocking GET through the QGIS network stack (proxy settings, and the
    authentication configuration when given). Returns
    (status code or None, body bytes, network error text or '').
    '''

    request = QNetworkRequest(QUrl(url))
    blocking_request = QgsBlockingNetworkRequest()
    if authcfg:
        blocking_request.setAuthCfg(authcfg)

    error_code = blocking_request.get(request, True)
    reply = blocking_request.reply()

    no_error = _enum_member(QgsBlockingNetworkRequest, 'ErrorCode', 'NoError')
    status_attribute = _enum_member(QNetworkRequest, 'Attribute', 'HttpStatusCodeAttribute')
    status_code = reply.attribute(status_attribute)
    network_error = reply.errorString() if error_code != no_error else ''

    if status_code is None and not network_error and error_code != no_error:
        network_error = str(error_code)

    return (
        int(status_code) if status_code is not None else None,
        bytes(reply.content()),
        network_error,
    )


def fetch_nib_capabilities(capabilities_url: str, authcfg: str = '') -> tuple:
    '''
    Requests the Norge i bilder WMTS GetCapabilities document with the
    user's credentials. Returns (capabilities bytes or None, Norwegian error
    message or None). The layer is only added when this passes, so a bad
    token is reported to the user instead of silently producing a missing
    layer.
    '''

    status_code, body, network_error = fetch_url(capabilities_url, authcfg)
    error = classify_nib_capabilities_response(
        status_code=status_code, body=body, network_error=network_error,
    )
    return (None if error else body), error


def check_nib_access(capabilities_url: str, authcfg: str = '') -> Union[str, None]:
    '''Returns a Norwegian error message when NiB cannot be used, else None.'''
    return fetch_nib_capabilities(capabilities_url, authcfg)[1]


def _nib_token() -> str:
    return os.getenv('NIN_NIB_TOKEN') or os.getenv('NIB_TOKEN') or ''


# Name of the QGIS authentication configuration the plugin creates for the
# Norge i bilder token (visible under Settings -> Options -> Authentication)
NIB_AUTHCFG_NAME = 'NiN plugin: Norge i bilder'


def ensure_nib_auth_config(token: str) -> tuple:
    '''
    Stores the Norge i bilder token as a QGIS "EsriToken" authentication
    configuration and returns (authcfg id, error message or None).

    QGIS only forwards URL parameters of a WMTS URL to GetCapabilities, not
    to the GetTile requests, so a token in the URL loads the layer but every
    tile is unauthorized. The EsriToken method adds the header
    'X-Esri-Authorization: Bearer <token>' to every request, which is what
    Geonorge documents for the NiB services. An existing configuration with
    the plugin's name is updated so users can renew the token by running
    the plugin again.
    '''

    manager = QgsApplication.authManager()

    # Unlocks the authentication database; in QGIS desktop this prompts for
    # the master password (or asks to create one) when needed.
    if not manager.masterPasswordIsSet() and not manager.setMasterPassword(True):
        return '', (
            'Kunne ikke låse opp QGIS sin autentiseringsdatabase (hovedpassord), '
            'så tokenet kunne ikke lagres.'
        )

    existing_id = ''
    for config_id, existing in manager.availableAuthMethodConfigs().items():
        if existing.name() == NIB_AUTHCFG_NAME:
            existing_id = config_id
            break

    config = QgsAuthMethodConfig('EsriToken')
    config.setName(NIB_AUTHCFG_NAME)
    config.setConfig('token', token)

    if existing_id:
        config.setId(existing_id)
        stored = manager.updateAuthenticationConfig(config)
    else:
        stored = manager.storeAuthenticationConfig(config)
        # The Python binding returns (bool, config) for the store call
        if isinstance(stored, tuple):
            stored = stored[0]

    if not stored or not config.id():
        return '', 'Kunne ikke lagre tokenet som autentiseringskonfigurasjon i QGIS.'

    return config.id(), None


def _nib_authcfg() -> str:
    return os.getenv('NIN_NIB_AUTHCFG') or os.getenv('NIB_AUTHCFG') or ''


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
        nin_polygons_layer_name: Union[str, None] = None,
    ) -> None:
        '''
        Constructor defining instance variables.

        nin_polygons_layer_name defaults to 'nin_polygons_<scale>'.
        '''

        self.gpkg_path = gpkg_path
        self.selected_type_id = selected_type_id
        self.selected_hovedtypegrupper = selected_hovedtypegrupper
        self.selected_mapping_scale = selected_mapping_scale
        self.canvas = canvas
        self.proj_crs = proj_crs
        # Geopackage layer names carry the mapping scale suffix (issue #66):
        # {'nin_polygons': 'nin_polygons_M005', 'nin_points': 'nin_points_M005', ...}
        self.mapping_layer_names = mapping_layer_names(selected_mapping_scale)
        self.nin_polygons_layer_name = nin_polygons_layer_name or mapping_layer_name(
            POLYGON_LAYER_BASE_NAME, selected_mapping_scale
        )
        # One colour per kode_id, shared by all mapping layers in this project
        self._kode_id_palette: Union[dict, None] = None

    def get_layer(self, layer_name: str) -> QgsVectorLayer:
        '''Returns the project layer with the given name.'''
        return QGS_PROJECT.mapLayersByName(layer_name)[0]

    def get_nin_polygons_layer(self):
        '''
        Returns the nin_polygons layer with layer name defined
        in 'self.nin_polygons_layer_name'.
        '''
        return self.get_layer(self.nin_polygons_layer_name)

    def load_gpkg_layers(self) -> List[QgsVectorLayer]:
        '''
        Loads all .gpkg layers into current QGIS project.

        Returns list of QgsVectorLayers contained in geopackage.
        '''

        # Accessing layers' tree root
        root = QgsProject.instance().layerTreeRoot()

        # Add layer groups (reuse an existing group when adding to an open project)
        groupNameList = ['Tabeller']  # May add several group names in the []
        for groupName in groupNameList:
            group = root.findGroup(groupName) or root.addGroup(groupName)
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
            if name not in (*self.mapping_layer_names.values(), HELPER_POINT_LAYER_NAME):  # Only adding table-layers to this group
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
        layer: QgsVectorLayer = None,
    ) -> None:
        #print(f"apply_on_update for {field_name}: {apply_on_update}")
        '''
        Adds QGIS field logic to populate field values automatically when creating
        new features. Optionally toggles "Apply default value on update."

        Applies to 'layer' if given, otherwise to the nin_polygons layer.
        '''

        # Get layer from project
        if layer is None:
            layer = self.get_nin_polygons_layer()

        # Find the index of the field
        field_index = layer.fields().indexOf(field_name)
        if field_index < 0:
            print(f"Field '{field_name}' not found in layer '{layer.name()}', skipping defaults.")
            return

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

        # https://api.qgis.org/api/classQgsVectorLayer.html
        # ConstraintStrengthSoft = User is warned if constraint is violated but feature can still be accepted.
        layer.setFieldConstraint(field_index, QgsFieldConstraints.ConstraintExpression, QgsFieldConstraints.ConstraintStrengthSoft)
        layer.setConstraintExpression(field_index, expression)

        # If decimal degrees, the CRS is transformed to UTM33 N before computing planimetric area
        # If that's the case, the field "area"'s default value must be changed
        if proj_crs == 'EPSG:4258':
            default_value = QgsDefaultValue()
            default_value.setExpression("round(area(Transform($geometry,'"+proj_crs+"','EPSG:25833')),1)")
            layer.setDefaultValueDefinition(field_index, default_value)

        # Update the field in the layer
        layer.updateFields()
        print(f"Constraints expression for field '{field_name}' set to '{expression}'.")

    def field_to_datetime(
        self,
        field_name: str,
        layer: QgsVectorLayer = None,
    ) -> None:
        '''
        Adjusts save and display options for the specified DateTime field.
        Applies to 'layer' if given, otherwise to the nin_polygons layer.

        From: https://gisunchained.wordpress.com/2019/09/30/configure-editing-form-widgets-using-pyqgis/
        '''
        config = {
            'allow_null': True,
            'calendar_popup': True,
            'display_format': 'yyyy-MM-dd HH:mm:ss',
            'field_format': 'yyyy-MM-dd HH:mm:ss',
            'field_iso_format': False,
        }

        if layer is None:
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

    def get_kode_id_palette(self) -> dict:
        '''
        Returns one colour (RGB tuple) per 'kode_id' of the selected mapping
        scale. Colours are derived deterministically from the code (see
        'symbology_colors.kode_id_color'), so the same mapping unit gets the
        same colour on polygons, points and lines, in every project and on
        every computer.
        '''

        if self._kode_id_palette is None:
            attribute_table_path = Path(__file__).parent / 'csv' / \
                'attribute_tables' / \
                f"{self.selected_mapping_scale}_attribute_table.csv"

            unique_values = list(dict.fromkeys(
                _read_csv_column(attribute_table_path, 'kode_id')
            ))

            self._kode_id_palette = {
                value: kode_id_color(value)
                for value in unique_values
            }

        return self._kode_id_palette

    def set_kode_id_styling(
        self,
        layer: QgsVectorLayer,
        label_expression: str,
        label_placement,
        symbol_alpha: int = 128,
    ) -> None:
        '''
        Defines a categorized symbology (one colour per 'kode_id' of the
        mapping units, red for unmatched values) and an expression label
        for a mapping layer. Works for polygon, point and line layers.
        '''

        if not layer.isValid():
            print(f"Failed to load layer {layer.name()}")
            return

        # Prepare categorized symbology
        categories = []

        for value, (red, green, blue) in self.get_kode_id_palette().items():
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            self._size_symbol(symbol)
            symbol.setColor(QColor(red, green, blue, symbol_alpha))
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        # Add a default category for all other strings
        default_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        self._size_symbol(default_symbol)
        # Red color
        default_symbol.setColor(QColor(255, 0, 0, symbol_alpha))
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
        label_settings.placement = label_placement

        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial", 12))
        text_format.setSize(12)
        text_format.setColor(QColor(0, 0, 0))  # Black color for text
        label_settings.setFormat(text_format)

        label_settings.fieldName = label_expression
        label_settings.isExpression = True
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)
        layer.setLabelsEnabled(True)

        # Refresh layer
        layer.triggerRepaint()

        layer.saveStyleToDatabase(layer.name(), "Default style for {}".format(layer.name()), True, "")

    @staticmethod
    def _size_symbol(symbol: QgsSymbol) -> None:
        '''Gives point markers and lines a size that is visible in the field.'''

        if isinstance(symbol, QgsMarkerSymbol):
            symbol.setSize(3.0)  # mm
        elif isinstance(symbol, QgsLineSymbol):
            symbol.setWidth(0.8)  # mm

    def set_nin_polygons_styling(self) -> None:
        '''
        Defines the symbology and labels of the nin_polygons layer.
        '''

        self.set_kode_id_styling(
            layer=self.get_nin_polygons_layer(),
            label_expression=POLYGON_LABEL_EXPRESSION,
            label_placement=Qgis.LabelPlacement.OverPoint,
            symbol_alpha=128,  # semi-transparent fill
        )

    def set_point_line_styling(self, layer: QgsVectorLayer) -> None:
        '''
        Defines the symbology and labels of the nin_points / nin_lines layers.
        '''

        is_line = isinstance(
            QgsSymbol.defaultSymbol(layer.geometryType()), QgsLineSymbol
        )

        self.set_kode_id_styling(
            layer=layer,
            label_expression=SIMPLE_LABEL_EXPRESSION,
            label_placement=(
                Qgis.LabelPlacement.Line if is_line
                else Qgis.LabelPlacement.AroundPoint
            ),
            symbol_alpha=255,  # opaque markers and lines
        )

    def add_wms_layer(
        self,
        wms_service_url: str,
        wms_layer_names: str,
        wms_style: str,
        wms_crs: str,
        new_qgis_layer_name: str,
        wmts: str,
        zoom_to_extent=True,
        authcfg: str = '',
        tile_matrix_set: str = '',
        image_format: str = 'image/png',
    ) -> bool:
        '''
        Adds WMS layers from a specified URL to the project instance.
        Returns True when the layer was valid and added, False otherwise.

        For WMTS, pass the tile matrix set read from the capabilities (see
        wmts_capabilities.select_wmts_layer_parameters); the URI is then
        built exactly like the QGIS connection dialog builds it. Without it
        a few common tile matrix set names are tried.
        '''

        # Format the WMS/WMTS URI
        authcfg_param = f"&authcfg={quote_plus(authcfg)}" if authcfg else ''
        # The service URL is a value inside the provider URI, so any '&' or '='
        # it contains (e.g. GetCapabilities parameters) must be escaped or
        # QgsDataSourceUri splits it into separate params.
        encoded_service_url = _encode_uri_value(wms_service_url)
        wms_layer = None
        if wmts == '1' and tile_matrix_set:
            # Same parameter set as a WMTS layer added from the QGIS browser
            wms_uri = (
                f"crs={wms_crs}&dpiMode=7&format={image_format}&layers={wms_layer_names}"
                f"&styles={wms_style}&tileMatrixSet={tile_matrix_set}"
                f"&url={encoded_service_url}{authcfg_param}"
            )
            wms_layer = QgsRasterLayer(wms_uri, f'{new_qgis_layer_name}', 'wms')
        elif wmts == '1':
            tile_matrix_candidates = [
                f"utm{_utm_zone_from_crs(wms_crs)}_euref89",
                'default028mm',
            ]
            wmts_uri_candidates = [
                f"type=wmts&crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&tileMatrixSet={tile_matrix_set}&format=image/png{authcfg_param}&url={encoded_service_url}"
                for tile_matrix_set in tile_matrix_candidates
            ]
            wmts_uri_candidates.append(
                f"type=wmts&crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&format=image/png{authcfg_param}&url={encoded_service_url}"
            )

            for wmts_uri in wmts_uri_candidates:
                candidate_layer = QgsRasterLayer(
                    wmts_uri,
                    f'{new_qgis_layer_name}',
                    'wms',
                )
                if candidate_layer.isValid():
                    wms_layer = candidate_layer
                    break
        else:
            wms_uri = f"crs={wms_crs}&layers={wms_layer_names}&styles={wms_style}&format=image/png{authcfg_param}&url={encoded_service_url}"
            wms_layer = QgsRasterLayer(
                wms_uri,
                f'{new_qgis_layer_name}',
                'wms',
            )

        # Check if the layer is valid
        if wms_layer is None or not wms_layer.isValid():
            safe_url = wms_service_url
            if '&token=' in safe_url:
                safe_url = safe_url.split('&token=')[0] + '&token=<redacted>'
            print(
                f"WMS layer '{new_qgis_layer_name}' failed to load! "
                + "Make sure the provided URI information is correct!"
            )
            QgsMessageLog.logMessage(
                f"Failed to load layer '{new_qgis_layer_name}' from '{safe_url}'. "
                + "If this is the NiB WMTS, verify the token (authentication configuration 'NiN plugin: Norge i bilder').",
                'NiN plugin',
                Qgis.Warning,
            )
            return False

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
        return True

    def set_field_aliases(
        self,
        aliases: dict,
        layer: QgsVectorLayer = None,
    ) -> None:
        '''
        Sets human-readable aliases for the field names in a mapping layer
        ('layer' if given, otherwise nin_polygons). Aliases for fields the
        layer does not have are skipped.
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
        if layer is None:
            layer = self.get_nin_polygons_layer()

        # Get layer fields
        fields = layer.fields()

        for key, value in aliases.items():
            field_index = fields.indexFromName(key)
            if field_index < 0:
                continue
            layer.setFieldAlias(
                index=field_index,
                aliasString=value
            )

    def set_snap_overlap(self):
        '''
        Sets snapping tolerance to 1.0 meter on vertex and segments for the
        mapping layers (polygons, points, lines), while preserving existing
        snapping settings in the project.
        Enables "Avoid Overlap" for the polygon layer.
        '''
        pollyr = self.get_nin_polygons_layer()

        # Get current project snapping configuration
        snapping_config = QGS_PROJECT.snappingConfig()

        # Enable snapping and set mode to AdvancedConfiguration
        snapping_config.setEnabled(True)
        snapping_config.setMode(QgsSnappingConfig.AdvancedConfiguration)

        # Define individual snapping settings
        snap_settings = QgsSnappingConfig.IndividualLayerSettings(
            True,
            Qgis.SnappingTypes(Qgis.SnappingType.Vertex | Qgis.SnappingType.Segment),
            1.0,
            QgsTolerance.ProjectUnits,
            0.0,
            0.0
        )

        # Update snapping settings for the mapping layers
        for layer_name in self.mapping_layer_names.values():
            snapping_config.setIndividualLayerSettings(
                self.get_layer(layer_name), snap_settings
            )

        # Apply updated snapping config to the project
        QGS_PROJECT.setSnappingConfig(snapping_config)

        # Enable topological editing
        QGS_PROJECT.setTopologicalEditing(True)

        # Enable "Avoid Overlap" behavior
        QGS_PROJECT.setAvoidIntersectionsMode(Qgis.AvoidIntersectionsMode(2))
        QGS_PROJECT.setAvoidIntersectionsLayers([pollyr])


def main(
    selected_items: list,
    selected_type_id: str,
    gpkg_path: Union[str, Path],
    canvas,
    proj_crs: str,
    wms_settings: dict,
    selected_mapping_scale="M005",  # ??? Hardkoda? Hva med grunntyper?
    add_to_open_project: bool = False,
) -> List[str]:
    '''
    Adapt QGIS project settings.

    Returns a list of user-facing (Norwegian) warnings, e.g. background
    layers that could not be loaded or a failed Norge i bilder login.
    An empty list means everything was set up.

    add_to_open_project (issue #72): when True and the open QGIS project has
    a file name, the layers are added to that project, its CRS is kept and it
    is saved in place. Otherwise the project is saved as
    'NiN_kartlegging.qgz' next to the geopackage and set to the chosen CRS.
    '''

    keep_open_project = bool(add_to_open_project and QGS_PROJECT.fileName())

    # Pass user selection to create ProjectSetup() instance
    project_setup = ProjectSetup(
        gpkg_path=gpkg_path,
        selected_type_id=selected_type_id,
        selected_hovedtypegrupper=selected_items,
        selected_mapping_scale=selected_mapping_scale,
        canvas=canvas,
        proj_crs=proj_crs,
    )

    # Load all layers from geopackage
    _ = project_setup.load_gpkg_layers()

    # Set the project CRS (an existing project keeps its own CRS)
    if not keep_open_project:
        project_setup.set_project_crs(crs=proj_crs)

    # Configure the mapping layers (polygons, points, lines): widgets,
    # default values, hierarchical dropdowns, styling, aliases and edit form
    for base_name, layer_name in project_setup.mapping_layer_names.items():
        layer = project_setup.get_layer(layer_name)
        is_polygon_layer = base_name == POLYGON_LAYER_BASE_NAME

        # Adjust datetime format of regdato
        project_setup.field_to_datetime(field_name='regdato', layer=layer)

        project_setup.set_photo_widget(layer=layer)

        # Set default values defined in 'default_values.py'
        for default_value in get_default_values(
            selected_type_id=selected_type_id,
            selected_hovedtypegrupper=selected_items,
            base_layer_name=base_name,
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
                layer=layer,
            )

        # Set value relations defined in 'value_relations.py'
        for rel in get_value_relations(
            selected_type_id=selected_type_id,
            selected_mapping_scale=selected_mapping_scale,
            selected_items=selected_items,
            layer_name=layer_name,
            base_layer_name=base_name,
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
        if is_polygon_layer:
            project_setup.set_nin_polygons_styling()
        else:
            project_setup.set_point_line_styling(layer=layer)

        # Set field aliases
        project_setup.set_field_aliases(
            aliases=get_field_aliases(),
            layer=layer,
        )

        # Adjust edit form
        adjust_layer_edit_form(
            layer=layer,
            layout=POLYGON_LAYOUT if is_polygon_layer else SIMPLE_LAYOUT,
        )

    # Set MMU depending on the chosen mapping scale (polygons only)
    field_name = "area"
    if selected_mapping_scale == "grunntyper":
        expression = "area($geometry)>=1"   # Secure MMU
    elif selected_mapping_scale == "M005":
        expression = "area($geometry)>=500"   # Secure MMU
    elif selected_mapping_scale == "M020":
        expression = "area($geometry)>=2500"  # Secure MMU
    else:
        expression = "area($geometry)>=10000"  # Secure MMU

    # Set the constraints expression for the specified field
    project_setup.set_constraints_expression(
        project_setup.get_nin_polygons_layer(), field_name, expression, proj_crs
    )

    warnings: List[str] = []

    def _layer_failed(layer_name: str) -> str:
        return (
            f"Bakgrunnskartet '{layer_name}' kunne ikke lastes. "
            "Se meldingsloggen 'NiN plugin' i QGIS for detaljer."
        )

    # Add Norway topography WMS raster layer
    if wms_settings['checkBoxNorgeTopo']:
        if not project_setup.add_wms_layer(
            wms_service_url="https://wms.geonorge.no/skwms1/wms.topo?",
            wms_layer_names='topo',
            wms_style='default',
            wms_crs=proj_crs,
            new_qgis_layer_name="Topografisk norgeskart",
            wmts='0',
            zoom_to_extent=True,
        ):
            warnings.append(_layer_failed("Topografisk norgeskart"))

    # Add Norway topography grayscale WMS raster layer
    if wms_settings['checkBoxNorgeTopoGraa']:
        if not project_setup.add_wms_layer(
            wms_service_url="https://wms.geonorge.no/skwms1/wms.topograatone?",
            wms_layer_names='topograatone',
            wms_style='default',
            wms_crs=proj_crs,
            new_qgis_layer_name="Topografisk norgeskart gråtone",
            wmts='0',
            zoom_to_extent=True,
        ):
            warnings.append(_layer_failed("Topografisk norgeskart gråtone"))

    # Add "Norway in images" WMTS raster layer. The token is sent as the
    # 'X-Esri-Authorization' header through a QGIS authentication
    # configuration (see ensure_nib_auth_config), never as a URL parameter.
    if wms_settings['checkBoxNiB']:
        crs_zone = _utm_zone_from_crs(proj_crs)
        nib_authcfg = (wms_settings.get('nib_authcfg') or '').strip() or _nib_authcfg()
        nib_token = (wms_settings.get('nib_token') or '').strip() or _nib_token()
        # Bare service URL, as in a QGIS WMTS connection; QGIS appends the
        # GetCapabilities parameters itself
        nib_service_url = f"https://tilecache.norgeibilder.no/wmts/utm{crs_zone}_euref89"
        nib_capabilities_url = f"{nib_service_url}?SERVICE=WMTS&REQUEST=GetCapabilities"
        nib_layer_name = f'Nibcache_UTM{crs_zone}_EUREF89_v2'

        nib_error = None
        nib_parameters = None
        if not nib_authcfg:
            if not nib_token:
                nib_error = 'Ingen token for Norge i bilder ble oppgitt.'
            else:
                nib_authcfg, nib_error = ensure_nib_auth_config(nib_token)

        # Verify the login first so a bad token is reported, not silently
        # skipped, and read layer/style/format/tile matrix set from the
        # capabilities instead of guessing them
        if not nib_error:
            capabilities, nib_error = fetch_nib_capabilities(
                nib_capabilities_url, authcfg=nib_authcfg
            )
        if not nib_error:
            try:
                nib_parameters = select_wmts_layer_parameters(
                    capabilities, nib_layer_name, proj_crs
                )
            except WmtsCapabilitiesError as exception:
                nib_error = str(exception)

        if nib_error:
            QgsMessageLog.logMessage(
                f"Norge i bilder: {nib_error}", 'NiN plugin', Qgis.Warning
            )
            warnings.append(
                f"{nib_error} Kartlaget fra Norge i bilder ble ikke lagt til."
            )
        else:
            QgsMessageLog.logMessage(
                f"Norge i bilder: legger til {nib_parameters['layer']} "
                f"(stil {nib_parameters['style']}, format {nib_parameters['format']}, "
                f"flisrutenett {nib_parameters['tile_matrix_set']})",
                'NiN plugin', Qgis.Info,
            )
            if not project_setup.add_wms_layer(
                wms_service_url=nib_service_url,
                wms_layer_names=nib_parameters['layer'],
                wms_style=nib_parameters['style'],
                wms_crs=proj_crs,
                new_qgis_layer_name=nib_parameters['layer'],
                wmts='1',
                zoom_to_extent=False,  # keep the extent of the mapping area
                authcfg=nib_authcfg,
                tile_matrix_set=nib_parameters['tile_matrix_set'],
                image_format=nib_parameters['format'],
            ):
                warnings.append(_layer_failed(nib_parameters['layer']))

    # Adjust project snapping and overlap options
    project_setup.set_snap_overlap()

    # Save the project: in place when adding to an open project (#72),
    # otherwise as NiN_kartlegging.qgz next to the geopackage
    if not keep_open_project:
        project_path = str(Path(gpkg_path).parent / "NiN_kartlegging.qgz")
        QGS_PROJECT.setFileName(project_path)
    QGS_PROJECT.write()

    return warnings
