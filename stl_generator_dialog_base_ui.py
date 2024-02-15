# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'stl_generator_dialog_base.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from qgsfilewidget import QgsFileWidget
from qgsmaplayercombobox import QgsMapLayerComboBox

import resources_rc

class Ui_StlGeneratorDialogBase(object):
    def setupUi(self, StlGeneratorDialogBase):
        if not StlGeneratorDialogBase.objectName():
            StlGeneratorDialogBase.setObjectName(u"StlGeneratorDialogBase")
        StlGeneratorDialogBase.resize(377, 480)
        icon = QIcon()
        icon.addFile(u":/plugins/stl_generator/icon.png", QSize(), QIcon.Normal, QIcon.Off)
        StlGeneratorDialogBase.setWindowIcon(icon)
        self.verticalLayout_3 = QVBoxLayout(StlGeneratorDialogBase)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.groupBox = QGroupBox(StlGeneratorDialogBase)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setFlat(False)
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.layers_comboBox = QgsMapLayerComboBox(self.groupBox)
        self.layers_comboBox.setObjectName(u"layers_comboBox")
        self.layers_comboBox.setShowCrs(True)

        self.verticalLayout.addWidget(self.layers_comboBox)


        self.verticalLayout_3.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(StlGeneratorDialogBase)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SetFixedSize)
        self.formLayout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.formLayout.setItem(0, QFormLayout.LabelRole, self.verticalSpacer)

        self.printHeight_input = QDoubleSpinBox(self.groupBox_2)
        self.printHeight_input.setObjectName(u"printHeight_input")
        self.printHeight_input.setValue(10.000000000000000)

        self.formLayout.setWidget(2, QFormLayout.LabelRole, self.printHeight_input)

        self.printHeight_label = QLabel(self.groupBox_2)
        self.printHeight_label.setObjectName(u"printHeight_label")

        self.formLayout.setWidget(2, QFormLayout.FieldRole, self.printHeight_label)

        self.baseHeight_input = QDoubleSpinBox(self.groupBox_2)
        self.baseHeight_input.setObjectName(u"baseHeight_input")
        self.baseHeight_input.setValue(10.000000000000000)

        self.formLayout.setWidget(3, QFormLayout.LabelRole, self.baseHeight_input)

        self.base_label = QLabel(self.groupBox_2)
        self.base_label.setObjectName(u"base_label")

        self.formLayout.setWidget(3, QFormLayout.FieldRole, self.base_label)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.formLayout.setItem(4, QFormLayout.LabelRole, self.verticalSpacer_2)


        self.verticalLayout_2.addLayout(self.formLayout)


        self.verticalLayout_3.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(StlGeneratorDialogBase)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setSizeConstraint(QLayout.SetFixedSize)
        self.formLayout_2.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.verticalSpacer_5 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.formLayout_2.setItem(0, QFormLayout.LabelRole, self.verticalSpacer_5)

        self.label_6 = QLabel(self.groupBox_3)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.label_6)

        self.label_7 = QLabel(self.groupBox_3)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.label_7)

        self.label_8 = QLabel(self.groupBox_3)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.label_8)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.formLayout_2.setItem(4, QFormLayout.LabelRole, self.verticalSpacer_4)

        self.bedWidth_input = QDoubleSpinBox(self.groupBox_3)
        self.bedWidth_input.setObjectName(u"bedWidth_input")
        self.bedWidth_input.setMaximum(10000.000000000000000)
        self.bedWidth_input.setValue(200.000000000000000)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.bedWidth_input)

        self.bedLength_input = QDoubleSpinBox(self.groupBox_3)
        self.bedLength_input.setObjectName(u"bedLength_input")
        self.bedLength_input.setMaximum(10000.000000000000000)
        self.bedLength_input.setValue(200.000000000000000)

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.bedLength_input)

        self.lineWidth_input = QDoubleSpinBox(self.groupBox_3)
        self.lineWidth_input.setObjectName(u"lineWidth_input")
        self.lineWidth_input.setSingleStep(0.100000000000000)
        self.lineWidth_input.setValue(0.400000000000000)

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.lineWidth_input)


        self.verticalLayout_4.addLayout(self.formLayout_2)


        self.verticalLayout_3.addWidget(self.groupBox_3)

        self.groupBox_4 = QGroupBox(StlGeneratorDialogBase)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.verticalLayout_5 = QVBoxLayout(self.groupBox_4)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.saveLocation_input = QgsFileWidget(self.groupBox_4)
        self.saveLocation_input.setObjectName(u"saveLocation_input")
        self.saveLocation_input.setStorageMode(QgsFileWidget.GetDirectory)

        self.verticalLayout_5.addWidget(self.saveLocation_input)


        self.verticalLayout_3.addWidget(self.groupBox_4)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.preview_checkBox = QCheckBox(StlGeneratorDialogBase)
        self.preview_checkBox.setObjectName(u"preview_checkBox")

        self.horizontalLayout_2.addWidget(self.preview_checkBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.line = QFrame(StlGeneratorDialogBase)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_3.addWidget(self.line)

        self.progress = QProgressBar(StlGeneratorDialogBase)
        self.progress.setObjectName(u"progress")
        self.progress.setValue(0)

        self.verticalLayout_3.addWidget(self.progress)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.generateSTL_button = QPushButton(StlGeneratorDialogBase)
        self.generateSTL_button.setObjectName(u"generateSTL_button")

        self.horizontalLayout.addWidget(self.generateSTL_button)

        self.exit_button = QPushButton(StlGeneratorDialogBase)
        self.exit_button.setObjectName(u"exit_button")
        self.exit_button.setFlat(False)

        self.horizontalLayout.addWidget(self.exit_button)

        self.horizontalLayout.setStretch(0, 12)
        self.horizontalLayout.setStretch(1, 2)

        self.verticalLayout_3.addLayout(self.horizontalLayout)


        self.retranslateUi(StlGeneratorDialogBase)

        self.exit_button.setDefault(False)


        QMetaObject.connectSlotsByName(StlGeneratorDialogBase)
    # setupUi

    def retranslateUi(self, StlGeneratorDialogBase):
        StlGeneratorDialogBase.setWindowTitle(QCoreApplication.translate("StlGeneratorDialogBase", u"STLGenerator", None))
        self.groupBox.setTitle(QCoreApplication.translate("StlGeneratorDialogBase", u"Layer to Print", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("StlGeneratorDialogBase", u"Model Settings", None))
        self.printHeight_label.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Model Height (mm)", None))
        self.base_label.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Base Thickness (mm)", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("StlGeneratorDialogBase", u"Printer Settings", None))
        self.label_6.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Bed Width (mm)", None))
        self.label_7.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Bed Length (mm)", None))
        self.label_8.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Line Width (mm)", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("StlGeneratorDialogBase", u"File Location", None))
        self.preview_checkBox.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Show preview once STL is generated", None))
        self.generateSTL_button.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Generate STL", None))
        self.exit_button.setText(QCoreApplication.translate("StlGeneratorDialogBase", u"Exit", None))
    # retranslateUi

