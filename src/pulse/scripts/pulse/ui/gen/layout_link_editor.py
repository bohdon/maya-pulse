# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'layout_link_editor.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QSpacerItem,
    QToolButton, QVBoxLayout, QWidget)
from . import icons_rc

class Ui_LayoutLinkEditor(object):
    def setupUi(self, LayoutLinkEditor):
        if not LayoutLinkEditor.objectName():
            LayoutLinkEditor.setObjectName(u"LayoutLinkEditor")
        LayoutLinkEditor.resize(404, 415)
        self.verticalLayout = QVBoxLayout(LayoutLinkEditor)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.keep_offsets_check = QCheckBox(LayoutLinkEditor)
        self.keep_offsets_check.setObjectName(u"keep_offsets_check")

        self.verticalLayout.addWidget(self.keep_offsets_check)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.link_center_btn = QPushButton(LayoutLinkEditor)
        self.link_center_btn.setObjectName(u"link_center_btn")

        self.horizontalLayout.addWidget(self.link_center_btn)

        self.link_ikpole_btn = QPushButton(LayoutLinkEditor)
        self.link_ikpole_btn.setObjectName(u"link_ikpole_btn")

        self.horizontalLayout.addWidget(self.link_ikpole_btn)

        self.link_btn = QPushButton(LayoutLinkEditor)
        self.link_btn.setObjectName(u"link_btn")

        self.horizontalLayout.addWidget(self.link_btn)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(2)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.recreate_link_btn = QPushButton(LayoutLinkEditor)
        self.recreate_link_btn.setObjectName(u"recreate_link_btn")

        self.horizontalLayout_2.addWidget(self.recreate_link_btn)

        self.unlink_btn = QPushButton(LayoutLinkEditor)
        self.unlink_btn.setObjectName(u"unlink_btn")

        self.horizontalLayout_2.addWidget(self.unlink_btn)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.snap_to_targets_btn = QPushButton(LayoutLinkEditor)
        self.snap_to_targets_btn.setObjectName(u"snap_to_targets_btn")

        self.verticalLayout.addWidget(self.snap_to_targets_btn)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.section_title_links = QLabel(LayoutLinkEditor)
        self.section_title_links.setObjectName(u"section_title_links")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.section_title_links.sizePolicy().hasHeightForWidth())
        self.section_title_links.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.section_title_links)

        self.refresh_btn = QToolButton(LayoutLinkEditor)
        self.refresh_btn.setObjectName(u"refresh_btn")
        icon = QIcon()
        icon.addFile(u":/icon/rotate_right.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.refresh_btn.setIcon(icon)

        self.horizontalLayout_3.addWidget(self.refresh_btn)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.link_info_scroll_area = QScrollArea(LayoutLinkEditor)
        self.link_info_scroll_area.setObjectName(u"link_info_scroll_area")
        self.link_info_scroll_area.setWidgetResizable(True)
        self.link_info_scroll_area_widget = QWidget()
        self.link_info_scroll_area_widget.setObjectName(u"link_info_scroll_area_widget")
        self.link_info_scroll_area_widget.setGeometry(QRect(0, 0, 384, 249))
        self.verticalLayout_3 = QVBoxLayout(self.link_info_scroll_area_widget)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.link_info_vbox = QVBoxLayout()
        self.link_info_vbox.setSpacing(2)
        self.link_info_vbox.setObjectName(u"link_info_vbox")

        self.verticalLayout_3.addLayout(self.link_info_vbox)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_2)

        self.verticalLayout_3.setStretch(1, 1)
        self.link_info_scroll_area.setWidget(self.link_info_scroll_area_widget)

        self.verticalLayout.addWidget(self.link_info_scroll_area)


        self.retranslateUi(LayoutLinkEditor)

        QMetaObject.connectSlotsByName(LayoutLinkEditor)
    # setupUi

    def retranslateUi(self, LayoutLinkEditor):
        LayoutLinkEditor.setWindowTitle(QCoreApplication.translate("LayoutLinkEditor", u"Form", None))
#if QT_CONFIG(tooltip)
        self.keep_offsets_check.setToolTip(QCoreApplication.translate("LayoutLinkEditor", u"Store relative offsets when creating or updating links.", None))
#endif // QT_CONFIG(tooltip)
        self.keep_offsets_check.setText(QCoreApplication.translate("LayoutLinkEditor", u"Keep Offsets", None))
        self.link_center_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Link Centered", None))
        self.link_ikpole_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Link IK Pole", None))
        self.link_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Link", None))
#if QT_CONFIG(tooltip)
        self.recreate_link_btn.setToolTip(QCoreApplication.translate("LayoutLinkEditor", u"Recreate links for the selected nodes, updating or removing offsets.", None))
#endif // QT_CONFIG(tooltip)
        self.recreate_link_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Recreate Link", None))
        self.unlink_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Unlink", None))
        self.snap_to_targets_btn.setText(QCoreApplication.translate("LayoutLinkEditor", u"Snap to Targets", None))
        self.section_title_links.setText(QCoreApplication.translate("LayoutLinkEditor", u"Links", None))
        self.section_title_links.setProperty("cssClasses", QCoreApplication.translate("LayoutLinkEditor", u"section-title", None))
#if QT_CONFIG(tooltip)
        self.refresh_btn.setToolTip(QCoreApplication.translate("LayoutLinkEditor", u"Refresh the link data for the selected nodes.", None))
#endif // QT_CONFIG(tooltip)
        self.refresh_btn.setText("")
    # retranslateUi

