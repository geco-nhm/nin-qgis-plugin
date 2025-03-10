from qgis.core import (
    QgsProject,
    QgsExpression,
    QgsEditorWidgetSetup,
    QgsDefaultValue,
    QgsFieldConstraints,
    QgsVectorLayer
)

# Retrieve the layer named "andel2"
layer_name = "nin_polygons"
layer = QgsProject.instance().mapLayersByName(layer_name)
if not layer:
    print(f"❌ Layer '{layer_name}' not found! Ensure it is loaded in QGIS.")
    exit()
layer = layer[0]  # Assuming the first match is the desired layer

# Function to configure a field
def configure_field(
    layer: QgsVectorLayer,
    field_name: str,
    default_value_expr: str,
    widget_type: str,
    min_val: int,
    max_val: int,
    step: int,
    suffix: str,
    constraint_expr: str,
    constraint_desc: str,
    constraint_enforced: bool
):
    # Get the field index
    field_idx = layer.fields().indexFromName(field_name)
    if field_idx == -1:
        print(f"❌ Field '{field_name}' not found in the layer!")
        return

    # Set default value expression
    default_value = QgsDefaultValue(default_value_expr)
    layer.setDefaultValueDefinition(field_idx, default_value)

    # Set widget type and configuration
    config = {
        "Min": min_val,
        "Max": max_val,
        "Step": step,
        "Suffix": suffix
    }
    layer.setEditorWidgetSetup(field_idx, QgsEditorWidgetSetup(widget_type, config))

    # Set constraint expression
    if constraint_expr:
        layer.setConstraintExpression(field_idx, constraint_expr, constraint_desc)
        if constraint_enforced:
            layer.setFieldConstraint(field_idx, QgsFieldConstraints.ConstraintNotNull, True)

# Start Editing Mode
layer.startEditing()

# Configure Fields
configure_field(
    layer,
    "andel_kle_1",
    "100.0",
    "Range",
    50,
    100,
    10,
    "%",
    "\"andel_kle_1\" IS NOT NULL",
    "andel_kle_1 must have a value",
    True
)

configure_field(
    layer,
    "andel_kle_2",
    "if(\"andel_kle_1\" >= 100, 0, 100 - (\"andel_kle_1\" + \"andel_kle_3\"))",
    "Range",
    0,
    100,
    10,
    "%",
    "(\"andel_kle_1\" + \"andel_kle_2\" + \"andel_kle_3\") = 100 AND \"andel_kle_2\" <= \"andel_kle_1\"",
    "Sum must be 100% and andel_kle_2 cannot be greater than andel_kle_1",
    True
)

configure_field(
    layer,
    "andel_kle_3",
    "if((\"andel_kle_1\" + \"andel_kle_2\") >= 100, 0, 100 - (\"andel_kle_1\" + \"andel_kle_2\"))",
    "Range",
    0,
    100,
    10,
    "%",
    "(\"andel_kle_1\" + \"andel_kle_2\" + \"andel_kle_3\") = 100 AND \"andel_kle_3\" <= \"andel_kle_2\"",
    "Sum must be 100% and andel_kle_3 cannot be greater than andel_kle_2",
    True
)

# Commit changes
if layer.commitChanges():
    print(f"✅ Fields successfully configured on layer '{layer_name}'!")
else:
    print(f"❌ Failed to commit changes to layer '{layer_name}'. Please check for errors.")
