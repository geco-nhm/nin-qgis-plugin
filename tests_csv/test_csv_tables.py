"""
Tests to verify the CSV attribute tables and metadata files
are up-to-date and consistent with the NiN Kode API data.

Run with: python -m pytest nin_qgis_plugin/test/test_csv_tables.py -v
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import pytest

# Paths
REPO_ROOT = Path(__file__).parents[1]
PLUGIN_ROOT = REPO_ROOT / "nin_qgis_plugin"
ATTRIBUTE_TABLES_PATH = PLUGIN_ROOT / "csv" / "attribute_tables"
FIELD_META_PATH = PLUGIN_ROOT / "csv" / "layer_fields_meta"
API_VERSION_FILE = REPO_ROOT / "nin_api_version_info.txt"

# All expected table names (without var_ prefix variants)
HIERARCHY_TABLES = ["typer", "hovedtypegrupper", "hovedtyper", "grunntyper"]
MAPPING_SCALES = ["M005", "M020", "M050"]
VAR_TABLES = [f"var_{s}" for s in MAPPING_SCALES] + ["var_grunntyper"]
ALL_TABLES = HIERARCHY_TABLES + MAPPING_SCALES + VAR_TABLES


# ---------- Fixtures ----------

@pytest.fixture(params=ALL_TABLES)
def table_name(request):
    return request.param


@pytest.fixture(params=HIERARCHY_TABLES + MAPPING_SCALES)
def hierarchy_table_name(request):
    return request.param


# ---------- API Version Info ----------

class TestAPIVersionInfo:
    """Check that the API version tracking file is present and recent."""

    def test_version_file_exists(self):
        assert API_VERSION_FILE.exists(), (
            f"Missing {API_VERSION_FILE}. "
            "Run: python nin-qgis-handling/python/generate_api_version_info.py"
        )

    def test_version_file_has_commit_sha(self):
        content = API_VERSION_FILE.read_text()
        assert "latest commit:" in content, "Version file missing commit SHA"
        # Extract SHA — should be 40 hex chars
        for line in content.splitlines():
            if "latest commit:" in line:
                sha = line.split("latest commit:")[-1].strip()
                assert len(sha) == 40, f"Commit SHA has unexpected length: {sha}"
                assert all(c in "0123456789abcdef" for c in sha), (
                    f"Commit SHA contains non-hex chars: {sha}"
                )
                break

    def test_version_file_is_recent(self):
        """Check the recorded date is within the last 90 days."""
        content = API_VERSION_FILE.read_text()
        for line in content.splitlines():
            if line.startswith("date:"):
                date_str = line.split("date:")[-1].strip()
                # Format: 2026/03/17, 14:07:59
                recorded = datetime.strptime(date_str, "%Y/%m/%d, %H:%M:%S")
                age = datetime.now() - recorded
                assert age < timedelta(days=90), (
                    f"API version info is {age.days} days old. "
                    "Consider re-running generate_api_version_info.py"
                )
                break


# ---------- CSV File Existence ----------

class TestCSVFilesExist:
    """Verify all expected CSV files are present."""

    def test_attribute_table_exists(self, table_name):
        csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"
        assert csv_path.exists(), f"Missing attribute table: {csv_path}"

    def test_meta_file_exists(self, table_name):
        meta_path = FIELD_META_PATH / f"{table_name}_meta.csv"
        assert meta_path.exists(), f"Missing meta file: {meta_path}"

    def test_nin_polygons_meta_exists(self):
        meta_path = FIELD_META_PATH / "nin_polygons_meta.csv"
        assert meta_path.exists(), f"Missing nin_polygons_meta.csv"


# ---------- CSV Integrity ----------

class TestCSVIntegrity:
    """Check CSV files are well-formed and non-empty."""

    def test_attribute_table_not_empty(self, table_name):
        csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"
        df = pd.read_csv(csv_path)
        assert len(df) > 0, f"{table_name} attribute table is empty"

    def test_attribute_table_has_fid(self, table_name):
        csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"
        df = pd.read_csv(csv_path)
        assert "fid" in df.columns, f"{table_name} is missing 'fid' column"

    def test_meta_has_required_columns(self, table_name):
        meta_path = FIELD_META_PATH / f"{table_name}_meta.csv"
        df = pd.read_csv(meta_path)
        required_cols = {"name", "type", "length", "precision"}
        assert required_cols.issubset(set(df.columns)), (
            f"{table_name}_meta.csv missing columns: "
            f"{required_cols - set(df.columns)}"
        )

    def test_fid_is_unique(self, table_name):
        csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"
        df = pd.read_csv(csv_path)
        assert df["fid"].is_unique, (
            f"{table_name} has duplicate fid values"
        )


# ---------- Meta ↔ Attribute Table Consistency ----------

class TestMetaConsistency:
    """Verify meta (field definitions) match attribute table columns."""

    def test_meta_fields_match_attribute_columns(self, table_name):
        meta_path = FIELD_META_PATH / f"{table_name}_meta.csv"
        csv_path = ATTRIBUTE_TABLES_PATH / f"{table_name}_attribute_table.csv"

        meta_df = pd.read_csv(meta_path)
        attr_df = pd.read_csv(csv_path)

        meta_fields = set(meta_df["name"].tolist())
        attr_fields = set(attr_df.columns.tolist())

        assert meta_fields == attr_fields, (
            f"Column mismatch in {table_name}:\n"
            f"  In meta but not in attribute table: {meta_fields - attr_fields}\n"
            f"  In attribute table but not in meta: {attr_fields - meta_fields}"
        )


# ---------- Hierarchy Relationships ----------

class TestHierarchyRelationships:
    """Verify foreign key relationships between hierarchy tables."""

    def test_typer_has_expected_count(self):
        df = pd.read_csv(ATTRIBUTE_TABLES_PATH / "typer_attribute_table.csv")
        assert len(df) >= 5, (
            f"typer table has only {len(df)} rows, expected at least 5"
        )

    def test_hovedtypegrupper_references_typer(self):
        htg = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "hovedtypegrupper_attribute_table.csv"
        )
        typer = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "typer_attribute_table.csv"
        )
        if "typer_fkey" in htg.columns:
            typer_fids = set(typer["fid"].tolist())
            htg_fkeys = set(htg["typer_fkey"].dropna().astype(int).tolist())
            orphans = htg_fkeys - typer_fids
            assert not orphans, (
                f"hovedtypegrupper has orphan typer_fkey values: {orphans}"
            )

    def test_hovedtyper_references_hovedtypegrupper(self):
        ht = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "hovedtyper_attribute_table.csv"
        )
        htg = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "hovedtypegrupper_attribute_table.csv"
        )
        if "hovedtypegrupper_fkey" in ht.columns:
            htg_fids = set(htg["fid"].tolist())
            ht_fkeys = set(
                ht["hovedtypegrupper_fkey"].dropna().astype(int).tolist()
            )
            orphans = ht_fkeys - htg_fids
            assert not orphans, (
                f"hovedtyper has orphan hovedtypegrupper_fkey values: {orphans}"
            )

    def test_grunntyper_references_hovedtyper(self):
        gt = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "grunntyper_attribute_table.csv"
        )
        ht = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "hovedtyper_attribute_table.csv"
        )
        if "hovedtyper_fkey" in gt.columns:
            ht_fids = set(ht["fid"].tolist())
            gt_fkeys = set(
                gt["hovedtyper_fkey"].dropna().astype(int).tolist()
            )
            orphans = gt_fkeys - ht_fids
            assert not orphans, (
                f"grunntyper has orphan hovedtyper_fkey values: {orphans}"
            )

    @pytest.mark.parametrize("scale", MAPPING_SCALES)
    def test_mapping_units_reference_hovedtyper(self, scale):
        mu = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / f"{scale}_attribute_table.csv"
        )
        ht = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "hovedtyper_attribute_table.csv"
        )
        if "hovedtyper_fkey" in mu.columns:
            ht_fids = set(ht["fid"].tolist())
            mu_fkeys = set(
                mu["hovedtyper_fkey"].dropna().astype(int).tolist()
            )
            orphans = mu_fkeys - ht_fids
            assert not orphans, (
                f"{scale} has orphan hovedtyper_fkey values: {orphans}"
            )


# ---------- Variable Tables ----------

class TestVariableTables:
    """Verify variable attribute tables have expected structure."""

    def test_var_grunntyper_has_expected_columns(self):
        df = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "var_grunntyper_attribute_table.csv"
        )
        expected = {"fid", "grunntype_or_kle_fkey", "var_name",
                    "var_kode_id", "maaleskala", "values", "display_str"}
        assert expected.issubset(set(df.columns)), (
            f"var_grunntyper missing columns: {expected - set(df.columns)}"
        )

    def test_var_grunntyper_references_grunntyper(self):
        var_gt = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "var_grunntyper_attribute_table.csv"
        )
        gt = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "grunntyper_attribute_table.csv"
        )
        gt_fids = set(gt["fid"].tolist())
        var_fkeys = set(
            var_gt["grunntype_or_kle_fkey"].dropna().astype(int).tolist()
        )
        orphans = var_fkeys - gt_fids
        assert not orphans, (
            f"var_grunntyper has {len(orphans)} orphan "
            f"grunntype_or_kle_fkey values (sample: {list(orphans)[:5]})"
        )

    @pytest.mark.parametrize("scale", MAPPING_SCALES)
    def test_var_scale_table_not_empty(self, scale):
        csv_path = ATTRIBUTE_TABLES_PATH / f"var_{scale}_attribute_table.csv"
        df = pd.read_csv(csv_path)
        assert len(df) > 0, f"var_{scale} table is empty"


# ---------- Row Count Sanity Checks ----------

class TestRowCounts:
    """Basic sanity checks on expected data volume."""

    def test_grunntyper_row_count(self):
        df = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "grunntyper_attribute_table.csv"
        )
        assert len(df) > 500, (
            f"grunntyper has only {len(df)} rows — expected 500+"
        )

    @pytest.mark.parametrize("scale", MAPPING_SCALES)
    def test_mapping_unit_row_count(self, scale):
        df = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / f"{scale}_attribute_table.csv"
        )
        assert len(df) > 100, (
            f"{scale} has only {len(df)} rows — expected 100+"
        )

    def test_var_grunntyper_row_count(self):
        df = pd.read_csv(
            ATTRIBUTE_TABLES_PATH / "var_grunntyper_attribute_table.csv"
        )
        assert len(df) > 1000, (
            f"var_grunntyper has only {len(df)} rows — expected 1000+"
        )
