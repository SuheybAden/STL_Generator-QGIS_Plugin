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

        # Define the numpy data type for the STL triangles
        self.triangle_dtype = np.dtype([
            ("normal",  np.float32, (3,)),
            ("vertices", np.float32, (3,3,)),
            ("attr",    np.uint16),
        ], align=False)

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

        gdal.DontUseExceptions()

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

        self.logger.info(
            f"The raster's size is {larger_img_axis} by {smaller_img_axis}")

        # Gets the scaling factor needed to preserve the raster's ratio
        # while not going over the maximum resolutions of the printer
        scalingFactor = min(1, larger_bed_axis / (self.lineWidth * larger_img_axis), smaller_bed_axis / (self.lineWidth * smaller_img_axis))

        self.logger.info(f"The scale factor for {self.name} is {scalingFactor}")

        # *************************** GET VERTICAL EXAGGERATION FOR RASTER *************************** #
        # Load stats from the raster image
        minValue = band.GetMinimum()
        maxValue = band.GetMaximum()
        if not minValue or not maxValue:
            (minValue, maxValue) = band.ComputeRasterMinMax(True)

        self.logger.info(f"The minimum and maximum values of the raster are {minValue} and {maxValue} respectively.")

        # Calculate the vertical exaggeration
        self.verticalExaggeration = self.printHeight / (maxValue - minValue)
        self.bottomLevel = (
            minValue * self.verticalExaggeration) - (self.baseHeight)

        self.logger.info(f"The vertical exaggeration is {self.verticalExaggeration}.")
        self.logger.info(
            f"The new minimum and maximum values of the raster are {minValue * self.verticalExaggeration} and {maxValue * self.verticalExaggeration} respectively and the difference between the two is {(maxValue * self.verticalExaggeration) - (minValue * self.verticalExaggeration)}.")
        self.logger.info(f"The bottom level of the model is {self.bottomLevel}.")

        # *************************** APPLY THE SCALE FACTOR AND VERTICAL EXAGGERATION *************************** #
        # Load the raster file as an array
        self.array = band.ReadAsArray(buf_xsize=math.ceil(dem.RasterXSize * scalingFactor),
                                      buf_ysize=math.ceil(
                                          dem.RasterYSize * scalingFactor),
                                      buf_type=gdal.GDT_Float64,
                                      resample_alg=gdal.GRIORA_NearestNeighbour)

        self.logger.info(
            f"The target raster size is {self.bedX / self.lineWidth} by {self.bedY / self.lineWidth}.")
        self.logger.info(
            f"The final raster size is {self.array.shape[0]} by {self.array.shape[1]}.")

        # Apply the vertical exaggeration
        if (self.verticalExaggeration == 0.0):
            self.array = np.where(
                self.array != self.noDataValue, 0, self.array)
            self.logger.info(
                "The vertical exaggeration is 0 so the resulting STL will have a flat surface!")
        else:
            self.array *= self.verticalExaggeration
            self.noDataValue *= self.verticalExaggeration
            self.logger.info(
                f"Applied the vertical exaggeration to the noDataValue. The new noDataValue is {self.noDataValue}")

    # Function for manually generating STL
    def manually_generate_stl(self):
        np_float_pointer = np.ctypeslib.ndpointer(
            dtype=np.float32, ndim=2, flags="C_CONTIGUOUS")

        self.lib.generateSTL.argtypes = [np_float_pointer, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_float, ctypes.c_float, ctypes.c_float,
                                         ctypes.c_char_p]
        self.lib.generateSTL.restype = None

        self.logger.info("Creating the STL file...")

        self.python_write_stl()

        # try:
        #     self.logger.info(
        #         "Sending the raster data and parameters to the meshgenerator library...")
        #     self.lib.generateSTL(self.array.astype(np.float32), self.array.shape[0], self.array.shape[1], self.noDataValue,
        #                          self.lineWidth, self.bottomLevel, bytes(self.saveLocation, 'utf-8'))

        # except Exception as e:
        #     self.logger.error("Library function call failed!")
        #     raise DLLFunctionFailedError("generateSTL")

        self.logger.info(
            "Successfully created the STL file at %s.", self.saveLocation)

    def make_triangles(self, vertices):
        triangles = np.empty(len(vertices), dtype=self.triangle_dtype)
        triangles["vertices"] = vertices
        triangles["attr"] = 0
        return triangles

    def python_write_stl(self):
        # Transpose the array to flip it along its diagonal
        # Needed b/c the generated STL will be flipped along its down diagonal otherwise
        # NOTE: This is a temporary solution. Should look into a way of avoiding having to do this
        self.array = self.array.T

        # A vertex in the array is valid if it's not equal to the noDataValue
        valid_vertices = self.array != self.noDataValue

        # Make 4 vertex arrays which tell whether the vertex for that cell is valid or not
        top_left_vertices = valid_vertices[:-1, :-1]
        bottom_left_vertices = valid_vertices[1:, :-1]
        top_right_vertices = valid_vertices[:-1, 1:]
        bottom_right_vertices = valid_vertices[1:, 1:]

        # Get all of the surface/floor triangles in the array
        top_left_triangles = top_left_vertices & bottom_left_vertices & top_right_vertices
        bottom_right_triangles = bottom_left_vertices & top_right_vertices & bottom_right_vertices
        
        is_orientation_2 = ~(top_left_triangles & bottom_right_triangles)

        bottom_left_triangles = is_orientation_2 & (top_left_vertices & bottom_right_vertices & bottom_left_vertices)
        top_right_triangles = is_orientation_2 & (top_left_vertices & bottom_right_vertices & top_right_vertices)

        # Get all of the triangle edges in the array
        has_left_edge = (top_left_triangles | bottom_left_triangles)
        has_right_edge = (top_right_triangles | bottom_right_triangles)
        has_top_edge = (top_left_triangles | top_right_triangles)
        has_bottom_edge = (bottom_left_triangles | bottom_right_triangles)

        # Determine if one of the edges of a triangle is also a wall
        # A wall only occurs if there is only valid triangle on one side of the edge
        has_left_wall = np.copy(has_left_edge)
        has_left_wall[:, 1:] = has_left_edge[:, 1:] & (~has_right_edge[:, :-1])

        has_right_wall = np.copy(has_right_edge)
        has_right_wall[:, :-1] = has_right_edge[:, :-1] & (~has_left_edge[:, 1:])

        has_top_wall = np.copy(has_top_edge)
        has_top_wall[1:, :] = has_top_edge[1:, :] & (~has_bottom_edge[:-1, :])

        has_bottom_wall = np.copy(has_bottom_edge)
        has_bottom_wall[:-1, :] = has_bottom_edge[:-1, :] & (~has_top_edge[1:, :])

        has_up_diag_wall = top_left_triangles ^ bottom_right_triangles

        has_down_diag_wall = bottom_left_triangles ^ top_right_triangles

        # Write all of the triangles for the STL into a numpy array


        y, x = np.where(top_left_triangles)

        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        top_left_portion_surface = self.make_triangles(np.stack([
                                                np.column_stack([x.astype(np.float32), y.astype(np.float32), self.array[y, x].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                ],
                                                axis=1))
        top_left_portion_floor = self.make_triangles(np.stack([
                                                np.column_stack([x.astype(np.float32), y.astype(np.float32), bottom]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), bottom]), 
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), bottom]),
                                                ],
                                                axis=1))

        # Calculate all of the bottom right triangles for the surface and floor portions of the STL
        y, x = np.where(bottom_right_triangles)

        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        bottom_right_portion_surface = self.make_triangles(np.stack([
                                                    np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                    np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                                    np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                    ],
                                                    axis=1))
        bottom_right_portion_floor = self.make_triangles(np.stack([
                                                    np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), bottom]),
                                                    np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                    np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                    ],
                                                    axis=1))

        # Calculate all of the bottom left triangles for the surface and floor portions of the STL
        y, x = np.where(bottom_left_triangles)

        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        bottom_left_portion_surface = self.make_triangles(np.stack([
                                                    np.column_stack([(x).astype(np.float32), (y).astype(np.float32), self.array[y, x].astype(np.float32)]),
                                                    np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                                    np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                    ],
                                                    axis=1))
        bottom_left_portion_floor = self.make_triangles(np.stack([
                                                    np.column_stack([(x).astype(np.float32), (y).astype(np.float32), bottom]),
                                                    np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                    np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                    ],
                                                    axis=1))

        # Calculate all of the top right triangles for the surface and floor portions of the STL
        y, x = np.where(top_right_triangles)

        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        top_right_portion_surface = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y).astype(np.float32), self.array[y, x].astype(np.float32)]),
                                                ],
                                                axis=1))
        top_right_portion_floor = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), bottom]),
                                                np.column_stack([x.astype(np.float32), (y).astype(np.float32), bottom]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                ],
                                                axis=1))

        # Write all of the wall triangles into a numpy array

        y, x = np.where(has_left_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        left_wall_1 = self.make_triangles(np.stack([
                                                np.column_stack([(x).astype(np.float32), y.astype(np.float32), self.array[y, x].astype(np.float32)]),
                                                np.column_stack([(x).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                np.column_stack([x.astype(np.float32), (y).astype(np.float32), bottom]),
                                                ],
                                                axis=1))
        left_wall_2 = self.make_triangles(np.stack([
                                                np.column_stack([(x).astype(np.float32), y.astype(np.float32), self.array[y, x].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                np.column_stack([(x).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                ],
                                                axis=1))

        y, x = np.where(has_right_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        right_wall_1 = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y).astype(np.float32), bottom]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                ],
                                                axis=1))
        right_wall_2 = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                                ],
                                                axis=1))

        y, x = np.where(has_top_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        top_wall_1 = self.make_triangles(np.stack([
                                            np.column_stack([(x).astype(np.float32), y.astype(np.float32), self.array[y, x].astype(np.float32)]),
                                            np.column_stack([(x).astype(np.float32), (y).astype(np.float32), bottom]),
                                            np.column_stack([(x + 1).astype(np.float32), (y).astype(np.float32), bottom]),
                                        ],
                                        axis=1))
        top_wall_2 = self.make_triangles(np.stack([
                                            np.column_stack([(x).astype(np.float32), y.astype(np.float32), self.array[y, x].astype(np.float32)]),
                                            np.column_stack([(x + 1).astype(np.float32), (y).astype(np.float32), bottom]),
                                            np.column_stack([(x + 1).astype(np.float32), (y).astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                        ],
                                        axis=1))

        y, x = np.where(has_bottom_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        bottom_wall_1 = self.make_triangles(np.stack([
                                                np.column_stack([(x).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                np.column_stack([(x).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                            ],
                                            axis=1))
        bottom_wall_2 = self.make_triangles(np.stack([
                                                np.column_stack([(x).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                                np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                            ],
                                            axis=1))

        y, x = np.where(has_up_diag_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        up_diag_wall_1 = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                ],
                                                axis=1))
        up_diag_wall_2 = self.make_triangles(np.stack([
                                                np.column_stack([(x + 1).astype(np.float32), y.astype(np.float32), self.array[y, x + 1].astype(np.float32)]),
                                                np.column_stack([x.astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                                np.column_stack([(x + 1).astype(np.float32), (y).astype(np.float32), bottom]),
                                                ],
                                                axis=1))

        y, x = np.where(has_down_diag_wall)
        bottom = np.full(len(y), self.bottomLevel, dtype=np.float32)

        down_diag_wall_1 = self.make_triangles(np.stack([
                                            np.column_stack([(x).astype(np.float32), (y).astype(np.float32), self.array[y, x].astype(np.float32)]),
                                            np.column_stack([x.astype(np.float32), (y).astype(np.float32), bottom]),
                                            np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                            ],
                                            axis=1))
        down_diag_wall_2 = self.make_triangles(np.stack([
                                            np.column_stack([(x).astype(np.float32), (y).astype(np.float32), self.array[y, x].astype(np.float32)]),
                                            np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), bottom]),
                                            np.column_stack([(x + 1).astype(np.float32), (y + 1).astype(np.float32), self.array[y + 1, x + 1].astype(np.float32)]),
                                            ],
                                            axis=1))

        # Combine all the triangle arrays

        triangles = np.concatenate([
            top_left_portion_surface, top_left_portion_floor,
            bottom_right_portion_surface, bottom_right_portion_floor,
            bottom_left_portion_surface, bottom_left_portion_floor,
            top_right_portion_surface, top_right_portion_floor,
            left_wall_1, left_wall_2,
            right_wall_1, right_wall_2,
            top_wall_1, top_wall_2,
            bottom_wall_1, bottom_wall_2,
            up_diag_wall_1, up_diag_wall_2,
            down_diag_wall_1, down_diag_wall_2,
        ])

        # Calculate normals
        v0 = triangles["vertices"][:, 0]
        v1 = triangles["vertices"][:, 1]
        v2 = triangles["vertices"][:, 2]

        edge1 = v1 - v0
        edge2 = v2 - v0

        normals = np.cross(edge1, edge2)

        lengths = np.linalg.norm(normals, axis=1)

        valid = lengths > 0
        normals[valid] /= lengths[valid, None]

        triangles["normal"] = normals

        # Scale by line width
        triangles["vertices"][:, :, 0] *= self.lineWidth
        triangles["vertices"][:, :, 1] *= self.lineWidth

        # Write the STL file
        with open(self.saveLocation, "wb") as f:
            # Write the header of the binary STL
            f.write(b"\0" * 80)

            # Write in the number of triangles
            f.write(np.uint32(len(triangles)).tobytes())
            
            # Write in the surface faces
            f.write(triangles.tobytes())

