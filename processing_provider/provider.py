from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .stl_from_raster import STLFromRaster
from .split_stl_using_vector import SplitSTLUsingVector


class Provider(QgsProcessingProvider):

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(STLFromRaster())
        self.addAlgorithm(SplitSTLUsingVector())
        
    def id(self, *args, **kwargs):
        """The ID of your plugin, used for identifying the provider.

        This string should be a unique, short, character only string,
        eg "qgis" or "gdal". This string should not be localised.
        """
        return 'stl_generator'

    def name(self, *args, **kwargs):
        """The human friendly name of your plugin in Processing.

        This string should be as short as possible (e.g. "Lastools", not
        "Lastools version 1.0.1 64-bit") and localised.
        """
        return self.tr('STL Generator')

    def icon(self):
        """Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        # return QgsProcessingProvider.icon(self)
        return QIcon(":/plugins/stl_generator/icon.png")
