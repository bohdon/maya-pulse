# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_weights.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_WeightsDesignPanel(object):
    def setupUi(self, WeightsDesignPanel):
        if not WeightsDesignPanel.objectName():
            WeightsDesignPanel.setObjectName(u"WeightsDesignPanel")
        WeightsDesignPanel.resize(317, 23)
        self.verticalLayout = QVBoxLayout(WeightsDesignPanel)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.save_weights_btn = QPushButton(WeightsDesignPanel)
        self.save_weights_btn.setObjectName(u"save_weights_btn")

        self.verticalLayout.addWidget(self.save_weights_btn)


        self.retranslateUi(WeightsDesignPanel)

        QMetaObject.connectSlotsByName(WeightsDesignPanel)
    # setupUi

    def retranslateUi(self, WeightsDesignPanel):
        WeightsDesignPanel.setWindowTitle(QCoreApplication.translate("WeightsDesignPanel", u"Form", None))
#if QT_CONFIG(statustip)
        self.save_weights_btn.setStatusTip(QCoreApplication.translate("WeightsDesignPanel", u"Save all skin weights in the scene a weights file.", None))
#endif // QT_CONFIG(statustip)
        self.save_weights_btn.setText(QCoreApplication.translate("WeightsDesignPanel", u"Save Skin Weights", None))
    # retranslateUi

