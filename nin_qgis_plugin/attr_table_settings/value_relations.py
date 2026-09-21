"""Defines the value relations between the mapping layer fields and the NiN tables"""

from typing import List
from qgis.core import QgsProject

QGIS_PROJECT = QgsProject.instance()

POLYGON_LAYER_NAME = 'nin_polygons'


def get_value_relations(
    selected_type_id: List[str],
    selected_mapping_scale: str,
    selected_items: List[str],
    layer_name: str = POLYGON_LAYER_NAME,
    base_layer_name: str = POLYGON_LAYER_NAME,
) -> tuple[dict]:
    '''
    Returns hardcoded value relations as a tuple.

    layer_name is the project layer to configure (e.g. 'nin_polygons_M005'),
    base_layer_name its kind without the scale suffix ('nin_polygons',
    'nin_points' or 'nin_lines').

    Every mapping layer (polygons, points, lines) gets the single-type
    hierarchy (type -> hovedtypegruppe -> hovedtype -> grunntype/KLE),
    the variables and the label relation. Only 'nin_polygons' gets the
    Type 2/3 relations.
    '''

    primary_layer = QGIS_PROJECT.mapLayersByName(layer_name)[0]
    typer_layer = QGIS_PROJECT.mapLayersByName('typer')[0]
    hovedtypegrupper_layer = QGIS_PROJECT.mapLayersByName('hovedtypegrupper')[0]
    hovedtyper_layer = QGIS_PROJECT.mapLayersByName('hovedtyper')[0]
    mapping_scale_layer = QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0]
    variables_layer = QGIS_PROJECT.mapLayersByName(f"var_{selected_mapping_scale}")[0]

    additional_filter = None
    if selected_items:
        selected_kode_ids = [f"'{item['kode_id']}'" for item in selected_items]
        # passing the selected "Hovedtypegrupper" from the UI
        additional_filter = \
            f'"kode_id" IN ({", ".join(map(str, selected_kode_ids))})'

    hovedtypegruppe_filter = (
        f'''"typer_fkey" = current_value('type') AND {additional_filter}'''
        if additional_filter else '''"typer_fkey" = current_value('type')'''
    )

    value_relations = [
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": typer_layer,
            "primary_key_field_name": "type",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f""""kode_id" = '{selected_type_id}'""",
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": hovedtypegrupper_layer,
            "primary_key_field_name": "hovedtypegruppe",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": hovedtypegruppe_filter,
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": hovedtyper_layer,
            "primary_key_field_name": "hovedtype",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": mapping_scale_layer,
            "primary_key_field_name": "grunntype_or_klenhet",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": variables_layer,
            "primary_key_field_name": "variabler",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "display_str",
            "filter_expression": '''"grunntype_or_kle_fkey" = current_value('grunntype_or_klenhet')''',
            "allow_multi": True,
        },
        {
            "primary_attribute_table_layer": primary_layer,
            "forgein_attribute_table_layer": mapping_scale_layer,
            "primary_key_field_name": "kode_id_label",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "kode_id",
            "filter_expression": "",
            "allow_multi": False,
        },
    ]

    if base_layer_name == POLYGON_LAYER_NAME:
        for suffix in ('_2', '_3'):
            value_relations.extend([
                {
                    "primary_attribute_table_layer": primary_layer,
                    "forgein_attribute_table_layer": hovedtypegrupper_layer,
                    "primary_key_field_name": f"hovedtypegruppe{suffix}",
                    "foreign_key_field_name": "fid",
                    "foreign_field_to_display": "navn",
                    "filter_expression": hovedtypegruppe_filter,
                    "allow_multi": False,
                },
                {
                    "primary_attribute_table_layer": primary_layer,
                    "forgein_attribute_table_layer": hovedtyper_layer,
                    "primary_key_field_name": f"hovedtype{suffix}",
                    "foreign_key_field_name": "fid",
                    "foreign_field_to_display": "navn",
                    "filter_expression": f'''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe{suffix}')''',
                    "allow_multi": False,
                },
                {
                    "primary_attribute_table_layer": primary_layer,
                    "forgein_attribute_table_layer": mapping_scale_layer,
                    "primary_key_field_name": f"grunntype_or_klenhet{suffix}",
                    "foreign_key_field_name": "fid",
                    "foreign_field_to_display": "navn",
                    "filter_expression": f'''"hovedtyper_fkey" = current_value('hovedtype{suffix}')''',
                    "allow_multi": False,
                },
            ])

    return tuple(value_relations)
