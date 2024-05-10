import ctypes
from enum import Enum
from locale import normalize
import math
import os
from shutil import ExecError
import platform
import struct
import sys
import logging

import numpy as np
from osgeo import gdal, ogr


class EdgePoint(Enum):
    NONE = 0
    TOP_LEFT = 1
    TOP_RIGHT = 2
    BOTTOM_RIGHT = 3
    BOTTOM_LEFT = 4


class MeshGeneratorErrors(Enum):
    NO_ERROR = 0,
    MISSING_DLL = 1,
    DEM_INACCESSIBLE = 2,
    INVALID_NO_DATA_VALUE = 3,
    DLL_FUNCTION_FAILED = 4


class MeshGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename="logging.log",
                            encoding='utf-8', level=logging.DEBUG)

        self.verticalExaggeration = .1
        self.bottomLevel = -100
        self.numTriangles = 0

        if platform.system() == "Windows":
            self.dll_path = os.path.join(os.path.dirname(
                __file__), 'backend', 'MeshGenerator', 'bin', 'MeshGenerator.dll')
        else:
            self.dll_path = os.path.join(os.path.dirname(
                __file__), 'backend', 'MeshGenerator', 'lib', 'libMeshGenerator.so')

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

        # Load the necessary DLL file(s)
        try:
            self.lib = ctypes.CDLL(self.dll_path)
        except Exception as e:
            return MeshGeneratorErrors.MISSING_DLL

        return MeshGeneratorErrors.NO_ERROR

    def generate_height_array(self, source_dem):

        # Opens the raster file being used
        dem = gdal.Open(source_dem, gdal.GA_ReadOnly)
        if not dem:
            return MeshGeneratorErrors.DEM_INACCESSIBLE
        band = dem.GetRasterBand(1)
        self.logger.info("Loaded the dem file")

        # Check that the raster has a valid no data value
        self.noDataValue = band.GetNoDataValue()
        if (self.noDataValue is None):
            return MeshGeneratorErrors.INVALID_NO_DATA_VALUE

        self.logger.info(f"The no data value is {self.noDataValue}")

        # Gets the maximum resolution of the printer on each axis
        maxResX = math.ceil(self.bedX/self.lineWidth)
        maxResY = math.ceil(self.bedY/self.lineWidth)

        # Loads the x and y lengths of the raster
        imgWidth = dem.RasterXSize
        imgHeight = dem.RasterYSize

        # Gets the scaling factor needed to preserve the image ratio
        # while not going over the maximum resolutions of the printer
        scalingFactor = min(1, maxResX / imgWidth, maxResY / imgHeight)

        # Load the raster file as an array
        self.array = band.ReadAsArray(buf_xsize=math.ceil(imgWidth * scalingFactor),
                                      buf_ysize=math.ceil(
                                          imgHeight * scalingFactor),
                                      buf_type=gdal.GDT_Float32,
                                      resample_alg=gdal.GRIORA_NearestNeighbour)

        # *************************** GET VERTICAL EXAGGERATION OF IMAGE *************************** #
        # Load stats from the raster image
        minValue = band.GetMinimum()
        maxValue = band.GetMaximum()
        if not minValue or not maxValue:
            (minValue, maxValue) = band.ComputeRasterMinMax(True)

        self.verticalExaggeration = self.printHeight / (maxValue - minValue)
        self.bottomLevel = (
            minValue * self.verticalExaggeration) - self.baseHeight

        self.array *= self.verticalExaggeration
        self.noDataValue *= self.verticalExaggeration

        return MeshGeneratorErrors.NO_ERROR

    # Function for manually generating STL
    def manually_generate_stl(self):
        np_float_pointer = np.ctypeslib.ndpointer(
            dtype=np.float32, ndim=2, flags="C_CONTIGUOUS")

        self.lib.generateSTL.argtypes = [np_float_pointer, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                         ctypes.c_char_p]
        self.lib.generateSTL.restype = None

        try:
            self.lib.generateSTL(self.array.astype(np.float32), self.array.shape[0], self.array.shape[1], self.noDataValue,
                                 self.lineWidth, self.bottomLevel, bytes(self.saveLocation, 'utf-8'))

        except Exception as e:
            return MeshGeneratorErrors.DLL_FUNCTION_FAILED

        return MeshGeneratorErrors.NO_ERROR
