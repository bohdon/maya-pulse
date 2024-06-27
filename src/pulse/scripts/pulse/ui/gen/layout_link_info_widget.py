# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout_link_info_widget.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QFormLayout, QFrame, QLabel,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_LayoutLinkInfoWidget(object):
    def setupUi(self, LayoutLinkInfoWidget):
        if not LayoutLinkInfoWidget.objectName():
            LayoutLinkInfoWidget.setObjectName(u"LayoutLinkInfoWidget")
        LayoutLinkInfoWidget.resize(285, 67)
        self.verticalLayout = QVBoxLayout(LayoutLinkInfoWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.frame = QFrame(LayoutLinkInfoWidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(4, 4, 4, 4)
        self.name_label = QLabel(self.frame)
        self.name_label.setObjectName(u"name_label")
        font = QFont()
        font.setBold(True)
        self.name_label.setFont(font)

        self.verticalLayout_2.addWidget(self.name_label)

        self.metadata_form = QFormLayout()
        self.metadata_form.setObjectName(u"metadata_form")
        self.metadata_form.setLabelAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)
        self.metadata_form.setHorizontalSpacing(12)
        self.metadata_form.setContentsMargins(20, -1, -1, -1)

        self.verticalLayout_2.addLayout(self.metadata_form)

        self.verticalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.frame)


        self.retranslateUi(LayoutLinkInfoWidget)

        QMetaObject.connectSlotsByName(LayoutLinkInfoWidget)
    # setupUi

    def retranslateUi(self, LayoutLinkInfoWidget):
        LayoutLinkInfoWidget.setWindowTitle(QCoreApplication.translate("LayoutLinkInfoWidget", u"Form", None))
        self.frame.setProperty("cssClasses", QCoreApplication.translate("LayoutLinkInfoWidget", u"block", None))
        self.name_label.setText(QCoreApplication.translate("LayoutLinkInfoWidget", u"<Node Name>", None))
    # retranslateUi

