# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'anim_picker.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AnimPicker(object):
    def setupUi(self, AnimPicker):
        if not AnimPicker.objectName():
            AnimPicker.setObjectName(u"AnimPicker")
        AnimPicker.resize(533, 470)
        self.horizontalLayoutWidget = QWidget(AnimPicker)
        self.horizontalLayoutWidget.setObjectName(u"horizontalLayoutWidget")
        self.horizontalLayoutWidget.setGeometry(QRect(10, 10, 160, 21))
        self.horizontalLayout = QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.horizontalLayoutWidget)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.zoom_label = QLabel(self.horizontalLayoutWidget)
        self.zoom_label.setObjectName(u"zoom_label")

        self.horizontalLayout.addWidget(self.zoom_label)


        self.retranslateUi(AnimPicker)

        QMetaObject.connectSlotsByName(AnimPicker)
    # setupUi

    def retranslateUi(self, AnimPicker):
        AnimPicker.setWindowTitle(QCoreApplication.translate("AnimPicker", u"Anim Picker", None))
        self.label.setText(QCoreApplication.translate("AnimPicker", u"Zoom:", None))
        self.zoom_label.setText(QCoreApplication.translate("AnimPicker", u"1.0", None))
    # retranslateUi

