"""
Programmatically designs a "drag and drop" form layout.
Necessary because QField does not support .ui files
for editing forms.
"""

from qgis.core import (
    QgsVectorLayer,
    QgsAttributeEditorField,
    QgsExpression,
    QgsOptionalExpression,
    QgsAttributeEditorContainer,
    Qgis,
)

# from qgis.PyQt5.QtWidgets import (
# QTabWidget, QVBoxLayout, QLineEdit, QLabel, QWidget, QComboBox
# )

# Form layouts:
# 'polygon': three tabs (Type 1/2/3) with mosaic share fields, for nin_polygons.
# 'simple': one container with the single-type fields, for nin_points and nin_lines.
POLYGON_LAYOUT = 'polygon'
SIMPLE_LAYOUT = 'simple'


def _set_drag_and_drop_layout(edit_form_config) -> None:
    '''Switches the form to the "drag and drop" (tab) layout.'''

    # OBS! We need to check Qgis version here, because prior
    # to 3.32 it was handled differently
    qgis_version = Qgis.version().split(".")

    if int(qgis_version[0]) >= 4 or (int(qgis_version[0]) == 3 and int(qgis_version[1]) >= 32):
        # Change to 'TabLayout', aka Drag and drop layout
        edit_form_config.setLayout(
            Qgis.AttributeFormLayout(1)
        )
    elif int(qgis_version[0]) == 3:
        edit_form_config.setLayout(1)
    else:
        raise NotImplementedError(
            f"Your Qgis version '{Qgis.version()}' is not supported, please download latest."
        )


def _add_fields_to_container(container, fields, field_names) -> None:
    '''Adds the named fields (skipping ones the layer lacks) to a form container.'''

    for field in field_names:
        field_idx = fields.indexFromName(field)
        if field_idx < 0:
            continue
        editor_field = QgsAttributeEditorField(
            name=field,
            idx=field_idx,
            parent=container,
        )
        container.addChildElement(editor_field)


def adjust_layer_edit_form(
    layer: QgsVectorLayer,
    layout: str = POLYGON_LAYOUT,
) -> QgsVectorLayer:
    '''
    Configures the edit form of a mapping layer.

    layout: 'polygon' (three type tabs, nin_polygons) or
            'simple' (one container, nin_points / nin_lines).
    '''

    if layout not in (POLYGON_LAYOUT, SIMPLE_LAYOUT):
        raise ValueError(f"Unknown edit form layout '{layout}'.")

    # Retrieve fields
    fields = layer.fields()

    # Retrieve existing edit form configuration
    edit_form_config = layer.editFormConfig()
    _set_drag_and_drop_layout(edit_form_config)

    # Retrieve root container and clear default layout
    root_container = edit_form_config.invisibleRootContainer()
    root_container.clear()

    if layout == SIMPLE_LAYOUT:
        container = QgsAttributeEditorContainer(
            name="Type",
            parent=root_container,
        )
        edit_form_config.addTab(container)

        _add_fields_to_container(
            container=container,
            fields=fields,
            field_names=[
                'type',
                'hovedtypegruppe',
                'hovedtype',
                'grunntype_or_klenhet',
                'variabler',
                'kode_id_label',
                'lengde',  # nin_lines only, skipped when missing
                'photo',
                'kommentar',
            ],
        )

        layer.setEditFormConfig(edit_form_config)
        return layer

    # Add the tabs
    tab_1 = QgsAttributeEditorContainer(
        name="Type 1",
        parent=root_container,
    )
    tab_2 = QgsAttributeEditorContainer(
        name="Type 2",
        parent=root_container,
    )
    tab_3 = QgsAttributeEditorContainer(
        name="Type 3",
        parent=root_container,
    )

    # Define visibility
    tab_2.setVisibilityExpression(
        QgsOptionalExpression(
            QgsExpression('''"andel_kle_1" < 100.0''')
        ),
    )
    tab_3.setVisibilityExpression(
        QgsOptionalExpression(
            QgsExpression('''("andel_kle_1" + "andel_kle_2") < 100.0''')
        ),
    )

    edit_form_config.addTab(tab_1)
    edit_form_config.addTab(tab_2)
    edit_form_config.addTab(tab_3)

    # edit_form_config.addTab(....) # -> QgsAttributeEditorElement
    # QgsAttributeEditorElement(type: Qgis.AttributeEditorType, name: Optional[str], parent: Optional[QgsAttributeEditorElement] = None)
    # AttributeEditorType(0) -> AeTypeContainer

    # Add all fields that should be shown in main tab
    fields_to_include = {
        'tab_1': {
            'tab': tab_1,
            'fields': [
                'area',
                'type',
                'hovedtypegruppe',
                'hovedtype',
                'grunntype_or_klenhet',
                'variabler',
                'andel_kle_1',
                'kode_id_label',
                'photo',
            ],
        },
        'tab_2': {
            'tab': tab_2,
            'fields': [
                'sammensatt',
                'mosaikk',
                'hovedtypegruppe_2',
                'hovedtype_2',
                'grunntype_or_klenhet_2',
                'andel_kle_2',
            ],
        },
        'tab_3': {
            'tab': tab_3,
            'fields': [
                'hovedtypegruppe_3',
                'hovedtype_3',
                'grunntype_or_klenhet_3',
                'andel_kle_3',
            ],
        },
    }

    for _, tab_fields in fields_to_include.items():
        _add_fields_to_container(
            container=tab_fields['tab'],
            fields=fields,
            field_names=tab_fields['fields'],
        )

    # Set as layers new form config
    layer.setEditFormConfig(edit_form_config)

    return layer
