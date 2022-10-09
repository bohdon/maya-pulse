# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'quick_name_editor.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_QuickNameEditor(object):
    def setupUi(self, QuickNameEditor):
        if not QuickNameEditor.objectName():
            QuickNameEditor.setObjectName(u"QuickNameEditor")
        QuickNameEditor.resize(505, 281)
        self.verticalLayout_4 = QVBoxLayout(QuickNameEditor)
        self.verticalLayout_4.setSpacing(2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.set_name_btn = QPushButton(QuickNameEditor)
        self.set_name_btn.setObjectName(u"set_name_btn")

        self.verticalLayout_4.addWidget(self.set_name_btn)

        self.verticalSpacer_4 = QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.verticalLayout_4.addItem(self.verticalSpacer_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.prefixes_title = QLabel(QuickNameEditor)
        self.prefixes_title.setObjectName(u"prefixes_title")
        self.prefixes_title.setMinimumSize(QSize(60, 0))

        self.verticalLayout.addWidget(self.prefixes_title)

        self.prefixes_vbox = QVBoxLayout()
        self.prefixes_vbox.setSpacing(2)
        self.prefixes_vbox.setObjectName(u"prefixes_vbox")

        self.verticalLayout.addLayout(self.prefixes_vbox)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.keywords_title = QLabel(QuickNameEditor)
        self.keywords_title.setObjectName(u"keywords_title")

        self.verticalLayout_2.addWidget(self.keywords_title)

        self.keywords_vbox = QVBoxLayout()
        self.keywords_vbox.setSpacing(2)
        self.keywords_vbox.setObjectName(u"keywords_vbox")

        self.verticalLayout_2.addLayout(self.keywords_vbox)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.suffixes_title = QLabel(QuickNameEditor)
        self.suffixes_title.setObjectName(u"suffixes_title")
        self.suffixes_title.setMinimumSize(QSize(60, 0))

        self.verticalLayout_3.addWidget(self.suffixes_title)

        self.suffixes_vbox = QVBoxLayout()
        self.suffixes_vbox.setSpacing(2)
        self.suffixes_vbox.setObjectName(u"suffixes_vbox")

        self.verticalLayout_3.addLayout(self.suffixes_vbox)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_3)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout)

        self.help_label = QLabel(QuickNameEditor)
        self.help_label.setObjectName(u"help_label")

        self.verticalLayout_4.addWidget(self.help_label)

        self.verticalLayout_4.setStretch(2, 1)

        self.retranslateUi(QuickNameEditor)

        QMetaObject.connectSlotsByName(QuickNameEditor)
    # setupUi

    def retranslateUi(self, QuickNameEditor):
        QuickNameEditor.setWindowTitle(QCoreApplication.translate("QuickNameEditor", u"Form", None))
#if QT_CONFIG(statustip)
        self.set_name_btn.setStatusTip(QCoreApplication.translate("QuickNameEditor", u"The current constructed name. Click to rename the selected node(s).", None))
#endif // QT_CONFIG(statustip)
        self.set_name_btn.setText(QCoreApplication.translate("QuickNameEditor", u"*", None))
        self.set_name_btn.setProperty("cssClasses", QCoreApplication.translate("QuickNameEditor", u"large", None))
        self.prefixes_title.setText(QCoreApplication.translate("QuickNameEditor", u"Prefixes", None))
        self.prefixes_title.setProperty("cssClasses", QCoreApplication.translate("QuickNameEditor", u" section-title", None))
        self.keywords_title.setText(QCoreApplication.translate("QuickNameEditor", u"Keywords", None))
        self.keywords_title.setProperty("cssClasses", QCoreApplication.translate("QuickNameEditor", u" section-title", None))
        self.suffixes_title.setText(QCoreApplication.translate("QuickNameEditor", u"Suffixes", None))
        self.suffixes_title.setProperty("cssClasses", QCoreApplication.translate("QuickNameEditor", u" section-title", None))
        self.help_label.setText(QCoreApplication.translate("QuickNameEditor", u"Edit the blueprint config to modify naming keywords.", None))
        self.help_label.setProperty("cssClasses", QCoreApplication.translate("QuickNameEditor", u"help", None))
    # retranslateUi
