# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Dem2StlDialog
                                 A QGIS plugin
 This plugin lets you generate an STL from a DEM and allows the exclusion of nodata regions.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-03-30
        git sha              : $Format:%H$
        copyright            : (C) 2022 by Suheyb Aden
        email                : suheyb1@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from threading import Thread
from .mesh_generator import MeshGenerator

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtCore

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'dem2stl_dialog_base.ui'))


class Dem2StlDialog(QtWidgets.QDialog, FORM_CLASS):
    start_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(Dem2StlDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.start_thread()

        self.running = False

    def connect_UI(self):
        self.generateSTL_button.clicked.connect(
            self.begin_generating_STL)
        self.worker.progress_changed.connect(self.progress.setValue)
        self.worker.progress_text.connect(self.progress.setFormat)
        self.worker.finished.connect(self.finished_generating_STL)
        self.start_signal.connect(self.worker.generate_STL)

    def start_thread(self):
        self.worker = WorkerObject()
        self.worker_thread = QtCore.QThread()
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.connect_UI()

    def begin_generating_STL(self):
        self.progress.setValue(0.0)
        self.progress.setFormat("%p% Beginning to Generate STL...")

        # Set the parameters for generating the STL file
        self.worker.mesh_generator.set_parameters(printHeight=self.printHeight_input.value(),
                                                  baseHeight=self.baseHeight_input.value(),
                                                  noDataValue=self.noDataValue_input.value(),
                                                  saveLocation=(self.saveLocation_input.filePath(
                                                  ) + "\\" + self.layers_comboBox.currentLayer().name()),
                                                  bedX=self.bedWidth_input.value(),
                                                  bedY=self.bedLength_input.value(),
                                                  lineWidth=self.lineWidth_input.value())

        self.worker.current_layer = self.layers_comboBox.currentLayer().source()

        if not self.running:
            self.running = True
            self.start_signal.emit()

    def finished_generating_STL(self):
        self.running = False

    def stop_thread(self):
        if self.worker_thread.isRunning():
            self.worker_thread.terminate()
            self.worker_thread.wait()
        self.finished_generating_STL()


class WorkerObject(QtCore.QObject):
    progress_changed = QtCore.pyqtSignal(float)
    progress_text = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.mesh_generator = MeshGenerator()
        self.running = False

    # Generates STL file on button press
    @QtCore.pyqtSlot()
    def generate_STL(self):
        try:
            self.progress_changed.emit(10.0)
            self.progress_text.emit("%p% Reading Raster Data...")
            input_array = self.mesh_generator.generate_height_array(
                source_dem=self.current_layer)

            self.progress_changed.emit(60.0)
            self.progress_text.emit("%p% Putting Together STL File...")
            self.mesh_generator.manually_generate_stl(input_array)

            self.progress_changed.emit(100.0)
            self.progress_text.emit("%p% Finished Generating STL File!")
        except:
            self.progress_text.emit("Failed to Generate STL.")

        self.finished.emit()
