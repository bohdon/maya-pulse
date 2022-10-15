# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_settings.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainSettings(object):
    def setupUi(self, MainSettings):
        if not MainSettings.objectName():
            MainSettings.setObjectName(u"MainSettings")
        MainSettings.resize(503, 400)
        MainSettings.setMinimumSize(QSize(350, 400))
        self.verticalLayout = QVBoxLayout(MainSettings)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(MainSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.blueprint_tab = QWidget()
        self.blueprint_tab.setObjectName(u"blueprint_tab")
        self.verticalLayout_2 = QVBoxLayout(self.blueprint_tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setVerticalSpacing(2)
        self.file_path_label = QLabel(self.blueprint_tab)
        self.file_path_label.setObjectName(u"file_path_label")
        self.file_path_label.setMinimumSize(QSize(120, 20))
        self.file_path_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.file_path_label)

        self.file_path_text_label = QLabel(self.blueprint_tab)
        self.file_path_text_label.setObjectName(u"file_path_text_label")
        self.file_path_text_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.file_path_text_label)

        self.rig_name_label = QLabel(self.blueprint_tab)
        self.rig_name_label.setObjectName(u"rig_name_label")
        self.rig_name_label.setMinimumSize(QSize(120, 0))
        self.rig_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.rig_name_label)

        self.rig_name_edit = QLineEdit(self.blueprint_tab)
        self.rig_name_edit.setObjectName(u"rig_name_edit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.rig_name_edit)

        self.rig_node_fmt_label = QLabel(self.blueprint_tab)
        self.rig_node_fmt_label.setObjectName(u"rig_node_fmt_label")
        self.rig_node_fmt_label.setMinimumSize(QSize(120, 0))
        self.rig_node_fmt_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(2, QFormLayout.LabelRole, self.rig_node_fmt_label)

        self.rig_node_fmt_edit = QLineEdit(self.blueprint_tab)
        self.rig_node_fmt_edit.setObjectName(u"rig_node_fmt_edit")

        self.formLayout_2.setWidget(2, QFormLayout.FieldRole, self.rig_node_fmt_edit)

        self.debug_build_label = QLabel(self.blueprint_tab)
        self.debug_build_label.setObjectName(u"debug_build_label")
        self.debug_build_label.setMinimumSize(QSize(120, 0))
        self.debug_build_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(3, QFormLayout.LabelRole, self.debug_build_label)

        self.debug_build_check = QCheckBox(self.blueprint_tab)
        self.debug_build_check.setObjectName(u"debug_build_check")
        self.debug_build_check.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(3, QFormLayout.FieldRole, self.debug_build_check)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.blueprint_help_label = QLabel(self.blueprint_tab)
        self.blueprint_help_label.setObjectName(u"blueprint_help_label")

        self.verticalLayout_2.addWidget(self.blueprint_help_label)

        self.tabWidget.addTab(self.blueprint_tab, "")
        self.actions_tab = QWidget()
        self.actions_tab.setObjectName(u"actions_tab")
        self.verticalLayout_3 = QVBoxLayout(self.actions_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_3 = QLabel(self.actions_tab)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_3.addWidget(self.label_3)

        self.action_pkgs_layout = QVBoxLayout()
        self.action_pkgs_layout.setObjectName(u"action_pkgs_layout")

        self.verticalLayout_3.addLayout(self.action_pkgs_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.blueprint_help_label_2 = QLabel(self.actions_tab)
        self.blueprint_help_label_2.setObjectName(u"blueprint_help_label_2")

        self.verticalLayout_3.addWidget(self.blueprint_help_label_2)

        self.tabWidget.addTab(self.actions_tab, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(MainSettings)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainSettings)
    # setupUi

    def retranslateUi(self, MainSettings):
        MainSettings.setWindowTitle(QCoreApplication.translate("MainSettings", u"Pulse Settings", None))
#if QT_CONFIG(statustip)
        self.file_path_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The path to the currently open blueprint.", None))
#endif // QT_CONFIG(statustip)
        self.file_path_label.setText(QCoreApplication.translate("MainSettings", u"File Path", None))
        self.file_path_text_label.setText(QCoreApplication.translate("MainSettings", u"<File Path>", None))
#if QT_CONFIG(statustip)
        self.rig_name_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The name of the rig. Used to name the core hierarchy nodes and can be used by actions as well.", None))
#endif // QT_CONFIG(statustip)
        self.rig_name_label.setText(QCoreApplication.translate("MainSettings", u"Rig Name", None))
#if QT_CONFIG(statustip)
        self.rig_node_fmt_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The naming format to use for the parent rig node. Can use any settings key, such as {rigName}.", None))
#endif // QT_CONFIG(statustip)
        self.rig_node_fmt_label.setText(QCoreApplication.translate("MainSettings", u"Rig Node Name", None))
#if QT_CONFIG(statustip)
        self.debug_build_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The naming format to use for the parent rig node. Can use any settings key, such as {rigName}.", None))
#endif // QT_CONFIG(statustip)
        self.debug_build_label.setText(QCoreApplication.translate("MainSettings", u"Debug Build", None))
        self.debug_build_check.setText("")
        self.blueprint_help_label.setText(QCoreApplication.translate("MainSettings", u"Settings for the current blueprint.", None))
        self.blueprint_help_label.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"help", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.blueprint_tab), QCoreApplication.translate("MainSettings", u"Blueprint", None))
        self.label_3.setText(QCoreApplication.translate("MainSettings", u"Action Packages", None))
        self.label_3.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
        self.blueprint_help_label_2.setText(QCoreApplication.translate("MainSettings", u"Global action settings.", None))
        self.blueprint_help_label_2.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"help", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.actions_tab), QCoreApplication.translate("MainSettings", u"Actions", None))
    # retranslateUi

