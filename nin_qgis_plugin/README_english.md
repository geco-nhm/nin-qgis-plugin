# 1 Introduction

![QGIS 3.34+ required](https://img.shields.io/badge/QGIS-3.34%252B-green?logo=qgis&logoColor=white)

<a href="README.md" style="padding: 6px 12px; background-color: #007acc; color: white; border-radius: 4px; text-decoration: none;">🌐 Bytt til norsk</a>

## 1.1 Background

The Norwegian Biodiversity Information Centre (Artsdatabanken) launched version 3.0 of Nature in Norway (NiN) in 2024. To support this, a plugin has been developed for QGIS to facilitate field-based mapping according to NiN 3.0.

The purpose of the plugin is to make NiN mapping more accessible and efficient -- for both professionals and users without specialized technical expertise.

## 1.2 About this guide

This guide provides a practical introduction to using the plugin. It assumes the user has basic knowledge of NiN 3.0 mapping. The guide walks through the full workflow -- from setup in QGIS, to field-based mapping, and post-processing.

The plugin supports all NiN 3.0 type systems and adapted mapping scales, but currently does not include the variable system.

📘 [Read the full guide here (in Norwegian)](https://geco-nhm.github.io/nin-qgis-plugin/)

# 2 Installation

The plugin can be installed via the QGIS Plugin Manager:

1.  Open QGIS
2.  Go to `Plugins` → `Manage and Install Plugins...`
3.  Search for "Natur i Norge kartlegging"
4.  Click `Installer`

## 2.1 Alternative: Install the latest version from GitHub

Since development is ongoing, newer versions may be available on GitHub before being added to the QGIS plugin repository:

-   Go to <https://github.com/Artsdatabanken/nin-innsyn>
-   Download the `.zip` file
-   Extract it and add it manually via `Plugins` → `Install from ZIP`

# 3 Usage

## 3.1 Features

The plugin lets you configure a custom mapping project with options to:

-   Select type system and relevant major-type groups
-   Choose preferred mapping scale
-   Define storage location for the project
-   Set coordinate reference system (CRS) for project and `.gpkg` files
-   Choose background maps

## 3.2 Getting started

1.  Open QGIS
2.  Install and activate the plugin
3.  Launch the plugin and set up a project by choosing:
    -   Type system
    -   Mapping scale
    -   Coordinate reference system
    -   Storage folder
    -   Desired background maps
4.  Click `Lag geopackage-fil og forbered prosjekt`

**This will automatically create:**

-   A QGIS project file
-   A `.gpkg` file with the required layers for mapping

**Result:**

-   All layers from the `.gpkg` file are loaded
-   Hierarchical dependencies are established (between major types and major-type groups)
-   `Topological editing` is enabled
-   `Avoid overlap` is enabled for `nin_polygons`
-   Snapping is set to 5 px (vertices and segments)
-   The `nin_polygons` layer is configured with:
    -   Random color symbology
    -   Labels based on minor type within the selected major-type group

## 3.3 Further customization

If your project requires a different setup than the default:

-   Add custom raster or vector data (e.g. aerial imagery, protected areas, elevation data) using standard QGIS tools
-   Create new layers, symbology, or adjust layout as needed

## 3.4 Export to QField

Once the project and `.gpkg` files are ready, they can be transferred to QField for use in field-based mapping:

1.  Copy the entire project folder to a mobile device/tablet/field PC
2.  Open the project in QField
3.  Begin field-based mapping

When fieldwork is complete, data can be synced back to QGIS for further processing.

## 3.5 Mapping procedure

1.  Select the `nin_polygons` layer
2.  Enable editing
3.  Add a new polygon
4.  Fill in NiN attributes in the form
5.  Choose relevant variables for the selected type
6.  If the polygon includes multiple types:
    -   Set `Andel av naturtype` to less than 100
    -   Choose `sammensatt` or `mosaikk`
7.  Optionally take a photo (if device has a camera)
8.  Click `OK` to save the polygon

Mapping guidelines are available at [Artsdatabanken's website](https://www.artsdatabanken.no).

# 4 For developers

The source code is available on GitHub: <https://github.com/geco-nhm/nin-qgis-plugin>

## 4.1 Functionality

-   Generation of QGIS project and `.gpkg` files
-   Automatic setup of layers and symbology
-   Support for export to QField

## 4.2 Contributing

Developers and domain experts are welcome to contribute through:

-   Bug reports
-   Suggestions for improvements
-   Pull requests on GitHub

# 5 Help

[QGIS Help Pages](https://docs.qgis.org/3.34/en/docs/training_manual/index.html)\
[QField Help Pages](https://docs.qfield.org/get-started/tutorials/get-started-qfs/)\
[NiN Help Pages](https://naturinorge.artsdatabanken.no/)

# 6 Authors

Names and contact info:

[Lasse Keetz](https://github.com/orgs/geco-nhm/people/lasseke)\
[Peter Horvath](https://github.com/orgs/geco-nhm/people/peterhor)\
[Anne B. Nilsen](https://github.com/orgs/geco-nhm/people/9ls1)

The plugin was developed with financial support from [NINA](https://www.nina.no/)

The plugin icon was downloaded from Flaticon - Environment icons created by Eucalyp