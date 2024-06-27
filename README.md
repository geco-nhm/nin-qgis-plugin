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
3. pick the relevant subsystem, scale and background maps for mapping
4. click "create project" 

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
