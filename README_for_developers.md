# Generate Relational NiN CSV Tables from NiN-Kode API

The NiN QGIS plugin depends on a set of **relational CSV tables** that describe the hierarchical structure of NiN classification systems, such as `typer`, `hovedtypegrupper`, `hovedtyper`, `grunntyper`, and various mapping scales (e.g., `M005`, `M020`, `M050`). These tables are built dynamically by querying the [NiN Kode API](https://nin-kode-api.artsdatabanken.no/swagger/index.html).

This section provides an overview of the scripts responsible for generating and maintaining these tables. It also includes setup instructions for developers working in the `nin-qgis-handling` environment.

> To update tables, navigate to the Python directory:
>
> ```
> cd <project_root>/nin-qgis-handling/python
> ```

Ensure your Python environment is activated and all dependencies are installed. The current integration **does not automatically track API versioning**—you must manually compare the latest API state with the `nin_api_version_info.txt` file, which records the Git commit SHA and timestamp at the time of data extraction.

---

## Development Environment

### Dependencies

* **Python** 3.12+
* [**Poetry**](https://python-poetry.org/) (tested with v1.8.2)
* [**mamba**](https://mamba.readthedocs.io/) / [**Anaconda**](https://www.anaconda.com/) (recommended for environment management)

### Installation

```bash
# Clone the repository
git clone https://github.com/geco-nhm/nin-qgis-plugin.git
cd nin-qgis-plugin
```

#### Create & activate environment:

```bash
mamba env create --file=environment.yaml
mamba activate nin-qgis-env
```

#### Install Python dependencies:

```bash
poetry install
```

### Symbolic Link to QGIS Plugin Directory (Windows only)

To use the plugin in QGIS, create a symbolic link from the plugin folder to the QGIS profile directory. Open PowerShell **as administrator** and run:

```powershell
New-Item -ItemType SymbolicLink `
  -Path "<path_to_qgis>\QGIS3\profiles\default\python\plugins\nin-qgis-plugin" `
  -Target "<path_to_nin_qgis_plugin>\nin_qgis_plugin"
```

For example, with a default QGIS installation path:

```powershell
New-Item -ItemType SymbolicLink `
  -Path "C:\Users\<user>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\nin-qgis-plugin" `
  -Target "C:\Users\<user>\Documents\GitHub\nin-qgis-plugin\nin_qgis_plugin"
```

---

## Configuration

* All save paths and API endpoint URLs are configured in `nin-qgis-handling/config.toml`.

---

## Tools in `nin-qgis-handling/python`

### Create Metadata Schemas

```bash
python3 create_attribute_meta_tables.py
```

* Creates `csv` files with QGIS field definitions for each attribute table based on `attribute_meta.json`
* `attribute_meta.json` defines field names, types, lengths, and precision in the GPKG layers.
* Edit `attribute_meta.json` if you need to add or remove fields from attribute tables, or when you need to create new ones.
* Resulting `csv` files stored in `<root>/nin_qgis_plugin_/csv/layer_fields_meta` by default (note: save path defined in `config.toml`).

---

### Build Hierarchical Type Tables

```bash
python3 create_type_tables_from_api.py
```

* Queries the NiN Kode API to build QGIS attribute tables for: `typer`, `hovedtypegrupper`, `hovedtyper`, `grunntyper`, and mapping unit tables (`M005`, `M020`, `M050`).
* Defines relations between hierarchical levels (e.g., which `hovedtype` a `grunntype` belongs to) by creating a column with IDs/keys.
* Resulting attribute table `csv` files stored in `<root>/nin_qgis_plugin_/csv/attribute_tables` by default (note: save path defined in `config.toml`).
* Excludes variable definitions (see below).

---

### Add Limniske Vannmasser (Special Case)

```bash
python3 add_limniske_vannmasse_to_kle.py
```

* Adds `NA-F Limniske vannmassesystemer` entries as `grunntyper` to mapping units (`M005`, `M020`, `M050`).
* Applies a hardcoded fix to maintain completeness. Use with caution.

---

### Create Variable Tables for Grunntyper

```bash
pip install requests tqdm
python3 create_variable_tables_from_api.py
```

* Fetches NiN variables from the API and links them to their associated `grunntyper`.
* Creates `all_variables.csv` and `var_grunntyper_attribute_table.csv`.
* Depends on `requests` and `tqdm`.

---

### Infer Variables for Mapping Units

```bash
python3 infer_kartleggingsenheter_vars.py
```

* Aggregates variables from `grunntyper` to coarser units (`kartleggingsenheter`).
* Creates variable attribute tables for each mapping scale.
* Still under active development and subject to changes.

---

### Track API Version Used

```bash
python3 generate_api_version_info.py
```

* Generates `nin_api_version_info.txt` with timestamp and latest commit SHA from the NiN Kode API GitHub repo.
* Used for version auditing (must be run manually).

---

# Under the hood

Short description which changes are happening in which file.

---

## CHANGES TO THE GEOPACKAGE (`.gpkg`)

**Responsible script:** `create_gpkg.py`

### 1. **Creation of Layers in the GPKG**

| Layer name             | Geometry       | Purpose                                       |
| ---------------------- | -------------- | --------------------------------------------- |
| `nin_polygons`         | `multipolygon` | Main mapping layer for classified polygons    |
| `nin_helper_points`    | `multipoint`   | Temporary data or helper points               |
| `typer`                | None           | Attribute hierarchy: top-level types          |
| `hovedtypegrupper`     | None           | Subtypes of `typer`                           |
| `hovedtyper`           | None           | Subtypes of `hovedtypegrupper`                |
| `M005`, `M020`, `M050` | None           | Mapping scale-specific `mapping units`       |
| `var_<scale>`          | None           | Variables per mapping unit (e.g., `var_M005`) |

### 2. **Populating Fields and Records**

* Each geometry-less layer is defined by a corresponding metadata `.csv` (e.g. `grunntyper_meta.csv`) and filled with attribute data from `<name>_attribute_table.csv`.
* Done via `add_layer_attributes_from_file()` and `add_attribute_values_from_csv()`.

### 3. **Field Definitions**

* Pulled from `csv/layer_fields_meta/`
* Fields include `fid`, `kode_id`, `langkode`, `navn`, foreign keys (e.g. `hovedtyper_fkey`), and mapping unit FKs (e.g. `kartleggingsenhet_m005_fkey`).

---

## CHANGES TO THE QGIS PROJECT

**Responsible script:** `project_setup.py`

### 1. **Symbology Configuration**

**Method:** `ProjectSetup.set_nin_polygons_styling()`
**Functionality:**

* **Random semi-transparent color per `kode_id_label`** from attribute table for selected mapping scale.
* Coded using `QgsCategorizedSymbolRenderer`.

**Example:**

* Polygon with `kode_id_label` = `FM05-M005-19` gets a distinct color.
* Unmatched entries shown in red.

### 2. **Labeling Logic**

**Same method:** `set_nin_polygons_styling()`
**Label expression:**

```sql
CASE
    WHEN "type" IN (1,2,3,4,5) THEN regexp_substr(represent_value("hovedtype"), '^[A-Z]+-[A-Z0-9]+')
    WHEN "kode_id_label" IS NULL AND "grunntype_or_klenhet_2" IS NULL THEN 'ikke kartlagt'
    ...
END
```

**Effect:**

* Removes the mapping scale part from label:
  `FM05-M005-19` → `FM05-19`
* Shows `"ikke kartlagt"` when no type assigned.

### 3. **Field Aliases**

**Method:** `ProjectSetup.set_field_aliases()`
**Effect:**

| Field Name               | Alias (example if `M005` selected) |
| ------------------------ | ---------------------------------- |
| `grunntype_or_klenhet`   | `Kartleggingsenhet`                |
| `grunntype_or_klenhet_2` | `Kartleggingsenhet 2`              |
| `kode_id_label`          | `Kode-ID navn` (if set via alias)  |

### 4. **Field Behavior: Defaults, Constraints, Widgets**

Defined by:

* `get_default_values()` (default\_values.py)
* `set_layer_field_default_values()`
* `set_constraints_expression()`

**Examples:**

* `regdato`: auto-filled on feature creation with current date/time.
* `area`: must meet MMU requirement based on scale (e.g., ≥ 500 m² for `M005`).
* Fields can be uneditable and invisible during edit (`form_config.setReadOnly()`).

### 5. **Hierarchical Drop-downs**

**Method:** `field_to_value_relation()`
**Source:** `get_value_relations()` (value\_relations.py)

**Effect:**

* Choosing a `type` filters the options for `hovedtypegrupper`, which filters `hovedtyper`, and so on.
* Implemented using **value relation widgets** with expression filters:

  ```python
  filter_expression = '''"typer_fkey" = current_value('type')'''
  ```

### 6. **Photo Widget**

**Method:** `set_photo_widget()`
**Effect:**

* Field `photo` allows attaching images/documents.
* Uses `ExternalResource` widget with viewer, path relative to project.

### 7. **DateTime Widget**

**Method:** `field_to_datetime()`
**Effect:**

* For fields like `regdato`, uses popup calendar and consistent format (`yyyy-MM-dd HH:mm:ss`).

---

## PROJECT-WIDE SETTINGS

### CRS Setting

**Method:** `set_project_crs()`
**Effect:** Project set to user-selected CRS (e.g., `EPSG:25833`).

### Snapping and Intersection Avoidance

**Method:** `set_snap_ovelap()`
**Effect:**

* Snapping tolerance: **1.0 meter** (vertex & segment).
* **Avoid intersections**: enabled for `nin_polygons`.
* Topological editing: enabled.

---

## WMS/WMTS BACKGROUND LAYERS

**Method:** `add_wms_layer()`
**Controlled by UI checkboxes. Adds:**

* **Topografisk norgeskart**: `https://wms.geonorge.no/skwms1/wms.topo?`
* **Topografisk gråtone**: `https://wms.geonorge.no/skwms1/wms.topograatone?`
* **Norway in Images** (NiB): dynamically adds by CRS zone.

---

##  EXAMPLES OF USAGE

| Task                   | Before           | After                                                  |
| ---------------------- | ---------------- | ------------------------------------------------------ |
| User draws polygon     | Just a shape     | Now gets a color, area auto-calculated, MMU validated  |
| Enters type info       | Manual typing    | Dropdown menu filtered based on higher-level selection |
| Sets registration date | Empty            | Filled with current timestamp                          |
| Labels                 | Full code        | Simplified: `FM05-M005-19` → `FM05-19`                 |
| Unmapped area          | No label          | Shows `"ikke kartlagt"`                                |
| Adds photo             | Manual file path | Take photo with tablet/phone with inline preview                  |


