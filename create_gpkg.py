# -*- coding: utf-8 -*-
# (linja over bruker vi for å kunne bruke æøå uten advarsler.

############################
# Creates GPKG with layers #
############################

# import modules
from qgis.core import QgsApplication, QgsFields, QgsField, QgsWkbTypes, QgsVectorFileWriter, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext, QgsVectorLayer, QgsFeatureRequest, QgsDataProvider
from qgis.PyQt.QtCore import QVariant
import os  # to get current working directory, change directory a.o.


# Initialize QGIS Application
# Supply path to qgis install location
QgsApplication.setPrefixPath(r"C:\OSGeo4W64\bin", True)
# Create a reference to the QgsApplication setting the second argument to False disables the GUI
qgs = QgsApplication([], False)
# Load providers
qgs.initQgis()

# For å vise layer i python console
# lyr = QgsVectorLayer(r"S:\Forvaltning\Geomatikk\abni\fugler\demo.gpkg", "fugleobs", "ogr")    
# QgsProject.instance().addMapLayer(lyr)

# https://gis.stackexchange.com/questions/417916/creating-empty-layers-in-a-geopackage-using-pyqgis?noredirect=1&lq=1
def create_blank_gpkg_layer(gpkg_path: str, layer_name: str, geometry: int,
                            crs: str, fields: QgsFields, append: bool = False
                            ) -> bool:
    # To add a layer to an existing GPKG file, pass 'append' as True
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    if append:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    writer = QgsVectorFileWriter.create(
        gpkg_path,
        fields,
        geometry,
        QgsCoordinateReferenceSystem(crs),
        QgsCoordinateTransformContext(),
        options)
    del writer
    return True

# https://gis.stackexchange.com/questions/205947/duplicating-layer-in-memory-using-pyqgis
def copy_layer(gpkg_path: str, layer_name: str):
    plyr = QgsVectorLayer(gpkg_path, layer_name, "ogr")  # Open existing gpkg-file fuglepunkter with the one layer fuglepunkter 
    plyr.selectAll()        # select all features in fuglepunkter layer
    newlyr = plyr.materialize(QgsFeatureRequest().setFilterFids(plyr.selectedFeatureIds()))  #create a new layer from selected features
    plyr.removeSelection()  # remove selection in the original layer
    return newlyr

# https://gis.stackexchange.com/questions/262549/pyqgis-adding-fields-to-a-feature-layer
def add_attributes_from_file(attrfile: str, dp: QgsDataProvider, lyr: QgsVectorLayer):
    f = open(attrfile,'r')   # open file
    f.readline()             # read the first line of the file (the "metadata"/heading)
    for line in f:           # Read attrubutes from csv-file
    	r = {}
    	r = line.split(';')  # 0 navn, 1 QVariant-type, 2 lengde og 3 presisjon
    	fname = r[0]
    	l = int(r[2])
    	p = int(r[3])
    	try:
    		dp.addAttributes([QgsField(fname,set_variant(r[1]),'',l,p)])  # add field to layer
    		lyr.updateFields()                                         # update vector layer from the datasource
    	except:
    		print("Noe gikk galt - får ikke laget egenskaper fra " +str(f))
    f.close()  # close file
    return lyr

# https://gis.stackexchange.com/questions/435772/pyqgis-qgsvectorfilewriter-writeasvectorformatv3-export-z-dimension-not-workin
def create_gpkg_layer(layer_name: str, layer: QgsVectorLayer, gpkg_path: str, append: bool = False) -> bool:
    # To add a layer to an existing GPKG file, pass 'append' as True
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "GPKG"
    options.layerName = layer_name
    if append:
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    writer = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer,
        gpkg_path,
        QgsCoordinateTransformContext(),
        options)
    del writer
    return True

# https://gis.stackexchange.com/questions/364211/importing-csv-table-to-geopackage-with-pyqgis-using-csv-file-name
def create_table_from_csv(csv_path: str, gpkg_path: str, layer_name: str):
    table = QgsVectorLayer(csv, "csv", 'delimitedtext')
    opt = QgsVectorFileWriter.SaveVectorOptions()
    opt.EditionCapability = QgsVectorFileWriter.CanAddNewLayer
    opt.layerName = lyrname
    opt.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    tw = QgsVectorFileWriter.writeAsVectorFormatV3(table, gpkg_path, QgsCoordinateTransformContext(), opt)
    del tw

# https://gis.stackexchange.com/questions/276743/saving-styles-for-all-layers-using-pyqgis-sld-qml-databases
def set_style(layer: str, lname: str):
    lyr = QgsVectorLayer(layer,lname,"ogr")
    name = lyr.name()
    lyr.loadNamedStyle('S:/.../qml/'+lname+'.qml')
    lyr.saveStyleToDatabase(name,'style '+lname,True,'')

# Funsksjon for å sette riktig QVaraint-type
def set_variant(inn):
	if inn == 'Int':
		return QVariant.Int
	if inn == 'String':
		return QVariant.String
	if inn == 'Date':
		return QVariant.Date
	if inn == 'Double':
		return QVariant.Double
	if inn == 'DateTime':
		return QVariant.DateTime
	if inn == 'Bool':
		return QVariant.Bool

# Create layers and add to the gpkg-file
# Gjort i forkant:
# Tar utgangspunkt i S:\Forvaltning\3Q\biologisk_mangfold\Fugler\Fuglepunkt\Fuglepunkt_UTM33\2020\fuglepunkt_130_flater_ETRSutm33p_flateinfo_2020.shp
# Eksporterer alle forekomster til fuglepunkter.gpkg med layernavn fugleepunkter med egenskapene flatenr, Q_FUGLEID, ost og nord (koord. i 
# ETRS89/UTM33) i tillegg til de nye x33, y33 og diffx og diffy (for å se om noen punkter er flyttet fra oppr. ost og nord)
# NB! Inkluderer z-dimension slik at Geoemtry type blit PointZ, setter crs til EPSG 25833.






print(os.getcwd())                                    # print current working directory
os.chdir('S:\\Forvaltning\\Geomatikk\\abni\\fugler')  # change directory
gpkg_reg = "fugleregistrering.gpkg"                   # the NEW gpkg to be created
if os.path.exists(gpkg_reg):                          # If gpkg-file already exists, delete it
    os.remove(gpkg_reg)

# # All spatial layers and non-spatial tables are saved in the same geopackage-file fugleregistrering.gpkg
# gpkg_pkt = "S:/.../gpkg/fuglepunkter.gpkg"  # existing gpkg with 1162 fuglepunkter, fields flatenr and pnr exists

###### Hvis man skal kopiere et lag i en gpkg-fil #####
# # Åpner fuglepunkter.gpkg, kopierer alle punkter til nytt layer fugleobs, legger til egenskaper og lagrer i NY gpkg-fil: fugleregistrering.gpkg. 
# # data provider is the connection to the underlying file or db that holds the geospatial information to be displayed
# newlyr = copy_layer(gpkg_pkt,"fuglepunkter")  # make a copy of the fuglepunkter layer
# pr = newlyr.dataProvider()  # you access the real datasource behind your layer
# nl = add_attributes_from_file("S:\\Forvaltning\\Geomatikk\\abni\\fugler\\egenskaper\\egenskaper_fugleobs.csv", pr, newlyr)  # add fields from csv-file to this copy
# create_gpkg_layer("fugleobs", nl, gpkg_reg)  # Save as new layer fugleobs, geometry type and crs inherited from original point-layer
#####

# Layer 1 fugleobs (to be added to the new gpkg-file juest created above)
f = open("./egenskaper/egenskaper_fugleobs.csv",'r') # open file
f.readline()
layer_name = "fugleobs" 
print('creates layer', layer_name)   # print layer name
geom = QgsWkbTypes.PointZ            # geometrytype
crs = 'epsg:25833'                   # coordinate system
fields = QgsFields()
for line in f:                       # Read attrubutes from csv-file
	r = {}
	r = line.split(';')  # 0 navn, 1 QVariant-type, 2 lengde og 3 presisjon
	fname = r[0]
	l = int(r[2])
	p = int(r[3])
	try:
		fields.append(QgsField(fname,set_variant(r[1]),'',l,p))  # add field to layer 
	except:
		print("Noe gikk galt - får ikke laget egenskaper fra " +str(f))
f.close()  # close file

create_blank_gpkg_layer(gpkg_reg, layer_name, geom, crs, fields)  # Ikke inkl. True når FØRSTE lag lages

# Add a cvs-file as a table in the gpkg
# Layer 3 fugleartsliste
csv = "file:///S:\\...\\fugler\\egenskaper\\fugleartsliste.csv?delimiter=;"
lyrname = 'fugleartsliste'
create_table_from_csv(csv, gpkg_reg, lyrname)

# Layer 4 vegetasjonstypeliste
csv = "file:///S:\\...\\fugler\\egenskaper\\vegetasjonstypeliste.csv?delimiter=;"
lyrname = 'vegetasjonstypeliste'
create_table_from_csv(csv, gpkg_reg, lyrname)

# Create tables and add to gpkg
# Layer 5 vegtypedekning (lagre vegtype med tilhørednde prosentdekning)
layer_name = "vegreg"
geom = QgsWkbTypes.NoGeometry
crs = ''
fields = QgsFields()
fields.append(QgsField("delomr", QVariant.String, '', 1, 0))            # a-f
fields.append(QgsField("vegtype", QVariant.String, '', 50, 0))          # delområdets vegetasjonstype
fields.append(QgsField("pdekning", QVariant.Int, '', 3, 0))			    # aktuell vegetasjonsdekkeandel
fields.append(QgsField("vr_id", QVariant.String, '', 38, 0))            # Relasjon mellom NYE punkter i vv_vegtype med vegtypedekning
create_blank_gpkg_layer(gpkg_reg, layer_name, geom, crs, fields, True)  # create the layer, is added to the same gpkg

# Layer 6 fuglereg (lagrer art, ant, avst, delomr m.m.)
layer_name = "fuglereg"
geom = QgsWkbTypes.NoGeometry
crs = ''
fields = QgsFields()
fields.append(QgsField("art", QVariant.String, '', 50, 0))              # fugleart (norsk - latin)
fields.append(QgsField("art_annen", QVariant.String, '', 50, 0))        # hvis fugleart mangler i opprinnelige liste
fields.append(QgsField("ant", QVariant.Int, '', 3, 0))                  # antall hekkende par, hvis 999 skal flokk angis
fields.append(QgsField("flokk", QVariant.Int, '', 3, 0))                # antall individer hvis flokk
fields.append(QgsField("avst", QVariant.Int, '', 1, 0))                 # 1,2 eller 3 (innafor/utafor 50 m fra punkt eller mellom punkter)
fields.append(QgsField("delomr", QVariant.String, '', 1, 0))            # innhold bestemmes av delområder angitt i vegreg
fields.append(QgsField("fr_id", QVariant.String, '', 38, 0))            # relasjon mellom NYE punkter i fugleartsdekning med fugleobs
create_blank_gpkg_layer(gpkg_reg, layer_name, geom, crs, fields, True)  # create the layer, is added to the same gpkg 
# Load qml and save style in geopackage.
# Layer fugleobs gets style set when QGIS-project is created (see create_project.py) due to the project relations dependency
set_style('fugleregistrering.gpkg|layername=fuglereg',"fuglereg")
set_style('fugleregistrering.gpkg|layername=vegreg',"vegreg")
