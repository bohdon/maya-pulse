# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_general.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_GeneralDesignPanel(object):
    def setupUi(self, GeneralDesignPanel):
        if not GeneralDesignPanel.objectName():
            GeneralDesignPanel.setObjectName(u"GeneralDesignPanel")
        GeneralDesignPanel.resize(328, 112)
        self.verticalLayout = QVBoxLayout(GeneralDesignPanel)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.parent_selected_btn = QPushButton(GeneralDesignPanel)
        self.parent_selected_btn.setObjectName(u"parent_selected_btn")

        self.gridLayout.addWidget(self.parent_selected_btn, 1, 0, 1, 1)

        self.freeze_scales_btn = QPushButton(GeneralDesignPanel)
        self.freeze_scales_btn.setObjectName(u"freeze_scales_btn")

        self.gridLayout.addWidget(self.freeze_scales_btn, 3, 0, 1, 1)

        self.name_editor_btn = QPushButton(GeneralDesignPanel)
        self.name_editor_btn.setObjectName(u"name_editor_btn")

        self.gridLayout.addWidget(self.name_editor_btn, 0, 0, 1, 1)

        self.create_offset_btn = QPushButton(GeneralDesignPanel)
        self.create_offset_btn.setObjectName(u"create_offset_btn")

        self.gridLayout.addWidget(self.create_offset_btn, 2, 0, 1, 1)

        self.color_editor_btn = QPushButton(GeneralDesignPanel)
        self.color_editor_btn.setObjectName(u"color_editor_btn")

        self.gridLayout.addWidget(self.color_editor_btn, 0, 1, 1, 1)

        self.parent_in_order_btn = QPushButton(GeneralDesignPanel)
        self.parent_in_order_btn.setObjectName(u"parent_in_order_btn")

        self.gridLayout.addWidget(self.parent_in_order_btn, 1, 1, 1, 1)

        self.select_hierarchy_btn = QPushButton(GeneralDesignPanel)
        self.select_hierarchy_btn.setObjectName(u"select_hierarchy_btn")

        self.gridLayout.addWidget(self.select_hierarchy_btn, 2, 1, 1, 1)

        self.freeze_pivots_btn = QPushButton(GeneralDesignPanel)
        self.freeze_pivots_btn.setObjectName(u"freeze_pivots_btn")

        self.gridLayout.addWidget(self.freeze_pivots_btn, 3, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)


        self.retranslateUi(GeneralDesignPanel)

        QMetaObject.connectSlotsByName(GeneralDesignPanel)
    # setupUi

    def retranslateUi(self, GeneralDesignPanel):
        GeneralDesignPanel.setWindowTitle(QCoreApplication.translate("GeneralDesignPanel", u"Form", None))
#if QT_CONFIG(statustip)
        self.parent_selected_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Parent the selected nodes, select one leader then followers.", None))
#endif // QT_CONFIG(statustip)
        self.parent_selected_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Parent Selected", None))
#if QT_CONFIG(statustip)
        self.freeze_scales_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Freeze the scales of the selected node and its children without affecting their pivots.", None))
#endif // QT_CONFIG(statustip)
        self.freeze_scales_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Freeze Scales", None))
        self.name_editor_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Name Editor", None))
#if QT_CONFIG(statustip)
        self.create_offset_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Group the selected transform, creating the group exactly where the transform is.", None))
#endif // QT_CONFIG(statustip)
        self.create_offset_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Create Offset", None))
        self.color_editor_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Color Editor", None))
#if QT_CONFIG(statustip)
        self.parent_in_order_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Parent the selection in order, select leaders to followers.", None))
#endif // QT_CONFIG(statustip)
        self.parent_in_order_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Parent in Order", None))
#if QT_CONFIG(statustip)
        self.select_hierarchy_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Select all descendants of the selected node.", None))
#endif // QT_CONFIG(statustip)
        self.select_hierarchy_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Select Hierarchy", None))
#if QT_CONFIG(statustip)
        self.freeze_pivots_btn.setStatusTip(QCoreApplication.translate("GeneralDesignPanel", u"Freeze the local pivots of the selected node and its children by baking the values into translate.", None))
#endif // QT_CONFIG(statustip)
        self.freeze_pivots_btn.setText(QCoreApplication.translate("GeneralDesignPanel", u"Freeze Pivots", None))
    # retranslateUi

