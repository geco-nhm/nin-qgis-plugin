# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NinMapperDockWidget
                                 A QGIS plugin
 Natur i Norge (NiN) mapping tool.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-05-03
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Lasse Keetz, Peter Horvath, Anne B. Nilsen
        email                : test@dev.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import csv
from pathlib import Path
from . import create_gpkg as cgpkg
from . import project_setup as ps

from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsRectangle, QgsRasterLayer, QgsProject
from qgis.gui import QgsFileWidget
# from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt  # Import Qt from PyQt5.QtCore
from PyQt5.QtWidgets import (
    QMessageBox, QComboBox, QListWidget,
    QListWidgetItem, QPushButton,
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nin_qgis_plugin_dockwidget_base.ui'
))


class NinMapperDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, canvas, parent=None):
        """Constructor."""

        super(NinMapperDockWidget, self).__init__(parent)
        self.canvas = canvas

        self.setupUi(self)

        # Connect the button action to the create_geopackage method
        self.createPolygonButton.clicked.connect(self.create_geopackage)

        # Connect the button action to the create_geopackage method
        self.changeProjectSettingsButton.clicked.connect(self.load_project)

        # Access the combo box for Selecting Type and Selecting Hovedtypegruppe
        self.comboBox = self.findChild(QComboBox, 'SelectType')
        self.selectHovetypegrupperWidget = self.findChild(
            QListWidget, 'SelectHovedtypegrupper'
        )
        self.selectMappingScale = self.findChild(
            QComboBox, 'SelectMappingScale'
        )

        # Load the first combo box
        self.load_type_combo_box()

        # Connect the first combo box selection change to a handler
        self.comboBox.currentIndexChanged.connect(
            self.on_type_combo_box_changed
        )

        # Initialize selected type variable
        self.selected_type_id = None

        # Populate the mapping scale combo box
        self.load_mapping_scale_combo_box()

        # Initialize .gpkg path variable
        self.geopackage_path = None

        # Set UI default values
        self.set_ui_default_values()


    def load_type_combo_box(self):
        # Path to the typer CSV file
        csv_root = Path(__file__).parent / 'csv' / \
            'attribute_tables'
        type_file_path = csv_root / 'typer_attribute_table.csv'
        self.type_combo_data = {}  # To store data for the type combo box

        # Access the combo box
        # the objectName of your QComboBox
        self.comboBox = self.findChild(QComboBox, 'SelectType')

        # Path to the CSV file
        typer_path = csv_root / 'typer_attribute_table.csv'

        # Read the CSV file and add items to the combo box
        with open(typer_path, newline='', encoding='utf-8') as typefile:
            reader = csv.DictReader(typefile)
            for row in reader:
                self.comboBox.addItem(row['navn'], row['kode_id'])
                self.type_combo_data[row['kode_id']] = row['navn']

    def get_selected_type_id(self) -> str:
        return self.selected_type_id

    def on_type_combo_box_changed(self, index):
        self.selected_type_id = self.comboBox.itemData(index)
        self.load_hovedtypegruppe_list_widget()

    def load_hovedtypegruppe_list_widget(self):
        # Path to the hovedtypegrupper CSV file
        csv_root = Path(__file__).parent / 'csv' / 'attribute_tables'
        htgr_file_path = csv_root / 'hovedtypegrupper_attribute_table.csv'
        self.selectHovetypegrupperWidget.clear()  # Clear the second combo box
        # Read the CSV file and add items to the combo box
        with open(htgr_file_path, newline='', encoding='utf-8') as htgrfile:
            reader = csv.DictReader(htgrfile)
            for row in reader:
                # Filtering the rows based on the selected item in the "Type combo box".
                if row['typer_fkey'] == str(self.comboBox.currentIndex()):
                    # Creating a new list item for each matching row.
                    item = QListWidgetItem(row['navn'])
                    # Setting the display text and additional data for the list item.
                    item.setData(Qt.UserRole, row['kode_id'])
                    # Making the list item checkable and setting its initial check state.
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                    # Set initial state to unchecked
                    item.setCheckState(Qt.Unchecked)
                    # Adding the list item to the QListWidget.
                    self.selectHovetypegrupperWidget.addItem(item)
                    print(row)
            print(self.selectHovetypegrupperWidget)

    # DEBUG
    # print the selected items from the listWidget
    def get_selected_htgr_items(self):
        selected_items = []
        for index in range(self.selectHovetypegrupperWidget.count()):
            item = self.selectHovetypegrupperWidget.item(index)
            if item.checkState() == Qt.Checked:
                selected_items.append({
                    'display_text': item.text(),
                    # Retrieve associated data
                    'kode_id': item.data(Qt.UserRole)
                })

        # Print selected items to the console
        # print("Selected items:")
        # for item in selected_items:
        #     print(f"Display Text: {item['display_text']}, Kode ID: {item['kode_id']}")
        return selected_items

    def load_mapping_scale_combo_box(self):
        mappingScales = [
            ("1:500 - grunntyper", "grunntyper"), 
            ("1:5 000", "M005"), 
            ("1:20 000", "M020"), 
            ("1:50 000", "M050")
        ]
        for label, value in mappingScales:
            self.selectMappingScale.addItem(label, value)

    def file_location_selected(self):
        '''
        Path handling executed when users pick a file location in
        the file picker widget.
        '''

        file_suffix = ".gpkg"

        selected_path = Path(self.file_widget.filePath()).resolve()

        # Check if the directory exists
        if (not selected_path.parent.exists()):
            raise ValueError(
                f"""
                '{selected_path} is not a valid path for a new .gpkg file!
                """
            )

        # Append .gpkg suffix if necessary
        if selected_path.suffix != file_suffix:
            selected_path = selected_path.with_suffix(file_suffix)

        self.geopackage_path = selected_path


    def set_ui_default_values(self):
        '''Defines default values for UI'''

        # Set 'typer' combo box default
        self.comboBox.setCurrentIndex(
            self.comboBox.findText("C-PE-NA Natursystem", Qt.MatchFixedString)
        )

        # Setting default values for QListWidget
        # The items you want to be selected by default
        items_to_select = ["NA-T Fastmarkssystemer"]
        for item_to_select in items_to_select:
            items = self.selectHovetypegrupperWidget.findItems(
                item_to_select, Qt.MatchExactly
            )
            for item in items:
                # This sets the item as selected
                item.setCheckState(Qt.Checked)

    def create_geopackage(self) -> None:
        '''
        Creates a new .gpkg file based on user selections via 'create_gpkg.py'.
        '''

        # TODO: remove comments when done testing
        if self.geopackage_path is None:
            pass
            # QMessageBox.information(None, "No path entered!", "Enter a valid .gpkg file path!")
            # return

        cgpkg.main(
            selected_mapping_scale=self.selectMappingScale.currentText(),
            gpkg_path=self.geopackage_path,
        )

    def load_project(self) -> None:
        '''Loads project settings'''

        ps.main(
            self.get_selected_htgr_items(),
            self.get_selected_type_id(),
            gpkg_path=self.geopackage_path,
            selected_mapping_scale=self.selectMappingScale.currentText(),
        )


    def closeEvent(self, event) -> None:
        self.closingPlugin.emit()
        event.accept()

    def add_base_map(self):

        wmts_base_url = "https://opencache.statkart.no/gatekeeper/gk/gk.open_wmts?"
        layer_name = "norgeskart_bakgrunn"
        epsg = 3857

        wmts_layer = QgsRasterLayer(
            f'type=xyz&url={wmts_base_url}layer={layer_name}&style=default&tilematrixset=EPSG:{epsg}&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/png&TileMatrix=EPSG:{epsg}:{{z}}&TileCol={{x}}&TileRow={{y}}',
            'Norway Background Map',
            'wms'
        )

        if not wmts_layer.isValid():
            print("Failed to load the background map layer!")
        else:
            # Add the layer to QGIS
            QgsProject.instance().addMapLayer(wmts_layer, False)
            # Create a new layer tree group
            group = QgsProject.instance().layerTreeRoot().insertGroup(0, 'Base Maps')
            group.addLayer(wmts_layer)

            # Define bounds for Norway
            # norway_extent = QgsRectangle(4.0, 57.9, 31.1, 71.2)  # Approximate bounds for Norway in lon,lat
            # self.canvas.setExtent(norway_extent)
            # self.canvas.refresh()

            # Define the approximate bounding box for the Oslo area
            # You may need to adjust these coordinates based on the desired zoom and location
            # Coordinates around Oslo
            oslo_extent = QgsRectangle(10.645, 59.842, 10.916, 59.975)

            # Set the canvas to the Oslo extent
            self.canvas.setExtent(oslo_extent)

            # Set an appropriate zoom level if needed (optional)
            # Set the canvas zoom scale (the value may need adjustment)
            self.canvas.zoomScale(1)

            self.canvas.refreshAllLayers()
