import importlib.util
import csv
import tempfile
from pathlib import Path

import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / 'nin-qgis-handling'
    / 'python'
    / 'fid_stability.py'
)
SPEC = importlib.util.spec_from_file_location('fid_stability', MODULE_PATH)
FID_STABILITY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FID_STABILITY)
ATTRIBUTE_TABLES_DIR = Path(__file__).resolve().parents[1] / 'nin_qgis_plugin' / 'csv' / 'attribute_tables'


def test_assign_append_only_fids_preserves_existing_ids_and_appends_new_ones():
    rows = [
        {'kode_id': 'NA-V'},
        {'kode_id': 'NA-VA01'},
        {'kode_id': 'NA-NY'},
    ]
    existing_csv = '''fid,kode_id\n59,NA-V\n296,NA-VA01\n'''

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / 'hovedtyper_attribute_table.csv'
        csv_path.write_text(existing_csv, encoding='utf-8')

        assigned_fids = FID_STABILITY.assign_append_only_fids(
            rows=rows,
            identity_columns=('kode_id',),
            existing_csv_path=csv_path,
            table_name='hovedtyper',
        )

    assert assigned_fids == [59, 296, 297]


def test_assign_append_only_fids_supports_composite_variable_identity_keys():
    rows = [
        {
            'grunntype_or_kle_fkey': 668,
            'var_kode_id': 'LM-KA',
            'maaleskala': 'KA-SO',
        },
        {
            'grunntype_or_kle_fkey': 667,
            'var_kode_id': 'LM-KA',
            'maaleskala': 'KA-SO',
        },
        {
            'grunntype_or_kle_fkey': 999,
            'var_kode_id': 'NY-VAR',
            'maaleskala': 'SO',
        },
    ]
    existing_csv = (
        'fid,grunntype_or_kle_fkey,var_kode_id,maaleskala\n'
        '11,668,LM-KA,KA-SO\n'
        '12,667,LM-KA,KA-SO\n'
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / 'var_M005_attribute_table.csv'
        csv_path.write_text(existing_csv, encoding='utf-8')

        assigned_fids = FID_STABILITY.assign_append_only_fids(
            rows=rows,
            identity_columns=('grunntype_or_kle_fkey', 'var_kode_id', 'maaleskala'),
            existing_csv_path=csv_path,
            table_name='var_M005',
        )

    assert assigned_fids == [11, 12, 13]


def test_assign_append_only_fids_rejects_duplicate_identity_rows():
    rows = [
        {'kode_id': 'NA-V'},
        {'kode_id': 'NA-V'},
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / 'hovedtyper_attribute_table.csv'
        csv_path.write_text('fid,kode_id\n59,NA-V\n', encoding='utf-8')

        with pytest.raises(ValueError, match='Duplicate identity'):
            FID_STABILITY.assign_append_only_fids(
                rows=rows,
                identity_columns=('kode_id',),
                existing_csv_path=csv_path,
                table_name='hovedtyper',
            )


@pytest.mark.parametrize('table_name', ['var_grunntyper', 'var_M005', 'var_M020', 'var_M050'])
def test_variable_tables_have_unique_stable_identity(table_name):
    csv_path = ATTRIBUTE_TABLES_DIR / f'{table_name}_attribute_table.csv'

    with open(csv_path, newline='', encoding='utf-8') as csv_file:
        rows = list(csv.DictReader(csv_file))

    assigned_fids = FID_STABILITY.assign_append_only_fids(
        rows=rows,
        identity_columns=('grunntype_or_kle_fkey', 'var_kode_id', 'maaleskala'),
        existing_csv_path=csv_path,
        table_name=table_name,
    )

    assert len(assigned_fids) == len(rows)