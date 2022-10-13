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
        self.verticalLayout_3 = QVBoxLayout(ActionTree)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.main_stack = QStackedWidget(ActionTree)
        self.main_stack.setObjectName(u"main_stack")
        self.active_page = QWidget()
        self.active_page.setObjectName(u"active_page")
        self.verticalLayout = QVBoxLayout(self.active_page)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.search_edit = QLineEdit(self.active_page)
        self.search_edit.setObjectName(u"search_edit")

        self.verticalLayout.addWidget(self.search_edit)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName(u"main_layout")

        self.verticalLayout.addLayout(self.main_layout)

        self.main_stack.addWidget(self.active_page)
        self.inactive_page = QWidget()
        self.inactive_page.setObjectName(u"inactive_page")
        self.verticalLayout_2 = QVBoxLayout(self.inactive_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.begin_help_label = QLabel(self.inactive_page)
        self.begin_help_label.setObjectName(u"begin_help_label")
        self.begin_help_label.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.begin_help_label)

        self.main_stack.addWidget(self.inactive_page)

        self.verticalLayout_3.addWidget(self.main_stack)


        self.retranslateUi(ActionTree)

        QMetaObject.connectSlotsByName(ActionTree)
    # setupUi

    def retranslateUi(self, ActionTree):
        ActionTree.setWindowTitle(QCoreApplication.translate("ActionTree", u"Action Tree", None))
        self.search_edit.setPlaceholderText(QCoreApplication.translate("ActionTree", u"Search...", None))
        self.begin_help_label.setText(QCoreApplication.translate("ActionTree", u"Create a Blueprint to begin.", None))
        self.begin_help_label.setProperty("cssClasses", QCoreApplication.translate("ActionTree", u"help", None))
    # retranslateUi

