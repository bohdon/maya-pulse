# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_settings.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QCheckBox, QFormLayout, QLabel,
    QLineEdit, QSizePolicy, QSpacerItem, QTabWidget,
    QVBoxLayout, QWidget)
from . import icons_rc

class Ui_MainSettings(object):
    def setupUi(self, MainSettings):
        if not MainSettings.objectName():
            MainSettings.setObjectName(u"MainSettings")
        MainSettings.resize(600, 400)
        MainSettings.setMinimumSize(QSize(600, 400))
        self.verticalLayout = QVBoxLayout(MainSettings)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(MainSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.blueprint_tab = QWidget()
        self.blueprint_tab.setObjectName(u"blueprint_tab")
        self.verticalLayout_2 = QVBoxLayout(self.blueprint_tab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.formLayout_2 = QFormLayout()
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setVerticalSpacing(2)
        self.label_5 = QLabel(self.blueprint_tab)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(0, QFormLayout.SpanningRole, self.label_5)

        self.file_path_label = QLabel(self.blueprint_tab)
        self.file_path_label.setObjectName(u"file_path_label")
        self.file_path_label.setMinimumSize(QSize(120, 20))
        self.file_path_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.LabelRole, self.file_path_label)

        self.file_path_text_label = QLabel(self.blueprint_tab)
        self.file_path_text_label.setObjectName(u"file_path_text_label")
        self.file_path_text_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.formLayout_2.setWidget(1, QFormLayout.FieldRole, self.file_path_text_label)

        self.verticalSpacer_4 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.formLayout_2.setItem(2, QFormLayout.SpanningRole, self.verticalSpacer_4)

        self.label_2 = QLabel(self.blueprint_tab)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(3, QFormLayout.SpanningRole, self.label_2)

        self.rig_name_label = QLabel(self.blueprint_tab)
        self.rig_name_label.setObjectName(u"rig_name_label")
        self.rig_name_label.setMinimumSize(QSize(120, 0))
        self.rig_name_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(4, QFormLayout.LabelRole, self.rig_name_label)

        self.rig_name_edit = QLineEdit(self.blueprint_tab)
        self.rig_name_edit.setObjectName(u"rig_name_edit")

        self.formLayout_2.setWidget(4, QFormLayout.FieldRole, self.rig_name_edit)

        self.rig_node_fmt_label = QLabel(self.blueprint_tab)
        self.rig_node_fmt_label.setObjectName(u"rig_node_fmt_label")
        self.rig_node_fmt_label.setMinimumSize(QSize(120, 0))
        self.rig_node_fmt_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(5, QFormLayout.LabelRole, self.rig_node_fmt_label)

        self.rig_node_fmt_edit = QLineEdit(self.blueprint_tab)
        self.rig_node_fmt_edit.setObjectName(u"rig_node_fmt_edit")

        self.formLayout_2.setWidget(5, QFormLayout.FieldRole, self.rig_node_fmt_edit)

        self.debug_build_label = QLabel(self.blueprint_tab)
        self.debug_build_label.setObjectName(u"debug_build_label")
        self.debug_build_label.setMinimumSize(QSize(120, 0))
        self.debug_build_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_2.setWidget(6, QFormLayout.LabelRole, self.debug_build_label)

        self.debug_build_check = QCheckBox(self.blueprint_tab)
        self.debug_build_check.setObjectName(u"debug_build_check")
        self.debug_build_check.setMinimumSize(QSize(0, 20))

        self.formLayout_2.setWidget(6, QFormLayout.FieldRole, self.debug_build_check)


        self.verticalLayout_2.addLayout(self.formLayout_2)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.blueprint_help_label = QLabel(self.blueprint_tab)
        self.blueprint_help_label.setObjectName(u"blueprint_help_label")

        self.verticalLayout_2.addWidget(self.blueprint_help_label)

        self.tabWidget.addTab(self.blueprint_tab, "")
        self.global_tab = QWidget()
        self.global_tab.setObjectName(u"global_tab")
        self.verticalLayout_3 = QVBoxLayout(self.global_tab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setVerticalSpacing(2)
        self.label_4 = QLabel(self.global_tab)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_3.setWidget(0, QFormLayout.SpanningRole, self.label_4)

        self.config_file_form_label = QLabel(self.global_tab)
        self.config_file_form_label.setObjectName(u"config_file_form_label")
        self.config_file_form_label.setMinimumSize(QSize(120, 20))
        self.config_file_form_label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.config_file_form_label)

        self.config_file_path_label = QLabel(self.global_tab)
        self.config_file_path_label.setObjectName(u"config_file_path_label")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.config_file_path_label.sizePolicy().hasHeightForWidth())
        self.config_file_path_label.setSizePolicy(sizePolicy)
        self.config_file_path_label.setMinimumSize(QSize(20, 0))
        self.config_file_path_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse|Qt.TextSelectableByMouse)

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.config_file_path_label)

        self.verticalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.formLayout_3.setItem(2, QFormLayout.SpanningRole, self.verticalSpacer_3)

        self.label_3 = QLabel(self.global_tab)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_3.setWidget(3, QFormLayout.SpanningRole, self.label_3)

        self.action_pkgs_layout = QVBoxLayout()
        self.action_pkgs_layout.setObjectName(u"action_pkgs_layout")

        self.formLayout_3.setLayout(4, QFormLayout.SpanningRole, self.action_pkgs_layout)


        self.verticalLayout_3.addLayout(self.formLayout_3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)

        self.blueprint_help_label_2 = QLabel(self.global_tab)
        self.blueprint_help_label_2.setObjectName(u"blueprint_help_label_2")

        self.verticalLayout_3.addWidget(self.blueprint_help_label_2)

        self.tabWidget.addTab(self.global_tab, "")

        self.verticalLayout.addWidget(self.tabWidget)


        self.retranslateUi(MainSettings)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainSettings)
    # setupUi

    def retranslateUi(self, MainSettings):
        MainSettings.setWindowTitle(QCoreApplication.translate("MainSettings", u"Pulse Settings", None))
        self.label_5.setText(QCoreApplication.translate("MainSettings", u"File", None))
        self.label_5.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
#if QT_CONFIG(statustip)
        self.file_path_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The path to the currently open blueprint.", None))
#endif // QT_CONFIG(statustip)
        self.file_path_label.setText(QCoreApplication.translate("MainSettings", u"File Path", None))
        self.file_path_text_label.setText(QCoreApplication.translate("MainSettings", u"<File Path>", None))
        self.label_2.setText(QCoreApplication.translate("MainSettings", u"Settings", None))
        self.label_2.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
#if QT_CONFIG(statustip)
        self.rig_name_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The name of the rig. Used to name the core hierarchy nodes and can be used by actions as well.", None))
#endif // QT_CONFIG(statustip)
        self.rig_name_label.setText(QCoreApplication.translate("MainSettings", u"Rig Name", None))
#if QT_CONFIG(statustip)
        self.rig_node_fmt_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The naming format to use for the parent rig node. Can use any settings key, such as {rigName}.", None))
#endif // QT_CONFIG(statustip)
        self.rig_node_fmt_label.setText(QCoreApplication.translate("MainSettings", u"Rig Node Name", None))
#if QT_CONFIG(statustip)
        self.debug_build_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The naming format to use for the parent rig node. Can use any settings key, such as {rigName}.", None))
#endif // QT_CONFIG(statustip)
        self.debug_build_label.setText(QCoreApplication.translate("MainSettings", u"Debug Build", None))
        self.debug_build_check.setText("")
        self.blueprint_help_label.setText(QCoreApplication.translate("MainSettings", u"Settings for the current blueprint.", None))
        self.blueprint_help_label.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"help", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.blueprint_tab), QCoreApplication.translate("MainSettings", u"Blueprint", None))
        self.label_4.setText(QCoreApplication.translate("MainSettings", u"Config", None))
        self.label_4.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
#if QT_CONFIG(statustip)
        self.config_file_form_label.setStatusTip(QCoreApplication.translate("MainSettings", u"The global config that affects overall settings and behavior.", None))
#endif // QT_CONFIG(statustip)
        self.config_file_form_label.setText(QCoreApplication.translate("MainSettings", u"Config File", None))
        self.config_file_path_label.setText(QCoreApplication.translate("MainSettings", u"<File Path>", None))
        self.label_3.setText(QCoreApplication.translate("MainSettings", u"Action Packages", None))
        self.label_3.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"section-title", None))
        self.blueprint_help_label_2.setText(QCoreApplication.translate("MainSettings", u"General settings that affect all Blueprints.", None))
        self.blueprint_help_label_2.setProperty("cssClasses", QCoreApplication.translate("MainSettings", u"help", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.global_tab), QCoreApplication.translate("MainSettings", u"General", None))
    # retranslateUi

