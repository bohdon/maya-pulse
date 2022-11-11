from functools import partial

import pymel.core as pm

from ...vendor.Qt import QtWidgets
from ... import editor_utils
from ...prefs import option_var_property
from ..utils import undo_and_repeat_partial as cmd

from ..gen.designpanel_joints import Ui_JointsDesignPanel
from ..gen.designpanel_joint_orients import Ui_JointOrientsDesignPanel


class JointsDesignPanel(QtWidgets.QWidget):
    def __init__(self, parent):
        super(JointsDesignPanel, self).__init__(parent)

        self.ui = Ui_JointsDesignPanel()
        self.ui.setupUi(self)

        self.ui.joint_tool_btn.clicked.connect(cmd(pm.mel.JointTool))
        self.ui.insert_joint_tool_btn.clicked.connect(cmd(pm.mel.InsertJointTool))
        self.ui.center_btn.clicked.connect(cmd(editor_utils.center_selected_joints))
        self.ui.insert_btn.clicked.connect(cmd(editor_utils.insert_joint_for_selected))
        self.ui.disable_ssc_btn.clicked.connect(cmd(editor_utils.disable_segment_scale_compensate_for_selected))
        self.ui.freeze_btn.clicked.connect(cmd(editor_utils.freeze_joints_for_selected_hierarchies))
        self.ui.mark_end_joints_btn.clicked.connect(cmd(editor_utils.mark_end_joints_for_selected))


class DesignPanelJointOrients(QtWidgets.QWidget):
    AXIS_ORDER_OPTIONS = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
    UP_AXIS_OPTIONS = ["X", "Y", "Z"]

    axis_order = option_var_property("pulse.editor.orientAxisOrder", 0)
    up_axis = option_var_property("pulse.editor.orientUpAxis", 1)
    keep_axes_synced = option_var_property("pulse.editor.keepAxesSynced", True)
    preserve_children = option_var_property("pulse.editor.orientPreserveChildren", True)
    preserve_shapes = option_var_property("pulse.editor.orientPreserveShapes", True)
    include_children = option_var_property("pulse.editor.orientIncludeChildren", False)

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
        self.ui.toggle_lras_btn.clicked.connect(cmd(editor_utils.toggle_local_rotation_axes_for_selected))
        self.ui.toggle_cb_attrs_btn.clicked.connect(cmd(editor_utils.toggle_detailed_channel_box_for_selected))
        self.ui.interactive_btn.clicked.connect(cmd(editor_utils.interactive_orient_for_selected))
        self.ui.sync_axes_btn.clicked.connect(cmd(editor_utils.match_joint_rotation_to_orient_for_selected))

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
            preserve_children=self.preserve_children,
            preserve_shapes=self.preserve_shapes,
            sync_joint_axes=self.keep_axes_synced,
        )
        cmd(editor_utils.rotate_selected_orients_around_axis, axis, degrees, **kw)()

    def orient_to_world_for_selected(self):
        kw = dict(
            include_children=self.include_children,
            preserve_children=self.preserve_children,
            preserve_shapes=self.preserve_shapes,
            sync_joint_axes=self.keep_axes_synced,
        )
        cmd(editor_utils.orient_to_world_for_selected, **kw)()

    def orient_to_joint_for_selected(self):
        kw = dict(
            axis_order=self.get_axis_order_str(),
            up_axis_str=self.get_up_axis_str(),
            include_children=self.include_children,
            preserve_children=self.preserve_children,
            preserve_shapes=self.preserve_shapes,
            sync_joint_axes=self.keep_axes_synced,
        )
        cmd(editor_utils.orient_to_joint_for_selected, **kw)()

    def orient_to_parent_for_selected(self):
        kw = dict(
            include_children=self.include_children,
            preserve_children=self.preserve_children,
        )
        cmd(editor_utils.orient_to_parent_for_selected, **kw)()

    def orient_ik_joints_for_selected(self):
        kw = dict(
            aim_axis=self.get_axis_order_str()[0],
            pole_axis=self.get_up_axis_str(),
            preserve_children=self.preserve_children,
        )
        cmd(editor_utils.orient_ik_joints_for_selected, **kw)()

    def fixup_orient_for_selected(self):
        kw = dict(
            aim_axis=self.get_axis_order_str()[0],
            keep_axis=self.get_up_axis_str(),
            preserve_children=self.preserve_children,
        )
        cmd(editor_utils.fixup_joint_orient_for_selected, **kw)()
