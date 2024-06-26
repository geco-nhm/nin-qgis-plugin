"""
Defines the human-readable aliases in the nin_polygons form
editor.
"""


def get_field_aliases() -> dict:
    '''Returns a dict with predefined field aliases for field names.'''

    field_aliases = {
        'fid': 'ID',
        'area': 'Areal',
        'regdato': 'Dato',
        'type': 'Type',
        'hovedtypegruppe': 'Hovedtypegruppe',
        'hovedtype': 'Hovedtype',
        # USES CONDITION IN 'project_setup.py' INSTEAD!
        # grunntype_or_klenhet': 'Grunntype/Kartleggingsenhet'
        'variabler': 'Variabler',
        'kode_id_label': 'Label',
    }

    return field_aliases
