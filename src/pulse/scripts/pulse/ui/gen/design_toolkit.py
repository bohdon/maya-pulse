# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'design_toolkit.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_DesignToolkit(object):
    def setupUi(self, DesignToolkit):
        if not DesignToolkit.objectName():
            DesignToolkit.setObjectName(u"DesignToolkit")
        DesignToolkit.resize(300, 264)
        DesignToolkit.setMinimumSize(QSize(300, 0))
        self.verticalLayout = QVBoxLayout(DesignToolkit)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(DesignToolkit)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setObjectName(u"scroll_area_widget")
        self.scroll_area_widget.setGeometry(QRect(0, 0, 298, 262))
        self.verticalLayout_3 = QVBoxLayout(self.scroll_area_widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(9, 9, 9, 9)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(8)
        self.main_layout.setObjectName(u"main_layout")

        self.verticalLayout_3.addLayout(self.main_layout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_widget)

        self.verticalLayout.addWidget(self.scroll_area)


        self.retranslateUi(DesignToolkit)

        QMetaObject.connectSlotsByName(DesignToolkit)
    # setupUi

    def retranslateUi(self, DesignToolkit):
        DesignToolkit.setWindowTitle(QCoreApplication.translate("DesignToolkit", u"Design Toolkit", None))
    # retranslateUi

