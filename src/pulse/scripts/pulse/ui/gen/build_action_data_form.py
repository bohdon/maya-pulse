# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'build_action_data_form.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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
from ...vendor.Qt.QtWidgets import (QApplication, QFrame, QHBoxLayout, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget)
from . import icons_rc

class Ui_BuildActionDataForm(object):
    def setupUi(self, BuildActionDataForm):
        if not BuildActionDataForm.objectName():
            BuildActionDataForm.setObjectName(u"BuildActionDataForm")
        BuildActionDataForm.resize(386, 26)
        self.main_layout = QVBoxLayout(BuildActionDataForm)
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(BuildActionDataForm)
        self.frame.setObjectName(u"frame")
        self.h_layout = QHBoxLayout(self.frame)
        self.h_layout.setObjectName(u"h_layout")
        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.remove_btn = QToolButton(self.frame)
        self.remove_btn.setObjectName(u"remove_btn")
        self.remove_btn.setMaximumSize(QSize(26, 26))
        self.remove_btn.setStyleSheet(u"margin: 3px; padding: 3px;")
        icon = QIcon()
        icon.addFile(u":/icon/xmark.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.remove_btn.setIcon(icon)

        self.h_layout.addWidget(self.remove_btn, 0, Qt.AlignTop)

        self.attr_list_layout = QVBoxLayout()
        self.attr_list_layout.setSpacing(0)
        self.attr_list_layout.setObjectName(u"attr_list_layout")

        self.h_layout.addLayout(self.attr_list_layout)


        self.main_layout.addWidget(self.frame)


        self.retranslateUi(BuildActionDataForm)

        QMetaObject.connectSlotsByName(BuildActionDataForm)
    # setupUi

    def retranslateUi(self, BuildActionDataForm):
        BuildActionDataForm.setWindowTitle(QCoreApplication.translate("BuildActionDataForm", u"Build Action Data Form", None))
        self.frame.setProperty("cssClasses", QCoreApplication.translate("BuildActionDataForm", u"block", None))
#if QT_CONFIG(statustip)
        self.remove_btn.setStatusTip(QCoreApplication.translate("BuildActionDataForm", u"Remove this variant.", None))
#endif // QT_CONFIG(statustip)
    # retranslateUi

