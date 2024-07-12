# Natur i Norge (NiN) QGIS plugin
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

### this creates all the necessary files for mapping in QGIS and adapts the QGIS environment with the following:
- all layers from the geopackage are loaded containing necessary tables with the NiN type-system
- hierarchical relations are set (major types dependencies on major type groups)
- CRS is set to ETRS89 UTM33 ("EPSG:25833")
- topological editing is turned on
- avoid overlap on the *nin_polygons* layer is enabled
- snapping is set to 5px on vertex and segment
- *nin_polygons* layer is set up with unique random color symbology and labeled by the minor type- depending on the selected Major type groups


## exporting the project to Qfield
5. After project and geopackage were generated, users can transfer the project to [Qfield](https://docs.qfield.org/get-started/tutorials/get-started-qfs/) 

### mapping procedure
6. select layer 'nin_polygons'
7. toggle layer editing 
8. add poygon feature
9. fill out the attributes about the NiN type

### 

## Help

Any advise for common problems or issues.
```
command to run if program contains helper info
```

## Authors

Contributors names and contact info
@ [Lasse Keetz](https://github.com/orgs/geco-nhm/people/lasseke)
@ [Peter Horvath](https://github.com/orgs/geco-nhm/people/peterhor)
@ [Anne B. Nilsen](https://github.com/orgs/geco-nhm/people/9ls1)

this plugin was developed with financial support from [NINA](https://www.nina.no/)

the icon used for this plugin was downloaded from <a href="https://www.flaticon.com/free-icons/enviroment" title="enviroment icons">Flaticon - Enviroment icons created by Eucalyp</a>
