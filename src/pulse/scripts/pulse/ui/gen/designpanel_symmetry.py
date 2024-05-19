# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_symmetry.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_SymmetryDesignPanel(object):
    def setupUi(self, SymmetryDesignPanel):
        if not SymmetryDesignPanel.objectName():
            SymmetryDesignPanel.setObjectName(u"SymmetryDesignPanel")
        SymmetryDesignPanel.resize(271, 212)
        self.verticalLayout = QVBoxLayout(SymmetryDesignPanel)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.appearance_check = QCheckBox(SymmetryDesignPanel)
        self.appearance_check.setObjectName(u"appearance_check")

        self.gridLayout.addWidget(self.appearance_check, 1, 1, 1, 1)

        self.links_check = QCheckBox(SymmetryDesignPanel)
        self.links_check.setObjectName(u"links_check")

        self.gridLayout.addWidget(self.links_check, 3, 0, 1, 1)

        self.parenting_check = QCheckBox(SymmetryDesignPanel)
        self.parenting_check.setObjectName(u"parenting_check")

        self.gridLayout.addWidget(self.parenting_check, 2, 0, 1, 1)

        self.include_children_check = QCheckBox(SymmetryDesignPanel)
        self.include_children_check.setObjectName(u"include_children_check")

        self.gridLayout.addWidget(self.include_children_check, 5, 0, 1, 1)

        self.transforms_check = QCheckBox(SymmetryDesignPanel)
        self.transforms_check.setObjectName(u"transforms_check")

        self.gridLayout.addWidget(self.transforms_check, 1, 0, 1, 1)

        self.allow_create_check = QCheckBox(SymmetryDesignPanel)
        self.allow_create_check.setObjectName(u"allow_create_check")

        self.gridLayout.addWidget(self.allow_create_check, 5, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.verticalSpacer, 4, 0, 1, 1)

        self.curve_shapes_check = QCheckBox(SymmetryDesignPanel)
        self.curve_shapes_check.setObjectName(u"curve_shapes_check")

        self.gridLayout.addWidget(self.curve_shapes_check, 2, 1, 1, 1)

        self.axis_combo = QComboBox(SymmetryDesignPanel)
        self.axis_combo.addItem("")
        self.axis_combo.addItem("")
        self.axis_combo.addItem("")
        self.axis_combo.setObjectName(u"axis_combo")

        self.gridLayout.addWidget(self.axis_combo, 0, 0, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.unpair_btn = QPushButton(SymmetryDesignPanel)
        self.unpair_btn.setObjectName(u"unpair_btn")

        self.gridLayout_3.addWidget(self.unpair_btn, 1, 1, 1, 1)

        self.pair_btn = QPushButton(SymmetryDesignPanel)
        self.pair_btn.setObjectName(u"pair_btn")

        self.gridLayout_3.addWidget(self.pair_btn, 1, 0, 1, 1)

        self.mirror_btn = QPushButton(SymmetryDesignPanel)
        self.mirror_btn.setObjectName(u"mirror_btn")

        self.gridLayout_3.addWidget(self.mirror_btn, 0, 0, 1, 2)


        self.verticalLayout.addLayout(self.gridLayout_3)


        self.retranslateUi(SymmetryDesignPanel)

        QMetaObject.connectSlotsByName(SymmetryDesignPanel)
    # setupUi

    def retranslateUi(self, SymmetryDesignPanel):
        SymmetryDesignPanel.setWindowTitle(QCoreApplication.translate("SymmetryDesignPanel", u"Form", None))
#if QT_CONFIG(statustip)
        self.appearance_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror the name and color of the nodes.", None))
#endif // QT_CONFIG(statustip)
        self.appearance_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Appearance", None))
#if QT_CONFIG(statustip)
        self.links_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror the layout links of the nodes, allowing mirrored nodes to snap to their linked mirror nodes.", None))
#endif // QT_CONFIG(statustip)
        self.links_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Links", None))
#if QT_CONFIG(statustip)
        self.parenting_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror the parenting structure of the nodes.", None))
#endif // QT_CONFIG(statustip)
        self.parenting_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Parenting", None))
#if QT_CONFIG(statustip)
        self.include_children_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Recursively mirror the selected nodes and all of their children.", None))
#endif // QT_CONFIG(statustip)
        self.include_children_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Include Children", None))
#if QT_CONFIG(statustip)
        self.transforms_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror the transform matrices of the nodes.", None))
#endif // QT_CONFIG(statustip)
        self.transforms_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Transforms", None))
#if QT_CONFIG(statustip)
        self.allow_create_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Allow the creation of nodes when mirroring recursively.", None))
#endif // QT_CONFIG(statustip)
        self.allow_create_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Allow Node Creation", None))
#if QT_CONFIG(statustip)
        self.curve_shapes_check.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror curve shapes.", None))
#endif // QT_CONFIG(statustip)
        self.curve_shapes_check.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Curve Shapes", None))
        self.axis_combo.setItemText(0, QCoreApplication.translate("SymmetryDesignPanel", u"+/- X", None))
        self.axis_combo.setItemText(1, QCoreApplication.translate("SymmetryDesignPanel", u"+/- Y", None))
        self.axis_combo.setItemText(2, QCoreApplication.translate("SymmetryDesignPanel", u"+/- Z", None))

#if QT_CONFIG(tooltip)
        self.axis_combo.setToolTip(QCoreApplication.translate("SymmetryDesignPanel", u"The local axes to use when orienting.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.unpair_btn.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Unpair the selected node or nodes (can be many at once).", None))
#endif // QT_CONFIG(statustip)
        self.unpair_btn.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Unpair", None))
#if QT_CONFIG(statustip)
        self.pair_btn.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Pair the two selected nodes as mirroring counterparts.", None))
#endif // QT_CONFIG(statustip)
        self.pair_btn.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Pair", None))
#if QT_CONFIG(statustip)
        self.mirror_btn.setStatusTip(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror the selected nodes.", None))
#endif // QT_CONFIG(statustip)
        self.mirror_btn.setText(QCoreApplication.translate("SymmetryDesignPanel", u"Mirror", None))
    # retranslateUi

