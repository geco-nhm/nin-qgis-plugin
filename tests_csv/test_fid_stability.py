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


def test_reordered_rows_preserve_stable_fids_and_parent_relationships():
    existing_typer_csv = 'fid,kode_id\n7,C-PE-NA\n3,C-LI\n'
    existing_hovedtypegrupper_csv = 'fid,kode_id\n10,NA-T\n11,LI-S\n'

    typer_rows = [
        {'fid': 0, 'kode_id': 'C-LI'},
        {'fid': 1, 'kode_id': 'C-PE-NA'},
    ]
    hovedtypegrupper_rows = [
        {'fid': 0, 'kode_id': 'LI-S', 'typer_fkey': 0},
        {'fid': 1, 'kode_id': 'NA-T', 'typer_fkey': 1},
    ]

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        typer_csv_path = tmp_path / 'typer_attribute_table.csv'
        hovedtypegrupper_csv_path = tmp_path / 'hovedtypegrupper_attribute_table.csv'
        typer_csv_path.write_text(existing_typer_csv, encoding='utf-8')
        hovedtypegrupper_csv_path.write_text(existing_hovedtypegrupper_csv, encoding='utf-8')

        stable_typer_fids = FID_STABILITY.assign_append_only_fids(
            rows=typer_rows,
            identity_columns=('kode_id',),
            existing_csv_path=typer_csv_path,
            table_name='typer',
        )
        typer_fid_remap = FID_STABILITY.build_fid_remap(
            rows=typer_rows,
            assigned_fids=stable_typer_fids,
        )

        stable_hovedtypegruppe_fids = FID_STABILITY.assign_append_only_fids(
            rows=hovedtypegrupper_rows,
            identity_columns=('kode_id',),
            existing_csv_path=hovedtypegrupper_csv_path,
            table_name='hovedtypegrupper',
        )
        remapped_parent_fkeys = FID_STABILITY.remap_foreign_key_values(
            values=[row['typer_fkey'] for row in hovedtypegrupper_rows],
            fid_remap=typer_fid_remap,
        )

    assert stable_typer_fids == [3, 7]
    assert stable_hovedtypegruppe_fids == [11, 10]
    assert remapped_parent_fkeys == [3, 7]


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