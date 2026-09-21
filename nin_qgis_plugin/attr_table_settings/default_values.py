"""Defines the default field values and widget settings of the mapping layers"""

import csv
from typing import List, Union
from pathlib import Path

CSV_ROOT_PATH = Path(__file__).parents[1] / 'csv' / 'attribute_tables'

POLYGON_LAYER_NAME = 'nin_polygons'
LINE_LAYER_NAME = 'nin_lines'


def get_fid_from_kode_id(
    attr_table_csv_path: Union[str, Path],
    kode_id: str,
) -> int:
    '''Retrieves the fid in an attribute table from kode_id'''

    with open(attr_table_csv_path, newline='', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row['kode_id'] == kode_id:
                return int(row['fid'])

    raise ValueError(
        f"Could not find kode_id '{kode_id}' in '{attr_table_csv_path}'."
    )


def get_default_values(
    selected_type_id: str,
    selected_hovedtypegrupper: List[str],
    layer_name: str = POLYGON_LAYER_NAME,
) -> List[dict]:
    """
    Returns a list of predefined default values for the given mapping layer.

    All mapping layers (polygons, points, lines) share the single-type fields.
    Only 'nin_polygons' gets the area, mosaic and Type 2/3 share fields, and
    only 'nin_lines' gets the length field.
    """

    type_fid = get_fid_from_kode_id(
        attr_table_csv_path=CSV_ROOT_PATH / 'typer_attribute_table.csv',
        kode_id=selected_type_id,
    )

    common_field_values: List[dict] = [
        {
            "field_name": "fid",
            "default_value_expression": "",
            "make_field_uneditable": True,
            "apply_on_update": False,
        },
        {
            "field_name": "regdato",
            "default_value_expression": "now()",
            "make_field_uneditable": True,
            "apply_on_update": False,
        },
        {
            "field_name": "type",
            "default_value_expression": f"{type_fid}",
            "make_field_uneditable": True,
            "apply_on_update": True,
        },
        {
            "field_name": "kode_id_label",
            "default_value_expression": '''"grunntype_or_klenhet"''',
            "make_field_uneditable": True,
            "apply_on_update": True,
        },
        {
            "field_name": "variabler",
            "default_value_expression": "",
            "make_field_uneditable": True,
            "apply_on_update": False,
        },
    ]

    polygon_field_values: List[dict] = [
        {
            "field_name": "area",
            "default_value_expression": "round(area($geometry),1)",  # always planimetric
            "make_field_uneditable": True,
            "apply_on_update": False,
        },
        {
            "field_name": "andel_kle_1",
            "default_value_expression": "100.0",
            "widget_type": "Range",
            "widget_config": {
                "Min": 50,
                "Max": 100,
                "Step": 10,
                'AllowNull': False,
                "Suffix": "%"
            },
            "constraints": "(\"andel_kle_1\" + \"andel_kle_2\" + \"andel_kle_3\") = 100",
            "constraint_description": "grunntype 1 må være over 50% og sum grunntype 1, 2 og 3 må være 100 %",
            "not_null": True,
            "enforce_not_null": True,
            "make_field_uneditable": False,
            "apply_on_update": False,
        },
        {
            "field_name": "andel_kle_2",
            "default_value_expression": "if(\"andel_kle_1\"=100, 0, 100-(\"andel_kle_1\" + \"andel_kle_3\"))",
            "widget_type": "Range",
            "widget_config": {
                "Min": 0,
                "Max": 100,
                "Step": 10,
                "Suffix": "%"
            },
            "constraints": "(\"andel_kle_1\" + \"andel_kle_2\" + \"andel_kle_3\") = 100 AND \"andel_kle_2\" <= \"andel_kle_1\"",
            "constraint_description": "Sum grunntype 1, 2 og 3 må være 100 %",
            "make_field_uneditable": False,
            "apply_on_update": True,
        },
        {
            "field_name": "andel_kle_3",
            "default_value_expression": "if((\"andel_kle_1\" + \"andel_kle_2\")=100, 0, 100 - (\"andel_kle_1\" + \"andel_kle_2\"))",
            "widget_type": "Range",
            "widget_config": {
                "Min": 0,
                "Max": 100,
                "Step": 10,
                "Suffix": "%"
            },
            "constraints": "(\"andel_kle_1\" + \"andel_kle_2\" + \"andel_kle_3\") = 100 AND \"andel_kle_3\" <= \"andel_kle_2\"",
            "constraint_description": "Andel grunntype 3 må være <= andel grunntype 2",
            "make_field_uneditable": False,
            "apply_on_update": True,
        },
        {
            "field_name": "sammensatt",
            "default_value_expression": '''if("andel_kle_1" = 100, False, if("andel_kle_1" < 100, if("mosaikk" = True, False, True), True))''',
            "make_field_uneditable": False,
            "apply_on_update": False,
        },
        {
            "field_name": "mosaikk",
            "default_value_expression": '''if("andel_kle_1" = 100, False, if("andel_kle_1" < 100, if("sammensatt" = True, False, True), True))''',
            "make_field_uneditable": False,
            "apply_on_update": False,
        },
    ]

    line_field_values: List[dict] = [
        {
            "field_name": "lengde",
            "default_value_expression": "round(length($geometry),1)",  # always planimetric
            "make_field_uneditable": True,
            "apply_on_update": False,
        },
    ]

    default_field_values = list(common_field_values)
    if layer_name == POLYGON_LAYER_NAME:
        default_field_values.extend(polygon_field_values)
    elif layer_name == LINE_LAYER_NAME:
        default_field_values.extend(line_field_values)

    # If only one hovedtypegruppe selected, also set as default
    if len(selected_hovedtypegrupper) == 1:
        hovedtypegruppe_fid = get_fid_from_kode_id(
            attr_table_csv_path=CSV_ROOT_PATH / 'hovedtypegrupper_attribute_table.csv',
            kode_id=selected_hovedtypegrupper[0]['kode_id'],
        )

        default_field_values.append(
            {
                "field_name": "hovedtypegruppe",
                "default_value_expression": f"{hovedtypegruppe_fid}",
                "make_field_uneditable": True,
            }
        )

    for default_value in default_field_values:
        default_value["layer_name"] = layer_name

    return default_field_values
