import ctypes
from enum import Enum
from locale import normalize
import math
import os
from shutil import ExecError
import struct
import sys
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
        self.verticalExaggeration = .1
        self.bottomLevel = -100
        self.numTriangles = 0

        self.dll_path = os.path.join(os.path.dirname(
            __file__), 'backend/MeshGenerator.dll')

        # QgsMessageLog.logMessage(
        #     "Path to dll is " + self.dll_path, level=Qgis.Info)

        self.lib = ctypes.CDLL(self.dll_path)

    def set_parameters(self, parameters):
        # ***************************** USER INPUT *************************** #
        # Height of print excluding the base height (in mm)
        self.printHeight = parameters["printHeight"]
        # Height of extruded base (in mm)
        self.baseHeight = parameters["baseHeight"]
        self.saveLocation = parameters["saveLocation"] + ".stl"

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
        if (self.noDataValue is None):
            QgsMessageLog.logMessage(
                "NoDataValue of the raster file is NoneType", level=Qgis.Critical)
            raise ValueError

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

        # np.save("test_data.npy", array)

        QgsMessageLog.logMessage(
            "Time to generate height array: " + str(time.time() - start_time), level=Qgis.Info)

        return array

    # Function for manually generating STL without the Open3D library
    def manually_generate_stl(self, array):
        start_time = time.time()

        np_float_pointer = np.ctypeslib.ndpointer(
            dtype=np.float32, ndim=2, flags="C_CONTIGUOUS")

        self.lib.generateSTL.argtypes = [np_float_pointer, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_char_p]
        self.lib.generateSTL.restype = None

        self.lib.generateSTL(array.astype(np.float32), array.shape[0], array.shape[1], self.noDataValue,
                             self.lineWidth, self.bottomLevel, bytes(self.saveLocation, 'utf-8'))

        QgsMessageLog.logMessage(
            "Time to generate STL: " + str(time.time() - start_time), level=Qgis.Info)
