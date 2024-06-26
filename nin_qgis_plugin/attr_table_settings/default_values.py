"""Defines the value relations between nin_polygons fields"""

from typing import List, Union
from pathlib import Path

from qgis.core import QgsProject
import pandas as pd

CSV_ROOT_PATH = Path(__file__).parents[1] / 'csv' / 'attribute_tables'


def get_fid_from_kode_id(
    attr_table_csv_path: Union[str, Path],
    kode_id: Union[str, List[str]],
) -> int:
    '''Retrieves the fid in an attribute table from kode_id'''

    df = pd.read_csv(
        attr_table_csv_path,
        index_col=False,
        encoding="utf-8",
    )

    fid = df.loc[
        df["kode_id"] == kode_id,
        "fid"
    ].values[0]

    return int(fid)


def get_default_values(
    selected_type_id: str,
    selected_hovedtypegrupper: List[str],
) -> List[dict]:
    """Returns a list of predefined default values"""

    type_fid = get_fid_from_kode_id(
        attr_table_csv_path=CSV_ROOT_PATH / 'typer_attribute_table.csv',
        kode_id=selected_type_id,
    )

    default_field_values: List[dict] = [
        {
            "layer_name": "nin_polygons",
            "field_name": "fid",
            "default_value_expression": "",
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "regdato",
            "default_value_expression": "now()",
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "area",
            "default_value_expression": "$area",
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "type",
            "default_value_expression": f"{type_fid}",
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "kode_id_label",
            "default_value_expression": '''"grunntype_or_klenhet"''',
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "variabler",
            "default_value_expression": "",
            "make_field_uneditable": True,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "andel_kle_1",
            "default_value_expression": "100.0",
            "make_field_uneditable": False,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "andel_kle_2",
            "default_value_expression": "0.0",
            "make_field_uneditable": False,
        },
        {
            "layer_name": "nin_polygons",
            "field_name": "andel_kle_3",
            "default_value_expression": "0.0",
            "make_field_uneditable": False,
        },
    ]

    # If only one hovedtypegruppe selected, also set as default
    if len(selected_hovedtypegrupper) == 1:
        
        hovedtypegruppe_fid = get_fid_from_kode_id(
            attr_table_csv_path=CSV_ROOT_PATH / 'hovedtypegrupper_attribute_table.csv',
            kode_id=selected_hovedtypegrupper[0]['kode_id'],
        )

        default_field_values.append(
            {
                "layer_name": "nin_polygons",
                "field_name": "hovedtypegruppe",
                "default_value_expression": f"{hovedtypegruppe_fid}",
                "make_field_uneditable": True,
            }
        )

    return default_field_values
