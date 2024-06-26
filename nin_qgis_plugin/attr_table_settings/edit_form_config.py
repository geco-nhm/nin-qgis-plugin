"""
Programmatically specifies a "drag and drop" layer editor
widget. Necessary because QField does not support .ui files
for editor widgets.
"""

from qgis.core import (
    QgsVectorLayer, QgsAttributeEditorField, Qgis
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
    if int(qgis_version[1]) < 32:
        edit_form_config.setLayout(1)
    else:
        # Change to 'TabLayout', aka Drag and drop layout
        edit_form_config.setLayout(
            Qgis.AttributeFormLayout(1)
        )

    # edit_form_config.addTab(....) # -> QgsAttributeEditorElement
    # QgsAttributeEditorElement(type: Qgis.AttributeEditorType, name: Optional[str], parent: Optional[QgsAttributeEditorElement] = None)
    # AttributeEditorType(0) -> AeTypeContainer

    root_container = edit_form_config.invisibleRootContainer()
    root_container.clear()

    # Containers for different tabs
    # main_tab_container = Qgis.AttributeEditorType(0)

    # Add all that should be shown
    fields_to_include = [
        'area',
        'type',
        'andel_kle_1',
        'hovedtypegruppe',
        'hovedtype',
        'grunntype_or_klenhet',
        'variabler',
        'sammensatt',
        'mosaikk',
        'andel_kle_2',
        'hovedtypegruppe_2',
        'hovedtype_2',
        'grunntype_or_klenhet_2',
        'andel_kle_3',
        'hovedtypegruppe_3',
        'hovedtype_3',
        'grunntype_or_klenhet_3',
    ]

    for field in fields_to_include:

        editor_field = QgsAttributeEditorField(
            name=field,
            idx=fields.indexFromName(field),
            parent=root_container,
        )
        root_container.addChildElement(editor_field)

    # Set as layers new form config
    layer.setEditFormConfig(edit_form_config)

    # To get Entries on the Tab boxes, you need to create QgsAttributeEditorField
    # items with the Tab Boxes as Parent Containers.

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
