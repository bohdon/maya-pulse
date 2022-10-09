from functools import partial

import pymel.core as pm

from ...vendor.Qt import QtWidgets
from ... import editorutils
from ...prefs import optionVarProperty
from ..utils import undoAndRepeatPartial as cmd

from ..gen.designpanel_joints import Ui_JointsDesignPanel
from ..gen.designpanel_joint_orients import Ui_JointOrientsDesignPanel


class JointsDesignPanel(QtWidgets.QWidget):

    def __init__(self, parent):
        super(JointsDesignPanel, self).__init__(parent)

        self.ui = Ui_JointsDesignPanel()
        self.ui.setupUi(self)

        self.ui.joint_tool_btn.clicked.connect(cmd(pm.mel.JointTool))
        self.ui.insert_joint_tool_btn.clicked.connect(cmd(pm.mel.InsertJointTool))
        self.ui.center_btn.clicked.connect(cmd(editorutils.centerSelectedJoints))
        self.ui.insert_btn.clicked.connect(cmd(editorutils.insertJointForSelected))
        self.ui.disable_ssc_btn.clicked.connect(cmd(editorutils.disableSegmentScaleCompensateForSelected))
        self.ui.freeze_btn.clicked.connect(cmd(editorutils.freezeJointsForSelectedHierarchies))
        self.ui.mark_end_joints_btn.clicked.connect(cmd(editorutils.markEndJointsForSelected))


class DesignPanelJointOrients(QtWidgets.QWidget):
    AXIS_ORDER_OPTIONS = ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']
    UP_AXIS_OPTIONS = ['X', 'Y', 'Z']

    axis_order = optionVarProperty('pulse.editor.orientAxisOrder', 0)
    up_axis = optionVarProperty('pulse.editor.orientUpAxis', 1)
    keep_axes_synced = optionVarProperty('pulse.editor.keepAxesSynced', True)
    preserve_children = optionVarProperty('pulse.editor.orientPreserveChildren', True)
    preserve_shapes = optionVarProperty('pulse.editor.orientPreserveShapes', True)
    include_children = optionVarProperty('pulse.editor.orientIncludeChildren', False)

    def set_axis_order(self, value):
        self.axis_order = value

    def set_up_axis(self, value):
        self.up_axis = value

    def set_keep_axes_synced(self, value):
        self.keep_axes_synced = value

    def set_preserve_children(self, value):
        self.preserve_children = value

    def set_preserve_shapes(self, value):
        self.preserve_shapes = value

    def set_include_children(self, value):
        self.include_children = value

    def __init__(self, parent):
        super(DesignPanelJointOrients, self).__init__(parent)

        self.ui = Ui_JointOrientsDesignPanel()
        self.ui.setupUi(self)
        self._update_settings()

        # general utils
        self.ui.toggle_lras_btn.clicked.connect(cmd(editorutils.toggleLocalRotationAxesForSelected))
        self.ui.toggle_cb_attrs_btn.clicked.connect(cmd(editorutils.toggleDetailedChannelBoxForSelected))
        self.ui.interactive_btn.clicked.connect(cmd(editorutils.interactiveOrientForSelected))
        self.ui.sync_axes_btn.clicked.connect(cmd(editorutils.matchJointRotationToOrientForSelected))

        # incremental rotate buttons
        self.ui.rot_x_neg_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 0, -90))
        self.ui.rot_x_pos_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 0, 90))
        self.ui.rot_y_neg_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 1, -90))
        self.ui.rot_y_pos_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 1, 90))
        self.ui.rot_z_neg_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 2, -90))
        self.ui.rot_z_pos_btn.clicked.connect(partial(self.rotate_selected_orients_around_axis, 2, 90))

        # auto orient settings
        self.ui.axis_order_combo.currentIndexChanged.connect(self.set_axis_order)
        self.ui.up_axis_combo.currentIndexChanged.connect(self.set_up_axis)
        self.ui.include_children_check.stateChanged.connect(self.set_include_children)
        self.ui.keep_axes_synced_check.stateChanged.connect(self.set_keep_axes_synced)
        self.ui.preserve_children_check.stateChanged.connect(self.set_preserve_children)
        self.ui.preserve_shapes_check.stateChanged.connect(self.set_preserve_shapes)

        # auto orient buttons
        self.ui.orient_to_joint_btn.clicked.connect(self.orient_to_joint_for_selected)
        self.ui.orient_to_parent_btn.clicked.connect(self.orient_to_parent_for_selected)
        self.ui.orient_to_world_btn.clicked.connect(self.orient_to_world_for_selected)
        self.ui.orient_ik_joints_btn.clicked.connect(self.orient_ik_joints_for_selected)
        self.ui.fixup_btn.clicked.connect(self.fixup_orient_for_selected)

    def _update_settings(self):
        self.ui.axis_order_combo.setCurrentIndex(self.axis_order)
        self.ui.up_axis_combo.setCurrentIndex(self.up_axis)

        self.ui.include_children_check.setChecked(self.include_children)
        self.ui.keep_axes_synced_check.setChecked(self.keep_axes_synced)
        self.ui.preserve_children_check.setChecked(self.preserve_children)
        self.ui.preserve_shapes_check.setChecked(self.preserve_shapes)

    def get_up_axis_str(self):
        """
        Returns:
            An str representing the up axis
                e.g. 'x', 'y', 'z'
        """
        return self.UP_AXIS_OPTIONS[self.up_axis].lower()

    def get_axis_order_str(self):
        """
        Returns:
            A string representing the orient axis order,
                e.g. 'xyz', 'zyx', ...
        """
        return self.AXIS_ORDER_OPTIONS[self.axis_order].lower()

    def rotate_selected_orients_around_axis(self, axis, degrees):
        kw = dict(
            preserveChildren=self.preserve_children,
            preserveShapes=self.preserve_shapes,
            syncJointAxes=self.keep_axes_synced,
        )
        cmd(editorutils.rotateSelectedOrientsAroundAxis, axis, degrees, **kw)()

    def orient_to_world_for_selected(self):
        kw = dict(
            includeChildren=self.include_children,
            preserveChildren=self.preserve_children,
            preserveShapes=self.preserve_shapes,
            syncJointAxes=self.keep_axes_synced,
        )
        cmd(editorutils.orientToWorldForSelected, **kw)()

    def orient_to_joint_for_selected(self):
        kw = dict(
            axisOrder=self.get_axis_order_str(),
            upAxisStr=self.get_up_axis_str(),
            includeChildren=self.include_children,
            preserveChildren=self.preserve_children,
            preserveShapes=self.preserve_shapes,
            syncJointAxes=self.keep_axes_synced,
        )
        cmd(editorutils.orientToJointForSelected, **kw)()

    def orient_to_parent_for_selected(self):
        kw = dict(
            includeChildren=self.include_children,
            preserveChildren=self.preserve_children,
        )
        cmd(editorutils.orientToParentForSelected, **kw)()

    def orient_ik_joints_for_selected(self):
        kw = dict(
            aimAxis=self.get_axis_order_str()[0],
            poleAxis=self.get_up_axis_str(),
            preserveChildren=self.preserve_children,
        )
        cmd(editorutils.orientIKJointsForSelected, **kw)()

    def fixup_orient_for_selected(self):
        kw = dict(
            aimAxis=self.get_axis_order_str()[0],
            keepAxis=self.get_up_axis_str(),
            preserveChildren=self.preserve_children,
        )
        cmd(editorutils.fixupJointOrientForSelected, **kw)()