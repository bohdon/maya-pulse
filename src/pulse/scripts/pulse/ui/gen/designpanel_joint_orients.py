# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'designpanel_joint_orients.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_DesignPanelJointOrients(object):
    def setupUi(self, DesignPanelJointOrients):
        if not DesignPanelJointOrients.objectName():
            DesignPanelJointOrients.setObjectName(u"DesignPanelJointOrients")
        DesignPanelJointOrients.resize(227, 299)
        self.verticalLayout = QVBoxLayout(DesignPanelJointOrients)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.sync_axes_btn = QPushButton(DesignPanelJointOrients)
        self.sync_axes_btn.setObjectName(u"sync_axes_btn")

        self.gridLayout_2.addWidget(self.sync_axes_btn, 1, 3, 1, 1)

        self.interactive_btn = QPushButton(DesignPanelJointOrients)
        self.interactive_btn.setObjectName(u"interactive_btn")

        self.gridLayout_2.addWidget(self.interactive_btn, 1, 2, 1, 1)

        self.toggle_lras_btn = QPushButton(DesignPanelJointOrients)
        self.toggle_lras_btn.setObjectName(u"toggle_lras_btn")

        self.gridLayout_2.addWidget(self.toggle_lras_btn, 0, 2, 1, 1)

        self.toggle_cb_attrs_btn = QPushButton(DesignPanelJointOrients)
        self.toggle_cb_attrs_btn.setObjectName(u"toggle_cb_attrs_btn")

        self.gridLayout_2.addWidget(self.toggle_cb_attrs_btn, 0, 3, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout_2)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.rot_x_neg_btn = QPushButton(DesignPanelJointOrients)
        self.rot_x_neg_btn.setObjectName(u"rot_x_neg_btn")
        self.rot_x_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_x_neg_btn)

        self.rot_x_pos_btn = QPushButton(DesignPanelJointOrients)
        self.rot_x_pos_btn.setObjectName(u"rot_x_pos_btn")
        self.rot_x_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_x_pos_btn)

        self.rot_y_neg_btn = QPushButton(DesignPanelJointOrients)
        self.rot_y_neg_btn.setObjectName(u"rot_y_neg_btn")
        self.rot_y_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_y_neg_btn)

        self.rot_y_pos_btn = QPushButton(DesignPanelJointOrients)
        self.rot_y_pos_btn.setObjectName(u"rot_y_pos_btn")
        self.rot_y_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_y_pos_btn)

        self.rot_z_neg_btn = QPushButton(DesignPanelJointOrients)
        self.rot_z_neg_btn.setObjectName(u"rot_z_neg_btn")
        self.rot_z_neg_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_z_neg_btn)

        self.rot_z_pos_btn = QPushButton(DesignPanelJointOrients)
        self.rot_z_pos_btn.setObjectName(u"rot_z_pos_btn")
        self.rot_z_pos_btn.setMinimumSize(QSize(10, 0))

        self.horizontalLayout_4.addWidget(self.rot_z_pos_btn)


        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.verticalSpacer_2 = QSpacerItem(20, 6, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacer_2)

        self.line = QFrame(DesignPanelJointOrients)
        self.line.setObjectName(u"line")
        self.line.setFrameShadow(QFrame.Plain)
        self.line.setFrameShape(QFrame.HLine)

        self.verticalLayout.addWidget(self.line)

        self.verticalSpacer_4 = QSpacerItem(20, 6, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacer_4)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.preserve_children_check = QCheckBox(DesignPanelJointOrients)
        self.preserve_children_check.setObjectName(u"preserve_children_check")

        self.verticalLayout_2.addWidget(self.preserve_children_check)

        self.preserve_shapes_check = QCheckBox(DesignPanelJointOrients)
        self.preserve_shapes_check.setObjectName(u"preserve_shapes_check")

        self.verticalLayout_2.addWidget(self.preserve_shapes_check)

        self.keep_axes_synced_check = QCheckBox(DesignPanelJointOrients)
        self.keep_axes_synced_check.setObjectName(u"keep_axes_synced_check")

        self.verticalLayout_2.addWidget(self.keep_axes_synced_check)

        self.include_children_check = QCheckBox(DesignPanelJointOrients)
        self.include_children_check.setObjectName(u"include_children_check")

        self.verticalLayout_2.addWidget(self.include_children_check)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.axis_order_combo = QComboBox(DesignPanelJointOrients)
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.addItem("")
        self.axis_order_combo.setObjectName(u"axis_order_combo")

        self.verticalLayout_3.addWidget(self.axis_order_combo)

        self.up_axis_combo = QComboBox(DesignPanelJointOrients)
        self.up_axis_combo.addItem("")
        self.up_axis_combo.addItem("")
        self.up_axis_combo.addItem("")
        self.up_axis_combo.setObjectName(u"up_axis_combo")

        self.verticalLayout_3.addWidget(self.up_axis_combo)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.verticalLayout_3)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.verticalSpacer_3 = QSpacerItem(20, 6, QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.verticalLayout.addItem(self.verticalSpacer_3)

        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.orient_ik_joints_btn = QPushButton(DesignPanelJointOrients)
        self.orient_ik_joints_btn.setObjectName(u"orient_ik_joints_btn")

        self.gridLayout.addWidget(self.orient_ik_joints_btn, 2, 1, 1, 1)

        self.orient_to_world_btn = QPushButton(DesignPanelJointOrients)
        self.orient_to_world_btn.setObjectName(u"orient_to_world_btn")

        self.gridLayout.addWidget(self.orient_to_world_btn, 2, 0, 1, 1)

        self.orient_to_joint_btn = QPushButton(DesignPanelJointOrients)
        self.orient_to_joint_btn.setObjectName(u"orient_to_joint_btn")

        self.gridLayout.addWidget(self.orient_to_joint_btn, 1, 0, 1, 1)

        self.orient_to_parent_btn = QPushButton(DesignPanelJointOrients)
        self.orient_to_parent_btn.setObjectName(u"orient_to_parent_btn")

        self.gridLayout.addWidget(self.orient_to_parent_btn, 1, 1, 1, 1)


        self.verticalLayout.addLayout(self.gridLayout)

        self.fixup_btn = QPushButton(DesignPanelJointOrients)
        self.fixup_btn.setObjectName(u"fixup_btn")

        self.verticalLayout.addWidget(self.fixup_btn)


        self.retranslateUi(DesignPanelJointOrients)

        QMetaObject.connectSlotsByName(DesignPanelJointOrients)
    # setupUi

    def retranslateUi(self, DesignPanelJointOrients):
        DesignPanelJointOrients.setWindowTitle(QCoreApplication.translate("DesignPanelJointOrients", u"Form", None))
#if QT_CONFIG(statustip)
        self.sync_axes_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Match the translate and scale axes of a joint to its orientation.", None))
#endif // QT_CONFIG(statustip)
        self.sync_axes_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Synx Axes", None))
        self.interactive_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Interactive", None))
#if QT_CONFIG(statustip)
        self.toggle_lras_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Toggle the display of local rotation axes.", None))
#endif // QT_CONFIG(statustip)
        self.toggle_lras_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Toggle LRAs", None))
#if QT_CONFIG(statustip)
        self.toggle_cb_attrs_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Toggle the display of orientation attributes in the channel box.", None))
#endif // QT_CONFIG(statustip)
        self.toggle_cb_attrs_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Toggle CB Attrs", None))
#if QT_CONFIG(statustip)
        self.rot_x_neg_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_x_neg_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"- X", None))
        self.rot_x_neg_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"x-axis", None))
#if QT_CONFIG(statustip)
        self.rot_x_pos_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_x_pos_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"+ X", None))
        self.rot_x_pos_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"x-axis", None))
#if QT_CONFIG(statustip)
        self.rot_y_neg_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_y_neg_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"- Y", None))
        self.rot_y_neg_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"y-axis", None))
#if QT_CONFIG(statustip)
        self.rot_y_pos_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_y_pos_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"+ Y", None))
        self.rot_y_pos_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"y-axis", None))
#if QT_CONFIG(statustip)
        self.rot_z_neg_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_z_neg_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"- Z", None))
        self.rot_z_neg_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"z-axis", None))
#if QT_CONFIG(statustip)
        self.rot_z_pos_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Rotate the orients in controlled increments.", None))
#endif // QT_CONFIG(statustip)
        self.rot_z_pos_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"+ Z", None))
        self.rot_z_pos_btn.setProperty("cssClasses", QCoreApplication.translate("DesignPanelJointOrients", u"z-axis", None))
#if QT_CONFIG(statustip)
        self.preserve_children_check.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Preseve the positions of child nodes when rotating or orienting a transform or joint.", None))
#endif // QT_CONFIG(statustip)
        self.preserve_children_check.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Preserve Children", None))
#if QT_CONFIG(statustip)
        self.preserve_shapes_check.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Preseve the orientation of shapes when rotating nodes.", None))
#endif // QT_CONFIG(statustip)
        self.preserve_shapes_check.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Preserve Shapes", None))
#if QT_CONFIG(statustip)
        self.keep_axes_synced_check.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"When enabled, joint translate and scale axes are automatically updated when the jointOrient and rotateAxis values are changed.", None))
#endif // QT_CONFIG(statustip)
        self.keep_axes_synced_check.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Keep Axes Synced", None))
#if QT_CONFIG(statustip)
        self.include_children_check.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Update all child joints when using orient to joint or world.", None))
#endif // QT_CONFIG(statustip)
        self.include_children_check.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Include Children", None))
        self.axis_order_combo.setItemText(0, QCoreApplication.translate("DesignPanelJointOrients", u"X forward, Y up", None))
        self.axis_order_combo.setItemText(1, QCoreApplication.translate("DesignPanelJointOrients", u"X forward, Z up", None))
        self.axis_order_combo.setItemText(2, QCoreApplication.translate("DesignPanelJointOrients", u"Y forward, X up", None))
        self.axis_order_combo.setItemText(3, QCoreApplication.translate("DesignPanelJointOrients", u"Y forward, Z up", None))
        self.axis_order_combo.setItemText(4, QCoreApplication.translate("DesignPanelJointOrients", u"Z forward, X up", None))
        self.axis_order_combo.setItemText(5, QCoreApplication.translate("DesignPanelJointOrients", u"Z forward, Y up", None))

#if QT_CONFIG(tooltip)
        self.axis_order_combo.setToolTip(QCoreApplication.translate("DesignPanelJointOrients", u"The local axes to use when orienting.", None))
#endif // QT_CONFIG(tooltip)
        self.up_axis_combo.setItemText(0, QCoreApplication.translate("DesignPanelJointOrients", u"X world up", None))
        self.up_axis_combo.setItemText(1, QCoreApplication.translate("DesignPanelJointOrients", u"Y world up", None))
        self.up_axis_combo.setItemText(2, QCoreApplication.translate("DesignPanelJointOrients", u"Z world up", None))

#if QT_CONFIG(tooltip)
        self.up_axis_combo.setToolTip(QCoreApplication.translate("DesignPanelJointOrients", u"The world up axis to align with the local up axis.", None))
#endif // QT_CONFIG(tooltip)
        self.orient_ik_joints_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Orient IK Joints", None))
        self.orient_to_world_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Orient to World", None))
        self.orient_to_joint_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Orient to Joint", None))
        self.orient_to_parent_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Orient to Parent", None))
#if QT_CONFIG(statustip)
        self.fixup_btn.setStatusTip(QCoreApplication.translate("DesignPanelJointOrients", u"Adjust joint orientation to point down the bone, whilst preserving the other axes as much as possible. Currently hard-coded to point down X and prioritize Z.", None))
#endif // QT_CONFIG(statustip)
        self.fixup_btn.setText(QCoreApplication.translate("DesignPanelJointOrients", u"Fixup", None))
    # retranslateUi

