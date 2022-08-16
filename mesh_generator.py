from enum import Enum
from locale import normalize
import math
import struct
from qgis.core import (
    QgsMessageLog,
    Qgis
)

import numpy as np
from osgeo import gdal, ogr
import time


class EdgePoint(Enum):
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_RIGHT = 3
    BOTTOM_LEFT = 4


class MeshGenerator:
    def __init__(self):
        self.abort = False

        self.verticalExaggeration = .1
        self.bottomLevel = -100
        self.numTriangles = 0

    def set_parameters(self, parameters):
        # ***************************** USER INPUT *************************** #
        # Height of print excluding the base height (in mm)
        self.printHeight = parameters["printHeight"]
        # Height of extruded base (in mm)
        self.baseHeight = parameters["baseHeight"]
        self.saveLocation = parameters["saveLocation"]

        # Printer settings in mm
        self.bedX = parameters["bedX"]
        self.bedY = parameters["bedY"]
        self.lineWidth = parameters["lineWidth"]

    def generate_height_array(self, source_dem):
        start_time = time.time()

        dem = gdal.Open(source_dem, gdal.GA_ReadOnly)

        if not dem:
            QgsMessageLog.logMessage("Failed to open DEM", level=Qgis.Critical)
            return

        QgsMessageLog.logMessage("Opened DEM", level=Qgis.Info)

        band = dem.GetRasterBand(1)
        self.noDataValue = band.GetNoDataValue()
        QgsMessageLog.logMessage(
            "No data value is: " + str(band.GetNoDataValue()), level=Qgis.Info)
        array = band.ReadAsArray()

        # ****************************** GET FINAL RESOLUTION OF IMAGE ***************************** #
        # Downscales array if the raster image is at a higher resolution than the printer can make
        imgWidth, imgHeight = array.shape

        # Gets the maximum resolution of the printer on each axis
        maxResX = self.bedX/self.lineWidth
        maxResY = self.bedY/self.lineWidth

        xScaling = math.floor(imgWidth/maxResX) if imgWidth > maxResX else 0
        yScaling = math.floor(imgHeight/maxResY) if imgHeight > maxResY else 0

        # Gets the larger of the two scaling factors
        scalingFactor = max(xScaling, yScaling)

        # Downscales array by scaling factor
        array = array[::scalingFactor, :: scalingFactor]

        # *************************** GET VERTICAL EXAGGERATION OF IMAGE *************************** #
        # Get min and max height values
        stats = band.GetStatistics(True, True)
        minValue = stats[0]
        maxValue = stats[1]

        imgWidth, imgHeight = array.shape
        heightDiff = maxValue - minValue

        self.verticalExaggeration = self.printHeight / heightDiff
        self.bottomLevel = (
            minValue * self.verticalExaggeration) - self.baseHeight

        array = array * self.verticalExaggeration
        self.noDataValue *= self.verticalExaggeration

        QgsMessageLog.logMessage(
            "Time to generate height array: " + str(time.time() - start_time), level=Qgis.Info)

        return array

    # Function for manually generating STL without the Open3D library
    def manually_generate_stl(self, array):
        start_time = time.time()
        self.numTriangles = 0
        header = [0] * 80

        with open(self.saveLocation + ".stl", "wb+") as file:
            file.write(struct.pack('<' + 'B' * len(header), * header))
            file.write(struct.pack('<I', 0))

        size_x, size_y = array.shape
        for x in range(size_x - 1):
            for y in range(size_y - 1):
                if(not self.abort):
                    # Get a 2x2 window
                    window = array[x:x+2, y:y+2]

                    orientation = np.packbits(
                        (window != self.noDataValue).flatten())

                    if (window[0][0] != self.noDataValue and
                            window[1][0] != self.noDataValue and
                            window[0][1] != self.noDataValue):

                        # Add top face
                        self.write_face([[x, y, window[0][0]],
                                         [x, y + 1, window[0][1]],
                                         [x + 1, y, window[1][0]]])
                        # Add bottom face
                        self.write_face([[x, y, self.bottomLevel],
                                         [x + 1, y, self.bottomLevel],
                                         [x, y + 1, self.bottomLevel]])
                        # Add side faces
                        self.add_side_face(x, y, x + 1, y, array)
                        self.add_side_face(x, y, x, y + 1, array)
                        self.add_side_face(x + 1, y, x, y + 1, array)

                    if (window[1][1] != self.noDataValue and
                            window[1][0] != self.noDataValue and
                            window[0][1] != self.noDataValue):
                        # Add top face
                        self.write_face([[x + 1, y + 1, window[1][1]],
                                         [x + 1, y, window[1][0]],
                                         [x, y + 1, window[0][1]]])
                        # Add bottom face
                        self.write_face([[x + 1, y + 1, self.bottomLevel],
                                         [x, y + 1, self.bottomLevel],
                                         [x + 1, y, self.bottomLevel]])
                        # Add side faces
                        self.add_side_face(x + 1, y + 1, x + 1, y, array)
                        self.add_side_face(x + 1, y + 1, x, y + 1, array)
                        self.add_side_face(x + 1, y, x, y + 1, array)
                else:
                    self.abort = False
                    return

        print(self.numTriangles)

        # Write the header and number of triangles to the beginning of the file
        with open(self.saveLocation + ".stl", "r+b") as file:
            file.seek(0)
            file.write(struct.pack('<' + 'B'*len(header), *header))
            file.write(struct.pack('<I', self.numTriangles))

        print("Time to generate STL: " + str(time.time() - start_time))

        QgsMessageLog.logMessage(
            "Time to generate STL: " + str(time.time() - start_time), level=Qgis.Info)

    def write_face(self, vertices):
        self.numTriangles += 1

        with open(self.saveLocation + ".stl", "ab") as file:
            # Writes normal vector
            normal = [0.0, 0.0, 0.0]
            file.write(struct.pack('<' + 'f'*len(normal), *normal))

            # Writes the 3 vertices
            for row in vertices:
                file.write(struct.pack('<' + 'f'*len(row), *row))

            # Writes attribute byte count
            file.write(struct.pack('<H', 0))

    def add_side_face(self, x1, y1, x2, y2, array):
        if(self.isEdgePoint(x1, y1, array) and self.isEdgePoint(x2, y2, array)):
            self.write_face([[x1, y1, array[x1][y1]],
                             [x1, y1, self.bottomLevel],
                             [x2, y2, array[x2][y2]]])
            self.write_face([[x1, y1, self.bottomLevel],
                             [x2, y2, self.bottomLevel],
                             [x2, y2, array[x2][y2]]])

    # Returns whether or not a data point will be on the edge of the model
    def isEdgePoint(self, x, y, array):
        window = array[x-1:x+2, y-1:y+2]
        return window.shape != (3, 3) or (self.noDataValue in window)
