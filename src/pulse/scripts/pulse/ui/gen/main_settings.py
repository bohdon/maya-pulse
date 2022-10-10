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
        MainSettings.resize(350, 400)
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
        self.file_path_label.setMinimumSize(QSize(80, 0))
        self.file_path_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.file_path_label)

        self.file_path_hbox = QHBoxLayout()
        self.file_path_hbox.setObjectName(u"file_path_hbox")
        self.file_path_edit = QLineEdit(MainSettings)
        self.file_path_edit.setObjectName(u"file_path_edit")
        self.file_path_edit.setReadOnly(True)

        self.file_path_hbox.addWidget(self.file_path_edit)

        self.file_path_browse_btn = QToolButton(MainSettings)
        self.file_path_browse_btn.setObjectName(u"file_path_browse_btn")
        self.file_path_browse_btn.setEnabled(False)

        self.file_path_hbox.addWidget(self.file_path_browse_btn)


        self.formLayout_2.setLayout(0, QFormLayout.FieldRole, self.file_path_hbox)


        self.verticalLayout.addLayout(self.formLayout_2)

        self.blueprint_properties_title = QLabel(MainSettings)
        self.blueprint_properties_title.setObjectName(u"blueprint_properties_title")

        self.verticalLayout.addWidget(self.blueprint_properties_title)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setVerticalSpacing(2)
        self.rig_name_label = QLabel(MainSettings)
        self.rig_name_label.setObjectName(u"rig_name_label")
        self.rig_name_label.setMinimumSize(QSize(80, 0))
        self.rig_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.rig_name_label)

        self.rig_name_edit = QLineEdit(MainSettings)
        self.rig_name_edit.setObjectName(u"rig_name_edit")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.rig_name_edit)


        self.verticalLayout.addLayout(self.formLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.retranslateUi(MainSettings)

        QMetaObject.connectSlotsByName(MainSettings)
    # setupUi

    def retranslateUi(self, MainSettings):
        MainSettings.setWindowTitle(QCoreApplication.translate("MainSettings", u"Pulse Settings", None))
        self.blueprint_properties_title_2.setText(QCoreApplication.translate("MainSettings", u"Blueprint", None))
        self.blueprint_properties_title_2.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
        self.file_path_label.setText(QCoreApplication.translate("MainSettings", u"File Path", None))
#if QT_CONFIG(tooltip)
        self.file_path_browse_btn.setToolTip(QCoreApplication.translate("MainSettings", u"Custom blueprint file paths are not yet supported.", None))
#endif // QT_CONFIG(tooltip)
        self.file_path_browse_btn.setText(QCoreApplication.translate("MainSettings", u"...", None))
        self.blueprint_properties_title.setText(QCoreApplication.translate("MainSettings", u"Properties", None))
        self.blueprint_properties_title.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
        self.rig_name_label.setText(QCoreApplication.translate("MainSettings", u"Rig Name", None))
    # retranslateUi

