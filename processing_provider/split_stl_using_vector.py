"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsGeometry,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterField,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFolderDestination,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)
from qgis import processing

from ..mesh_generator import MeshGenerator, MeshGeneratorErrors

import os


class SplitSTLUsingVector(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_RASTER = "INPUT RASTER"
    INPUT_VECTOR = "INPUT VECTOR"
    INPUT_FIELD = "INPUT FIELD"
    MODEL_HEIGHT = "MODEL HEIGHT"
    BASE_THICKNESS = "BASE THICKNESS"
    BED_WIDTH = "BED WIDTH"
    BED_LENGTH = "BED LENGTH"
    LINE_WIDTH = "LINE WIDTH"
    OUTPUT = "OUTPUT"
    SUCCESS = "SUCCESS"

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return SplitSTLUsingVector()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "splitstlusingvector"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Generate STL(s) from raster split by vector layer")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("Raster Processing")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "rasterprocessing"

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(
            "Generates STL(s) from a raster layer clipped by the provided vector layer"
        )

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The input raster features source
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_RASTER, self.tr("Input DEM layer")
            )
        )

        # The input vector features source
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_VECTOR, self.tr("Input Vector layer")
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD,
                self.tr("Field to Use"),
                allowMultiple=False,
                parentLayerParameterName=self.INPUT_VECTOR,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MODEL_HEIGHT,
                self.tr("Model Height (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BASE_THICKNESS,
                self.tr("Base Thickness (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_WIDTH,
                self.tr("Bed Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_LENGTH,
                self.tr("Bed Length (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINE_WIDTH,
                self.tr("Line Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.4,
                minValue=0
            )
        )
        # The folder destination where we'll save the generated STL
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT, self.tr("Output File Destination"), os.path.expanduser("~")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Load all the parameters
        orig_raster_layer = self.parameterAsRasterLayer(
            parameters, self.INPUT_RASTER, context
        )
        raster_path = orig_raster_layer.source()

        orig_vector_layer = self.parameterAsVectorLayer(
            parameters, self.INPUT_VECTOR, context
        )
        vector_path = orig_vector_layer.source()

        field = self.parameterAsString(parameters, self.INPUT_FIELD, context)
        print_height = self.parameterAsDouble(parameters, self.MODEL_HEIGHT, context)
        base_thickness = self.parameterAsDouble(
            parameters, self.BASE_THICKNESS, context
        )
        bed_width = self.parameterAsDouble(parameters, self.BED_WIDTH, context)
        bed_length = self.parameterAsDouble(parameters, self.BED_LENGTH, context)
        line_width = self.parameterAsDouble(parameters, self.LINE_WIDTH, context)
        dest_folder = self.parameterAsFile(parameters, self.OUTPUT, context)

        # Send some information to the user
        feedback.pushInfo("Loaded all the parameters\n")

        # Make sure the vector layer has the same projection as the raster layer
        if orig_vector_layer.crs() != orig_raster_layer.crs():
            vector_path = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": vector_path,
                    "TARGET_CRS": orig_raster_layer.crs(),
                    "OUTPUT": "TEMPORARY_OUTPUT"
                }
            )["OUTPUT"]

            # Send some information to the user
            feedback.pushInfo("Reprojected the vector layer\n")

        # Split the multi polygon layer into multiple vector layers using the "split vector layer" algorithm
        vector_filenames: list[str] = processing.run(
            "native:splitvectorlayer",
            {
                "FIELD": field,
                "FILE_TYPE": 0,
                "INPUT": vector_path,
                "OUTPUT": "TEMPORARY_OUTPUT",
                "PREFIX_FIELD": True
            }
        )["OUTPUT_LAYERS"]

        # Send some information to the user
        feedback.pushInfo("Split the vector file")

        # Clip the raster file using the vector masks and
        # find the scale factor required to fit the largest STL in the print bed
        scale_factor = 1
        clipped_rasters: list[QgsRasterLayer] = []
        for mask_filename in vector_filenames:
            layer = QgsVectorLayer(path=mask_filename)

            # Skip any mask layers that don't overlap with the raster file
            overlap = layer.extent().intersect(orig_raster_layer.extent())
            if overlap.isEmpty():
                continue

            # Send some information to the user
            feedback.pushInfo(str(mask_filename) +
                              " intersects the raster at " + overlap.toString())

            clipped_raster_filename = os.path.join(
                dest_folder, mask_filename + ".tif"
            )
            processing.run(
                "gdal:cliprasterbymasklayer",
                {
                    "INPUT": raster_path,
                    "MASK": mask_filename,
                    "SOURCE_CRS": None,
                    "TARGET_CRS": None,
                    "TARGET_EXTENT": f'{overlap.xMinimum()}, {overlap.xMaximum()}, {overlap.yMinimum()}, {overlap.yMaximum()}',
                    "MULTITHREADING": False,
                    "OUTPUT": clipped_raster_filename,
                }
            )["OUTPUT"]

            # Load the raster layer and get its height and width
            clipped_raster_layer = QgsRasterLayer(clipped_raster_filename)

            larger_bed_axis = max(bed_length, bed_width)
            smaller_bed_axis = min(bed_length, bed_width)
            larger_layer_axis = max(clipped_raster_layer.height(), clipped_raster_layer.width())
            smaller_layer_axis = min(clipped_raster_layer.height(),
                                     clipped_raster_layer.width())

            # Send some information to the user
            feedback.pushInfo(str(larger_bed_axis) + ", " + str(smaller_bed_axis) + ", "
                              + str(larger_layer_axis) + ", " + str(smaller_layer_axis))

            # Get the min scale factor needed to downscale the raster to fit in the print bed
            scale_factor = min(
                scale_factor,
                min(
                    larger_bed_axis / larger_layer_axis,
                    smaller_bed_axis / smaller_layer_axis
                )
            )

            clipped_rasters.append(clipped_raster_layer)

        # Send some information to the user
        feedback.pushInfo("Found the required scale factor: " + str(scale_factor))

        # Generates an STL from each of the clipped raster files
        generated_STLs: list[str] = []
        for clipped_raster_layer in clipped_rasters:
            result = processing.run(
                "stl_generator:stlfromraster",
                {
                    "INPUT": clipped_raster_layer.source(),
                    "MODEL_HEIGHT": print_height,
                    "BASE THICKNESS": base_thickness,
                    "BED WIDTH": clipped_raster_layer.height() * scale_factor,
                    "BED LENGTH": clipped_raster_layer.width() * scale_factor,
                    "LINE WIDTH": line_width,
                    "OUTPUT": dest_folder,
                }
            )

            if result["SUCCESS"]:
                generated_STLs.append(result["OUTPUT"])

                # Send some information to the user
                feedback.pushInfo("Made an stl file for the raster\n")

        # Send some information to the user
        feedback.pushInfo("DONE")

        # Return the results of the algorithm
        return {self.SUCCESS: True, self.OUTPUT: generated_STLs}
