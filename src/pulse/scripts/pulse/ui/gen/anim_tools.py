# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'anim_tools.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_AnimTools(object):
    def setupUi(self, AnimTools):
        if not AnimTools.objectName():
            AnimTools.setObjectName(u"AnimTools")
        AnimTools.resize(334, 300)
        self.verticalLayout = QVBoxLayout(AnimTools)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.move_keys_spin_box = QDoubleSpinBox(AnimTools)
        self.move_keys_spin_box.setObjectName(u"move_keys_spin_box")
        self.move_keys_spin_box.setMinimum(-1000.000000000000000)
        self.move_keys_spin_box.setMaximum(1000.000000000000000)
        self.move_keys_spin_box.setValue(1.000000000000000)

        self.horizontalLayout.addWidget(self.move_keys_spin_box)

        self.move_keys_btn = QPushButton(AnimTools)
        self.move_keys_btn.setObjectName(u"move_keys_btn")

        self.horizontalLayout.addWidget(self.move_keys_btn)

        self.horizontalLayout.setStretch(0, 1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(AnimTools)

        QMetaObject.connectSlotsByName(AnimTools)
    # setupUi

    def retranslateUi(self, AnimTools):
        AnimTools.setWindowTitle(QCoreApplication.translate("AnimTools", u"Form", None))
        self.move_keys_btn.setText(QCoreApplication.translate("AnimTools", u"Move Keys", None))
    # retranslateUi

