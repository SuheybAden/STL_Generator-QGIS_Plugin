from enum import Enum
import math
# from qgis.core import (
#     QgsMessageLog,
#     Qgis
# )

import numpy as np
from osgeo import gdal, ogr


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
        self.bottomLevel = 20

    def set_parameters(self, parameters):
        # ***************************** USER INPUT *************************** #
        # Height of print excluding the base height (in mm)
        self.printHeight = parameters["printHeight"]
        # Height of extruded base (in mm)
        self.baseHeight = parameters["baseHeight"]
        self.noDataValue = parameters["noDataValue"]
        self.saveLocation = parameters["saveLocation"]

        # Printer settings in mm
        self.bedX = parameters["bedX"]
        self.bedY = parameters["bedY"]
        self.lineWidth = parameters["lineWidth"]

    def dem_to_mesh(self, source_dem):
        input_array = self.generate_height_array(source_dem=source_dem)
        self.manually_generate_stl(input_array)

    def generate_height_array(self, source_dem):
        dem = gdal.Open(source_dem, gdal.GA_ReadOnly)
        if not dem:
            # print("Failed to open DEM")
            # QgsMessageLog.logMessage("Failed to open DEM", level=Qgis.Critical)
            return

        band = dem.GetRasterBand(1)
        # self.noDataValue = band.GetNoDataValue()
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

        # # Debugging logs for checking scaling values
        # QgsMessageLog.logMessage(
        #     "X stats: " + str(imgWidth) + ", " + str(maxResX) + ", " + str(xScaling), level=Qgis.Info)
        # QgsMessageLog.logMessage(
        #     "Y stats: " + str(imgHeight) + ", " + str(maxResY) + ", " + str(yScaling), level=Qgis.Info)

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

        # np.save("C:/Code/array_data.npy", array)

        # # Debugging logs for checking scaling values
        # QgsMessageLog.logMessage(
        #     "X stats: " + str(imgWidth) + ", " + str(maxResX) + ", " + str(xScaling), level=Qgis.Info)
        # QgsMessageLog.logMessage(
        #     "Y stats: " + str(imgHeight) + ", " + str(maxResY) + ", " + str(yScaling), level=Qgis.Info)
        return array

    # Function for manually generating STL without the Open3D library
    def manually_generate_stl(self, array):
        with open(self.saveLocation + ".stl", "w+") as file:
            file.write("solid QGIS_STL\n")

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

        with open(self.saveLocation + ".stl", "a") as file:
            file.write("endsolid\n")

    def write_face(self, vertices):
        with open(self.saveLocation + ".stl", "a") as file:
            file.writelines(
                ["\tfacet normal 0.0 0.0 0.0\n", "\t\touter loop\n"])

            file.writelines(["\t\t\tvertex {0} {1} {2}\n".format(
                vertices[0][0] * self.lineWidth, vertices[0][1] * self.lineWidth, vertices[0][2]),
                "\t\t\tvertex {0} {1} {2}\n".format(
                vertices[1][0] * self.lineWidth, vertices[1][1] * self.lineWidth, vertices[1][2]),
                "\t\t\tvertex {0} {1} {2}\n".format(
                vertices[2][0] * self.lineWidth, vertices[2][1] * self.lineWidth, vertices[2][2])])

            file.writelines(["\t\tendloop\n", "\tendfacet\n"])

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
        # print("(" + str(x) + ", " + str(y) + ")")
        # print(window.shape)
        # print("\n")
        return (window.shape != (3, 3)) or (-9999 in window)


def main():
    mesh_generator = MeshGenerator()
    mesh_generator.set_parameters(printHeight=20,
                                  baseHeight=20,
                                  noDataValue=-9999,
                                  saveLocation="C:/Code/test",
                                  bedX=200,
                                  bedY=200,
                                  lineWidth=0.4)
    data = np.load("C:/Code/array_data.npy")
    print(data.shape)
    # test_array = np.array([[1, 2, 7, 21312, 590],
    #                        [3, -9999, 9, 21093, -45],
    #                        [421, 214, 156, 2913, 493],
    #                        [2891, 3902, 219, 4891, 214],
    #                        [324, 8421, 58, 32, 89412]])
    # x = 2
    # y = 2
    # print(test_array[x][y])
    # print(mesh_generator.isEdgePoint(x, y, test_array))
    # mesh_generator.manually_generate_stl(data)


if __name__ == "__main__":
    main()
