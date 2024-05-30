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

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsRectangle, QgsRasterLayer, QgsProject
#from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QAction, QFileDialog
from PyQt5.QtCore import Qt  # Import Qt from PyQt5.QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QComboBox, QListWidget, QListWidgetItem, QPushButton

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nin_qgis_plugin_dockwidget_base.ui'))


class NinMapperDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, canvas, parent=None):
        """Constructor."""

        super(NinMapperDockWidget, self).__init__(parent)
        self.canvas = canvas

        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Connect the button action to the create_polygon method
        self.createPolygonButton.clicked.connect(self.create_polygon)

        # Connect the button action to the create_polygon method
        self.changeProjectSettingsButton.clicked.connect(self.load_project)

        # Access the combo box for Selecting Type and Selecting Hovedtypegruppe
        self.comboBox = self.findChild(QComboBox, 'SelectType')  # 
        self.selectHovetypegrupperWidget = self.findChild(QListWidget, 'SelectHovedtypegrupper') 
        self.printButton = self.findChild(QPushButton, 'printSelection')  # replace 'printButton' with the objectName of your QPushButton

        # Load the first combo box
        self.load_type_combo_box()

        # Connect the first combo box selection change to a handler
        self.comboBox.currentIndexChanged.connect(self.on_type_combo_box_changed)
        
        # Connect the print button to the print_selection method
        self.printButton.clicked.connect(self.get_selected_htgr_items)

    def load_type_combo_box(self):
        # Path to the typer CSV file
        csv_root = Path(__file__).parent
        type_file_path = csv_root / 'typer_attribute_table.csv'
        self.type_combo_data = {} # To store data for the type combo box
        # Read the CSV file and add items to the combo box
        with open(type_file_path, newline='', encoding='utf-8') as typefile:
            reader = csv.DictReader(typefile)
            for row in reader:
                self.comboBox.addItem(row['navn'], row['kode_id'])
                self.type_combo_data[row['kode_id']] = row['navn']

    def on_type_combo_box_changed(self, index):
        selected_code_id = self.comboBox.itemData(index)
        print(f"Selected code_id: {selected_code_id}")
        self.load_hovedtypegruppe_list_widget(selected_code_id)

    def load_hovedtypegruppe_list_widget(self, selected_code_id):    
            # Path to the hovedtypegrupper CSV file
            csv_root = Path(__file__).parent
            htgr_file_path = csv_root / 'hovedtypgrupper_attribute_table.csv'
            self.selectHovetypegrupperWidget.clear()  # Clear the second combo box
            # Read the CSV file and add items to the combo box
            with open(htgr_file_path, newline='', encoding='utf-8') as htgrfile:
                reader = csv.DictReader(htgrfile)
                for row in reader:
                    if row['typer_fkey'] == str(self.comboBox.currentIndex()): #Filtering the rows based on the selected item in the "Type combo box".
                        item = QListWidgetItem(row['navn']) #Creating a new list item for each matching row.
                        item.setData(Qt.UserRole, row['kode_id']) #Setting the display text and additional data for the list item.
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)  # Making the list item checkable and setting its initial check state.
                        item.setCheckState(Qt.Unchecked)  # Set initial state to unchecked
                        self.selectHovetypegrupperWidget.addItem(item) #Adding the list item to the QListWidget.
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
                    'kode_id': item.data(Qt.UserRole)  # Retrieve associated data
                })
        return selected_items
        # Print selected items to the console
        print("Selected items:")
        for item in selected_items:
            print(f"Display Text: {item['display_text']}, Kode ID: {item['kode_id']}")

    def select_output_file(self):

        file_suffix = ".gpkg"
        
        file_name = QFileDialog.getSaveFileName(
            self.dlg,
            "Select output file ",
            "",
            f'*{file_suffix}'
        )
        
        if not file_name.endswith(file_suffix):
            file_name += file_suffix

        self.dlg.lineEdit.setText(file_name)

    def create_polygon(self):

        # Draw map canvas
        # self.add_base_map()

        # Get the filename from the QLineEdit widget.
        file_name = self.filenameLineEdit.text()

        if file_name:  # Simple check to make sure it's not empty.
            # Logic for creating the polygon goes here.
            # You can now use the `file_name` as needed to store the new feature.
            print("The 'Create new polygon' button was clicked.")
            print(f"File name entered: {file_name}")

            cgpkg.main()

        else:
            # Inform the user to enter a file name or handle as needed.
            print("Please enter a file name.")

    def load_project(self) -> None:
        '''Loads project settings'''

        ps.main()

    def closeEvent(self, event):
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
