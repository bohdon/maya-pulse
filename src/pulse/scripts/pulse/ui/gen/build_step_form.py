# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_step_form.ui'
##
## Created by: Qt User Interface Compiler version 6.7.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from ...vendor.Qt.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from ...vendor.Qt.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from ...vendor.Qt.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QSizePolicy, QToolButton, QVBoxLayout, QWidget)

from ..action_editor.build_step_notifications import BuildStepNotifications
from . import icons_rc

class Ui_BuildStepForm(object):
    def setupUi(self, BuildStepForm):
        if not BuildStepForm.objectName():
            BuildStepForm.setObjectName(u"BuildStepForm")
        BuildStepForm.resize(363, 94)
        self.verticalLayout = QVBoxLayout(BuildStepForm)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.header_frame = QFrame(BuildStepForm)
        self.header_frame.setObjectName(u"header_frame")
        self.header_frame.setFrameShape(QFrame.StyledPanel)
        self.header_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.header_frame)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(3, 3, 3, 3)
        self.toggle_enable_btn = QToolButton(self.header_frame)
        self.toggle_enable_btn.setObjectName(u"toggle_enable_btn")
        icon = QIcon()
        icon.addFile(u":/icon/step_action.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toggle_enable_btn.setIcon(icon)

        self.horizontalLayout.addWidget(self.toggle_enable_btn, 0, Qt.AlignTop)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.display_name_label = QLabel(self.header_frame)
        self.display_name_label.setObjectName(u"display_name_label")
        font = QFont()
        font.setBold(True)
        self.display_name_label.setFont(font)

        self.verticalLayout_2.addWidget(self.display_name_label)

        self.description_label = QLabel(self.header_frame)
        self.description_label.setObjectName(u"description_label")
        self.description_label.setWordWrap(True)

        self.verticalLayout_2.addWidget(self.description_label)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.edit_source_btn = QToolButton(self.header_frame)
        self.edit_source_btn.setObjectName(u"edit_source_btn")
        icon1 = QIcon()
        icon1.addFile(u":/icon/file_pen.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.edit_source_btn.setIcon(icon1)

        self.horizontalLayout.addWidget(self.edit_source_btn, 0, Qt.AlignTop)


        self.verticalLayout.addWidget(self.header_frame)

        self.notifications = BuildStepNotifications(BuildStepForm)
        self.notifications.setObjectName(u"notifications")

        self.verticalLayout.addWidget(self.notifications)


        self.retranslateUi(BuildStepForm)

        QMetaObject.connectSlotsByName(BuildStepForm)
    # setupUi

    def retranslateUi(self, BuildStepForm):
        BuildStepForm.setWindowTitle(QCoreApplication.translate("BuildStepForm", u"Build Step Form", None))
        self.header_frame.setProperty("cssClasses", QCoreApplication.translate("BuildStepForm", u"block", None))
#if QT_CONFIG(statustip)
        self.toggle_enable_btn.setStatusTip(QCoreApplication.translate("BuildStepForm", u"Edit this action's python script.", None))
#endif // QT_CONFIG(statustip)
        self.display_name_label.setText(QCoreApplication.translate("BuildStepForm", u"{Display Name}", None))
        self.display_name_label.setProperty("cssClasses", "")
        self.description_label.setText(QCoreApplication.translate("BuildStepForm", u"{Description}", None))
        self.description_label.setProperty("cssClasses", QCoreApplication.translate("BuildStepForm", u"help", None))
#if QT_CONFIG(statustip)
        self.edit_source_btn.setStatusTip(QCoreApplication.translate("BuildStepForm", u"Edit this action's python script.", None))
#endif // QT_CONFIG(statustip)
    # retranslateUi

