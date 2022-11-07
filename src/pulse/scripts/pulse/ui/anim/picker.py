"""
An anim picker for easily selecting controls while animating.
"""
import logging
from typing import List, Optional, Union
from maya import OpenMaya, cmds
import pymel.core as pm

from ... import nodes
from ...colors import LinearColor
from ...prefs import option_var_property
from ...vendor.Qt import QtCore, QtGui, QtWidgets
from ...vendor.Qt.QtCore import QPoint, QPointF, QRect, QSize

from ..core import PulseWindow

from ..gen.anim_picker import Ui_AnimPicker

logger = logging.getLogger(__name__)


def scale_rect(rect: QRect, scale: float) -> QRect:
    top_left = (QPointF(rect.topLeft()) * scale).toPoint()
    return QRect(top_left, rect.size() * scale)


class AnimPickerButton(QtWidgets.QPushButton):
    def __init__(self, location: Union[QPointF, QPoint], size: QSize, node: Optional[str] = None, parent=None):
        """
        Args:
            location: The center location of the button.
            size: The size of the button.
            node: The node to select when this button is selected.
            parent: The parent object.
        """
        super(AnimPickerButton, self).__init__(parent=parent)

        # the geometry of this button at 1x zoom
        self.location = QPointF(location)
        self.size = size
        # the node this button selects
        self.node = node
        self.base_color_alpha = 0.5
        self.color: Optional[LinearColor] = LinearColor(0.5, 0.5, 0.5, self.base_color_alpha)
        self.pre_select_color = LinearColor(1, 1, 1, 0.75)
        self.select_color = LinearColor(1, 1, 1, 1)
        self._is_selected = False

        self.setProperty("cssClasses", "anim-picker-btn")

        self.clicked.connect(self.select)

        self._update_node_info()
        self._update_style()

    def set_location(self, pos: Union[QPointF, QPoint]):
        """Set the center location of the button."""
        # ensure its a floating point
        self.location = QPointF(pos)

    def is_selected(self) -> bool:
        """
        Is this button itself currently selected? Does not represent the selection
        of the button's node in the scene.
        """
        return self._is_selected

    def is_node_selected(self, sel: List[Union[str, pm.PyNode]] = None) -> bool:
        """
        Is the node for this button currently selected?

        Args:
            sel: The list of currently selected nodes to check against. If not given, will retrieve the selection
                from the scene. Use this for performance in order to avoid retrieving the selection multiple times
                during a single large operation.
        """
        if not sel:
            sel = cmds.ls(selection=True)
        if sel and isinstance(sel[0], pm.PyNode):
            # convert to node names
            sel = [n.nodeName() for n in sel]
        return self.node and self.node in sel

    def is_node_set(self) -> bool:
        """
        Return true if a node has been set for this button. Does not check whether the node exists in the scene.
        """
        return bool(self.node)

    def has_valid_node(self) -> bool:
        """
        Return true if this button has a node that is valid and exists in the scene.
        """
        return bool(self.node and cmds.ls(self.node))

    def select(self, is_pre_select=False):
        """
        Select this button's node.

        Args:
            is_pre_select: If true, don't select the nodes in the scene, just indicate
                visually that the button is selected.
        """
        self.set_is_selected(True, is_pre_select)
        if not is_pre_select:
            try:
                pm.select(self.node, add=True)
            except TypeError as e:
                logger.warning(f"{e}")

    def deselect(self, is_pre_select=False):
        """Deselect the button's node."""
        self.set_is_selected(False)
        if not is_pre_select:
            try:
                pm.select(self.node, deselect=True)
            except TypeError as e:
                pass

    def set_is_selected(self, value: bool, is_pre_select=False):
        self._is_selected = value
        self._update_style(is_pre_select)

    def _update_style(self, is_pre_selected=False):
        if self.node:
            # a node value is set, show with fill
            if self.is_selected():
                if is_pre_selected:
                    self.setStyleSheet(f"background-color: {self.pre_select_color.as_style()};")
                else:
                    self.setStyleSheet(f"background-color: {self.select_color.as_style()};")
            else:
                self.setStyleSheet(f"background-color: {self.color.as_style()};")
        else:
            # no node, show as hollow
            if self.is_selected():
                self.setStyleSheet(f"border: 2px solid {self.pre_select_color.as_style()};")
            else:
                self.setStyleSheet(f"border: 2px solid {self.color.as_style()};")

    def set_node(self, node: Optional[str]):
        self.node = node
        self._update_node_info()

    def _update_node_info(self):
        """
        Attempt to pull node information for display purposes, e.g. status tip, color.
        """
        self.setStatusTip(self.node if self.node else "")
        try:
            pynode = pm.PyNode(self.node)
        except:
            pass
        else:
            node_color = nodes.get_override_color(pynode)
            if node_color:
                self.color = node_color
                # dim the color a bit to make white selection stand out
                self.color.a = self.base_color_alpha


class AnimPickerSelectOperation(object):
    """
    The types of selection operations, e.g. replace, add, etc.
    """

    NONE = None
    # replace the selection completely
    REPLACE = "replace"
    # add to the selection
    ADD = "add"
    # toggle the selection
    TOGGLE = "toggle"
    # deselect nodes
    DESELECT = "deselect"
    # select only the picker buttons for editing, unavailable when locked
    EDIT = "edit"


class AnimPickerPanel(QtWidgets.QWidget):
    viewScaleChanged = QtCore.Signal(float)
    viewOffsetChanged = QtCore.Signal(QPoint)

    def __init__(self, parent=None):
        super(AnimPickerPanel, self).__init__(parent=parent)

        # is the picker currently locked for editing?
        self.is_locked = True

        self.rubber_band: Optional[QtWidgets.QRubberBand] = None
        self.default_btn_size = QSize(40, 40)
        self.view_offset_raw = QPointF()
        self.grid_size = QPoint(10, 10)
        self.view_scale = 1.0
        self.view_scale_min = 0.25
        self.view_scale_max = 3.0
        self.wheel_zoom_sensitivity = 0.001
        self.drag_zoom_sensitivity = 0.002
        # if true, update scene selection while dragging
        self.select_on_drag = False
        self.pending_node_selection: List[pm.PyNode] = []
        self.selection_rect = QRect()
        # the current selection operation
        self.select_operation: Optional[str] = AnimPickerSelectOperation.NONE
        self.is_drag_selecting = False
        # the list of all buttons
        self.buttons: List[AnimPickerButton] = []
        # the current button being placed with left click, gives an opportunity to reposition before committing
        self.placement_btn: Optional[AnimPickerButton] = None
        self.cb_ids = []
        # last mouse position during drags, used for panning, zooming, and dragging buttons
        self.drag_last_pos = QPoint()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.bg_frame = QtWidgets.QFrame(self)
        self.bg_frame.setStyleSheet("background-color: rgba(255, 255, 255, 5%)")
        layout.addWidget(self.bg_frame)

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def __del__(self):
        self._unregister_callbacks()

    def set_is_locked(self, value: bool):
        self.is_locked = value
        if self.is_locked:
            self.bg_frame.setStyleSheet("background-color: rgba(255, 255, 255, 5%)")
        else:
            self.bg_frame.setStyleSheet("background-color: rgba(0, 0, 0, 20%)")

    def _register_callbacks(self):
        if not self.cb_ids:
            cb_id = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self._on_scene_selection_changed)
            self.cb_ids.append(cb_id)

    def _unregister_callbacks(self):
        for cb_id in self.cb_ids:
            OpenMaya.MMessage.removeCallback(cb_id)
        self.cb_ids.clear()

    @property
    def panel_center(self) -> QPoint:
        return (QPointF(*self.rect().size().toTuple()) * 0.5).toPoint()

    @property
    def view_offset(self) -> QPoint:
        """
        The view offset, rounded to ints.
        """
        return self.view_offset_raw.toPoint()

    @property
    def center_view_offset(self) -> QPoint:
        """
        The effective view offset, rounded to ints, and offset by half the panel size
        to default to the origin at the center.
        """
        return self.view_offset + self.panel_center

    def transform_rect(self, rect: QRect) -> QRect:
        """Transform a position to view space."""
        return scale_rect(rect, self.view_scale).translated(self.center_view_offset)

    def inverse_transform_rect(self, rect: QRect) -> QRect:
        """Inverse transform from view space."""
        return scale_rect(rect.translated(-self.center_view_offset), 1.0 / self.view_scale)

    def transform_pos(self, point: QPoint) -> QPoint:
        return (QPointF(point) * self.view_scale).toPoint() + self.center_view_offset

    def inverse_transform_pos(self, point: QPoint) -> QPoint:
        return (QPointF(point - self.center_view_offset) * (1.0 / self.view_scale)).toPoint()

    def paintEvent(self, event: QtGui.QPaintEvent):
        super(AnimPickerPanel, self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QColor(0, 0, 0, 30))

        # draw axes
        rect = self.rect()
        # the axes origin in view-space
        origin_x, origin_y = self.transform_pos(QPoint()).toTuple()
        if 0 < origin_y < rect.bottom():
            p1 = QPoint(rect.left(), origin_y)
            p2 = QPoint(rect.right(), origin_y)
            painter.drawLine(p1, p2)
        if 0 < origin_x < rect.right():
            p3 = QPoint(origin_x, rect.top())
            p4 = QPoint(origin_x, rect.bottom())
            painter.drawLine(p3, p4)

    def showEvent(self, event: QtGui.QShowEvent):
        super(AnimPickerPanel, self).showEvent(event)
        self._register_callbacks()

    def hideEvent(self, event: QtGui.QHideEvent):
        super(AnimPickerPanel, self).hideEvent(event)
        self._unregister_callbacks()

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if self.is_drag_selecting and (event.key() == QtCore.Qt.Key_Shift or event.key() == QtCore.Qt.Key_Control):
            # refresh selection for modifier key change
            self.update_select_operation(event.modifiers())
            self.select_buttons_in_rect(self.selection_rect)

        elif event.key() == QtCore.Qt.Key_Backspace or event.key() == QtCore.Qt.Key_Delete:
            if not self.is_locked:
                self.delete_selected_buttons()
            # consume the key press anyway, in case the user thinks they are in editing mode
            # TODO: show 'locked' feedback on attempted edit
            return

        super(AnimPickerPanel, self).keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        if self.is_drag_selecting and (event.key() == QtCore.Qt.Key_Shift or event.key() == QtCore.Qt.Key_Control):
            # refresh selection for modifier key change
            self.update_select_operation(event.modifiers())
            self.select_buttons_in_rect(self.selection_rect)

        super(AnimPickerPanel, self).keyReleaseEvent(event)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        # zoom in and out
        delta_scale = event.delta() * self.wheel_zoom_sensitivity
        self.add_view_scale(delta_scale, event.pos())

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        mods = event.modifiers()
        self.drag_last_pos = event.pos()

        if event.buttons() == QtCore.Qt.LeftButton and mods == QtCore.Qt.ShiftModifier and not self.is_locked:
            location = self.inverse_transform_pos(event.localPos().toPoint())
            self.placement_btn = self.add_picker_btn(location, self.default_btn_size)

        elif mods == QtCore.Qt.AltModifier:
            # start drag for pan or zoom
            pass

        elif event.button() == QtCore.Qt.MiddleButton and not self.is_locked:
            # drag move selected buttons
            pass

        elif event.button() == QtCore.Qt.LeftButton:
            # start selection
            self.update_select_operation(mods)
            self.start_selection(event.pos())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        btns = event.buttons()
        mods = event.modifiers()
        drag_delta: QPointF = QPointF(event.pos() - self.drag_last_pos)
        self.drag_last_pos = event.pos()

        if self.placement_btn:
            # placing a new button
            location = self.inverse_transform_pos(event.pos())
            self.placement_btn.set_location(location)
            self._update_btn_geometry(self.placement_btn)
            pass

        elif self.is_drag_selecting:
            self.update_select_operation(mods)
            self.update_selection(event.pos())
            if not self.rubber_band:
                # show rubber band for the first time when starting to move mouse
                self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
            self.rubber_band.setGeometry(self.selection_rect.normalized())
            self.rubber_band.show()

        elif mods & QtCore.Qt.AltModifier:
            if btns & QtCore.Qt.RightButton:
                # drag zooming
                delta_zoom = (drag_delta.x() + drag_delta.y()) * self.drag_zoom_sensitivity
                self.add_view_scale(delta_zoom, self.panel_center)
            elif btns & QtCore.Qt.MiddleButton | QtCore.Qt.LeftButton:
                # drag panning
                self.set_view_offset_raw(self.view_offset_raw + drag_delta)

        elif btns & QtCore.Qt.MiddleButton and not self.is_locked:
            # drag move selected buttons
            for btn in self.buttons:
                if btn.is_selected():
                    # add offset
                    btn.set_location(btn.location + (drag_delta * (1.0 / self.view_scale)))
                    self._update_btn_geometry(btn)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        mods = event.modifiers()
        if self.placement_btn:
            # commit snapping to grid
            self.placement_btn.set_location(self._snap_pos_to_grid(self.placement_btn.location))
            self._update_btn_geometry(self.placement_btn)
            self.placement_btn = None

        elif self.is_drag_selecting:
            self.update_select_operation(mods)
            self.finish_selection(event.pos())
            if self.rubber_band:
                self.rubber_band.hide()

        elif event.button() == QtCore.Qt.MiddleButton and not self.is_locked:
            # drag moved buttons, commit snapping to grid
            for btn in self.buttons:
                if btn.is_selected():
                    btn.set_location(self._snap_pos_to_grid(btn.location))
                    self._update_btn_geometry(btn)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        # update all button geometry, the view changes based on panel size
        for btn in self.buttons:
            self._update_btn_geometry(btn)

        super(AnimPickerPanel, self).resizeEvent(event)

    def start_selection(self, origin: QPoint):
        if self.select_on_drag and self.select_operation == AnimPickerSelectOperation.REPLACE:
            pm.select(clear=True)
        self.is_drag_selecting = True
        self.selection_rect = QRect(origin, QSize())

    def update_select_operation(self, modifiers: QtCore.Qt.KeyboardModifiers):
        """Update the current select operation based on keyboard modifiers."""
        self.select_operation = AnimPickerSelectOperation.REPLACE
        if modifiers == QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier:
            self.select_operation = AnimPickerSelectOperation.ADD
        elif modifiers == QtCore.Qt.ShiftModifier:
            if self.is_locked:
                self.select_operation = AnimPickerSelectOperation.TOGGLE
            else:
                # shift while editing places new nodes
                self.select_operation = AnimPickerSelectOperation.NONE
        elif modifiers == QtCore.Qt.ControlModifier:
            if self.is_locked:
                self.select_operation = AnimPickerSelectOperation.DESELECT
            else:
                # ctrl while editing selects buttons without nodes
                self.select_operation = AnimPickerSelectOperation.EDIT

    def update_selection(self, pos: QPoint):
        # always set bottom right to preserve direction, use normalize when needed
        self.selection_rect.setBottomRight(pos)
        self.select_buttons_in_rect(self.selection_rect.normalized())

    def finish_selection(self, pos: QPoint):
        """Finish the current drag selection."""
        self.is_drag_selecting = False
        self.selection_rect.setBottomRight(pos)
        self.select_buttons_in_rect(self.selection_rect.normalized())
        if not self.select_on_drag:
            self.commit_selections()

    def add_view_scale(self, delta_scale: float, focus_point: QPoint):
        old_view_scale = self.view_scale
        self.set_view_scale(self.view_scale + delta_scale)
        real_delta_scale = self.view_scale - old_view_scale

        # apply zoom centered on panel position
        focus_pos_ws = QPointF(self.inverse_transform_pos(focus_point))
        delta_offset = focus_pos_ws * -real_delta_scale
        self.set_view_offset_raw(self.view_offset_raw + delta_offset)

    def set_view_scale(self, scale: float):
        self.view_scale = max(min(scale, self.view_scale_max), self.view_scale_min)
        self._on_view_changed()
        self.viewScaleChanged.emit(self.view_scale)

    def reset_view(self):
        self.set_view_scale(1.0)
        self.set_view_offset_raw(QPointF())

    def set_view_offset_raw(self, offset: QPointF):
        self.view_offset_raw = offset
        self.viewOffsetChanged.emit(self.center_view_offset)
        self._on_view_changed()

    def _on_view_changed(self):
        # TODO: use event, or custom layout
        # update all geometry
        for btn in self.buttons:
            self._update_btn_geometry(btn)

    def _on_scene_selection_changed(self, client_data=None):
        """Called when the Maya scene selection has changed. Update the picker's display."""
        self.update_btn_selection_to_match_scene()

    def update_btn_selection_to_match_scene(self):
        sel = pm.selected()
        for btn in self.buttons:
            btn.set_is_selected(btn.is_node_selected(sel))

    def add_picker_btn(self, location: QPoint, size: QSize):
        """
        Add a picker button at the given unscaled location and size.
        """
        node = None
        sel = pm.selected()
        if sel:
            node = sel[0].nodeName()
            pm.select(sel[0], deselect=True)

        btn = AnimPickerButton(location, size, node, self)
        self._update_btn_geometry(btn)
        self.buttons.append(btn)
        btn.show()
        return btn

    def delete_selected_buttons(self):
        sel_btns = [btn for btn in self.buttons if btn.is_selected()]
        for btn in sel_btns:
            btn.setParent(None)
            btn.deleteLater()
            self.buttons.remove(btn)

    def _update_btn_geometry(self, btn: AnimPickerButton):
        """
        Update the actual geometry of a button to include its position and view transformations.
        """
        grid_location = self._snap_pos_to_grid(btn.location)
        center_offset = (QPointF(*btn.size.toTuple()) * 0.5).toPoint()
        rect = QRect(grid_location - center_offset, btn.size)
        btn.setGeometry(self.transform_rect(rect))

    def _snap_pos_to_grid(self, pos: QPoint):
        """
        Snap a position to the picker grid.
        """
        x = round(pos.x() / self.grid_size.x()) * self.grid_size.x()
        y = round(pos.y() / self.grid_size.y()) * self.grid_size.y()
        return QPoint(x, y)

    def get_buttons_in_rect(self, rect: QRect):
        """
        Return all buttons intersecting a rect.

        Args:
            rect: A rectangle in view space.
        """
        for btn in self.buttons:
            if btn.geometry().intersects(rect):
                yield btn

    def select_buttons_in_rect(self, rect: QRect):
        """
        Select all buttons that intersect a rectangle.

        Args:
            rect: A rectangle in view space.
        """
        sel_nodes = pm.selected()

        def _should_btn_be_selected(_btn):
            is_intersecting = _btn.geometry().intersects(rect)
            if _btn.is_node_set():
                # use scene selection
                if self.select_operation == AnimPickerSelectOperation.ADD:
                    # either intersecting, or previously selected
                    return is_intersecting or _btn.is_node_selected(sel_nodes)
                elif self.select_operation == AnimPickerSelectOperation.TOGGLE:
                    # return the inverse of selected if intersecting
                    is_selected = _btn.is_node_selected(sel_nodes)
                    return (not is_selected) if is_intersecting else is_selected
                elif self.select_operation == AnimPickerSelectOperation.DESELECT:
                    # must not be intersecting and previously selected
                    return not is_intersecting and _btn.is_node_selected(sel_nodes)
                else:
                    # operation is either REPLACE or EDIT
                    # intersection fully determines selection
                    return is_intersecting
            else:
                # use button selection only
                if (
                    self.select_operation == AnimPickerSelectOperation.ADD
                    or self.select_operation == AnimPickerSelectOperation.TOGGLE
                ):
                    # no toggle for node-less buttons, only add
                    return is_intersecting or _btn.is_selected()
                elif self.select_operation == AnimPickerSelectOperation.DESELECT:
                    return not is_intersecting and _btn.is_selected()
                else:
                    # operation is either REPLACE or EDIT
                    # intersection fully determines selection
                    return is_intersecting

        # pre-selecting means the scene nodes will not be selected until we
        # commit this selection later, the buttons will just be highlighted
        is_pre_select = (not self.select_on_drag) or (self.select_operation == AnimPickerSelectOperation.EDIT)

        for btn in self.buttons:
            should_be_selected = _should_btn_be_selected(btn)
            if btn.is_selected() != should_be_selected:
                if should_be_selected:
                    btn.select(is_pre_select)
                else:
                    btn.deselect(is_pre_select)

    def cancel_selections(self):
        """
        Cancel any currently pending drag selection.
        """
        self.update_btn_selection_to_match_scene()

    def commit_selections(self):
        """
        Select/add/deselect any pending nodes that were pre-selected during a drag select.
        """
        if self.select_operation == AnimPickerSelectOperation.REPLACE:
            # select all selected btn nodes
            node_args = [btn.node for btn in self.buttons if btn.is_selected()]
            sel_kwargs = dict(replace=True)

        elif self.select_operation == AnimPickerSelectOperation.ADD:
            # find buttons that are selected, but their nodes are not
            sel = cmds.ls(selection=True)
            node_args = [btn.node for btn in self.buttons if btn.is_selected() and not btn.is_node_selected(sel)]
            sel_kwargs = dict(add=True)

        elif self.select_operation == AnimPickerSelectOperation.TOGGLE:
            # find any buttons that don't match, and mark them for toggle
            sel = cmds.ls(selection=True)
            node_args = [btn.node for btn in self.buttons if btn.is_selected() != btn.is_node_selected(sel)]
            sel_kwargs = dict(toggle=True)

        elif self.select_operation == AnimPickerSelectOperation.DESELECT:
            # find buttons that are no longer selected, and deselect their nodes
            sel = cmds.ls(selection=True)
            node_args = [btn.node for btn in self.buttons if not btn.is_selected() and btn.is_node_selected(sel)]
            sel_kwargs = dict(deselect=True)

        else:
            # don't change scene selection when using EDIT or NONE operation
            return

        # run the select
        try:
            pm.select(node_args, **sel_kwargs)
        except TypeError as e:
            logger.warning(f"{e}")
            # if selection fails, make sure buttons revert to match scene selection
            self.update_btn_selection_to_match_scene()


class AnimPickerWidget(QtWidgets.QWidget):
    is_locked = option_var_property("pulse.anim.pickerLocked", True)

    def set_is_locked(self, value: bool):
        if self.is_locked != value:
            self.is_locked = value
            self._on_locked_changed()

    # called when the locked state of the picker has changed
    lockedChanged = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super(AnimPickerWidget, self).__init__(parent=parent)

        self.ui = Ui_AnimPicker()
        self.ui.setupUi(self)

        self.picker_panel = AnimPickerPanel(self)
        self.picker_panel.viewScaleChanged.connect(self._on_view_scale_changed)
        self.picker_panel.viewOffsetChanged.connect(self._on_view_offset_changed)
        self.ui.panel_layout.addWidget(self.picker_panel)

        self.ui.toggle_lock_btn.clicked.connect(self.toggle_locked)
        self.ui.zoom_reset_btn.clicked.connect(self.picker_panel.reset_view)

        self._update_zoom_label()
        self._on_locked_changed()

    def _on_view_scale_changed(self, view_scale: float):
        self._update_zoom_label()

    def _on_view_offset_changed(self, offset: QPoint):
        self._update_zoom_label()

    def _update_zoom_label(self):
        panel = self.picker_panel
        self.ui.zoom_label.setText(f"{panel.view_scale:.02f} ({panel.view_offset.x()}, {panel.view_offset.y()})")

    def toggle_locked(self):
        self.set_is_locked(not self.is_locked)

    def _on_locked_changed(self):
        self.picker_panel.set_is_locked(self.is_locked)
        if self.is_locked:
            self.ui.toggle_lock_btn.setIcon(QtGui.QIcon(":/icon/lock.svg"))
            self.ui.locked_label.setText("Locked")
        else:
            self.ui.toggle_lock_btn.setIcon(QtGui.QIcon(":/icon/lock_open.svg"))
            self.ui.locked_label.setText("Unlocked")


class AnimPickerWindow(PulseWindow):
    OBJECT_NAME = "pulseAnimPickerWindow"
    WINDOW_MODULE = "pulse.ui.anim.picker"
    WINDOW_TITLE = "Anim Picker"
    WIDGET_CLASS = AnimPickerWidget
