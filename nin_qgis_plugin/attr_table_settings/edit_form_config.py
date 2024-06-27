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


def adjust_layer_edit_form(layer: QgsVectorLayer) -> QgsVectorLayer:
    '''TODO.'''

    # Retrieve fields
    fields = layer.fields()

    # Retrieve existing edit form configuration
    edit_form_config = layer.editFormConfig()

    # OBS! We need to check Qgis version here, because prior
    # to 3.32 it was handled differently
    qgis_version = Qgis.version().split(".")

    if int(qgis_version[0]) >= 3:
        if int(qgis_version[1]) < 32:
            edit_form_config.setLayout(1)
        else:
            # Change to 'TabLayout', aka Drag and drop layout
            edit_form_config.setLayout(
                Qgis.AttributeFormLayout(1)
            )
    else:
        raise NotImplementedError(
            f"Your Qgis version '{Qgis.version()}' is not supported, please download latest."
        )

    # Retrieve root container and clear default layout
    root_container = edit_form_config.invisibleRootContainer()
    root_container.clear()

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

    # Containers for different tabs
    # main_tab_container = Qgis.AttributeEditorType(0)

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
                'sammensatt',
                'mosaikk',
                'kode_id_label',
            ],
        },
        'tab_2': {
            'tab': tab_2,
            'fields': [
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

        cur_tab = tab_fields['tab']

        for field in tab_fields['fields']:
            editor_field = QgsAttributeEditorField(
                name=field,
                idx=fields.indexFromName(field),
                parent=cur_tab,
            )
            cur_tab.addChildElement(editor_field)
            # root_container.addChildElement(editor_field)

    # Set as layers new form config
    layer.setEditFormConfig(edit_form_config)

    return layer

    '''
    # Tab 1
    tab1 = QWidget()
    tab1_layout = QVBoxLayout()
    # Assuming 'my_field_1' is the name of the field
    box1 = QComboBox()
    box1.insertItem(0, "Test")
    box1.insertItem(1, "Bla")
    tab1_layout.addWidget(QLabel('Field 1:'))
    tab1_layout.addWidget(box1)
    tab1.setLayout(tab1_layout)
    edit_form_config.addTab(tab1, "First Tab")

    # Tab 2
    tab2 = QWidget()
    tab2_layout = QVBoxLayout()
    # Assuming 'my_field_1' is the name of the field
    box2 = QComboBox()
    box2.insertItem(0, "Test")
    box2.insertItem(1, "Bla")
    tab2_layout.addWidget(QLabel('Field 2:'))
    tab2_layout.addWidget(box2)
    tab2.setLayout(tab2_layout)
    edit_form_config.addTab(tab2, "Second Tab")
    '''
