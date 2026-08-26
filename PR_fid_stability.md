# Stabilize relation-facing `fid` values and record catalogue provenance

## Summary

This PR addresses the `fid` drift problem described in issue #73 in two parts:

1. Generated GeoPackages now record catalogue provenance so downstream users can detect which catalogue they were built from.
2. CSV catalogue generators now preserve relation-facing `fid` values append-only instead of reassigning them from traversal order.

The current QGIS value-relation model remains `fid`-based in this PR. This change is intended to stop silent meaning changes for existing stored integers without redesigning the widget/filter contract.

## Problem

The plugin stores mapped selections as lookup-table `fid` values. Those `fid` values were previously assigned as positional row numbers while traversing API responses. When the NiN catalogue was regenerated from the API, rows could move and old stored integers would point at a different `kode_id`.

That meant previously valid field data could silently change meaning after catalogue regeneration.

## What changed

### GeoPackage provenance

- Add [nin_qgis_plugin/catalogue_provenance.py](nin_qgis_plugin/catalogue_provenance.py) to read:
  - plugin version from [nin_qgis_plugin/metadata.txt](nin_qgis_plugin/metadata.txt)
  - `nin-kode-api` SHA from [nin_api_version_info.txt](nin_api_version_info.txt)
- Write a new `catalogue_provenance` table from [nin_qgis_plugin/create_gpkg.py](nin_qgis_plugin/create_gpkg.py)
  - `plugin_version`
  - `nin_kode_api_sha`
  - `generated_at`

### Append-only `fid` stabilization

- Add [nin-qgis-handling/python/fid_stability.py](nin-qgis-handling/python/fid_stability.py)
  - stable identity matching against the checked-in CSV baseline
  - append-only `fid` allocation for new rows
  - parent foreign-key remapping helpers after child rows receive stable ids
- Apply the stabilization logic in:
  - [nin-qgis-handling/python/create_type_tables_from_api.py](nin-qgis-handling/python/create_type_tables_from_api.py)
  - [nin-qgis-handling/python/create_variable_tables_from_api.py](nin-qgis-handling/python/create_variable_tables_from_api.py)
  - [nin-qgis-handling/python/infer_kartleggingsenheter_vars.py](nin-qgis-handling/python/infer_kartleggingsenheter_vars.py)
  - [nin-qgis-handling/python/add_limniske_vannmasse_to_kle.py](nin-qgis-handling/python/add_limniske_vannmasse_to_kle.py)

### Limnic special-case handling

- Fold the limnic KLE append into the stabilized generation path so those rows also preserve historical `fid`s rather than being renumbered on every rebuild.

## Identity rules used in this PR

- `typer`, `hovedtypegrupper`, `hovedtyper`, `grunntyper`, `M005`, `M020`, `M050`: stable identity is `kode_id`
- `var_grunntyper`, `var_M005`, `var_M020`, `var_M050`: stable identity is `(grunntype_or_kle_fkey, var_kode_id, maaleskala)`

These rules keep the current `ValueRelation` contract intact while making regenerated row ids stable for existing identities.

## Validation

### Focused tests

- `python -m pytest tests_csv/test_catalogue_provenance.py -q`
- `python -m pytest tests_csv/test_fid_stability.py -q`
- `C:\OSGeo4W\bin\python-qgis-ltr.bat -m unittest nin_qgis_plugin.test.test_create_gpkg -v`

### End-to-end regeneration check

The full CSV generation sequence was run against the live API and compared to the checked-in catalogue.

No checked-in CSV updates were required for this branch after validation. The stabilized generators reproduced the current catalogue identities and `fid` assignments exactly.

Observed result:

- `typer`: 10 / 10 unchanged `fid`s
- `hovedtypegrupper`: 68 / 68 unchanged `fid`s
- `hovedtyper`: 430 / 430 unchanged `fid`s
- `grunntyper`: 1401 / 1401 unchanged `fid`s
- `M005`: 759 / 759 unchanged `fid`s
- `M020`: 493 / 493 unchanged `fid`s
- `M050`: 332 / 332 unchanged `fid`s
- `var_grunntyper`: 5367 / 5367 unchanged `fid`s
- `var_M005`: 2470 / 2470 unchanged `fid`s
- `var_M020`: 1270 / 1270 unchanged `fid`s
- `var_M050`: 758 / 758 unchanged `fid`s

No missing identities and no unexpected new identities were observed in that validation run.

## Scope deliberately not changed here

- No switch from stored `fid` values to stored `kode_id` values
- No redesign of QGIS filter expressions or relation schema
- No migration/remapper tooling included in-tree

Those remain follow-up design decisions. This PR is intended as the smallest upstream fix that prevents future renumbering while preserving current project behavior.