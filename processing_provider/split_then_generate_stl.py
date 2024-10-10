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


class SplitThenGenerateSTLs(QgsProcessingAlgorithm):
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
    TOTAL_WIDTH = "TOTAL WIDTH"
    TOTAL_LENGTH = "TOTAL LENGTH"
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
        return SplitThenGenerateSTLs()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "splitthengeneratestl"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Generate STL(s) from a raster split by a vector layer")

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

        # The field to split the vector file by
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD,
                self.tr("Field to Split By"),
                allowMultiple=False,
                parentLayerParameterName=self.INPUT_VECTOR,
            )
        )

        # The distance (in mm) from the lowest point of the model to the highest, not including the base
        self.addParameter(
            QgsProcessingParameterNumber(
                self.MODEL_HEIGHT,
                self.tr("Model Height (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0,
            )
        )

        # The thickness of the base in mm
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BASE_THICKNESS,
                self.tr("Base Thickness (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=10.0,
                minValue=0,
            )
        )

        # The target combined width of all of the STLs
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOTAL_WIDTH,
                self.tr("Total Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0.0,
            )
        )

        # The target combined length of all of the STLs
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOTAL_LENGTH,
                self.tr("Total Length (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0.0,
            )
        )

        # The bed width of the user's 3D printer
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_WIDTH,
                self.tr("Bed Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0,
            )
        )

        # The bed length of the user's 3D printer
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BED_LENGTH,
                self.tr("Bed Length (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=200.0,
                minValue=0,
            )
        )

        # The line width being used by the user's 3D printer
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINE_WIDTH,
                self.tr("Line Width (mm)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.4,
                minValue=0,
            )
        )

        # The folder destination where we'll save the generated STL(s)
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT, self.tr("Output File Destination"), os.path.expanduser("~")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # **************************************************************************************************
        # 1) LOAD ALL THE PARAMETERS
        orig_raster_layer = self.parameterAsRasterLayer(
            parameters, self.INPUT_RASTER, context
        )
        raster_filepath = orig_raster_layer.source()

        orig_vector_layer = self.parameterAsVectorLayer(
            parameters, self.INPUT_VECTOR, context
        )
        vector_filepath = orig_vector_layer.source()

        field = self.parameterAsString(parameters, self.INPUT_FIELD, context)
        print_height = self.parameterAsDouble(parameters, self.MODEL_HEIGHT, context)
        base_thickness = self.parameterAsDouble(
            parameters, self.BASE_THICKNESS, context
        )
        bed_width = self.parameterAsDouble(parameters, self.BED_WIDTH, context)
        bed_length = self.parameterAsDouble(parameters, self.BED_LENGTH, context)
        total_width = self.parameterAsDouble(parameters, self.TOTAL_WIDTH, context)
        total_length = self.parameterAsDouble(parameters, self.TOTAL_LENGTH, context)
        line_width = self.parameterAsDouble(parameters, self.LINE_WIDTH, context)
        dest_folder = self.parameterAsFile(parameters, self.OUTPUT, context)

        # Send some information to the user
        feedback.pushInfo("Loaded all the parameters\n")

        # **************************************************************************************************
        # 2) VERIFY THAT THE INPUT LAYERS ARE PROPERLY FORMATTED

        # Verify that the raster layer has a no data value
        feedback.pushInfo("Getting the no data value of the raster layer...")

        if (not orig_raster_layer.dataProvider().sourceHasNoDataValue(1)):
            feedback.pushWarning("The given raster layer doesn't have a no data value! Setting the no data value to the default of -9999.\n")
            if (not orig_raster_layer.dataProvider().setNoDataValue(1, -9999)):
                feedback.pushWarning("ERROR: Failed to set the no data value!")
                return {self.SUCCESS: False, self.OUTPUT: []}
            orig_raster_layer.reload()
            feedback.pushInfo(f"The new no data value is {orig_raster_layer.dataProvider().sourceNoDataValue(1)}\n")

        else:
            feedback.pushInfo(f"The no data value is {orig_raster_layer.dataProvider().sourceNoDataValue(1)}\n")

        # Change the projection of the vector layer to match the raster layer if it doesn't already
        feedback.pushInfo("Checking if the raster and vector layers have the same projection...")
        feedback.pushInfo(
            f"Raster projection: {orig_raster_layer.crs()},\t Vector projection: {orig_vector_layer.crs()}")

        if orig_vector_layer.crs() != orig_raster_layer.crs():
            orig_vector_layer = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": vector_filepath,
                    "TARGET_CRS": orig_raster_layer.crs(),
                    "OUTPUT": "TEMPORARY_OUTPUT",
                },
            )["OUTPUT"]

            # Send some information to the user
            feedback.pushInfo(
                f"Reprojected the vector layer to {orig_vector_layer.crs()}!\n"
            )

        else:
            # Send some information to the user
            feedback.pushInfo("The layer projections match!\n")

        # **************************************************************************************************
        # 3) SPLIT THE VECTOR LAYER ACCORDING TO THE FIELD CHOSEN BY THE USER

        # Send some information to the user
        feedback.pushInfo(f"Splitting the vector file based on the {field} field...")

        # Split the multi polygon layer into multiple vector layers using the "split vector layer" algorithm
        vector_filepaths: list[str] = processing.run(
            "native:splitvectorlayer",
            {
                "FIELD": field,
                "FILE_TYPE": 0,
                "INPUT": vector_filepath,
                "OUTPUT": "TEMPORARY_OUTPUT",
                "PREFIX_FIELD": True,
            },
        )["OUTPUT_LAYERS"]

        # Send some information to the user
        feedback.pushInfo(f"Finished splitting the vector layer!\n")

        # **************************************************************************************************
        # 4) CLIP THE RASTER LAYER AND FIND THE APPROPRIATE SCALE FACTOR

        # Send some information to the user
        feedback.pushInfo("Started clipping the raster layer by the split vector layer.\n")

        bed_scale_factor = 1.0
        rasters_to_process: list[QgsRasterLayer] = []

        # Clip the raster file using the vector masks and
        # find the scale factor required to fit the largest clipped raster onto the print bed
        for mask_filepath in vector_filepaths:
            # Get the filename of the mask layer so the clipped raster can get the same name
            filename = mask_filepath.split(".")[-2]
            clipped_raster_filepath = os.path.join(dest_folder, filename + "_raster.tif")

            # Load the mask layer
            mask_layer = QgsVectorLayer(path=mask_filepath)

            # Skip any mask layers that don't overlap with the raster file
            overlap = mask_layer.extent().intersect(orig_raster_layer.extent())
            if overlap.isEmpty():
                # Send some information to the user
                feedback.pushInfo(f"{filename} has no overlap with the input raster.\n")
                continue

            # Send some information to the user
            feedback.pushInfo(f"Clipping the input raster layer using {filename}...")
            feedback.pushInfo(f"{overlap.xMinimum()}, {overlap.xMaximum()}, {overlap.yMinimum()}, {overlap.yMaximum()}")

            try:
                # Clip the raster layer with the mask layer
                clipped_raster_filepath = processing.run(
                    "gdal:cliprasterbymasklayer",
                    {
                        "INPUT": raster_filepath,
                        "MASK": mask_filepath,
                        "SOURCE_CRS": orig_raster_layer.crs(),
                        "TARGET_CRS": mask_layer.crs(),
                        "TARGET_EXTENT": f"{overlap.xMinimum()}, {overlap.xMaximum()}, {overlap.yMinimum()}, {overlap.yMaximum()}",
                        "MULTITHREADING": True,
                        # "KEEP_RESOLUTION": True,
                        "OUTPUT": clipped_raster_filepath,
                    },
                )["OUTPUT"]

            except QgsProcessingException as e:
                feedback.pushInfo(f"Error: {e}")
                return {self.SUCCESS: False, self.OUTPUT: []}

            # Send some information to the user
            feedback.pushInfo(f"Clipped raster filname: {clipped_raster_filepath}")

            # Load the clipped raster layer and get its height and width
            clipped_raster_layer = QgsRasterLayer(clipped_raster_filepath)

            larger_bed_axis = max(bed_length, bed_width)
            smaller_bed_axis = min(bed_length, bed_width)
            larger_layer_axis = max(
                clipped_raster_layer.height(), clipped_raster_layer.width()
            )
            smaller_layer_axis = min(
                clipped_raster_layer.height(), clipped_raster_layer.width()
            )

            # Get the min scale factor needed to downscale the raster to fit in the print bed
            bed_scale_factor = min(
                bed_scale_factor,
                (larger_bed_axis / line_width) / larger_layer_axis,
                (smaller_bed_axis / line_width) / smaller_layer_axis,
            )

            # Add the clipped raster to the list of rasters to process
            rasters_to_process.append(clipped_raster_layer)

            # Send some information to the user
            feedback.pushInfo(f"Finished clipping the input raster layer using {filename}.\n")

        feedback.pushInfo("Getting the total extent of the clipped rasters...")

        # Merge all the relevant raster files together
        output = processing.run(
            "gdal:merge", {"INPUT": rasters_to_process, "OUTPUT": "TEMPORARY_OUTPUT"}
        )["OUTPUT"]
        merged_raster = QgsRasterLayer(output)

        # Calculate the min scale factor needed to downscale the raster to fit the user's parameters
        larger_total_axis = max(total_length, total_width)
        smaller_total_axis = min(total_length, total_width)
        larger_raster_axis = max(merged_raster.height(), merged_raster.width())
        smaller_raster_axis = min(merged_raster.height(), merged_raster.width())

        total_raster_scale_factor = min(
            (larger_total_axis / line_width) / larger_raster_axis,
            (smaller_total_axis / line_width) / smaller_raster_axis,
        )

        if total_raster_scale_factor <= bed_scale_factor:
            scale_factor = total_raster_scale_factor

        else:
            scale_factor = bed_scale_factor

            feedback.pushWarning(
                "*** WARNING: The total height/width of the STL files will be smaller than expected so that all STLs can fit on the print bed"
            )
            
        feedback.pushInfo(
            f"The total length and width of the models are {(merged_raster.height() * line_width) * scale_factor} mm and {(merged_raster.width() * line_width) * scale_factor} mm respectively.\n"
        )

        # **************************************************************************************************
        # 5) GENERATE AN STL FOR EACH CLIPPED RASTER LAYER
        feedback.pushInfo("Generating the STL files...\n")

        generated_STLs: list[str] = []
        success = True

        # Generates an STL from each of the clipped raster layers
        for clipped_raster_layer in rasters_to_process:
            width = (clipped_raster_layer.height() * line_width) * scale_factor
            height = (clipped_raster_layer.width() * line_width) * scale_factor

            result = processing.run(
                "stl_generator:stlfromraster",
                {
                    "INPUT": clipped_raster_layer.source(),
                    "MODEL_HEIGHT": print_height,
                    "BASE THICKNESS": base_thickness,
                    "BED WIDTH": width,
                    "BED LENGTH": height,
                    "LINE WIDTH": line_width,
                    "OUTPUT": dest_folder,
                }, context=context, feedback=feedback
            )

            stl_filename = result["OUTPUT"]
            if result["SUCCESS"]:
                generated_STLs.append(stl_filename)

                # Send some information to the user
                feedback.pushInfo(f"Created a new STL: {stl_filename}")
                feedback.pushInfo(
                    f"Its height and width are {height} mm and {width} mm\n"
                )
            else:
                feedback.pushWarning(f"Failed to generate the STL file {stl_filename}\n")
                success = False

        # Return the results of the algorithm
        return {self.SUCCESS: success, self.OUTPUT: generated_STLs}
