"""
An anim picker for easily selecting controls while animating.
"""

from typing import List, Optional
from maya import OpenMaya
import pymel.core as pm

from ...vendor.Qt import QtCore, QtGui, QtWidgets
from ...vendor.Qt.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF

from ..core import PulseWindow

from ..gen.anim_picker import Ui_AnimPicker


def scale_rect(rect: QRect, scale: float) -> QRect:
    top_left = (QPointF(rect.topLeft()) * scale).toPoint()
    return QRect(top_left, rect.size() * scale)


class AnimPickerButton(QtWidgets.QPushButton):
    def __init__(self, base_rect: QRect, parent=None):
        super(AnimPickerButton, self).__init__(parent=parent)

        # the geometry of this button at 1x zoom
        self.base_rect = base_rect
        self._is_selected = False
        # the node this button selects
        self.node: Optional[pm.PyNode] = None

    def is_selected(self):
        return self._is_selected

    def select(self):
        """Select this button's node."""
        pm.select(self.node, add=True)
        self.set_is_selected(True)

    def deselect(self):
        """Deselect the button's node."""
        pm.select(self.node, deselect=True)
        self.set_is_selected(False)

    def set_is_selected(self, value: bool):
        self._is_selected = value
        if value:
            self.setStyleSheet("background-color: white")
        else:
            self.setStyleSheet("")

    def set_node(self, node: Optional[pm.PyNode]):
        self.node = node


class AnimPickerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AnimPickerWidget, self).__init__(parent=parent)

        self.rubber_band: Optional[QtWidgets.QRubberBand] = None
        self.default_btn_size = QSize(20, 20)
        self.view_offset = QPoint()
        self.view_scale = 1.0
        self.view_scale_min = 0.1
        self.view_scale_max = 5.0
        self.wheel_zoom_sensitivity = 0.001
        self.select_on_drag = True
        # the current list of selected buttons
        self.selection: List[AnimPickerButton] = []
        self.selection_rect = QRect()
        self.is_drag_selecting = False
        # the list of all buttons
        self.buttons: List[AnimPickerButton] = []
        self.cb_ids = []

        self.ui = Ui_AnimPicker()
        self.ui.setupUi(self)

        self.ui.zoom_reset_btn.clicked.connect(self.reset_view_scale)

        self._update_zoom_label()

    def showEvent(self, event: QtGui.QShowEvent):
        super(AnimPickerWidget, self).showEvent(event)
        cb_id = OpenMaya.MEventMessage.addEventCallback("SelectionChanged", self._on_scene_selection_changed)
        self.cb_ids.append(cb_id)

    def hideEvent(self, event: QtGui.QHideEvent):
        super(AnimPickerWidget, self).hideEvent(event)
        for cb_id in self.cb_ids:
            OpenMaya.MMessage.removeCallback(cb_id)

    def transform_rect(self, rect: QRect) -> QRect:
        """Transform a position to view space."""
        return scale_rect(rect, self.view_scale)

    def inverse_transform_rect(self, rect: QRect) -> QRect:
        """Inverse transform from view space."""
        return scale_rect(rect, 1.0 / self.view_scale)

    def transform_pos(self, point: QPoint) -> QPoint:
        return ((QPointF(point) + self.view_offset) * self.view_scale).toPoint()

    def inverse_transform_pos(self, point: QPoint) -> QPoint:
        return (QPointF(point) * (1 / self.view_scale) - self.view_offset).toPoint()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        delta_scale = event.delta() * self.wheel_zoom_sensitivity
        self.set_view_scale(self.view_scale + delta_scale)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            location = self.inverse_transform_pos(event.localPos().toPoint())
            self.add_picker_btn(location, self.default_btn_size)
        else:
            # start selection
            self.start_selection(event.pos())
            if self.is_drag_selecting:
                if not self.rubber_band:
                    self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
                self.rubber_band.setGeometry(self.selection_rect.normalized())
                self.rubber_band.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.is_drag_selecting:
            self.update_selection(event.pos())
            if self.rubber_band:
                self.rubber_band.setGeometry(self.selection_rect.normalized())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        if self.is_drag_selecting:
            self.finish_selection(event.pos())
            if self.rubber_band:
                self.rubber_band.hide()

    def start_selection(self, origin: QPoint):
        pm.select(clear=True)
        self.is_drag_selecting = True
        self.selection_rect = QRect(origin, QSize())

    def update_selection(self, pos: QPoint):
        # always set bottom right to preserve direction, use normalize when needed
        self.selection_rect.setBottomRight(pos)
        if self.select_on_drag:
            self.select_buttons_in_rect(self.selection_rect.normalized())

    def finish_selection(self, pos: QPoint):
        self.is_drag_selecting = False
        self.selection_rect.setBottomRight(pos)
        self.select_buttons_in_rect(self.selection_rect.normalized())

    def set_view_scale(self, scale: float):
        self.view_scale = max(min(scale, self.view_scale_max), self.view_scale_min)
        self._on_view_scale_changed()

    def reset_view_scale(self):
        self.set_view_scale(1.0)

    def _update_zoom_label(self):
        self.ui.zoom_label.setText("%.02f" % self.view_scale)

    def _on_view_scale_changed(self):
        self._update_zoom_label()

        # TODO: use event, or custom layout
        # update all geometry
        for btn in self.buttons:
            btn.setGeometry(self.transform_rect(btn.base_rect))

    def _on_scene_selection_changed(self, client_data=None):
        """Called when the Maya scene selection has changed. Update the picker's display."""
        sel = pm.selected()
        for btn in self.buttons:
            btn.set_is_selected(btn.node in sel)

    def add_picker_btn(self, location: QPoint, size: QSize):
        """
        Add a picker button at the given unscaled location and size.
        """
        base_rect = QRect(location, size)
        sel = pm.selected()
        btn = AnimPickerButton(base_rect, self)
        btn.setGeometry(self.transform_rect(btn.base_rect))
        if sel:
            btn.set_node(sel[0])
            pm.select(sel[0], deselect=True)
        self.buttons.append(btn)
        btn.show()

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
        self.selection.clear()
        for btn in self.buttons:
            is_intersecting = btn.geometry().intersects(rect)
            if is_intersecting:
                if not btn.is_selected():
                    self.selection.append(btn)
                    btn.select()
            elif btn.is_selected():
                btn.deselect()


class AnimPickerWindow(PulseWindow):
    OBJECT_NAME = "pulseAnimPickerWindow"
    WINDOW_MODULE = "pulse.ui.anim.picker"
    WINDOW_TITLE = "Anim Picker"
    WIDGET_CLASS = AnimPickerWidget
