'''Adapt project setting for NiN-mapping'''

from pathlib import Path
from typing import Union
from qgis.core import (
    QgsDataProvider, QgsVectorLayer, QgsProject,
    QgsCoordinateReferenceSystem
)

class GpkgSettings:
    '''Handles .gpkg settings'''

    def __init__(self, path: Union[str, Path]) -> None:
        if (path := Path(path)).is_file() and (path.suffix == '.gpkg'):
            self.path = path

    def get_path(self) -> Path:
        '''Return path to geopackage'''
        return self.path


def load_gpkg_layers(settings: GpkgSettings) -> None:
    '''Loads all .gpkg layers into current QGIS project'''

    gpkg_path = settings.get_path()

    layer = QgsVectorLayer(
        str(gpkg_path),
        "test",
        "ogr"
    )

    sub_layers = layer.dataProvider().subLayers()

    for sub_layer in sub_layers:

        name = sub_layer.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]

        uri = f"{gpkg_path}|layername={name}"

        # Create layer
        sub_vlayer = QgsVectorLayer(uri, name, 'ogr')

        # Add layer to map
        QgsProject.instance().addMapLayer(sub_vlayer)

    return layer


def main() -> None:
    '''Adapt QGIS project settings.'''
        
    # Get the project instance
    project = QgsProject.instance()

    # Define name and path of existing geopackage
    gpkg_name = "nin_survey.gpkg"
    gpkg_path = Path(__file__).parent / gpkg_name
    gpkg_settings = GpkgSettings(path=gpkg_path)

    # Declare a SpatialReference 
    # PostGIS SRID 25833 is allocated for ETRS89 UTM-zone 33N
    crs = QgsCoordinateReferenceSystem.fromEpsgId(25833)
    if crs.isValid():
        project.setCrs(crs)
    else:
        print("Invalid CRS!")

    load_gpkg_layers(gpkg_settings)


if __name__ == "__main__":
    main()
