# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_joint_orients.ui'
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
from ...vendor.Qt.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_JointOrientsDesignPanel(object):
    def setupUi(self, JointOrientsDesignPanel):
        if not JointOrientsDesignPanel.objectName():
            JointOrientsDesignPanel.setObjectName(u"JointOrientsDesignPanel")
        JointOrientsDesignPanel.resize(334, 264)
        self.verticalLayout = QVBoxLayout(JointOrientsDesignPanel)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.sync_axes_btn = QPushButton(JointOrientsDesignPanel)
        self.sync_axes_btn.setObjectName(u"sync_axes_btn")

        self.gridLayout_2.addWidget(self.sync_axes_btn, 1, 3, 1, 1)

        self.interactive_btn = QPushButton(JointOrientsDesignPanel)
        self.interactive_btn.setObjectName(u"interactive_btn")

        self.gridLayout_2.addWidget(self.interactive_btn, 1, 2, 1, 1)

        self.toggle_lras_btn = QPushButton(JointOrientsDesignPanel)
        self.toggle_lras_btn.setObjectName(u"toggle_lras_btn")

        self.gridLayout_2.addWidget(self.toggle_lras_btn, 0, 2, 1, 1)

        self.toggle_cb_attrs_btn = QPushButton(JointOrientsDesignPanel)
        self.toggle_cb_attrs_btn.setObjectName(u"toggle_cb_attrs_btn")

        self.gridLayout_2.addWidget(self.toggle_cb_attrs_btn, 0, 3, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.rot_x_neg_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_x_neg_btn.setObjectName(u"rot_x_neg_btn")
        self.rot_x_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_x_neg_btn)

        self.rot_x_pos_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_x_pos_btn.setObjectName(u"rot_x_pos_btn")
        self.rot_x_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_x_pos_btn)

        self.rot_y_neg_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_y_neg_btn.setObjectName(u"rot_y_neg_btn")
        self.rot_y_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_y_neg_btn)

        self.rot_y_pos_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_y_pos_btn.setObjectName(u"rot_y_pos_btn")
        self.rot_y_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_y_pos_btn)

        self.rot_z_neg_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_z_neg_btn.setObjectName(u"rot_z_neg_btn")
        self.rot_z_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_z_neg_btn)

        self.rot_z_pos_btn = QPushButton(JointOrientsDesignPanel)
        self.rot_z_pos_btn.setObjectName(u"rot_z_pos_btn")
        self.rot_z_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_z_pos_btn)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.verticalSpacer_2 = QSpacerItem(20, 12, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.preserve_children_check = QCheckBox(JointOrientsDesignPanel)
        self.preserve_children_check.setObjectName(u"preserve_children_check")

        self.gridLayout_3.addWidget(self.preserve_children_check, 1, 0, 1, 1)

        self.orient_to_world_btn = QPushButton(JointOrientsDesignPanel)
        self.orient_to_world_btn.setObjectName(u"orient_to_world_btn")

        self.gridLayout_3.addWidget(self.orient_to_world_btn, 5, 0, 1, 1)

        self.keep_axes_synced_check = QCheckBox(JointOrientsDesignPanel)
        self.keep_axes_synced_check.setObjectName(u"keep_axes_synced_check")

        self.gridLayout_3.addWidget(self.keep_axes_synced_check, 2, 1, 1, 1)

        self.orient_to_parent_btn = QPushButton(JointOrientsDesignPanel)
        self.orient_to_parent_btn.setObjectName(u"orient_to_parent_btn")

        self.gridLayout_3.addWidget(self.orient_to_parent_btn, 4, 1, 1, 1)

        self.include_children_check = QCheckBox(JointOrientsDesignPanel)
        self.include_children_check.setObjectName(u"include_children_check")

        self.gridLayout_3.addWidget(self.include_children_check, 2, 0, 1, 1)

        self.axis_order_combo = QComboBox(JointOrientsDesignPanel)
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.setObjectName(u"axis_order_combo")

        self.gridLayout_3.addWidget(self.axis_order_combo, 0, 0, 1, 1)

        self.verticalSpacer_3 = QSpacerItem(20, 6, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.gridLayout_3.addItem(self.verticalSpacer_3, 3, 0, 1, 2)

        self.orient_to_joint_btn = QPushButton(JointOrientsDesignPanel)
        self.orient_to_joint_btn.setObjectName(u"orient_to_joint_btn")

        self.gridLayout_3.addWidget(self.orient_to_joint_btn, 4, 0, 1, 1)

        self.orient_ik_joints_btn = QPushButton(JointOrientsDesignPanel)
        self.orient_ik_joints_btn.setObjectName(u"orient_ik_joints_btn")

        self.gridLayout_3.addWidget(self.orient_ik_joints_btn, 5, 1, 1, 1)

        self.preserve_shapes_check = QCheckBox(JointOrientsDesignPanel)
        self.preserve_shapes_check.setObjectName(u"preserve_shapes_check")

        self.gridLayout_3.addWidget(self.preserve_shapes_check, 1, 1, 1, 1)

        self.up_axis_combo = QComboBox(JointOrientsDesignPanel)
        self.up_axis_combo.addItem("")
        self.up_axis_combo.addItem("")
        self.up_axis_combo.addItem("")
        self.up_axis_combo.setObjectName(u"up_axis_combo")

        self.gridLayout_3.addWidget(self.up_axis_combo, 0, 1, 1, 1)

        self.fixup_btn = QPushButton(JointOrientsDesignPanel)
        self.fixup_btn.setObjectName(u"fixup_btn")

        self.gridLayout_3.addWidget(self.fixup_btn, 6, 0, 1, 2)


        self.verticalLayout.addLayout(self.gridLayout_3)


        self.retranslateUi(JointOrientsDesignPanel)

        QMetaObject.connectSlotsByName(JointOrientsDesignPanel)
    # setupUi

    def retranslateUi(self, JointOrientsDesignPanel):
        JointOrientsDesignPanel.setWindowTitle(QCoreApplication.translate("JointOrientsDesignPanel", u"Form", None))
#if QT_CONFIG(statustip)
        self.sync_axes_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Match the translate and scale axes of a joint to its orientation.", None))
#endif // QT_CONFIG(statustip)
        self.sync_axes_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Synx Axes", None))
        self.interactive_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Interactive", None))
#if QT_CONFIG(statustip)
        self.toggle_lras_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Toggle the display of local rotation axes.", None))
#endif // QT_CONFIG(statustip)
        self.toggle_lras_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Toggle LRAs", None))
#if QT_CONFIG(statustip)
        self.toggle_cb_attrs_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Toggle the display of orientation attributes in the channel box.", None))
#endif // QT_CONFIG(statustip)
        self.toggle_cb_attrs_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Toggle CB Attrs", None))
#if QT_CONFIG(statustip)
        self.rot_x_neg_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_x_neg_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"- X", None))
        self.rot_x_neg_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"x-axis", None))
#if QT_CONFIG(statustip)
        self.rot_x_pos_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_x_pos_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"+ X", None))
        self.rot_x_pos_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"x-axis", None))
#if QT_CONFIG(statustip)
        self.rot_y_neg_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_y_neg_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"- Y", None))
        self.rot_y_neg_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"y-axis", None))
#if QT_CONFIG(statustip)
        self.rot_y_pos_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_y_pos_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"+ Y", None))
        self.rot_y_pos_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"y-axis", None))
#if QT_CONFIG(statustip)
        self.rot_z_neg_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_z_neg_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"- Z", None))
        self.rot_z_neg_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"z-axis", None))
#if QT_CONFIG(statustip)
        self.rot_z_pos_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_z_pos_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"+ Z", None))
        self.rot_z_pos_btn.setProperty("cssClasses", QCoreApplication.translate("JointOrientsDesignPanel", u"z-axis", None))
#if QT_CONFIG(statustip)
        self.preserve_children_check.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Preseve the positions of child nodes when rotating or orienting a transform or joint.", None))
#endif // QT_CONFIG(statustip)
        self.preserve_children_check.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Preserve Children", None))
        self.orient_to_world_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Orient to World", None))
#if QT_CONFIG(statustip)
        self.keep_axes_synced_check.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"When enabled, joint translate and scale axes are automatically updated when the jointOrient and rotateAxis values are changed.", None))
#endif // QT_CONFIG(statustip)
        self.keep_axes_synced_check.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Keep Axes Synced", None))
        self.orient_to_parent_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Orient to Parent", None))
#if QT_CONFIG(statustip)
        self.include_children_check.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Update all child joints when using orient to joint or world.", None))
#endif // QT_CONFIG(statustip)
        self.include_children_check.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Include Children", None))
        self.axis_order_combo.setItemText(0, QCoreApplication.translate("JointOrientsDesignPanel", u"X forward, Y up", None))
        self.axis_order_combo.setItemText(1, QCoreApplication.translate("JointOrientsDesignPanel", u"X forward, Z up", None))
        self.axis_order_combo.setItemText(2, QCoreApplication.translate("JointOrientsDesignPanel", u"Y forward, X up", None))
        self.axis_order_combo.setItemText(3, QCoreApplication.translate("JointOrientsDesignPanel", u"Y forward, Z up", None))
        self.axis_order_combo.setItemText(4, QCoreApplication.translate("JointOrientsDesignPanel", u"Z forward, X up", None))
        self.axis_order_combo.setItemText(5, QCoreApplication.translate("JointOrientsDesignPanel", u"Z forward, Y up", None))

#if QT_CONFIG(tooltip)
        self.axis_order_combo.setToolTip(QCoreApplication.translate("JointOrientsDesignPanel", u"The local axes to use when orienting.", None))
#endif // QT_CONFIG(tooltip)
        self.orient_to_joint_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Orient to Joint", None))
        self.orient_ik_joints_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Orient IK Joints", None))
#if QT_CONFIG(statustip)
        self.preserve_shapes_check.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Preseve the orientation of shapes when rotating nodes.", None))
#endif // QT_CONFIG(statustip)
        self.preserve_shapes_check.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Preserve Shapes", None))
        self.up_axis_combo.setItemText(0, QCoreApplication.translate("JointOrientsDesignPanel", u"X world up", None))
        self.up_axis_combo.setItemText(1, QCoreApplication.translate("JointOrientsDesignPanel", u"Y world up", None))
        self.up_axis_combo.setItemText(2, QCoreApplication.translate("JointOrientsDesignPanel", u"Z world up", None))

#if QT_CONFIG(tooltip)
        self.up_axis_combo.setToolTip(QCoreApplication.translate("JointOrientsDesignPanel", u"The world up axis to align with the local up axis.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.fixup_btn.setStatusTip(QCoreApplication.translate("JointOrientsDesignPanel", u"Adjust joint orientation to point down the bone, whilst preserving the other axes as much as possible. Currently hard-coded to point down X and prioritize Z.", None))
#endif // QT_CONFIG(statustip)
        self.fixup_btn.setText(QCoreApplication.translate("JointOrientsDesignPanel", u"Fixup", None))
    # retranslateUi

