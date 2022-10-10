# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'action_tree.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ActionTree(object):
    def setupUi(self, ActionTree):
        if not ActionTree.objectName():
            ActionTree.setObjectName(u"ActionTree")
        ActionTree.resize(381, 293)
        self.verticalLayout = QVBoxLayout(ActionTree)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.search_edit = QLineEdit(ActionTree)
        self.search_edit.setObjectName(u"search_edit")

        self.verticalLayout.addWidget(self.search_edit)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName(u"main_layout")

        self.verticalLayout.addLayout(self.main_layout)

        self.verticalLayout.setStretch(1, 1)

        self.retranslateUi(ActionTree)

        QMetaObject.connectSlotsByName(ActionTree)
    # setupUi

    def retranslateUi(self, ActionTree):
        ActionTree.setWindowTitle(QCoreApplication.translate("ActionTree", u"Action Tree", None))
        self.search_edit.setPlaceholderText(QCoreApplication.translate("ActionTree", u"Search...", None))
    # retranslateUi

