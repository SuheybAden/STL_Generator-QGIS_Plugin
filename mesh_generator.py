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
import logging.handlers

import numpy as np
from osgeo import gdal, ogr

from qgis.core import QgsMessageLog
from qgis.core import Qgis


class MeshGeneratorError(Exception):
    def __init__(self, message="An error occured with the meshGenerator"):
        self.message = message
        super().__init__(self.message)


class MissingDLLError(MeshGeneratorError):
    def __init__(self, filepath, message="One of the program dependencies couldn't be loaded"):
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)


class InaccessibleDEMError(MeshGeneratorError):
    def __init__(self, filepath, message="Couldn't load the DEM"):
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)


class InvalidNoDataValueError (MeshGeneratorError):
    def __init__(self, no_data_value, message="The DEM file has an invalid no data value"):
        self.no_data_value = no_data_value
        self.message = message
        super().__init__(self.message)


class DLLFunctionFailedError (MeshGeneratorError):
    def __init__(self, function_name, message="One of the DLL functions failed"):
        self.name = function_name
        self.message = message
        super().__init__(self.message)


class NoValidPixelsError (MeshGeneratorError):
    def __init__(self, filepath, message="The DEM file has no valid pixels to sample data from"):
        self.filepath = filepath
        self.message = message
        super().__init__(self.message)


class MeshGenerator:
    def __init__(self):
        # Setup the logger
        logger_filepath = os.path.join(os.path.dirname(__file__), "logging.log")

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            filename=logger_filepath,
            encoding='utf-8',
            filemode='a',
            level=logging.DEBUG,
            format='%(asctime)s - %(name)-12s - %(levelname)-8s : %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )

        self.logger.info("Started a new logging session!")

        # Check if the log file was created
        if not os.path.exists(logger_filepath):
            QgsMessageLog.logMessage(f"The log file '{logger_filepath}' could not be created!", "STL_Generator", level=Qgis.Warning)

        # Define initial parameter values
        self.verticalExaggeration = .1
        self.bottomLevel = -100
        self.numTriangles = 0

        # Get the DLL path(s)
        if platform.system() == "Windows":
            self.dll_path = os.path.join(os.path.dirname(
                __file__), 'backend', 'MeshGenerator', 'bin', 'MeshGenerator.dll')
        else:
            self.dll_path = os.path.join(os.path.dirname(
                __file__), 'backend', 'MeshGenerator', 'lib', 'libMeshGenerator.so')

        # Load the necessary DLL file(s)
        try:
            self.lib = ctypes.CDLL(self.dll_path)
        except Exception as e:
            raise MissingDLLError(self.dll_path)

    def generate_height_array(self, parameters, source_dem):
        self.logger.info(
            f"******************************************************")
        self.logger.info(f"Starting to process the {source_dem} raster!")

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

        self.name = os.path.basename(self.saveLocation)

        # Opens the raster file being used
        dem = gdal.Open(source_dem, gdal.GA_ReadOnly)
        if not dem:
            self.logger.error("COULDN'T OPEN THE DEM FILE AT %s!", source_dem)
            raise InaccessibleDEMError(source_dem)
        band = dem.GetRasterBand(1)
        self.logger.info(f"Loaded the dem file: {source_dem}")

        # Check that the raster has a valid no data value
        self.noDataValue = band.GetNoDataValue()
        if (self.noDataValue is None):
            self.noDataValue = -9999.0
            self.logger.warning(f"The no data value is null so it is assumed to be -9999.0")
        else:
            self.logger.info(f"The no data value is {self.noDataValue}")

        # Gets the maximum resolution of the printer on each axis
        larger_bed_axis = max(math.ceil(self.bedX), math.ceil(self.bedY))
        smaller_bed_axis = min(math.ceil(self.bedX), math.ceil(self.bedY))

        self.logger.info(f"The bed size for {self.name} is {larger_bed_axis} by {smaller_bed_axis}")

        # *************************** GET SCALE FACTOR FOR X AND Y AXIS *************************** #
        # Loads the x and y lengths of the raster
        larger_img_axis = max(dem.RasterXSize, dem.RasterYSize)
        smaller_img_axis = min(dem.RasterXSize, dem.RasterYSize)

        self.logger.info(f"The image size is {larger_img_axis} by {smaller_img_axis}")

        # Gets the scaling factor needed to preserve the image ratio
        # while not going over the maximum resolutions of the printer
        scalingFactor = min(1, larger_bed_axis / (self.lineWidth * larger_img_axis), smaller_bed_axis / (self.lineWidth * smaller_img_axis))

        self.logger.info(f"The scale factor for {self.name} is {scalingFactor}")

        # *************************** GET VERTICAL EXAGGERATION OF IMAGE *************************** #
        # Load stats from the raster image
        minValue = band.GetMinimum()
        maxValue = band.GetMaximum()
        if not minValue or not maxValue:
            (minValue, maxValue) = band.ComputeRasterMinMax(True)

        self.logger.info(f"The minimum and maximum values of the raster are {minValue} and {maxValue} respectively.")

        # Calculate the vertical exaggeration
        self.verticalExaggeration = self.printHeight / (self.lineWidth * (maxValue - minValue))
        self.bottomLevel = (
            minValue * self.verticalExaggeration) - (self.baseHeight / self.lineWidth)

        self.logger.info(f"The vertical exaggeration is {self.verticalExaggeration}.")
        self.logger.info(f"The new minimum and maximum values of the raster are {minValue * self.verticalExaggeration} and {maxValue * self.verticalExaggeration} respectively.")
        self.logger.info(f"The bottom level of the model is {self.bottomLevel}.")

        # *************************** APPLY THE SCALE FACTOR AND VERTICAL EXAGGERATION *************************** #
        # Load the raster file as an array
        self.array = band.ReadAsArray(buf_xsize=math.ceil(dem.RasterXSize * scalingFactor),
                                      buf_ysize=math.ceil(
                                          dem.RasterYSize * scalingFactor),
                                      buf_type=gdal.GDT_Float64,
                                      resample_alg=gdal.GRIORA_NearestNeighbour)

        self.logger.info(
            f"The target STL size is {self.bedX / self.lineWidth} by {self.bedY / self.lineWidth}")
        self.logger.info(
            f"The acheived STL size is {self.array.shape[0]} by {self.array.shape[1]}")

        # Apply the vertical exaggeration
        self.array *= self.verticalExaggeration
        self.noDataValue *= self.verticalExaggeration
        self.logger.info("Applied the vertical exaggeration.")

        self.logger.info(f"Applied the vertical exaggeration to the noDataValue. The new noDataValue is {self.noDataValue}")

    # Function for manually generating STL
    def manually_generate_stl(self):
        np_float_pointer = np.ctypeslib.ndpointer(
            dtype=np.float32, ndim=2, flags="C_CONTIGUOUS")

        self.lib.generateSTL.argtypes = [np_float_pointer, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                         ctypes.c_char_p]
        self.lib.generateSTL.restype = None

        self.logger.info("Creating the STL file...")

        try:
            self.logger.info("Sending the image data and parameters to the meshgenerator library...")
            self.lib.generateSTL(self.array.astype(np.float32), self.array.shape[0], self.array.shape[1], self.noDataValue,
                                 self.lineWidth, self.bottomLevel, bytes(self.saveLocation, 'utf-8'))

        except Exception as e:
            self.logger.error("Library function call failed!")
            raise DLLFunctionFailedError("generateSTL")

        self.logger.info(
            "Successfully created the STL file at %s.", self.saveLocation)
