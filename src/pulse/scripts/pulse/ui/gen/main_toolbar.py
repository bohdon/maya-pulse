# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_toolbar.ui'
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
    QPushButton, QSizePolicy, QStackedWidget, QVBoxLayout,
    QWidget)
from . import icons_rc

class Ui_MainToolbar(object):
    def setupUi(self, MainToolbar):
        if not MainToolbar.objectName():
            MainToolbar.setObjectName(u"MainToolbar")
        MainToolbar.resize(431, 158)
        self.verticalLayout_5 = QVBoxLayout(MainToolbar)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.main_stack = QStackedWidget(MainToolbar)
        self.main_stack.setObjectName(u"main_stack")
        self.new_page = QWidget()
        self.new_page.setObjectName(u"new_page")
        self.verticalLayout_4 = QVBoxLayout(self.new_page)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.new_blueprint_btn = QPushButton(self.new_page)
        self.new_blueprint_btn.setObjectName(u"new_blueprint_btn")

        self.verticalLayout_4.addWidget(self.new_blueprint_btn)

        self.main_stack.addWidget(self.new_page)
        self.opened_page = QWidget()
        self.opened_page.setObjectName(u"opened_page")
        self.verticalLayout = QVBoxLayout(self.opened_page)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.mode_frame = QFrame(self.opened_page)
        self.mode_frame.setObjectName(u"mode_frame")
        self.mode_frame.setFrameShape(QFrame.StyledPanel)
        self.mode_frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.mode_frame)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.blueprint_file_name_label = QLabel(self.mode_frame)
        self.blueprint_file_name_label.setObjectName(u"blueprint_file_name_label")

        self.verticalLayout_3.addWidget(self.blueprint_file_name_label)

        self.rig_name_label = QLabel(self.mode_frame)
        self.rig_name_label.setObjectName(u"rig_name_label")

        self.verticalLayout_3.addWidget(self.rig_name_label)


        self.horizontalLayout_3.addLayout(self.verticalLayout_3)

        self.blueprint_mode_label = QLabel(self.mode_frame)
        self.blueprint_mode_label.setObjectName(u"blueprint_mode_label")

        self.horizontalLayout_3.addWidget(self.blueprint_mode_label)

        self.label_2 = QLabel(self.mode_frame)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setEnabled(False)

        self.horizontalLayout_3.addWidget(self.label_2)

        self.rig_mode_label = QLabel(self.mode_frame)
        self.rig_mode_label.setObjectName(u"rig_mode_label")

        self.horizontalLayout_3.addWidget(self.rig_mode_label)

        self.horizontalLayout_3.setStretch(0, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout_3)

        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setObjectName(u"buttons_layout")
        self.validate_btn = QPushButton(self.mode_frame)
        self.validate_btn.setObjectName(u"validate_btn")
        self.validate_btn.setMinimumSize(QSize(80, 0))
        icon = QIcon()
        icon.addFile(u":/icon/validate.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.validate_btn.setIcon(icon)
        self.validate_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.validate_btn)

        self.build_btn = QPushButton(self.mode_frame)
        self.build_btn.setObjectName(u"build_btn")
        self.build_btn.setMinimumSize(QSize(80, 0))
        icon1 = QIcon()
        icon1.addFile(u":/icon/build.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.build_btn.setIcon(icon1)
        self.build_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.build_btn)

        self.open_blueprint_btn = QPushButton(self.mode_frame)
        self.open_blueprint_btn.setObjectName(u"open_blueprint_btn")
        icon2 = QIcon()
        icon2.addFile(u":/icon/angle_left.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.open_blueprint_btn.setIcon(icon2)
        self.open_blueprint_btn.setIconSize(QSize(14, 14))

        self.buttons_layout.addWidget(self.open_blueprint_btn)


        self.verticalLayout_2.addLayout(self.buttons_layout)

        self.interactive_build_frame = QFrame(self.mode_frame)
        self.interactive_build_frame.setObjectName(u"interactive_build_frame")
        self.interactive_build_frame.setFrameShape(QFrame.StyledPanel)
        self.interactive_build_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.interactive_build_frame)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.interactive_next_btn = QPushButton(self.interactive_build_frame)
        self.interactive_next_btn.setObjectName(u"interactive_next_btn")
        self.interactive_next_btn.setMinimumSize(QSize(80, 0))
        icon3 = QIcon()
        icon3.addFile(u":/icon/forward_step.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.interactive_next_btn.setIcon(icon3)
        self.interactive_next_btn.setIconSize(QSize(14, 14))

        self.horizontalLayout_2.addWidget(self.interactive_next_btn)

        self.interactive_next_step_btn = QPushButton(self.interactive_build_frame)
        self.interactive_next_step_btn.setObjectName(u"interactive_next_step_btn")
        self.interactive_next_step_btn.setMinimumSize(QSize(80, 0))
        self.interactive_next_step_btn.setIcon(icon3)
        self.interactive_next_step_btn.setIconSize(QSize(14, 14))

        self.horizontalLayout_2.addWidget(self.interactive_next_step_btn)

        self.interactive_continue_btn = QPushButton(self.interactive_build_frame)
        self.interactive_continue_btn.setObjectName(u"interactive_continue_btn")
        self.interactive_continue_btn.setMinimumSize(QSize(80, 0))
        self.interactive_continue_btn.setIcon(icon1)
        self.interactive_continue_btn.setIconSize(QSize(14, 14))

        self.horizontalLayout_2.addWidget(self.interactive_continue_btn)


        self.verticalLayout_2.addWidget(self.interactive_build_frame)


        self.verticalLayout.addWidget(self.mode_frame)

        self.main_stack.addWidget(self.opened_page)

        self.verticalLayout_5.addWidget(self.main_stack)

        self.toolbar_frame = QFrame(MainToolbar)
        self.toolbar_frame.setObjectName(u"toolbar_frame")
        self.toolbar_frame.setFrameShape(QFrame.StyledPanel)
        self.toolbar_frame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout = QHBoxLayout(self.toolbar_frame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setObjectName(u"toolbar_layout")
        self.settings_btn = QPushButton(self.toolbar_frame)
        self.settings_btn.setObjectName(u"settings_btn")
        icon4 = QIcon()
        icon4.addFile(u":/icon/gear.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.settings_btn.setIcon(icon4)

        self.toolbar_layout.addWidget(self.settings_btn)

        self.design_toolkit_btn = QPushButton(self.toolbar_frame)
        self.design_toolkit_btn.setObjectName(u"design_toolkit_btn")
        icon5 = QIcon()
        icon5.addFile(u":/icon/design_toolkit.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.design_toolkit_btn.setIcon(icon5)

        self.toolbar_layout.addWidget(self.design_toolkit_btn)

        self.action_editor_btn = QPushButton(self.toolbar_frame)
        self.action_editor_btn.setObjectName(u"action_editor_btn")
        icon6 = QIcon()
        icon6.addFile(u":/icon/action_editor.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.action_editor_btn.setIcon(icon6)

        self.toolbar_layout.addWidget(self.action_editor_btn)


        self.horizontalLayout.addLayout(self.toolbar_layout)


        self.verticalLayout_5.addWidget(self.toolbar_frame)


        self.retranslateUi(MainToolbar)

        self.main_stack.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainToolbar)
    # setupUi

    def retranslateUi(self, MainToolbar):
        MainToolbar.setWindowTitle(QCoreApplication.translate("MainToolbar", u"Main Toolbar", None))
        self.new_blueprint_btn.setText(QCoreApplication.translate("MainToolbar", u"New Blueprint", None))
        self.blueprint_file_name_label.setText(QCoreApplication.translate("MainToolbar", u"<Blueprint File Name>", None))
        self.blueprint_file_name_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"subtitle", None))
        self.rig_name_label.setText(QCoreApplication.translate("MainToolbar", u"<Rig Name>", None))
        self.rig_name_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"help", None))
        self.blueprint_mode_label.setText(QCoreApplication.translate("MainToolbar", u"Blueprint", None))
        self.blueprint_mode_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
        self.label_2.setText(QCoreApplication.translate("MainToolbar", u"|", None))
        self.label_2.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
        self.rig_mode_label.setText(QCoreApplication.translate("MainToolbar", u"Rig", None))
        self.rig_mode_label.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"mode-title", None))
#if QT_CONFIG(statustip)
        self.validate_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Run validation on the blueprint and all actions.", None))
#endif // QT_CONFIG(statustip)
        self.validate_btn.setText(QCoreApplication.translate("MainToolbar", u" Validate", None))
#if QT_CONFIG(statustip)
        self.build_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Save the blueprint and scene and build the rig.", None))
#endif // QT_CONFIG(statustip)
        self.build_btn.setText(QCoreApplication.translate("MainToolbar", u" Build", None))
#if QT_CONFIG(statustip)
        self.open_blueprint_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Open the blueprint scene that built this rig.", None))
#endif // QT_CONFIG(statustip)
        self.open_blueprint_btn.setText(QCoreApplication.translate("MainToolbar", u" Open Blueprint", None))
#if QT_CONFIG(statustip)
        self.interactive_next_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Run the next action of the interactive build.", None))
#endif // QT_CONFIG(statustip)
        self.interactive_next_btn.setText(QCoreApplication.translate("MainToolbar", u" Next Action", None))
#if QT_CONFIG(statustip)
        self.interactive_next_step_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Skip to the next step of the interactive build.", None))
#endif // QT_CONFIG(statustip)
        self.interactive_next_step_btn.setText(QCoreApplication.translate("MainToolbar", u" Next Step", None))
#if QT_CONFIG(statustip)
        self.interactive_continue_btn.setStatusTip(QCoreApplication.translate("MainToolbar", u"Continue to the interactive build to the end.", None))
#endif // QT_CONFIG(statustip)
        self.interactive_continue_btn.setText(QCoreApplication.translate("MainToolbar", u" Continue", None))
        self.toolbar_frame.setProperty("cssClasses", QCoreApplication.translate("MainToolbar", u"toolbar", None))
        self.settings_btn.setText(QCoreApplication.translate("MainToolbar", u" Settings", None))
        self.design_toolkit_btn.setText(QCoreApplication.translate("MainToolbar", u" Design Toolkit", None))
        self.action_editor_btn.setText(QCoreApplication.translate("MainToolbar", u" Action Editor", None))
    # retranslateUi

