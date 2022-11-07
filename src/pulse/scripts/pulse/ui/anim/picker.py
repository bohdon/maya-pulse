"""
An anim picker for easily selecting controls while animating.
"""

from ...vendor.Qt import QtCore, QtGui, QtWidgets

from ..core import PulseWindow

from ..gen.anim_picker import Ui_AnimPicker


class AnimPickerButton(QtWidgets.QPushButton):
    def __init__(self, location: QtCore.QPoint, size: QtCore.QSize, parent=None):
        super(AnimPickerButton, self).__init__(parent=parent)

        # the virtual location of this button at 1x zoom
        self.location = location
        # the virtual size of this button at 1x zoom
        self.size = size


class AnimPickerWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(AnimPickerWidget, self).__init__(parent=parent)

        self.default_btn_size = QtCore.QSize(20, 20)
        self.view_scale = 1.0
        self.view_scale_min = 0.1
        self.view_scale_max = 5.0
        self.wheel_zoom_sensitivity = 0.001

        self.ui = Ui_AnimPicker()
        self.ui.setupUi(self)

        self._update_zoom_label()

    def wheelEvent(self, event: QtGui.QWheelEvent):
        delta_scale = event.delta() * self.wheel_zoom_sensitivity
        self.set_view_scale(self.view_scale + delta_scale)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        print(event.localPos())
        self.add_picker_btn(event.localPos().toPoint(), self.default_btn_size)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        print(event.localPos())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        print(event.localPos())

    def set_view_scale(self, scale: float):
        self.view_scale = max(min(scale, self.view_scale_max), self.view_scale_min)
        self._on_view_scale_changed()

    def _update_zoom_label(self):
        self.ui.zoom_label.setText("%.02f" % self.view_scale)

    def _on_view_scale_changed(self):
        self._update_zoom_label()

        # update all geometry
        for child in self.children():
            if isinstance(child, AnimPickerButton):
                child.setGeometry(self._get_scaled_geometry(child.location, child.size))

    def add_picker_btn(self, location: QtCore.QPoint, size: QtCore.QSize):
        print(f"adding button, location: {location}, size: {size}")
        btn = AnimPickerButton(location, size, self)
        btn.setGeometry(self._get_scaled_geometry(btn.location, btn.size))
        btn.show()

    def _get_scaled_geometry(self, location: QtCore.QPoint, size: QtCore.QSize) -> QtCore.QRect:
        x = location.x() * self.view_scale
        y = location.y() * self.view_scale
        width = size.width() * self.view_scale
        height = size.height() * self.view_scale
        return QtCore.QRect(int(x), int(y), int(width), int(height))


class AnimPickerWindow(PulseWindow):
    OBJECT_NAME = "pulseAnimPickerWindow"
    WINDOW_MODULE = "pulse.ui.anim.picker"
    WINDOW_TITLE = "Anim Picker"
    WIDGET_CLASS = AnimPickerWidget
