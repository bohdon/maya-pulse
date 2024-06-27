# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_editor.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QSizePolicy, QVBoxLayout, QWidget)

class Ui_MainEditor(object):
    def setupUi(self, MainEditor):
        if not MainEditor.objectName():
            MainEditor.setObjectName(u"MainEditor")
        MainEditor.resize(320, 239)
        MainEditor.setMinimumSize(QSize(320, 0))
        self.verticalLayout = QVBoxLayout(MainEditor)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName(u"main_layout")
        self.main_layout.setContentsMargins(-1, 6, -1, -1)
        self.toolbar_layout = QVBoxLayout()
        self.toolbar_layout.setObjectName(u"toolbar_layout")

        self.main_layout.addLayout(self.toolbar_layout)

        self.action_tree_layout = QVBoxLayout()
        self.action_tree_layout.setObjectName(u"action_tree_layout")

        self.main_layout.addLayout(self.action_tree_layout)

        self.main_layout.setStretch(1, 1)

        self.verticalLayout.addLayout(self.main_layout)


        self.retranslateUi(MainEditor)

        QMetaObject.connectSlotsByName(MainEditor)
    # setupUi

    def retranslateUi(self, MainEditor):
        MainEditor.setWindowTitle(QCoreApplication.translate("MainEditor", u"Main Editor", None))
    # retranslateUi

