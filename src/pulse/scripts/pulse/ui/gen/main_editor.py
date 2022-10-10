# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_editor.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainEditor(object):
    def setupUi(self, MainEditor):
        if not MainEditor.objectName():
            MainEditor.setObjectName(u"MainEditor")
        MainEditor.resize(300, 225)
        MainEditor.setMinimumSize(QSize(300, 0))
        self.verticalLayout = QVBoxLayout(MainEditor)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.toolbar_layout = QVBoxLayout()
        self.toolbar_layout.setObjectName(u"toolbar_layout")

        self.verticalLayout.addLayout(self.toolbar_layout)

        self.main_tab_widget = QTabWidget(MainEditor)
        self.main_tab_widget.setObjectName(u"main_tab_widget")

        self.verticalLayout.addWidget(self.main_tab_widget)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(MainEditor)

        self.main_tab_widget.setCurrentIndex(-1)


        QMetaObject.connectSlotsByName(MainEditor)
    # setupUi

    def retranslateUi(self, MainEditor):
        MainEditor.setWindowTitle(QCoreApplication.translate("MainEditor", u"Main Editor", None))
    # retranslateUi

