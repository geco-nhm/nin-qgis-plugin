# -*- coding: utf-8 -*-
# (linja over bruker vi for å kunne bruke æøå uten advarsler.

##################################################################################
# Creates QGIS project (fugleregistrering.qgs) with layers and project relations #
##################################################################################

# import modules
from qgis.core import QgsApplication, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsDataProvider, QgsVectorLayer, QgsMapLayer, QgsRelation, QgsSymbolLayerReference, QgsSnappingConfig, QgsTolerance
from qgis.gui import Qgis
import os              # to get current working directory, change directory a.o.
import sys             # to get input variables
# from glob import glob  # search filename


# Initialize QGIS Application
# Supply path to qgis install location
QgsApplication.setPrefixPath(r"C:\OSGeo4W64\bin", True)
# Create a reference to the QgsApplication setting the second argument to False disables the GUI
qgs = QgsApplication([], False)
# Load providers
qgs.initQgis()

# Get the project instance
project = QgsProject.instance()

# Declare a SpatialReference 
# PostGIS SRID 25833 is allocated for ETRS89 UTM-zone 33N
crs = QgsCoordinateReferenceSystem.fromEpsgId(25833)
if crs.isValid():
    # print("CRS Description: {}".format(crs.description()))  # CRS Description: ETRS89 / UTM zone 35N
    # print("CRS PROJ text: {}".format(crs.toProj()))         # CRS PROJ text: +proj=utm +zone=35 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs
    project.setCrs(crs)
else:
    print("Invalid CRS!")

# Get variables
fl=sys.argv[1]     # flatenummer(e)
u=sys.argv[2]      # user name
f_list=fl.split()  # legger flatenummer(e) i ei liste

print(fl)
print(u)

# https://superuser.com/questions/153165/what-does-represent-while-giving-path
print(os.getcwd())                                    # print current working directory
os.chdir('S:\\...\\fugler')  # change directory
pname = "freg_"+str(u)+".qgs"                         # set project name
print(pname)
if os.path.exists(pname):                             # If project already exists, delete it
    os.remove(pname)

# Accessing layers' tree root
root = QgsProject.instance().layerTreeRoot()

# Add layer groups
groupNameList = ['Registreringer','OF', 'N50']
for groupName in groupNameList:
    group = root.addGroup(groupName)
    group.setExpanded(True)   # Collapse the layer group

# For each 3Q-flate, add rasterfiles (orthophotos), navigate to the folder with the geopackage-files with ortohophotos, open and add the file


# 1 Raster- og vektorfiler hentes inn som hhv. COG- og gpkg-filer
p = 0                  # Index to place the added layer below the previous one
os.chdir('./bilde')    # os.chdir('.\\bilde') go to subfolder bilde
print(os.getcwd())     # print current working directory
rasdir = os.getcwd()   # Get the directory where the raster-files are stored
print('Henter inn OF- og N50 cog-tif-filer fra',rasdir)
# a) N50
# for f in glob(rasdir + '/*n50*.tif', recursive=True):  # Hvs man skal hente inn ALLE bildefiler (og ikke bare de som angår det individuelle prosjektet)
for flate in f_list:
    f = rasdir + '\\'+flate+'_n50_cog.tif'
    # print("Rasterfil er "+f)
    rfile = r""+f+""   # Leser inn filnavn som en inputvariabel
    # print('rfile er',rfile)
    rlayer_name = os.path.split(f)[1]
    # print('rlayer_name er',rlayer_name)
    rlayer = QgsRasterLayer(rfile, rlayer_name, "gdal")
    if rlayer.isValid():
        # Add the raster-layer to the QGIS Map Layer Registry in the "N50"-group
        mygroup = root.findGroup("N50")
        # False indicates to not show the layer on the top in the TOC...
        QgsProject.instance().addMapLayer(rlayer, False)
        # ...and instead insert the layer at given position p
        mygroup.insertLayer(p, rlayer)        # place the layer in pth posistion from top of TOC
        # Uncheck the layer
        QgsProject.instance().layerTreeRoot().findLayer(rlayer.id()).setItemVisibilityChecked(False)
        # Collapse the layer
        QgsProject.instance().layerTreeRoot().findLayer(rlayer.id()).setExpanded(False)
    else:
        print("Raster layer "+rlayer_name+" failed to load!")
    p = p + 1

# b) OF
p = 0                  # Index to place the added layer below the previous one
for flate in f_list:
    f = rasdir + '\\'+flate+'_of_cog.tif'
    # print("Rasterfil er "+f)
    rfile = r""+f+""   # Leser inn filnavn som en inputvariabel
    # print('rfile er',rfile)
    rlayer_name = os.path.split(f)[1]
    # print('rlayer_name er',rlayer_name)
    rlayer = QgsRasterLayer(rfile, rlayer_name, "gdal")
    if rlayer.isValid():
        # Add the raster-layer to the QGIS Map Layer Registry in the "N50"-group
        mygroup = root.findGroup("OF")
        # False indicates to not show the layer on the top in the TOC...
        QgsProject.instance().addMapLayer(rlayer, False)
        # ...and instead insert the layer at given position p
        mygroup.insertLayer(p, rlayer)        # place the layer in pth posistion from top of TOC
        # Uncheck the layer
        QgsProject.instance().layerTreeRoot().findLayer(rlayer.id()).setItemVisibilityChecked(False)
        # Collapse the layer
        QgsProject.instance().layerTreeRoot().findLayer(rlayer.id()).setExpanded(False)
    else:
        print("Raster layer "+rlayer_name+" failed to load!")
    p = p + 1

os.chdir('../gpkg') # ../ is the parent of the current directory.
gpkgdir = os.getcwd()
# print('gpkg-katalog'+os.getcwd())  # print current working directory

# 2 fuglepunkter 
# Add geopackage
# https://github.com/qgis/QGIS/blob/master/tests/src/python/test_provider_postgres.py
fileName =  str(gpkgdir)+'/fuglepunkter.gpkg'
layer = QgsVectorLayer(fileName, "fuglepunkter", "ogr") # Load gpkg-layer
print('liste foer',layer.listStylesInDatabase())        #(1, ['16'], ['fuglepunkter'], ['style fuglepunkter'], '')
styleinf = layer.listStylesInDatabase()
styleid = styleinf[1]                                   # ['16']
print('styleid =',styleid[0])                           # 16
layer.deleteStyleFromDatabase(str(styleid[0]))          # Delete style 16 from gpkg
print('liste etter slett',layer.listStylesInDatabase())
flater = "(1413,1434,1436,1437,1459,1461,1470,1507,1542,1544,1572,1589,1595,1603,1612,1652,1665,1668,1680,1702,1710,1711,1735,1736,1738,1740,1755,1817,1819,1899,1907,1910,1916,1925,1926,1932,1955,1957,1970,1980,1995,2012,2037,2051,2095,2098,2100,2185,2218,2325,2341,2382)"
layer.setSubsetString("flatenr in "+flater+"")          # Filtrer ut bare utvalgte flatenr
print('fuglepunkter: ',os.getcwd())                                      # print current working directory
if os.path.exists('../qml/fuglepunkter.qml'): 
  print('qml-fil eksisterer')
layer.loadNamedStyle('../qml/fuglepunkter.qml')         # Load style
QgsProject.instance().addMapLayer(layer, False)         # Add layer False to be able 
root.insertLayer(1,layer)                               # to specify a custom position
layer.saveStyleToDatabase(layer.name(),'style fuglepunkter',True,'')  # Add style to gpkg
layer.setFlags(QgsMapLayer.LayerFlag(2))                # Not searchable, required nor identifiable
print('liste etter qml-lagring i db',layer.listStylesInDatabase())

os.chdir('../')     # ../ is the parent of the current directory.
# print(os.getcwd())  # print current working directory

# 3 fugleobs med tilhørende tabell 
# Add geopackage
fileName = "fugleregistrering.gpkg"
layer = QgsVectorLayer(fileName, "test", "ogr")
subLayers = layer.dataProvider().subLayers()

#https://docs.qgis.org/3.28/en/docs/pyqgis_developer_cookbook/cheat_sheet.html#layers 
# scroll down to "Load all vector layers from GeoPackage"
p = 0
for subLayer in subLayers:
    name = subLayer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
    uri = "%s|layername=%s" % (fileName, name,)
    sub_vlayer = QgsVectorLayer(uri, name, 'ogr')             # Create layer
    print("Layername is: "+name)
    mygroup = root.findGroup("Registreringer")                # Add the vector-layer to the "Registreringer"-group
    if name not in ('fugleartsliste','vegetasjonstypeliste'):
        QgsProject.instance().addMapLayer(sub_vlayer, False)  # Add layer to map
        mygroup.insertLayer(p, sub_vlayer)                    # place the layer on top in the group
    else:
        QgsProject.instance().addMapLayer(sub_vlayer, True)   # Add layer to map
    p = p + 1

def set_relstrength(inn):
    if inn == 'comp':
        return QgsRelation.Composition
    if inn == 'asso':
        return QgsRelation.Association

def set_relation(parent: str, child: str, relname: str, child_fk: str, parent_pk: str, relid: str, strength: str):
    pl = QgsProject.instance().mapLayersByName(parent)[0] # parent layer
    plid = pl.id()
    cl = QgsProject.instance().mapLayersByName(child)[0]  # child layer
    clid = cl.id()
    rel = QgsRelation()
    rel.setName(relname)                       # name of relation
    rel.setReferencedLayer(plid)               # parent layer
    rel.setReferencingLayer(clid)              # child layer
    rel.addFieldPair(child_fk, parent_pk)      # first element are the field names of the foreign key
    rel.setId(relid)                           # id of relation
    rel.setStrength(set_relstrength(strength)) # strength of relation
    QgsProject.instance().relationManager().addRelation(rel)  # add this realtion to the project
    return pl                                  # returnerer parent-layer


set_relation('fugleobs','fuglereg','fr','fr_id','fugle_id','fuglereg_fugleobs','comp')
nplyr = set_relation('fugleobs','vegreg','vr','vr_id','fugle_id','vegreg_fugleobs','comp')
# Load style to get the relations right in the layer fugleobs's form where fuglereg and vegreg is used
nplyr.loadNamedStyle('./qml/fugleobs.qml')
nplyr.saveStyleToDatabase(nplyr.name(),'style fugleobs',True,'')


# Set the snapping tolerance on fuglepunkter and fugleobs (10 pixels) on vertex
lyr1 = QgsProject.instance().mapLayersByName('fugleobs')[0]     # Set the fugleobs layer
lyr2 = QgsProject.instance().mapLayersByName('fuglepunkter')[0]   # Set the fugleepunkter layer
snapping_config = QgsSnappingConfig()                             # Create a new snapping config object
snapping_config.setEnabled(True)                                  # Enable snapping
snapping_config.setMode(QgsSnappingConfig.AdvancedConfiguration)  # Set to AdvancedConfiguration
# Set individual snapping options for the specified layer
# https://api.qgis.org/api/3.30/classQgsSnappingConfig.html (1=vertex, 2=Segment, 3=VertexAndSegment)
snapping_config.setIndividualLayerSettings(lyr1,QgsSnappingConfig.IndividualLayerSettings(True,Qgis.SnappingType(1),10,QgsTolerance.Pixels,0.0,0.0))
snapping_config.setIndividualLayerSettings(lyr2,QgsSnappingConfig.IndividualLayerSettings(True,Qgis.SnappingType(1),10,QgsTolerance.Pixels,0.0,0.0))
QgsProject.instance().setSnappingConfig(snapping_config)          # Activate the snapping settings

# Save QGIS-prosject
print('Prosjekt lagres: '+pname)
project.write('S:\\...\\fugler\\'+pname)  # Save project
project.clear()                                                    # close project

# Close qgis and remove the provider and layer registries from memory
qgs.exitQgis()
