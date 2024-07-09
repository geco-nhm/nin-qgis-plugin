### Dependencies for development

* Python 3.12+ (recommended: use a [mamba](https://mamba.readthedocs.io/en/latest/)/[Anaconda](https://www.anaconda.com/download) virtual environment, see installation)
* [Poetry](https://python-poetry.org/) (tested with version 1.8.2)

### Installation

* Clone from `https://github.com/geco-nhm/nin-qgis-plugin.git`

In project directory:

* Recommended: Create virtual Python environment with mamba/conda.
```
mamba env create --file=environment.yaml
mamba activate nin-qgis-env
```
* Install Python dependencies with poetry:
```
poetry install
```

### Create relational NiN csv tables

The QGIS plugin relies on relational CSV tables that define the hierarchical relationships between NiN major types, minor types, etc. These tables are created from requests to the [NinKode API](https://nin-kode-api.artsdatabanken.no/swagger/index.html). The following section briefly describes the different tables, created by different python scripts. To update the tables, change into the directory (`cd <project_root>/nin-qgis-handling/python`) and make sure the virtual environment is activated and you have all dependecies installed.

Save paths and API URLs are defined in `nin-qgis-handling/config.toml`.

```
python3 create_attribute_meta_tables.py
```
* Creates csv files that define the field names and datatypes specified in `nin-qgis-handling/attribute_meta.json` for non-geometry features (i.e., attribute tables) in the output geopackage.

---

```
python3 create_type_tables_from_api.py
```
* Creates csv files for NiN major types, minor types, etc. OBS: variable information is generated separately (see below).
---

```
python3 add_limniske_vannmasse_to_kle.py
```
* This is a quick fix to add nature types belonging into the hovedtypegruppe 'NA-F Limniske vannmassesystemer' to the attribute tables of coarser mapping units. They will always be mapped as "grunntyper".

---

```
pip install requests # sending HTTP requests 
pip install tqdm # progress bar
python3 create_variable_tables_from_api.py
```
* Creates csv files to link the lowest NiN mapping units (grunntyper) to their associated NiN variables. OBS: the same information for aggregated mapping units ('kartleggingsenheter') is generated separately (see below). Dependent on library requests and tqdm.

---

```
python3 infer_kartleggingsenheter_vars.py
```
* Creates csv files aggregating the variable information of the lowest NiN mapping units (grunntyper) to the associated coarser mapping units ('kartleggingsenheter'). OBS: under heavy development and will likely change in the future.

---

```
python3 generate_api_version_info.py
```
* Creates the file `nin_api_version_info.txt`. Must be generated manually after updating all tables (for now).
