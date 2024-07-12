# Nature in Norway / Natur i Norge (NiN) QGIS plugin
This plugin is designed to create a QGIS project for mapping nature using the NiN system in the field. 

## Description
The user is presented with several options for customizing the QGIS project. 
- option to sub-set the NiN system by choosing the relevant [Type system](https://naturinorge.artsdatabanken.no/) and [Major Type Group/s](https://naturinorge.artsdatabanken.no/Natursystem) for the current mapping project. 
- mapping scale
- filepath to save the project to
- select background maps

This creates a QGIS project file and a geopackage file with the selected Type system and the underlying selected Major Type Groups. Mapping units are adjusted based on the selected mapping scale. 

## Getting Started

1. open QGIS
2. download and install **'nin-qgis-plugin'** in QGIS > Plugins > Manage and Install Plugins > searching for "Natur i Norge" 
3. pick the relevant NiN Type system, mapping scale, file location and background maps for the QGIS project
4. click "Load Geopackage and adapt project" 

#### this creates all the necessary files for mapping in QGIS and adapts the QGIS environment with the following:
- all layers from the geopackage are loaded containing necessary tables with the NiN type-system
- hierarchical relations are set (major types dependencies on major type groups)
- CRS is set to ETRS89 UTM33 ("EPSG:25833")
- topological editing is turned on
- avoid overlap on the *nin_polygons* layer is enabled
- snapping is set to 5px on vertex and segment
- *nin_polygons* layer is set up with unique random color symbology and labeled by the minor type- depending on the selected Major type groups

## in case further adaptation of the project is neccessary:
- users can add additional raster/vector layers using standart procedures in QGIS
  
## Exporting the project to Qfield
5. After project and geopackage were generated, users can transfer the project to [Qfield](https://docs.qfield.org/get-started/tutorials/get-started-qfs/) and hereby to a mobile device / tablet or a field computer

## The mapping procedure
6. select layer 'nin_polygons'
7. toggle layer editing 
8. add poygon feature
9. fill out the NiN information and attributes in the Attribute Form
10. relevant variables for the chosen NiN type are displayed for mappers convenience
11. mapper can select up to 3 NiN types within one polygon by selecting "Andel av naturtype" to less than 100 and selecting "sammensatt or mosaic" 
12. take a picture of the NiN type (available on devices with integrated camera)
13. approve the polygon registration with "OK" 


## Help

help sites for [QGIS](https://docs.qgis.org/3.34/en/docs/training_manual/index.html)
help sites for [Qfield](https://docs.qfield.org/get-started/tutorials/get-started-qfs/)

## Authors

Contributors names and contact info
@ [Lasse Keetz](https://github.com/orgs/geco-nhm/people/lasseke)
@ [Peter Horvath](https://github.com/orgs/geco-nhm/people/peterhor)
@ [Anne B. Nilsen](https://github.com/orgs/geco-nhm/people/9ls1)

this plugin was developed with financial support from [NINA](https://www.nina.no/)

the icon used for this plugin was downloaded from <a href="https://www.flaticon.com/free-icons/enviroment" title="enviroment icons">Flaticon - Enviroment icons created by Eucalyp</a>
