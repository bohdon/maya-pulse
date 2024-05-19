# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_layout.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QGridLayout, QPushButton, QSizePolicy,
    QWidget)

class Ui_LayoutDesignPanel(object):
    def setupUi(self, LayoutDesignPanel):
        if not LayoutDesignPanel.objectName():
            LayoutDesignPanel.setObjectName(u"LayoutDesignPanel")
        LayoutDesignPanel.resize(326, 23)
        self.gridLayout = QGridLayout(LayoutDesignPanel)
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.snap_to_targets_btn = QPushButton(LayoutDesignPanel)
        self.snap_to_targets_btn.setObjectName(u"snap_to_targets_btn")

        self.gridLayout.addWidget(self.snap_to_targets_btn, 0, 0, 1, 1)

        self.link_editor_btn = QPushButton(LayoutDesignPanel)
        self.link_editor_btn.setObjectName(u"link_editor_btn")

        self.gridLayout.addWidget(self.link_editor_btn, 0, 1, 1, 1)


        self.retranslateUi(LayoutDesignPanel)

        QMetaObject.connectSlotsByName(LayoutDesignPanel)
    # setupUi

    def retranslateUi(self, LayoutDesignPanel):
        LayoutDesignPanel.setWindowTitle(QCoreApplication.translate("LayoutDesignPanel", u"Form", None))
#if QT_CONFIG(statustip)
        self.snap_to_targets_btn.setStatusTip(QCoreApplication.translate("LayoutDesignPanel", u"Snap controls and linked objects to their target positions.", None))
#endif // QT_CONFIG(statustip)
        self.snap_to_targets_btn.setText(QCoreApplication.translate("LayoutDesignPanel", u"Snap to Targets", None))
#if QT_CONFIG(statustip)
        self.link_editor_btn.setStatusTip(QCoreApplication.translate("LayoutDesignPanel", u"Open the Layout Link Editor for managing how nodes are connected to each other during blueprint design.", None))
#endif // QT_CONFIG(statustip)
        self.link_editor_btn.setText(QCoreApplication.translate("LayoutDesignPanel", u"Link Editor", None))
    # retranslateUi

