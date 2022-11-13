# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_step_form.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from ..action_editor.build_step_notifications import BuildStepNotifications

from  . import icons_rc

class Ui_BuildStepForm(object):
    def setupUi(self, BuildStepForm):
        if not BuildStepForm.objectName():
            BuildStepForm.setObjectName(u"BuildStepForm")
        BuildStepForm.resize(326, 51)
        self.verticalLayout = QVBoxLayout(BuildStepForm)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.header_hbox = QHBoxLayout()
        self.header_hbox.setSpacing(2)
        self.header_hbox.setObjectName(u"header_hbox")
        self.display_name_label = QLabel(BuildStepForm)
        self.display_name_label.setObjectName(u"display_name_label")

        self.header_hbox.addWidget(self.display_name_label)

        self.edit_source_btn = QToolButton(BuildStepForm)
        self.edit_source_btn.setObjectName(u"edit_source_btn")
        icon = QIcon()
        icon.addFile(u":/icon/file_pen.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.edit_source_btn.setIcon(icon)

        self.header_hbox.addWidget(self.edit_source_btn)


        self.verticalLayout.addLayout(self.header_hbox)

        self.notifications = BuildStepNotifications(BuildStepForm)
        self.notifications.setObjectName(u"notifications")

        self.verticalLayout.addWidget(self.notifications)


        self.retranslateUi(BuildStepForm)

        QMetaObject.connectSlotsByName(BuildStepForm)
    # setupUi

    def retranslateUi(self, BuildStepForm):
        BuildStepForm.setWindowTitle(QCoreApplication.translate("BuildStepForm", u"Build Step Form", None))
        self.display_name_label.setText(QCoreApplication.translate("BuildStepForm", u"{Display Name}", None))
        self.display_name_label.setProperty("cssClasses", QCoreApplication.translate("BuildStepForm", u"section-title", None))
#if QT_CONFIG(statustip)
        self.edit_source_btn.setStatusTip(QCoreApplication.translate("BuildStepForm", u"Edit this action's python script.", None))
#endif // QT_CONFIG(statustip)
    # retranslateUi

