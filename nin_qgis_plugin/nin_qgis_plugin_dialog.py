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
from qgis.gui import QgsFileWidget
# from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt  # Import Qt from PyQt5.QtCore
from PyQt5.QtWidgets import (
    QMessageBox, QComboBox, QListWidget,
    QListWidgetItem, QGroupBox, QCheckBox,
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'nin_qgis_plugin_dialog_base.ui'
))


class NinMapperDialogWidget(QtWidgets.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, canvas, parent=None):
        """Constructor."""

        super(NinMapperDialogWidget, self).__init__(parent)
        self.canvas = canvas

        self.setupUi(self)

        # Connect the button action to the create_geopackage method
        self.changeProjectSettingsButton.clicked.connect(self.load_project)

        # Access the combo box for Selecting Type and Selecting Hovedtypegruppe
        self.comboBox = self.findChild(QComboBox, 'SelectType')
        self.selectHovetypegrupperWidget = self.findChild(
            QListWidget,
            'SelectHovedtypegrupper'
        )
        self.selectMappingScale = self.findChild(
            QComboBox,
            'SelectMappingScale'
        )

        # WMS checkbox handling
        self.wms_box_group = self.findChild(QGroupBox, 'groupBoxWMS')
        self.wms_check_box_names = [
            'checkBoxNorgeTopo',
            'checkBoxNorgeTopoGraa',
            'checkBoxNiB',
        ]

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
        self.file_widget = self.findChild(
            QgsFileWidget,
            'gpkgFilePicker'
        )
        # Set to None to force user to make a selection
        self.file_widget.setFilePath(None)

        # Set UI default values
        self.set_ui_default_values()

    def load_type_combo_box(self):

        # Path to the typer CSV file
        csv_root = Path(__file__).parent / 'csv' / \
            'attribute_tables'

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
        '''
        Returns the "typer" fid's selected in the UI.
        '''
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

        return selected_items

    def load_mapping_scale_combo_box(self):
        self.selectMappingScale.addItems(
            ["grunntyper", "M005", "M020", "M050"]
        )

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

    def load_project(self) -> None:
        '''
        Loads project settings
        '''

        # Retrieve user selection from CRS radiobutton
        # Iterate through all the children of type QRadioButton and check which one is checked
        for radiobutton in self.findChildren(QtWidgets.QRadioButton):
            if radiobutton.isChecked():
                print(f"Checked RadioButton: {radiobutton.text()}")
                # QMessageBox.information(
                               # None,
                               # "Koordinatsystem valgt",
                               # radiobutton.text()
                           # )
            return
 
        # Retrieve user selection in WMS checkboxes
        wms_settings = {
            box: self.wms_box_group.findChild(QCheckBox, box).isChecked()
            for box in self.wms_check_box_names
        }

        if not self.get_selected_htgr_items():
            QMessageBox.information(
                None,
                "Ingen hovedtypegruppe(r) valgt",
                "Velg hovedtypegruppe(r) som skal kartlegges"
            )
            return

        # passing the selected "Type" from the UI
        # per 11.07.24: type kan ikke settes til NULL (tom)
        if not self.get_selected_type_id():
            QMessageBox.information(
                None,
                "Ingen type valgt",
                "Velg type som skal kartlegges"
            )
            return

        # TODO: remove comments when done testing
        if self.file_widget.filePath():
            self.file_location_selected()
        else:
            QMessageBox.information(
                None,
                "Ingen filsti angitt",
                "Angi lovlig .gpkg-filsti"
            )
            return

        # Run create_gpkg.py
        cgpkg.main(
            selected_mapping_scale=self.selectMappingScale.currentText(),
            gpkg_path=self.geopackage_path,
        )

        # Run project_setup.py
        ps.main(
            selected_items=self.get_selected_htgr_items(),
            selected_type_id=self.get_selected_type_id(),
            gpkg_path=self.geopackage_path,
            canvas=self.canvas,
            wms_settings=wms_settings,
            selected_mapping_scale=self.selectMappingScale.currentText(),
        )

    def closeEvent(self, event) -> None:
        self.closingPlugin.emit()
        event.accept()
