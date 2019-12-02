# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'newcane.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgNewCane(object):
    def setupUi(self, DlgNewCane):
        DlgNewCane.setObjectName("DlgNewCane")
        DlgNewCane.setWindowModality(QtCore.Qt.ApplicationModal)
        DlgNewCane.resize(400, 150)
        self.formLayout = QtWidgets.QFormLayout(DlgNewCane)
        self.formLayout.setObjectName("formLayout")
        self.label_3 = QtWidgets.QLabel(DlgNewCane)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.spnCylinder = QtWidgets.QSpinBox(DlgNewCane)
        self.spnCylinder.setObjectName("spnCylinder")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.spnCylinder)
        self.label = QtWidgets.QLabel(DlgNewCane)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label)
        self.txtCaneColor = QtWidgets.QLineEdit(DlgNewCane)
        self.txtCaneColor.setObjectName("txtCaneColor")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.txtCaneColor)
        self.label_2 = QtWidgets.QLabel(DlgNewCane)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.txtCaneID = QtWidgets.QLineEdit(DlgNewCane)
        self.txtCaneID.setObjectName("txtCaneID")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.txtCaneID)
        self.buttonBox = QtWidgets.QDialogButtonBox(DlgNewCane)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.SpanningRole, self.buttonBox)

        self.retranslateUi(DlgNewCane)
        self.buttonBox.accepted.connect(DlgNewCane.accept)
        self.buttonBox.rejected.connect(DlgNewCane.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgNewCane)

    def retranslateUi(self, DlgNewCane):
        _translate = QtCore.QCoreApplication.translate
        DlgNewCane.setWindowTitle(_translate("DlgNewCane", "Create New Cane"))
        self.label_3.setText(_translate("DlgNewCane", "Cylinder"))
        self.label.setText(_translate("DlgNewCane", "Cane Color"))
        self.label_2.setText(_translate("DlgNewCane", "Cane ID"))

