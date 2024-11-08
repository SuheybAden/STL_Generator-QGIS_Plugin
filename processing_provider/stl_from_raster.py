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
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFolderDestination,
)
from qgis import processing

from ..mesh_generator import MeshGenerator, MeshGeneratorError

import os


class STLFromRaster(QgsProcessingAlgorithm):
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

    INPUT = "INPUT"
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
        return STLFromRaster()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "stlfromraster"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("STL from Raster")

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
        return self.tr("Generates an STL file from a raster file")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The input raster features source
        self.addParameter(
            QgsProcessingParameterRasterLayer(self.INPUT, self.tr("Input DEM layer"))
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MODEL_HEIGHT,
                self.tr("Model Height (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BASE_THICKNESS,
                self.tr("Base Thickness (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_WIDTH,
                self.tr("Bed Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_LENGTH,
                self.tr("Bed Length (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0,
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINE_WIDTH,
                self.tr("Line Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.4,
                minValue=0,
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
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        dem_path = raster_layer.source()

        print_height = self.parameterAsDouble(parameters, self.MODEL_HEIGHT, context)

        base_thickness = self.parameterAsDouble(
            parameters, self.BASE_THICKNESS, context
        )

        bed_width = self.parameterAsDouble(parameters, self.BED_WIDTH, context)

        bed_length = self.parameterAsDouble(parameters, self.BED_LENGTH, context)

        line_width = self.parameterAsDouble(parameters, self.LINE_WIDTH, context)

        dest_folder = self.parameterAsFile(parameters, self.OUTPUT, context)

        # Construct the name of the STL's output file
        output_filename = os.path.join(dest_folder, raster_layer.name() + ".stl")

        try:
            # Init the MeshGenerator used to create the STL
            mesh_generator = MeshGenerator()

            # Send all the parameters to the mesh generator
            mesh_generator.set_parameters(
                {
                    "printHeight": print_height,
                    "baseHeight": base_thickness,
                    "saveLocation": output_filename,
                    "bedX": bed_width,
                    "bedY": bed_length,
                    "lineWidth": line_width,
                }
            )

            # Preprocess the raster image
            mesh_generator.generate_height_array(source_dem=dem_path)

            # Generate the STL
            mesh_generator.manually_generate_stl()

        except Exception as e:
            feedback.pushWarning(f"{e}\n")
            return {self.OUTPUT: output_filename, self.SUCCESS: False}

        # Return the results of the algorithm
        return {self.OUTPUT: output_filename, self.SUCCESS: True}
