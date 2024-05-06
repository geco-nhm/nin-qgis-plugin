from qgis.gui import QgsMapToolEmitPoint, QgsMapCanvas, QgsRubberBand, QgsVertexMarker
from qgis.core import QgsPointXY, QgsGeometry, QgsFeature
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

class PolygonDrawTool(QgsMapToolEmitPoint):

    polygonCreated = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.points = []
        self.rubberBand = QgsRubberBand(self.canvas, True)
        self.rubberBand.setColor(QColor(255, 0, 0, 100))
        self.rubberBand.setWidth(2)


    def canvasPressEvent(self, e):
        # Left click to add a point
        if e.button() == Qt.LeftButton:
            point = self.toMapCoordinates(e.pos())
            self.points.append(QgsPointXY(point))
        # Right click to finish the polygon
        elif e.button() == Qt.RightButton and len(self.points) > 2:
            # Create a polygon geometry from the points
            geom = QgsGeometry.fromPolygonXY([self.points])
            self.polygonCreated.emit(geom)  # Emit the signal with the geometry
            self.points = []  # Reset points
            self.canvas.refreshAllLayers()  # Refresh to clear the rubber band

        # Add a point marker for visual feedback
        marker = QgsVertexMarker(self.canvas)
        marker.setCenter(self.points[-1])
        marker.setColor(QColor(255, 0, 0))
        marker.setOpacity(1)
        marker.setVisible(True)
        marker.setPenWidth(3)


    def canvasMoveEvent(self, e):
        if len(self.points) > 0:
            # Add the current mouse position as a temporary point.
            temp_point = self.toMapCoordinates(e.pos())
            self.rubberBand.reset(True)
            for point in self.points + [QgsPointXY(temp_point)]:
                self.rubberBand.addPoint(point, False)
            self.rubberBand.show()

    
    def deactivate(self):
        super().deactivate()
        self.deactivated.emit()  # Emit the signal
        # Reset the rubber band and remove point markers when the tool is deactivated
        self.rubberBand.reset(True)
        self.canvas.scene().clear()
