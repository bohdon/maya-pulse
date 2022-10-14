# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'action_editor.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_ActionEditor(object):
    def setupUi(self, ActionEditor):
        if not ActionEditor.objectName():
            ActionEditor.setObjectName(u"ActionEditor")
        ActionEditor.resize(300, 200)
        ActionEditor.setMinimumSize(QSize(300, 200))
        self.verticalLayout_3 = QVBoxLayout(ActionEditor)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.main_stack = QStackedWidget(ActionEditor)
        self.main_stack.setObjectName(u"main_stack")
        self.help_page = QWidget()
        self.help_page.setObjectName(u"help_page")
        self.verticalLayout_2 = QVBoxLayout(self.help_page)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 50, 0, 0)
        self.help_label = QLabel(self.help_page)
        self.help_label.setObjectName(u"help_label")
        self.help_label.setAlignment(Qt.AlignHCenter|Qt.AlignTop)

        self.verticalLayout_2.addWidget(self.help_label)

        self.main_stack.addWidget(self.help_page)
        self.content_page = QWidget()
        self.content_page.setObjectName(u"content_page")
        self.verticalLayout_4 = QVBoxLayout(self.content_page)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.scroll_area = QScrollArea(self.content_page)
        self.scroll_area.setObjectName(u"scroll_area")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_widget = QWidget()
        self.scroll_area_widget.setObjectName(u"scroll_area_widget")
        self.scroll_area_widget.setGeometry(QRect(0, 0, 298, 198))
        self.verticalLayout = QVBoxLayout(self.scroll_area_widget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(14)
        self.items_layout.setObjectName(u"items_layout")

        self.verticalLayout.addLayout(self.items_layout)

        self.verticalSpacer = QSpacerItem(20, 514, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.scroll_area.setWidget(self.scroll_area_widget)

        self.verticalLayout_4.addWidget(self.scroll_area)

        self.main_stack.addWidget(self.content_page)

        self.verticalLayout_3.addWidget(self.main_stack)


        self.retranslateUi(ActionEditor)

        self.main_stack.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(ActionEditor)
    # setupUi

    def retranslateUi(self, ActionEditor):
        ActionEditor.setWindowTitle(QCoreApplication.translate("ActionEditor", u"Action Editor", None))
        self.help_label.setText(QCoreApplication.translate("ActionEditor", u"Select an action to view and edit its properties.", None))
        self.help_label.setProperty("cssClasses", QCoreApplication.translate("ActionEditor", u"help", None))
    # retranslateUi

