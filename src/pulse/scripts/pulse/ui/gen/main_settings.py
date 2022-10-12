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
        MainSettings.resize(414, 423)
        MainSettings.setMinimumSize(QSize(350, 400))
        self.verticalLayout = QVBoxLayout(MainSettings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.blueprint_properties_title_2 = QLabel(MainSettings)
        self.blueprint_properties_title_2.setObjectName(u"blueprint_properties_title_2")

        self.verticalLayout.addWidget(self.blueprint_properties_title_2)

        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setVerticalSpacing(2)
        self.file_path_label = QLabel(MainSettings)
        self.file_path_label.setObjectName(u"file_path_label")
        self.file_path_label.setMinimumSize(QSize(80, 20))
        self.file_path_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.file_path_label)

        self.file_path_text_label = QLabel(MainSettings)
        self.file_path_text_label.setObjectName(u"file_path_text_label")
        self.file_path_text_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.file_path_text_label)

        self.rig_name_label = QLabel(MainSettings)
        self.rig_name_label.setObjectName(u"rig_name_label")
        self.rig_name_label.setMinimumSize(QSize(80, 0))
        self.rig_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.rig_name_label)

        self.rig_name_edit = QLineEdit(MainSettings)
        self.rig_name_edit.setObjectName(u"rig_name_edit")

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.rig_name_edit)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(MainSettings)

        QMetaObject.connectSlotsByName(MainSettings)
    # setupUi

    def retranslateUi(self, MainSettings):
        MainSettings.setWindowTitle(QCoreApplication.translate("MainSettings", u"Pulse Settings", None))
        self.blueprint_properties_title_2.setText(QCoreApplication.translate("MainSettings", u"Blueprint", None))
        self.blueprint_properties_title_2.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
#if QT_CONFIG(statustip)
        self.file_path_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The path to the currently open blueprint.", None))
#endif // QT_CONFIG(statustip)
        self.file_path_label.setText(QCoreApplication.translate("MainSettings", u"File Path", None))
        self.file_path_text_label.setText(QCoreApplication.translate("MainSettings", u"<File Path>", None))
#if QT_CONFIG(statustip)
        self.rig_name_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The name of the rig. Used to name the core hierarchy nodes and can be used by actions as well.", None))
#endif // QT_CONFIG(statustip)
        self.rig_name_label.setText(QCoreApplication.translate("MainSettings", u"Rig Name", None))
    # retranslateUi

