"""
Defines the human-readable aliases in the nin_polygons form
editor.
"""


def get_field_aliases() -> dict:
    '''Returns a dict with predefined field aliases for field names.'''

    field_aliases = {
        'fid': 'ID',
        'area': 'Areal (m²)',
        'regdato': 'Dato',
        'type': 'Type',
        'hovedtypegruppe': 'Hovedtypegruppe',
        'hovedtypegruppe_2': 'Hovedtypegruppe 2',
        'hovedtypegruppe_3': 'Hovedtypegruppe 3',
        'hovedtype': 'Hovedtype',
        'hovedtype_2': 'Hovedtype 2',
        'hovedtype_3': 'Hovedtype 3',
        # USES CONDITION IN 'project_setup.py' INSTEAD!
        # grunntype_or_klenhet': 'Grunntype/Kartleggingsenhet'
        'variabler': 'Variabler',
        'kode_id_label': 'Påskrift',
        'andel_kle_1': 'Andel av naturtype 1', 
        'andel_kle_2': 'Andel av naturtype 2', 
        'andel_kle_3': 'Andel av naturtype 3', 
    }

    return field_aliases
