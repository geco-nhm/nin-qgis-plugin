# coding=utf-8
"""The create-project button is enabled only once CRS, hovedtypegruppe and gpkg path are set (#47)."""

import unittest

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QRadioButton

from .utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()

from nin_qgis_plugin.nin_qgis_plugin_dialog import NinMapperDialogWidget  # noqa: E402


class TestMandatoryInputs(unittest.TestCase):

    def setUp(self):
        self.dialog = NinMapperDialogWidget(CANVAS)
        self.button = self.dialog.changeProjectSettingsButton
        self.radio_25833 = self.dialog.findChild(QRadioButton, 'radioBtn25833')

    def tearDown(self):
        self.dialog.close()
        self.dialog = None

    def _set_all_hovedtypegrupper(self, state):
        widget = self.dialog.selectHovetypegrupperWidget
        for index in range(widget.count()):
            widget.item(index).setCheckState(state)

    def test_button_disabled_until_all_mandatory_inputs_are_set(self):
        # Defaults: a hovedtypegruppe is pre-checked, but no CRS and no file
        self.assertTrue(self.dialog.get_selected_htgr_items())
        self.assertEqual(self.dialog.get_selected_crs(), '')
        self.assertFalse(self.button.isEnabled())
        self.assertIn('koordinatsystem', self.button.toolTip())
        self.assertIn('lagringssted', self.button.toolTip())

        self.radio_25833.setChecked(True)
        self.assertEqual(self.dialog.get_selected_crs(), 'EPSG:25833')
        self.assertFalse(self.button.isEnabled())
        self.assertNotIn('koordinatsystem', self.button.toolTip())

        self.dialog.file_widget.setFilePath('C:/tmp/kartlegging.gpkg')
        self.assertTrue(self.button.isEnabled())
        self.assertEqual(self.button.toolTip(), '')

    def test_button_disabled_again_when_no_hovedtypegruppe_is_checked(self):
        self.radio_25833.setChecked(True)
        self.dialog.file_widget.setFilePath('C:/tmp/kartlegging.gpkg')
        self.assertTrue(self.button.isEnabled())

        self._set_all_hovedtypegrupper(Qt.CheckState.Unchecked)
        self.assertFalse(self.button.isEnabled())
        self.assertIn('hovedtypegruppe', self.button.toolTip())

        self._set_all_hovedtypegrupper(Qt.CheckState.Checked)
        self.assertTrue(self.button.isEnabled())

    def test_add_to_open_project_requires_a_saved_project(self):
        from qgis.core import QgsProject

        new_radio = self.dialog.new_project_radio
        open_radio = self.dialog.open_project_radio
        project = QgsProject.instance()
        original_file_name = project.fileName()
        try:
            project.setFileName('')
            self.dialog.update_add_to_open_project_state()
            self.assertFalse(open_radio.isEnabled())
            self.assertTrue(new_radio.isChecked())
            self.assertFalse(self.dialog.add_to_open_project())

            project.setFileName('C:/tmp/eksisterende.qgz')
            self.dialog.update_add_to_open_project_state()
            self.assertTrue(open_radio.isEnabled())
            self.assertIn('eksisterende.qgz', open_radio.toolTip())
            open_radio.setChecked(True)
            self.assertFalse(new_radio.isChecked())
            self.assertTrue(self.dialog.add_to_open_project())

            # The project radios must not interfere with the CRS radios (#47)
            self.radio_25833.setChecked(True)
            self.assertTrue(open_radio.isChecked())
            self.assertEqual(self.dialog.get_selected_crs(), 'EPSG:25833')

            project.setFileName('')
            self.dialog.update_add_to_open_project_state()
            self.assertFalse(open_radio.isEnabled())
            self.assertTrue(new_radio.isChecked())
            self.assertFalse(self.dialog.add_to_open_project())
        finally:
            project.setFileName(original_file_name)

    def test_changing_type_reloads_list_and_disables_button(self):
        self.radio_25833.setChecked(True)
        self.dialog.file_widget.setFilePath('C:/tmp/kartlegging.gpkg')
        self.assertTrue(self.button.isEnabled())

        combo = self.dialog.comboBox
        combo.setCurrentIndex((combo.currentIndex() + 1) % combo.count())
        # The reloaded hovedtypegruppe list has nothing checked
        self.assertFalse(self.dialog.get_selected_htgr_items())
        self.assertFalse(self.button.isEnabled())


if __name__ == '__main__':
    unittest.main()
