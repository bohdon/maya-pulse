# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_joints.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QGridLayout, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget)

class Ui_JointsDesignPanel(object):
    def setupUi(self, JointsDesignPanel):
        if not JointsDesignPanel.objectName():
            JointsDesignPanel.setObjectName(u"JointsDesignPanel")
        JointsDesignPanel.resize(294, 112)
        self.verticalLayout = QVBoxLayout(JointsDesignPanel)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.insert_joint_tool_btn = QPushButton(JointsDesignPanel)
        self.insert_joint_tool_btn.setObjectName(u"insert_joint_tool_btn")

        self.gridLayout.addWidget(self.insert_joint_tool_btn, 0, 1, 1, 1)

        self.insert_btn = QPushButton(JointsDesignPanel)
        self.insert_btn.setObjectName(u"insert_btn")

        self.gridLayout.addWidget(self.insert_btn, 1, 1, 1, 1)

        self.center_btn = QPushButton(JointsDesignPanel)
        self.center_btn.setObjectName(u"center_btn")

        self.gridLayout.addWidget(self.center_btn, 1, 0, 1, 1)

        self.joint_tool_btn = QPushButton(JointsDesignPanel)
        self.joint_tool_btn.setObjectName(u"joint_tool_btn")

        self.gridLayout.addWidget(self.joint_tool_btn, 0, 0, 1, 1)

        self.freeze_btn = QPushButton(JointsDesignPanel)
        self.freeze_btn.setObjectName(u"freeze_btn")

        self.gridLayout.addWidget(self.freeze_btn, 2, 0, 1, 1)

        self.disable_ssc_btn = QPushButton(JointsDesignPanel)
        self.disable_ssc_btn.setObjectName(u"disable_ssc_btn")

        self.gridLayout.addWidget(self.disable_ssc_btn, 2, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.mark_end_joints_btn = QPushButton(JointsDesignPanel)
        self.mark_end_joints_btn.setObjectName(u"mark_end_joints_btn")

        self.verticalLayout.addWidget(self.mark_end_joints_btn)


        self.retranslateUi(JointsDesignPanel)

        QMetaObject.connectSlotsByName(JointsDesignPanel)
    # setupUi

    def retranslateUi(self, JointsDesignPanel):
        JointsDesignPanel.setWindowTitle(QCoreApplication.translate("JointsDesignPanel", u"Form", None))
        self.insert_joint_tool_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Insert Joint Tool", None))
        self.insert_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Insert", None))
        self.center_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Center", None))
        self.joint_tool_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Joint Tool", None))
#if QT_CONFIG(statustip)
        self.freeze_btn.setStatusTip(QCoreApplication.translate("JointsDesignPanel", u"Freeze rotates and scales on the selected joint hierarchies.", None))
#endif // QT_CONFIG(statustip)
        self.freeze_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Freeze Joints", None))
        self.disable_ssc_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Disable Scale Compensate", None))
#if QT_CONFIG(statustip)
        self.mark_end_joints_btn.setStatusTip(QCoreApplication.translate("JointsDesignPanel", u"Find all end joints in the selected hierarchy and rename and color them.", None))
#endif // QT_CONFIG(statustip)
        self.mark_end_joints_btn.setText(QCoreApplication.translate("JointsDesignPanel", u"Mark End Joints", None))
    # retranslateUi

