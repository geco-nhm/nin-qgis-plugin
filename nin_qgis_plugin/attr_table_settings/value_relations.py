"""Defines the value relations between nin_polygons fields"""

from typing import List
from qgis.core import QgsProject

QGIS_PROJECT = QgsProject.instance()

def get_value_relations(
    selected_type_id: List[str],
    selected_mapping_scale: str,
    selected_items: List[str],
) -> tuple[dict]:
    '''Returns hardcoded value relations as a tuple'''

    if selected_items:
        selected_kode_ids = [f"'{item['kode_id']}'" for item in selected_items]
        # passing the selected "Hovedtypegrupper" from the UI
        additional_filter = \
            f'"kode_id" IN ({", ".join(map(str, selected_kode_ids))})'

    value_relations = (
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('typer')[0],
            "primary_key_field_name": "type",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f""""kode_id" = '{selected_type_id}'""",
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtypegrupper')[0],
            "primary_key_field_name": "hovedtypegruppe",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f'''"typer_fkey" = current_value('type') AND {additional_filter}''' if additional_filter else '''"typer_fkey" = current_value('type')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtypegrupper')[0],
            "primary_key_field_name": "hovedtypegruppe_2",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f'''"typer_fkey" = current_value('type') AND {additional_filter}''' if additional_filter else '''"typer_fkey" = current_value('type')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtypegrupper')[0],
            "primary_key_field_name": "hovedtypegruppe_3",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": f'''"typer_fkey" = current_value('type') AND {additional_filter}''' if additional_filter else '''"typer_fkey" = current_value('type')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtyper')[0],
            "primary_key_field_name": "hovedtype",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtyper')[0],
            "primary_key_field_name": "hovedtype_2",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe_2')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName('hovedtyper')[0],
            "primary_key_field_name": "hovedtype_3",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtypegrupper_fkey" = current_value('hovedtypegruppe_3')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet_2",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype_2')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet_3",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype_3')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(f"var_{selected_mapping_scale}")[0],
            "primary_key_field_name": "variabler",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "display_str",
            "filter_expression": '''"grunntype_or_kle_fkey" = current_value('grunntype_or_klenhet')''',
            "allow_multi": True,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "kode_id_label",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "kode_id",
            "filter_expression": "",
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet_2",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype_2')''',
            "allow_multi": False,
        },
        {
            "primary_attribute_table_layer": QGIS_PROJECT.mapLayersByName('nin_polygons')[0],
            "forgein_attribute_table_layer": QGIS_PROJECT.mapLayersByName(selected_mapping_scale)[0],
            "primary_key_field_name": "grunntype_or_klenhet_3",
            "foreign_key_field_name": "fid",
            "foreign_field_to_display": "navn",
            "filter_expression": '''"hovedtyper_fkey" = current_value('hovedtype_3')''',
            "allow_multi": False,
        },
    )

    return value_relations
