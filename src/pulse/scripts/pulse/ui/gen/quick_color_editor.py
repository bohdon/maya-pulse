# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'quick_color_editor.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_QuickColorEditor(object):
    def setupUi(self, QuickColorEditor):
        if not QuickColorEditor.objectName():
            QuickColorEditor.setObjectName(u"QuickColorEditor")
        QuickColorEditor.resize(322, 137)
        QuickColorEditor.setMinimumSize(QSize(250, 100))
        self.verticalLayout_4 = QVBoxLayout(QuickColorEditor)
        self.verticalLayout_4.setSpacing(2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.remove_btn = QPushButton(QuickColorEditor)
        self.remove_btn.setObjectName(u"remove_btn")

        self.verticalLayout_4.addWidget(self.remove_btn)

        self.color_btns_layout = QGridLayout()
        self.color_btns_layout.setObjectName(u"color_btns_layout")

        self.verticalLayout_4.addLayout(self.color_btns_layout)

        self.verticalSpacer_4 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.edit_config_btn = QToolButton(QuickColorEditor)
        self.edit_config_btn.setObjectName(u"edit_config_btn")
        icon = QIcon()
        icon.addFile(u":/res/action_editor.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.edit_config_btn.setIcon(icon)

        self.horizontalLayout.addWidget(self.edit_config_btn)

        self.help_label = QLabel(QuickColorEditor)
        self.help_label.setObjectName(u"help_label")

        self.horizontalLayout.addWidget(self.help_label)


        self.verticalLayout_4.addLayout(self.horizontalLayout)


        self.retranslateUi(QuickColorEditor)

        QMetaObject.connectSlotsByName(QuickColorEditor)
    # setupUi

    def retranslateUi(self, QuickColorEditor):
        QuickColorEditor.setWindowTitle(QCoreApplication.translate("QuickColorEditor", u"Form", None))
#if QT_CONFIG(statustip)
        self.remove_btn.setStatusTip(QCoreApplication.translate("QuickColorEditor", u"Remove the override color from the selected nodes.", None))
#endif // QT_CONFIG(statustip)
        self.remove_btn.setText(QCoreApplication.translate("QuickColorEditor", u"Remove Color", None))
        self.edit_config_btn.setText("")
        self.help_label.setText(QCoreApplication.translate("QuickColorEditor", u"Edit the blueprint config to modify colors.", None))
        self.help_label.setProperty("cssClasses", QCoreApplication.translate("QuickColorEditor", u"help", None))
    # retranslateUi

