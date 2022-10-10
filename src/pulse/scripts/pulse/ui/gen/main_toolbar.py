# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_toolbar.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_MainToolbar(object):
    def setupUi(self, MainToolbar):
        if not MainToolbar.objectName():
            MainToolbar.setObjectName(u"MainToolbar")
        MainToolbar.resize(298, 117)
        self.verticalLayout = QVBoxLayout(MainToolbar)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.mode_frame = QFrame(MainToolbar)
        self.mode_frame.setObjectName(u"mode_frame")
        self.mode_frame.setFrameShape(QFrame.StyledPanel)
        self.mode_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.mode_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.header_stack_widget = QStackedWidget(self.mode_frame)
        self.header_stack_widget.setObjectName(u"header_stack_widget")
        self.blueprint_page = QWidget()
        self.blueprint_page.setObjectName(u"blueprint_page")
        self.horizontalLayout_2 = QHBoxLayout(self.blueprint_page)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.blueprint_name_label = QLabel(self.blueprint_page)
        self.blueprint_name_label.setObjectName(u"blueprint_name_label")

        self.horizontalLayout_4.addWidget(self.blueprint_name_label)


        self.horizontalLayout_2.addLayout(self.horizontalLayout_4)

        self.header_stack_widget.addWidget(self.blueprint_page)
        self.rig_page = QWidget()
        self.rig_page.setObjectName(u"rig_page")
        self.horizontalLayout_7 = QHBoxLayout(self.rig_page)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.rig_name_label = QLabel(self.rig_page)
        self.rig_name_label.setObjectName(u"rig_name_label")

        self.horizontalLayout_6.addWidget(self.rig_name_label)


        self.horizontalLayout_7.addLayout(self.horizontalLayout_6)

        self.header_stack_widget.addWidget(self.rig_page)

        self.horizontalLayout_3.addWidget(self.header_stack_widget)

        self.blueprint_mode_label = QLabel(self.mode_frame)
        self.blueprint_mode_label.setObjectName(u"blueprint_mode_label")

        self.horizontalLayout_3.addWidget(self.blueprint_mode_label)

        self.label_2 = QLabel(self.mode_frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setEnabled(False)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.rig_mode_label = QLabel(self.mode_frame)
        self.rig_mode_label.setObjectName(u"rig_mode_label")

        self.horizontalLayout_3.addWidget(self.rig_mode_label)


        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setObjectName(u"buttons_layout")
        self.validate_btn = QPushButton(self.mode_frame)
        self.validate_btn.setObjectName(u"validate_btn")
        self.validate_btn.setMinimumSize(QSize(80, 0))
        icon = QIcon()
        icon.addFile(u":/res/validate.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.validate_btn.setIcon(icon)
        self.validate_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.validate_btn)

        self.build_btn = QPushButton(self.mode_frame)
        self.build_btn.setObjectName(u"build_btn")
        self.build_btn.setMinimumSize(QSize(80, 0))
        icon1 = QIcon()
        icon1.addFile(u":/res/build.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.build_btn.setIcon(icon1)
        self.build_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.build_btn)

        self.open_blueprint_btn = QPushButton(self.mode_frame)
        self.open_blueprint_btn.setObjectName(u"open_blueprint_btn")
        icon2 = QIcon()
        icon2.addFile(u":/res/angle_left.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.open_blueprint_btn.setIcon(icon2)
        self.open_blueprint_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.open_blueprint_btn)


        self.verticalLayout_2.addLayout(self.buttons_layout)


        self.verticalLayout.addWidget(self.mode_frame)

        self.toolbar_frame = QFrame(MainToolbar)
        self.toolbar_frame.setObjectName(u"toolbar_frame")
        self.toolbar_frame.setFrameShape(QFrame.StyledPanel)
        self.toolbar_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.toolbar_frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setObjectName(u"toolbar_layout")
        self.settings_btn = QPushButton(self.toolbar_frame)
        self.settings_btn.setObjectName(u"settings_btn")
        icon3 = QIcon()
        icon3.addFile(u":/res/gear.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.settings_btn.setIcon(icon3)

        self.toolbar_layout.addWidget(self.settings_btn)

        self.design_toolkit_btn = QPushButton(self.toolbar_frame)
        self.design_toolkit_btn.setObjectName(u"design_toolkit_btn")
        icon4 = QIcon()
        icon4.addFile(u":/res/design_toolkit.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.design_toolkit_btn.setIcon(icon4)

        self.toolbar_layout.addWidget(self.design_toolkit_btn)

        self.action_editor_btn = QPushButton(self.toolbar_frame)
        self.action_editor_btn.setObjectName(u"action_editor_btn")
        icon5 = QIcon()
        icon5.addFile(u":/res/action_editor.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.action_editor_btn.setIcon(icon5)

        self.toolbar_layout.addWidget(self.action_editor_btn)


        self.horizontalLayout.addLayout(self.toolbar_layout)


        self.verticalLayout.addWidget(self.toolbar_frame)


        self.retranslateUi(MainToolbar)

        self.header_stack_widget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainToolbar)
    # setupUi

    def retranslateUi(self, MainToolbar):
        MainToolbar.setWindowTitle(QCoreApplication.translate("MainToolbar", u"Main Toolbar", None))
        self.blueprint_name_label.setText(QCoreApplication.translate("MainToolbar", u"<Blueprint File Name>", None))
        self.blueprint_name_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"subtitle", None))
        self.rig_name_label.setText(QCoreApplication.translate("MainToolbar", u"<Rig Name>", None))
        self.rig_name_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"subtitle", None))
        self.blueprint_mode_label.setText(QCoreApplication.translate("MainToolbar", u"Blueprint", None))
        self.blueprint_mode_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
        self.label_2.setText(QCoreApplication.translate("MainToolbar", u"|", None))
        self.label_2.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
        self.rig_mode_label.setText(QCoreApplication.translate("MainToolbar", u"Rig", None))
        self.rig_mode_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
        self.validate_btn.setText(QCoreApplication.translate("MainToolbar", u" Validate", None))
        self.build_btn.setText(QCoreApplication.translate("MainToolbar", u" Build", None))
        self.open_blueprint_btn.setText(QCoreApplication.translate("MainToolbar", u" Open Blueprint", None))
        self.toolbar_frame.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"toolbar", None))
        self.settings_btn.setText(QCoreApplication.translate("MainToolbar", u" Settings", None))
        self.design_toolkit_btn.setText(QCoreApplication.translate("MainToolbar", u" Design Toolkit", None))
        self.action_editor_btn.setText(QCoreApplication.translate("MainToolbar", u" Action Editor", None))
    # retranslateUi

