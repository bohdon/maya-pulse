# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_toolbar.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_BuildToolbar(object):
    def setupUi(self, BuildToolbar):
        if not BuildToolbar.objectName():
            BuildToolbar.setObjectName(u"BuildToolbar")
        BuildToolbar.resize(344, 97)
        self.verticalLayout = QVBoxLayout(BuildToolbar)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.mode_frame = QFrame(BuildToolbar)
        self.mode_frame.setObjectName(u"mode_frame")
        self.mode_frame.setFrameShape(QFrame.StyledPanel)
        self.mode_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.mode_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.main_stack = QStackedWidget(self.mode_frame)
        self.main_stack.setObjectName(u"main_stack")
        self.blueprint_page = QWidget()
        self.blueprint_page.setObjectName(u"blueprint_page")
        self.horizontalLayout_2 = QHBoxLayout(self.blueprint_page)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.blueprint_name_label = QLabel(self.blueprint_page)
        self.blueprint_name_label.setObjectName(u"blueprint_name_label")

        self.horizontalLayout_2.addWidget(self.blueprint_name_label)

        self.validate_btn = QPushButton(self.blueprint_page)
        self.validate_btn.setObjectName(u"validate_btn")
        self.validate_btn.setMinimumSize(QSize(80, 0))
        icon = QIcon()
        icon.addFile(u":/res/validate.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.validate_btn.setIcon(icon)
        self.validate_btn.setIconSize(QSize(14, 14))

        self.horizontalLayout_2.addWidget(self.validate_btn)

        self.build_btn = QPushButton(self.blueprint_page)
        self.build_btn.setObjectName(u"build_btn")
        self.build_btn.setMinimumSize(QSize(80, 0))
        icon1 = QIcon()
        icon1.addFile(u":/res/build.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.build_btn.setIcon(icon1)
        self.build_btn.setIconSize(QSize(14, 14))

        self.horizontalLayout_2.addWidget(self.build_btn)

        self.horizontalLayout_2.setStretch(0, 1)
        self.main_stack.addWidget(self.blueprint_page)
        self.rig_page = QWidget()
        self.rig_page.setObjectName(u"rig_page")
        self.horizontalLayout = QHBoxLayout(self.rig_page)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.rig_name_label = QLabel(self.rig_page)
        self.rig_name_label.setObjectName(u"rig_name_label")

        self.horizontalLayout.addWidget(self.rig_name_label)

        self.label = QLabel(self.rig_page)
        self.label.setObjectName(u"label")

        self.horizontalLayout.addWidget(self.label)

        self.open_blueprint_btn = QPushButton(self.rig_page)
        self.open_blueprint_btn.setObjectName(u"open_blueprint_btn")

        self.horizontalLayout.addWidget(self.open_blueprint_btn)

        self.horizontalLayout.setStretch(1, 1)
        self.main_stack.addWidget(self.rig_page)

        self.verticalLayout_2.addWidget(self.main_stack)

        self.header_layout = QHBoxLayout()
        self.header_layout.setObjectName(u"header_layout")
        self.mode_label = QLabel(self.mode_frame)
        self.mode_label.setObjectName(u"mode_label")

        self.header_layout.addWidget(self.mode_label)

        self.design_toolkit_btn = QToolButton(self.mode_frame)
        self.design_toolkit_btn.setObjectName(u"design_toolkit_btn")
        self.design_toolkit_btn.setMinimumSize(QSize(28, 28))
        icon2 = QIcon()
        icon2.addFile(u":/res/design_toolkit.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.design_toolkit_btn.setIcon(icon2)
        self.design_toolkit_btn.setIconSize(QSize(20, 20))

        self.header_layout.addWidget(self.design_toolkit_btn)

        self.action_editor_btn = QToolButton(self.mode_frame)
        self.action_editor_btn.setObjectName(u"action_editor_btn")
        self.action_editor_btn.setMinimumSize(QSize(28, 28))
        icon3 = QIcon()
        icon3.addFile(u":/res/action_editor.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.action_editor_btn.setIcon(icon3)
        self.action_editor_btn.setIconSize(QSize(20, 20))

        self.header_layout.addWidget(self.action_editor_btn)


        self.verticalLayout_2.addLayout(self.header_layout)


        self.verticalLayout.addWidget(self.mode_frame)


        self.retranslateUi(BuildToolbar)

        self.main_stack.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(BuildToolbar)
    # setupUi

    def retranslateUi(self, BuildToolbar):
        BuildToolbar.setWindowTitle(QCoreApplication.translate("BuildToolbar", u"Form", None))
        self.blueprint_name_label.setText(QCoreApplication.translate("BuildToolbar", u"<Blueprint Rig Name>", None))
        self.blueprint_name_label.setProperty("cssClasses", QCoreApplication.translate("BuildToolbar", u"title", None))
        self.validate_btn.setText(QCoreApplication.translate("BuildToolbar", u" Validate", None))
        self.build_btn.setText(QCoreApplication.translate("BuildToolbar", u" Build", None))
        self.rig_name_label.setText(QCoreApplication.translate("BuildToolbar", u"<Rig Name>", None))
        self.rig_name_label.setProperty("cssClasses", QCoreApplication.translate("BuildToolbar", u"title", None))
        self.label.setText(QCoreApplication.translate("BuildToolbar", u"(read-only)", None))
        self.label.setProperty("cssClasses", QCoreApplication.translate("BuildToolbar", u"help title", None))
        self.open_blueprint_btn.setText(QCoreApplication.translate("BuildToolbar", u"Open Blueprint", None))
        self.mode_label.setText(QCoreApplication.translate("BuildToolbar", u"<Mode>", None))
        self.mode_label.setProperty("cssClasses", QCoreApplication.translate("BuildToolbar", u"mode-title", None))
#if QT_CONFIG(statustip)
        self.design_toolkit_btn.setStatusTip(QCoreApplication.translate("BuildToolbar", u"Open the Pulse Design Toolkit", None))
#endif // QT_CONFIG(statustip)
        self.design_toolkit_btn.setText("")
#if QT_CONFIG(statustip)
        self.action_editor_btn.setStatusTip(QCoreApplication.translate("BuildToolbar", u"Open the Pulse Action Editor", None))
#endif // QT_CONFIG(statustip)
        self.action_editor_btn.setText("")
    # retranslateUi

