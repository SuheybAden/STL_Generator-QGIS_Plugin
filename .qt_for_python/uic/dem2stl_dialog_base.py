# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\Program Files\QGIS 3.16\apps\qgis\python\plugins\DEM2STL-QGIS_Plugin\dem2stl_dialog_base.ui'
#
# Created by: PyQt5 UI code generator 5.13.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dem2StlDialogBase(object):
    def setupUi(self, Dem2StlDialogBase):
        Dem2StlDialogBase.setObjectName("Dem2StlDialogBase")
        Dem2StlDialogBase.resize(535, 361)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(Dem2StlDialogBase)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox = QtWidgets.QGroupBox(Dem2StlDialogBase)
        self.groupBox.setFlat(False)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.selectedLayer_ComboBox = QtWidgets.QComboBox(self.groupBox)
        self.selectedLayer_ComboBox.setObjectName("selectedLayer_ComboBox")
        self.verticalLayout.addWidget(self.selectedLayer_ComboBox)
        self.verticalLayout_3.addWidget(self.groupBox)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_3.addItem(spacerItem)
        self.mMapLayerComboBox = QgsMapLayerComboBox(Dem2StlDialogBase)
        self.mMapLayerComboBox.setShowCrs(True)
        self.mMapLayerComboBox.setObjectName("mMapLayerComboBox")
        self.verticalLayout_3.addWidget(self.mMapLayerComboBox)
        self.groupBox_2 = QtWidgets.QGroupBox(Dem2StlDialogBase)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        self.formLayout.setObjectName("formLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit.setObjectName("lineEdit")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.lineEdit)
        self.label_2 = QtWidgets.QLabel(self.groupBox_2)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.label_2)
        self.lineEdit_2 = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.lineEdit_2)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.label_3)
        self.lineEdit_3 = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit_3.setObjectName("lineEdit_3")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.lineEdit_3)
        self.label = QtWidgets.QLabel(self.groupBox_2)
        self.label.setObjectName("label")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.label)
        self.lineEdit_4 = QtWidgets.QLineEdit(self.groupBox_2)
        self.lineEdit_4.setObjectName("lineEdit_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.lineEdit_4)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.label_4)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(5, QtWidgets.QFormLayout.LabelRole, spacerItem1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.formLayout.setItem(0, QtWidgets.QFormLayout.LabelRole, spacerItem2)
        self.verticalLayout_2.addLayout(self.formLayout)
        self.verticalLayout_3.addWidget(self.groupBox_2)
        self.button_box = QtWidgets.QDialogButtonBox(Dem2StlDialogBase)
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box.setObjectName("button_box")
        self.verticalLayout_3.addWidget(self.button_box)

        self.retranslateUi(Dem2StlDialogBase)
        self.button_box.accepted.connect(Dem2StlDialogBase.accept)
        self.button_box.rejected.connect(Dem2StlDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(Dem2StlDialogBase)

    def retranslateUi(self, Dem2StlDialogBase):
        _translate = QtCore.QCoreApplication.translate
        Dem2StlDialogBase.setWindowTitle(_translate("Dem2StlDialogBase", "DEM2STL"))
        self.groupBox.setTitle(_translate("Dem2StlDialogBase", "Layer to Print"))
        self.groupBox_2.setTitle(_translate("Dem2StlDialogBase", "Print Settings"))
        self.label_2.setText(_translate("Dem2StlDialogBase", "Model Height (mm)"))
        self.label_3.setText(_translate("Dem2StlDialogBase", "Width(mm)"))
        self.label.setText(_translate("Dem2StlDialogBase", "Length(mm)"))
        self.label_4.setText(_translate("Dem2StlDialogBase", "Base Thickness (mm)"))
from qgsmaplayercombobox import QgsMapLayerComboBox
