"""
An anim picker for easily selecting controls while animating.
"""
import logging
from typing import List, Optional
from maya import OpenMaya
import pymel.core as pm

from ... import nodes
from ...colors import LinearColor
from ...vendor.Qt import QtCore, QtGui, QtWidgets
from ...vendor.Qt.QtCore import QPoint, QPointF, QRect, QRectF, QSize, QSizeF

from ..core import PulseWindow

from ..gen.anim_picker import Ui_AnimPicker

logger = logging.getLogger(__name__)


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
        self.node: Optional[str] = None
        self.color: Optional[LinearColor] = None

        self.clicked.connect(self.select)

    def is_selected(self):
        return self._is_selected

    def select(self):
        """Select this button's node."""
        try:
            pm.select(self.node, add=True)
        except TypeError as e:
            logger.warning(f"{e}")
        self.set_is_selected(True)

    def deselect(self):
        """Deselect the button's node."""
        try:
            pm.select(self.node, deselect=True)
        except TypeError as e:
            pass
        self.set_is_selected(False)

    def set_is_selected(self, value: bool):
        self._is_selected = value
        if value:
            self.setStyleSheet("background-color: white")
        else:
            if self.color:
                self.setStyleSheet(self.color.as_bg_style())
            else:
                self.setStyleSheet("")

    def set_node(self, node: Optional[str]):
        self.node = node
        self.setStatusTip(self.node if self.node else "")
        try:
            pynode = pm.PyNode(node)
        except:
            pass
        else:
            self.color = nodes.get_override_color(pynode)
            if self.color and not self.is_selected():
                self.color.a = 0.5
                self.setStyleSheet(self.color.as_bg_style())


class AnimPickerPanel(QtWidgets.QWidget):
    viewScaleChanged = QtCore.Signal(float)
    viewOffsetChanged = QtCore.Signal(QPoint)

    def __init__(self, parent=None):
        super(AnimPickerPanel, self).__init__(parent=parent)

        self.rubber_band: Optional[QtWidgets.QRubberBand] = None
        self.default_btn_size = QSize(40, 40)
        self.view_offset_raw = QPointF()
        self.view_scale = 1.0
        self.view_scale_min = 0.25
        self.view_scale_max = 3.0
        self.wheel_zoom_sensitivity = 0.001
        self.select_on_drag = True
        # the current list of selected buttons
        self.selection: List[AnimPickerButton] = []
        self.selection_rect = QRect()
        self.is_drag_selecting = False
        # the list of all buttons
        self.buttons: List[AnimPickerButton] = []
        self.cb_ids = []
        self.drag_pan_last_pos = QPoint()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        frame = QtWidgets.QFrame(self)
        frame.setStyleSheet("background-color: rgba(255, 255, 255, 10%)")
        layout.addWidget(frame)

    def __del__(self):
        self._unregister_callbacks()

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

    def wheelEvent(self, event: QtGui.QWheelEvent):
        # zoom in and out
        old_view_scale = self.view_scale
        delta_scale = event.delta() * self.wheel_zoom_sensitivity
        self.set_view_scale(self.view_scale + delta_scale)
        real_delta_scale = self.view_scale - old_view_scale

        # apply zoom centered on panel position
        focus_pos_ws = QPointF(self.inverse_transform_pos(event.pos()))
        delta_offset = focus_pos_ws * -real_delta_scale
        self.set_view_offset_raw(self.view_offset_raw + delta_offset)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            location = self.inverse_transform_pos(event.localPos().toPoint())
            self.add_picker_btn(location, self.default_btn_size)

        elif event.modifiers() & QtCore.Qt.AltModifier:
            self.drag_pan_last_pos = event.pos()

        else:
            # start selection
            self.start_selection(event.pos())
            if self.is_drag_selecting:
                if not self.rubber_band:
                    self.rubber_band = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
                self.rubber_band.setGeometry(self.selection_rect.normalized())
                self.rubber_band.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if event.modifiers() & QtCore.Qt.AltModifier:
            # drag panning
            delta = event.pos() - self.drag_pan_last_pos
            self.set_view_offset_raw(self.view_offset_raw + delta)
            self.drag_pan_last_pos = event.pos()

        elif self.is_drag_selecting:
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
        print(f"Add button at {location}")
        center_offset = (QPointF(size.width(), size.width()) * 0.5).toPoint()
        base_rect = QRect(location - center_offset, size)
        sel = pm.selected()
        btn = AnimPickerButton(base_rect, self)
        btn.setGeometry(self.transform_rect(btn.base_rect))
        if sel:
            btn.set_node(sel[0].nodeName())
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


class AnimPickerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AnimPickerWidget, self).__init__(parent=parent)

        self.ui = Ui_AnimPicker()
        self.ui.setupUi(self)

        self.picker_panel = AnimPickerPanel(self)
        self.picker_panel.viewScaleChanged.connect(self._on_view_scale_changed)
        self.picker_panel.viewOffsetChanged.connect(self._on_view_offset_changed)
        self.ui.panel_layout.addWidget(self.picker_panel)

        self.ui.zoom_reset_btn.clicked.connect(self.picker_panel.reset_view)
        self._update_zoom_label()

    def _on_view_scale_changed(self, view_scale: float):
        self._update_zoom_label()

    def _on_view_offset_changed(self, offset: QPoint):
        self._update_zoom_label()

    def _update_zoom_label(self):
        panel = self.picker_panel
        self.ui.zoom_label.setText(f"{panel.view_scale:.02f} ({panel.view_offset.x()}, {panel.view_offset.y()})")


class AnimPickerWindow(PulseWindow):
    OBJECT_NAME = "pulseAnimPickerWindow"
    WINDOW_MODULE = "pulse.ui.anim.picker"
    WINDOW_TITLE = "Anim Picker"
    WIDGET_CLASS = AnimPickerWidget
