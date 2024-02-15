import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtCore

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'preview_window.ui'))


class PreviewWindow(QtWidgets.QDialog):
	def __init__(self):
		super().__init__()

		self.setupUI()
		self.connect_signals()

	def setupUI(self):
		dir = os.path.dirname(__file__)
		filename = os.path.splitext(os.path.basename(__file__))[0]
		uic.loadUi(dir + "/" + filename + ".ui", self)

	def connect_signals(self):
		pass
