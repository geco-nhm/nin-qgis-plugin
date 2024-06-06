# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NinMapper
                                 A QGIS plugin
 Natur i Norge (NiN) mapping tool.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-05-03
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Lasse Keetz, Peter Horvath
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

from pathlib import Path

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsVectorLayer, QgsField, QgsProject, QgsFeature
from PyQt5.QtCore import QVariant

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the dialog
from .nin_qgis_plugin_dialog import NinMapperDialogWidget
import os.path


class NinMapper:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # Now get the map canvas using the 'iface' object and assign it to 'self.canvas'
        self.canvas = iface.mapCanvas()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NinMapper_{}.qm'.format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Natur i Norge mapping')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('NinMapper')
        self.toolbar.setObjectName('NinMapper')

        # print "** INITIALIZING NinMapper"

        self.pluginIsActive = False
        self.dialog = None

    # noinspection PyMethodMayBeStatic

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NinMapper', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action
            )

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = Path(__file__).parent / 'icon.png'
        self.add_action(
            str(icon_path),
            text=self.tr('Open NiN mapper'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

        # Create an action to start the drawing tool
        # self.action = QAction("Draw Polygon", self.iface.mainWindow())
        # Add the action to a toolbar, menu, etc. as desired
        # ...

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dialog is closed"""

        # print "** CLOSING NinMapper"

        # disconnects
        self.dialog.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dialog is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dialog = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD NinMapper"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Natur i Norge mapping'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING NinMapper"

            # dialog may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dialog == None:
                # Create the dialog (after translation) and keep reference
                self.dialog = NinMapperDialogWidget(self.canvas)

            # connect to provide cleanup on closing of dialog
            self.dialog.closingPlugin.connect(self.onClosePlugin)

            # show the dialog
            self.dialog.show()
