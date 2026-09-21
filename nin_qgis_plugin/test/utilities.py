# coding=utf-8
"""Common functionality used by regression tests."""

import os
import sys
import logging
from pathlib import Path


LOGGER = logging.getLogger('QGIS')
QGIS_APP = None  # Static variable used to hold hand to running QGIS app
CANVAS = None
PARENT = None
IFACE = None


def _qgis_prefix_path():
    """
    Returns the QGIS install prefix (e.g. C:/OSGeo4W/apps/qgis-ltr) or None.

    Without a prefix path, QgsApplication.initQgis() loads no data providers
    (no 'wms', no 'ogr' sublayers) and GUI widgets such as QgsFileWidget
    crash the interpreter. QGIS_PREFIX_PATH in the environment wins; otherwise
    the prefix is derived from where the 'qgis' python package lives
    (<prefix>/python/qgis on OSGeo4W and standalone installers).
    """
    prefix = os.environ.get('QGIS_PREFIX_PATH')
    if prefix and Path(prefix).is_dir():
        return prefix

    try:
        import qgis
    except ImportError:
        return None

    candidate = Path(qgis.__file__).resolve().parents[2]
    if (candidate / 'plugins').is_dir() or (candidate / 'bin').is_dir():
        return str(candidate)

    return None


def get_qgis_app():
    """ Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent. If there are any
        errors the tuple members will be returned as None.
    :rtype: (QgsApplication, CANVAS, IFACE, PARENT)

    If QGIS is already running the handle to that app will be returned.
    """

    try:
        from qgis.PyQt import QtCore
        from qgis.PyQt.QtWidgets import QWidget
        from qgis.core import QgsApplication
        from qgis.gui import QgsMapCanvas
        from .qgis_interface import QgisInterface
    except ImportError as exception:
        # Do not hide this: tests would silently run without a QgsApplication,
        # which crashes as soon as a GUI widget is created.
        LOGGER.error('Could not import QGIS for the test app: %s', exception)
        raise

    global QGIS_APP  # pylint: disable=W0603

    if QGIS_APP is None:
        gui_flag = True  # All test will run qgis in gui mode
        prefix_path = _qgis_prefix_path()
        if prefix_path:
            QgsApplication.setPrefixPath(prefix_path, True)
        #noinspection PyPep8Naming
        QGIS_APP = QgsApplication([], gui_flag)  # sys.argv (str) is rejected by the binding
        QGIS_APP.initQgis()
        s = QGIS_APP.showSettings()
        LOGGER.debug(s)

    global PARENT  # pylint: disable=W0603
    if PARENT is None:
        #noinspection PyPep8Naming
        PARENT = QWidget()

    global CANVAS  # pylint: disable=W0603
    if CANVAS is None:
        #noinspection PyPep8Naming
        CANVAS = QgsMapCanvas(PARENT)
        CANVAS.resize(QtCore.QSize(400, 400))

    global IFACE  # pylint: disable=W0603
    if IFACE is None:
        # QgisInterface is a stub implementation of the QGIS plugin interface
        #noinspection PyPep8Naming
        IFACE = QgisInterface(CANVAS)

    return QGIS_APP, CANVAS, IFACE, PARENT
