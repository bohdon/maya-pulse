# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'action_palette.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_ActionPalette(object):
    def setupUi(self, ActionPalette):
        if not ActionPalette.objectName():
            ActionPalette.setObjectName(u"ActionPalette")
        ActionPalette.resize(200, 300)
        ActionPalette.setMinimumSize(QSize(200, 0))
        self.verticalLayout = QVBoxLayout(ActionPalette)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.header_layout = QVBoxLayout()
        self.header_layout.setSpacing(6)
        self.header_layout.setObjectName(u"header_layout")
        self.header_layout.setContentsMargins(9, 9, 9, 9)
        self.search_edit = QLineEdit(ActionPalette)
        self.search_edit.setObjectName(u"search_edit")

        self.header_layout.addWidget(self.search_edit)

        self.group_btn = QPushButton(ActionPalette)
        self.group_btn.setObjectName(u"group_btn")

        self.header_layout.addWidget(self.group_btn)


        self.verticalLayout.addLayout(self.header_layout)

        self.scroll_area = QScrollArea(ActionPalette)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setObjectName(u"scroll_area_widget")
        self.scroll_area_widget.setGeometry(QRect(0, 0, 198, 229))
        self.verticalLayout_2 = QVBoxLayout(self.scroll_area_widget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setObjectName(u"actions_layout")

        self.verticalLayout_2.addLayout(self.actions_layout)

        self.scroll_area.setWidget(self.scroll_area_widget)

        self.verticalLayout.addWidget(self.scroll_area)


        self.retranslateUi(ActionPalette)

        QMetaObject.connectSlotsByName(ActionPalette)
    # setupUi

    def retranslateUi(self, ActionPalette):
        ActionPalette.setWindowTitle(QCoreApplication.translate("ActionPalette", u"Action Palette", None))
        self.search_edit.setPlaceholderText(QCoreApplication.translate("ActionPalette", u"Search...", None))
        self.group_btn.setText(QCoreApplication.translate("ActionPalette", u"Group", None))
    # retranslateUi

