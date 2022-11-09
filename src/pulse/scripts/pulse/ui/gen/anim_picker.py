# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'anim_picker.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

from  . import icons_rc

class Ui_AnimPicker(object):
    def setupUi(self, AnimPicker):
        if not AnimPicker.objectName():
            AnimPicker.setObjectName(u"AnimPicker")
        AnimPicker.resize(564, 510)
        AnimPicker.setMinimumSize(QSize(200, 200))
        self.verticalLayout = QVBoxLayout(AnimPicker)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.header_frame = QFrame(AnimPicker)
        self.header_frame.setObjectName(u"header_frame")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.header_frame.sizePolicy().hasHeightForWidth())
        self.header_frame.setSizePolicy(sizePolicy)
        self.header_frame.setMinimumSize(QSize(0, 30))
        self.header_frame.setFrameShape(QFrame.StyledPanel)
        self.header_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.header_frame)
        self.horizontalLayout_2.setSpacing(4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(2, 2, 2, 2)
        self.refresh_btn = QToolButton(self.header_frame)
        self.refresh_btn.setObjectName(u"refresh_btn")
        icon = QIcon()
        icon.addFile(u":/icon/rotate_right.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.refresh_btn.setIcon(icon)

        self.horizontalLayout_2.addWidget(self.refresh_btn)

        self.picker_list_layout = QHBoxLayout()
        self.picker_list_layout.setObjectName(u"picker_list_layout")

        self.horizontalLayout_2.addLayout(self.picker_list_layout)

        self.new_btn = QToolButton(self.header_frame)
        self.new_btn.setObjectName(u"new_btn")
        icon1 = QIcon()
        icon1.addFile(u":/icon/plus.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.new_btn.setIcon(icon1)

        self.horizontalLayout_2.addWidget(self.new_btn)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.locked_label = QLabel(self.header_frame)
        self.locked_label.setObjectName(u"locked_label")

        self.horizontalLayout_2.addWidget(self.locked_label)

        self.toggle_lock_btn = QToolButton(self.header_frame)
        self.toggle_lock_btn.setObjectName(u"toggle_lock_btn")
        icon2 = QIcon()
        icon2.addFile(u":/icon/lock.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toggle_lock_btn.setIcon(icon2)

        self.horizontalLayout_2.addWidget(self.toggle_lock_btn)

        self.save_btn = QToolButton(self.header_frame)
        self.save_btn.setObjectName(u"save_btn")
        icon3 = QIcon()
        icon3.addFile(u":/icon/floppy_disk.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.save_btn.setIcon(icon3)

        self.horizontalLayout_2.addWidget(self.save_btn)


        self.verticalLayout.addWidget(self.header_frame)

        self.panel_layout = QVBoxLayout()
        self.panel_layout.setObjectName(u"panel_layout")

        self.verticalLayout.addLayout(self.panel_layout)

        self.footer_frame = QFrame(AnimPicker)
        self.footer_frame.setObjectName(u"footer_frame")
        sizePolicy.setHeightForWidth(self.footer_frame.sizePolicy().hasHeightForWidth())
        self.footer_frame.setSizePolicy(sizePolicy)
        self.footer_frame.setFrameShape(QFrame.StyledPanel)
        self.footer_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.footer_frame)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(2, 2, 2, 2)
        self.zoom_reset_btn = QToolButton(self.footer_frame)
        self.zoom_reset_btn.setObjectName(u"zoom_reset_btn")
        icon4 = QIcon()
        icon4.addFile(u":/icon/reset.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.zoom_reset_btn.setIcon(icon4)

        self.horizontalLayout.addWidget(self.zoom_reset_btn)

        self.zoom_label = QLabel(self.footer_frame)
        self.zoom_label.setObjectName(u"zoom_label")

        self.horizontalLayout.addWidget(self.zoom_label)


        self.verticalLayout.addWidget(self.footer_frame)


        self.retranslateUi(AnimPicker)

        QMetaObject.connectSlotsByName(AnimPicker)
    # setupUi

    def retranslateUi(self, AnimPicker):
        AnimPicker.setWindowTitle(QCoreApplication.translate("AnimPicker", u"Anim Picker", None))
#if QT_CONFIG(statustip)
        self.refresh_btn.setStatusTip(QCoreApplication.translate("AnimPicker", u"Refresh the available rigs.", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(statustip)
        self.new_btn.setStatusTip(QCoreApplication.translate("AnimPicker", u"Create a new picker for the selected node.", None))
#endif // QT_CONFIG(statustip)
        self.new_btn.setText(QCoreApplication.translate("AnimPicker", u"...", None))
        self.locked_label.setText(QCoreApplication.translate("AnimPicker", u"Locked", None))
        self.locked_label.setProperty("cssClasses", QCoreApplication.translate("AnimPicker", u"help", None))
#if QT_CONFIG(statustip)
        self.toggle_lock_btn.setStatusTip(QCoreApplication.translate("AnimPicker", u"Lock or unlock the picker for editing.", None))
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(statustip)
        self.zoom_reset_btn.setStatusTip(QCoreApplication.translate("AnimPicker", u"Reset the view to default.", None))
#endif // QT_CONFIG(statustip)
        self.zoom_reset_btn.setText("")
        self.zoom_label.setText(QCoreApplication.translate("AnimPicker", u"1.0", None))
        self.zoom_label.setProperty("cssClasses", QCoreApplication.translate("AnimPicker", u"help", None))
    # retranslateUi

