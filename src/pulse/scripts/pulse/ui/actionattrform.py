"""
Form ui classes for any type of action attribute, e.g.
float forms, node and node list forms, combo box forms, etc.
"""
import logging
import os.path
from typing import Optional, cast

import maya.cmds as cmds
import pymel.core as pm

from .core import BuildStepTreeModel
from ..build_items import BuildStep, BuildActionProxy, BuildActionAttribute, BuildActionAttributeType
from ..vendor import pymetanode as meta
from ..serializer import serialize_attr_value
from ..vendor.Qt import QtCore, QtGui, QtWidgets
from .. import names
from . import utils

LOG = logging.getLogger(__name__)

SELECT_ICON_PATH = ":/icon/circle_left.svg"
RESET_ICON_PATH = ":/icon/reset.svg"
TOOL_ICON_SIZE = QtCore.QSize(20, 20)


class ActionAttrFormBase(QtWidgets.QFrame):
    def __init__(self, index: QtCore.QModelIndex, attr: BuildActionAttribute, parent=None):
        super(ActionAttrFormBase, self).__init__(parent=parent)

        self.setObjectName("formFrame")

        # the model index of the action being edited
        self.index = QtCore.QPersistentModelIndex(index)
        # the attribute being edited
        self.attr = attr

        self.setup_ui(self)

        # listen to model change events
        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def on_model_data_changed(self):
        """
        Called when the data for this attribute has changed.
        """
        pass

    def can_ever_reset_value(self) -> bool:
        """
        Should a reset value button be created for this attribute form?
        """
        return True

    def setup_ui(self, parent):
        """
        Build the appropriate ui for the attribute.
        Should call `setup_default_form_ui` when using the standard form label and value layout.
        """
        raise NotImplementedError

    def setup_default_form_ui(self, parent):
        self.main_layout = QtWidgets.QHBoxLayout(parent)
        # margin that will give us some visible area of
        # the frame that can change color based on valid state
        self.main_layout.setMargin(2)

        # create main form layout
        self.form_layout = QtWidgets.QFormLayout(parent)
        self.form_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.form_layout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop | QtCore.Qt.AlignTrailing)
        self.form_layout.setHorizontalSpacing(10)

        # create and add label layout to form
        self.setup_label_ui(parent)
        self.form_layout.setLayout(0, QtWidgets.QFormLayout.LabelRole, self.label_layout)
        self.main_layout.addLayout(self.form_layout)

        if self.can_ever_reset_value():
            # add reset value button
            self.reset_value_btn = QtWidgets.QToolButton(parent)
            self.reset_value_btn.setIcon(QtGui.QIcon(RESET_ICON_PATH))
            self.reset_value_btn.setFixedSize(TOOL_ICON_SIZE)
            utils.set_retain_size_when_hidden(self.reset_value_btn, True)
            self.reset_value_btn.setStatusTip("Reset value to default")
            self.reset_value_btn.clicked.connect(self.reset_value_to_default)

            self.main_layout.addWidget(self.reset_value_btn)
            self.main_layout.setAlignment(self.reset_value_btn, QtCore.Qt.AlignTop)
        else:
            # ensure variable exists
            self.reset_value_btn = None

    def setup_label_ui(self, parent):
        """
        Create the label layout and add the main attribute label to it.
        """
        self.label_layout = QtWidgets.QHBoxLayout(parent)

        # attribute name label
        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignTop)
        # add some space above the label, so it lines up
        self.label.setMargin(2)
        self.label.setText(names.to_title(self.attr.name))
        # set description tooltips
        description = self.attr.description
        if description:
            self.label.setStatusTip(description)

        self.label_layout.addWidget(self.label)

    def set_default_form_widget(self, widget):
        """
        Set the widget to be used as the field in the default form layout
        Requires `setup_default_form_ui` to be used.
        """
        self.form_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, widget)

    def set_default_form_layout(self, layout):
        """
        Set the layout to be used as the field in the default form layout.
        Requires `setup_default_form_ui` to be used.
        """
        self.form_layout.setLayout(0, QtWidgets.QFormLayout.FieldRole, layout)


class ActionAttrForm(ActionAttrFormBase):
    """
    The base class for all forms used to edit action attributes.
    Provides input validation and basic signals for keeping
    track of value changes.
    """

    # map of attribute types to form widget classes
    TYPE_MAP: dict[Optional[str], type["ActionAttrForm"]] = {}

    LABEL_WIDTH = 120
    LABEL_HEIGHT = 20
    FORM_WIDTH_SMALL = 80

    @staticmethod
    def create_form(
        index: QtCore.QModelIndex, attr: BuildActionAttribute, variant_index=-1, parent=None
    ) -> "ActionAttrForm":
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            index: A QModelIndex pointing to the BuildStep being edited
            attr: The attribute being edited.
            variant_index: The variant index being edited.
            parent: The parent object.
        """
        if attr.type is None:
            LOG.error(f"Attribute has no type: {attr}")
            # TODO: create a generic attribute form that just displays the error

        if attr.type in ActionAttrForm.TYPE_MAP:
            return ActionAttrForm.TYPE_MAP[attr.type](index, attr, variant_index, parent=parent)

        # type not found, fallback to None type
        if None in ActionAttrForm.TYPE_MAP:
            return ActionAttrForm.TYPE_MAP[None](index, attr, variant_index, parent=parent)

    @classmethod
    def add_form_type(cls, type_name: Optional[str], form_cls: type["ActionAttrForm"]):
        """
        Register an attribute form by attribute type.
        Args:
            type_name: The attribute type.
            form_cls: The action attribute form to register for the type.
        """
        cls.TYPE_MAP[type_name] = form_cls

    def __init__(self, index: QtCore.QModelIndex, attr: BuildActionAttribute, variant_index: int, parent=None):
        # the index of the variant being edited
        self.variant_index = variant_index

        super(ActionAttrForm, self).__init__(index, attr, parent=parent)

        # update valid state, check both type and value here
        # because the current value may be of an invalid type
        self._update_valid_state()
        self._update_reset_visible()

    def _update_valid_state(self):
        """
        Update the state of the ui to represent whether the attribute value is currently valid.
        """
        # if false, the input is not acceptable, e.g. badly formatted
        is_form_valid = self._is_form_value_valid()

        # if false, the type might be wrong, value out of range, or missing a required input
        self.attr.validate()
        is_value_valid = self._is_form_value_valid() and self.attr.is_value_valid()

        self._set_ui_valid_state(is_value_valid, is_form_valid)

    def _update_reset_visible(self):
        if self.reset_value_btn:
            self.reset_value_btn.setVisible(self.is_value_set())

    def on_model_data_changed(self):
        """ """
        # TODO: only update if the change affected this attribute
        if not self.index.isValid():
            self.hide()
            return

        action_proxy = self.get_action_proxy()
        if not action_proxy:
            self.hide()
            return

        # update form
        self._set_form_value(self.get_attr_value())
        self._update_reset_visible()
        self._update_valid_state()

    def is_variant(self):
        return self.variant_index >= 0

    def get_attr_value(self):
        return self.attr.get_value()

    def set_attr_value(self, new_value):
        """
        Set the current value of the attribute in this form.
        Performs partial validation and prevents actually setting
        the attribute value if it's type is invalid.
        """
        if not self.attr.is_acceptable_value(new_value):
            # invalid type or otherwise unacceptable value
            return

        attr_path = self.get_attr_path()
        if not attr_path:
            return

        str_value = serialize_attr_value(new_value)
        cmds.pulseSetActionAttr(attr_path, str_value, v=self.variant_index)
        # refresh form to the new value in case it was cleaned up or processed
        self._set_form_value(self.attr.get_value())

    def is_value_set(self) -> bool:
        """
        Return true if the attribute has been set to a non-default value.
        """
        return self.attr.is_value_set() or self._get_form_value() != self.get_attr_value()

    def reset_value_to_default(self):
        self.set_attr_value(self.attr.default_value)

    def setup_ui(self, parent):
        """
        Build the appropriate ui for the attribute
        """
        raise NotImplementedError

    def get_step(self) -> BuildStep:
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_action_proxy(self) -> BuildActionProxy:
        step = self.get_step()
        if step and step.is_action():
            return step.action_proxy

    def get_attr_path(self):
        step = self.get_step()
        if not step:
            return

        return f"{step.get_full_path()}.{self.attr.name}"

    def _set_form_value(self, attr_value):
        """
        Set the current value displayed in the UI form
        """
        raise NotImplementedError

    def _get_form_value(self):
        """
        Return the current value entered into the form.
        It may not be an acceptable or valid attribute value.
        """
        # default implementation has no separate form value
        return self.get_attr_value()

    def _is_form_value_valid(self):
        """
        Return True if the current form contains valid data.
        The attribute value will not be set unless the form has valid data to prevent a bad state.
        """
        return self.attr.is_acceptable_value(self._get_form_value())

    def _on_value_edited(self):
        """
        Called when the value represented in the form has been edited by the user.
        Try to set the attribute to the new value, or update the valid state of the form.
        """
        if self._is_form_value_valid():
            # update the attributes value
            self.set_attr_value(self._get_form_value())
        else:
            # cant set the attribute, but indicate invalid state
            self._update_valid_state()
            self._update_reset_visible()

    def _set_ui_valid_state(self, is_valid, is_form_valid):
        if is_valid:
            self.label.setToolTip("")
            self.setProperty("cssClasses", "")
        elif is_form_valid:
            reason = self.attr.get_invalid_reason()
            self.label.setToolTip(f"Invalid: {reason}")
            self.setProperty("cssClasses", "warning")
        else:
            self.label.setToolTip("Invalid input")
            self.setProperty("cssClasses", "error")

        # force a styling refresh to make use of cssClasses
        self.setStyleSheet("")


class BatchAttrForm(ActionAttrFormBase):
    """
    The base class for an attribute form designed to bulk edit all variants
    of an attribute on an action proxy. This appears where the default attr
    form usually appears when the attribute is marked as variant.
    """

    TYPE_MAP: dict[Optional[str], type["BatchAttrForm"]] = {}

    LABEL_WIDTH = ActionAttrForm.LABEL_WIDTH
    LABEL_HEIGHT = ActionAttrForm.LABEL_HEIGHT
    FORM_WIDTH_SMALL = ActionAttrForm.FORM_WIDTH_SMALL

    @staticmethod
    def does_form_exist(attr: BuildActionAttribute):
        return attr.type in BatchAttrForm.TYPE_MAP

    @staticmethod
    def create_form(index, attr: BuildActionAttribute, parent=None):
        """
        Create a new ActionAttrForm of the appropriate type based on a BuildAction attribute.
        """
        if attr.type in BatchAttrForm.TYPE_MAP:
            return BatchAttrForm.TYPE_MAP[attr.type](index, attr, parent=parent)

        # type not found, fallback to None type
        if None in BatchAttrForm.TYPE_MAP:
            return BatchAttrForm.TYPE_MAP[None](index, attr, parent=parent)

    @classmethod
    def add_form_type(cls, attr_type: Optional[str], form_class: type["BatchAttrForm"]):
        cls.TYPE_MAP[attr_type] = form_class

    def can_ever_reset_value(self) -> bool:
        """
        Not allowed to reset values for batch attribute forms.
        """
        return False

    def setup_default_form_ui(self, parent):
        """
        Optional UI setup that builds a standardized layout.
        Includes a form layout and a label with the attributes name.
        Should be called at the start of setup_ui if desired.
        """
        super(BatchAttrForm, self).setup_default_form_ui(parent)
        # dim label for batch attributes
        self.label.setEnabled(False)

    def get_step(self) -> BuildStep:
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_action_proxy(self) -> BuildActionProxy:
        step = self.get_step()
        if step and step.is_action():
            return step.action_proxy

    def get_attr_path(self):
        step = self.get_step()
        if not step:
            return

        return f"{step.get_full_path()}.{self.attr.name}"

    def set_variant_values(self, values):
        attr_path = self.get_attr_path()
        if not attr_path:
            return

        for i, value in enumerate(values):
            str_value = serialize_attr_value(value)
            cmds.pulseSetActionAttr(attr_path, str_value, v=i)


class DefaultAttrForm(ActionAttrForm):
    """
    A catchall attribute form that can handle any attribute type by leveraging pymetanode serialization.
    Provides a text field where values can be typed in serialized string form.
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self._did_fail_decode = False

        self.text_edit = QtWidgets.QLineEdit(parent)
        # TODO: use cssClasses
        self.text_edit.setStyleSheet('font: 8pt "Consolas";')

        self._set_form_value(self.get_attr_value())

        self.text_edit.editingFinished.connect(self._on_value_edited)

        self.set_default_form_widget(self.text_edit)

    def _set_form_value(self, attr_value):
        if isinstance(attr_value, str):
            self.text_edit.setText(repr(attr_value))
        else:
            self.text_edit.setText(meta.encodeMetaData(attr_value))

    def _hasSyntaxErrors(self) -> bool:
        """
        Return true if the current form value has syntax errors that prevent
        it from being able to decode.
        """
        try:
            meta.decodeMetaData(self.text_edit.text())
            return True
        except:
            return False

    def _get_form_value(self):
        try:
            return meta.decodeMetaData(self.text_edit.text())
        except:
            return None

    def _is_form_value_valid(self):
        try:
            meta.decodeMetaData(self.text_edit.text())
        except Exception as e:
            return False
        return super(DefaultAttrForm, self)._is_form_value_valid()

    def _on_value_edited(self):
        """
        If the form text is empty, but the value is not acceptable, reset the attribute to the default
        value for the type. Useful for list or complex data types where typing the default value would be tedious.

        Note that that's not the same as the default value that may be set in the config, e.g. an empty list
        instead of potentially a list with config-defined default values in it.
        """
        if not self._is_form_value_valid():
            if not self.text_edit.text().strip(" "):
                self.set_attr_value(self.attr.get_type_default_value())
                self._update_valid_state()
                return

        super(DefaultAttrForm, self)._on_value_edited()


ActionAttrForm.add_form_type(BuildActionAttributeType.UNKNOWN, DefaultAttrForm)


class BoolAttrForm(ActionAttrForm):
    """
    A simple checkbox attribute form
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self.checkbox = QtWidgets.QCheckBox(parent)
        self._set_form_value(self.get_attr_value())
        self.checkbox.setMinimumHeight(self.LABEL_HEIGHT)
        self.checkbox.stateChanged.connect(self._on_value_edited)

        self.set_default_form_widget(self.checkbox)

    def _set_form_value(self, attr_value):
        self.checkbox.setChecked(attr_value)

    def _get_form_value(self):
        return self.checkbox.isChecked()


# TODO: put attribute type names in an enum class
ActionAttrForm.add_form_type(BuildActionAttributeType.BOOL, BoolAttrForm)


class IntAttrForm(ActionAttrForm):
    """
    A simple integer attribute form
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self.spin_box = QtWidgets.QSpinBox(parent)
        self.spin_box.setMinimumHeight(self.LABEL_HEIGHT)
        self.spin_box.setMinimumWidth(self.FORM_WIDTH_SMALL)
        self.spin_box.setRange(self.attr.config.get("min", 0), self.attr.config.get("max", 100))
        self._set_form_value(self.get_attr_value())
        self.spin_box.valueChanged.connect(self._on_value_edited)

        self.set_default_form_widget(self.spin_box)

    def _set_form_value(self, attr_value):
        self.spin_box.setValue(attr_value)

    def _get_form_value(self):
        return self.spin_box.value()


ActionAttrForm.add_form_type(BuildActionAttributeType.INT, IntAttrForm)


class FloatAttrForm(ActionAttrForm):
    """
    A simple float attribute form
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self.spin_box = QtWidgets.QDoubleSpinBox(parent)
        self.spin_box.setMinimumHeight(self.LABEL_HEIGHT)
        self.spin_box.setMinimumWidth(self.FORM_WIDTH_SMALL)
        self.spin_box.setDecimals(self.attr.config.get("decimals", 3))
        self.spin_box.setSingleStep(self.attr.config.get("stepSize", 0.1))
        self.spin_box.setRange(self.attr.config.get("min", 0), self.attr.config.get("max", 100))
        self._set_form_value(self.get_attr_value())
        self.spin_box.valueChanged.connect(self._on_value_edited)

        self.set_default_form_widget(self.spin_box)

    def _set_form_value(self, attr_value):
        self.spin_box.setValue(attr_value)

    def _get_form_value(self):
        return self.spin_box.value()


ActionAttrForm.add_form_type(BuildActionAttributeType.FLOAT, FloatAttrForm)


class StringAttrForm(ActionAttrForm):
    """
    A simple string attribute form
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self.line_edit = QtWidgets.QLineEdit(parent)
        self.line_edit.setMinimumHeight(self.LABEL_HEIGHT)
        self._set_form_value(self.get_attr_value())
        self.line_edit.editingFinished.connect(self._on_value_edited)

        self.set_default_form_widget(self.line_edit)

    def _set_form_value(self, attr_value):
        self.line_edit.setText(attr_value)

    def _get_form_value(self):
        return self.line_edit.text().strip(" ")


ActionAttrForm.add_form_type(BuildActionAttributeType.STRING, StringAttrForm)


class OptionAttrForm(ActionAttrForm):
    """
    An options list form that uses a combo box
    to display options and keeps data stored as an int value
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        self.combo = QtWidgets.QComboBox(parent)
        for option in self.attr.config.get("options", []):
            self.combo.addItem(option)
        self._set_form_value(self.get_attr_value())
        self.combo.currentIndexChanged.connect(self._on_value_edited)

        self.set_default_form_widget(self.combo)

    def _set_form_value(self, attr_value):
        self.combo.setCurrentIndex(attr_value)

    def _get_form_value(self):
        return self.combo.currentIndex()


ActionAttrForm.add_form_type(BuildActionAttributeType.OPTION, OptionAttrForm)


class NodeAttrForm(ActionAttrForm):
    """
    A special form that allows picking nodes from the scene.
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        h_layout = QtWidgets.QHBoxLayout(parent)
        h_layout.setSpacing(4)

        self.list_widget = QtWidgets.QListWidget(parent)
        self.list_widget.setFixedHeight(20)
        self.list_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.list_widget.setSortingEnabled(True)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self.onItemSelectionChanged)
        h_layout.addWidget(self.list_widget)

        self.pick_button = QtWidgets.QToolButton(parent)
        self.pick_button.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        self.pick_button.setStatusTip(
            "Assign the selected node. " "Ctrl + click to pop the assigned node from the selection."
        )
        self.pick_button.setFixedSize(TOOL_ICON_SIZE)
        self.pick_button.clicked.connect(self.setFromSelection)
        h_layout.addWidget(self.pick_button)
        h_layout.setAlignment(self.pick_button, QtCore.Qt.AlignTop)

        self._set_form_value(self.get_attr_value())

        self.set_default_form_layout(h_layout)

    def _set_form_value(self, attr_value):
        while self.list_widget.takeItem(0):
            pass
        if attr_value:
            item = QtWidgets.QListWidgetItem(attr_value.nodeName())
            uuid = meta.getUUID(attr_value)
            item.setData(QtCore.Qt.UserRole, uuid)
            self.list_widget.addItem(item)

    def _should_pop_selection(self):
        """
        Return true if the first selected node should be popped from the selection
        when assigning from selection. True when holding the control key.
        """
        return QtWidgets.QApplication.instance().keyboardModifiers() & QtCore.Qt.ControlModifier

    def setFromSelection(self):
        sel = pm.selected()
        if sel:
            self.set_attr_value(sel[0])
        else:
            self.set_attr_value(None)
        if self._should_pop_selection():
            pm.select(sel[1:])

    def onItemSelectionChanged(self):
        items = self.list_widget.selectedItems()
        nodes = []
        for item in items:
            node = meta.findNodeByUUID(item.data(QtCore.Qt.UserRole))
            if node:
                nodes.append(node)
        if nodes:
            pm.select(nodes)


ActionAttrForm.add_form_type(BuildActionAttributeType.NODE, NodeAttrForm)


class NodeListAttrForm(ActionAttrForm):
    """
    A special form that allows picking nodes from the scene.
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        h_layout = QtWidgets.QHBoxLayout(parent)
        h_layout.setSpacing(4)

        self.list_widget = QtWidgets.QListWidget(parent)
        self.list_widget.setSortingEnabled(True)
        self.list_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.list_widget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_item_selection_changed)
        h_layout.addWidget(self.list_widget)

        self.pick_button = QtWidgets.QToolButton(parent)
        self.pick_button.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        self.pick_button.setStatusTip("Assign the selected nodes.")
        self.pick_button.setFixedSize(TOOL_ICON_SIZE)
        self.pick_button.clicked.connect(self._set_from_selection)
        h_layout.addWidget(self.pick_button)
        h_layout.setAlignment(self.pick_button, QtCore.Qt.AlignTop)

        self.set_default_form_layout(h_layout)

        self._set_form_value(self.get_attr_value())

    def _set_form_value(self, attr_value):
        while self.list_widget.takeItem(0):
            pass
        for node in attr_value:
            if node:
                item = QtWidgets.QListWidgetItem(node.nodeName())
                uuid = meta.getUUID(node)
                item.setData(QtCore.Qt.UserRole, uuid)
                self.list_widget.addItem(item)
            else:
                self.list_widget.addItem("(missing)")
        # 13px line height per item, clamped in range 40..120, added 8px buffer
        new_height = max(40, min(120, 8 + 13 * self.list_widget.count()))
        self.list_widget.setFixedHeight(new_height)

    def _set_from_selection(self):
        self.set_attr_value(pm.selected())

    def _on_item_selection_changed(self):
        items = self.list_widget.selectedItems()
        nodes = []
        for item in items:
            node = meta.findNodeByUUID(item.data(QtCore.Qt.UserRole))
            if node:
                nodes.append(node)
        if nodes:
            pm.select(nodes)


ActionAttrForm.add_form_type(BuildActionAttributeType.NODE_LIST, NodeListAttrForm)


class FileAttrForm(ActionAttrForm):
    """
    Attribute form for a file path.

    Supports some custom attribute settings:
        startDir: The directory to start browsing from, defaults to the scene dir.
        fileFilter: The file type filter to apply, e.g. "FBX (*.fbx)"
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setSpacing(4)

        self.line_edit = QtWidgets.QLineEdit(parent)
        self.line_edit.setMinimumHeight(self.LABEL_HEIGHT)
        self._set_form_value(self.get_attr_value())
        self.line_edit.editingFinished.connect(self._on_value_edited)
        layout.addWidget(self.line_edit)

        btn = QtWidgets.QPushButton(parent)
        btn.setText("...")
        btn.clicked.connect(self._browse_for_file)
        btn.setFixedHeight(self.LABEL_HEIGHT - 2)
        layout.addWidget(btn)

        self.set_default_form_layout(layout)

    def _set_form_value(self, attr_value):
        self.line_edit.setText(attr_value)

    def _get_form_value(self):
        return self.line_edit.text().strip(" ")

    def _browse_for_file(self):
        kwargs = {}

        start_dir = self._get_starting_dir()
        if start_dir:
            kwargs["startingDirectory"] = start_dir

        file_filter = self.attr.config.get("fileFilter")
        if file_filter:
            kwargs["fileFilter"] = file_filter

        file_path_results = pm.fileDialog2(fileMode=1, **kwargs)
        if file_path_results:
            file_path = file_path_results[0]
            if start_dir:
                # convert to relative path
                rel_path = os.path.relpath(file_path, start_dir)
                self.set_attr_value(rel_path)
            else:
                # set as absolute path
                self.set_attr_value(file_path)

    def _get_starting_dir(self) -> str:
        """
        Return the effective starting directory to use for the path.
        This path is also used to convert absolute paths to relative paths when browsing.
        """
        start_dir = self.attr.config.get("startDir")
        if not start_dir:
            # use scene directory
            scene_name = pm.sceneName()
            if scene_name:
                start_dir = str(scene_name.parent)
        return start_dir


ActionAttrForm.add_form_type(BuildActionAttributeType.FILE, FileAttrForm)


class NodeBatchAttrForm(BatchAttrForm):
    """
    A batch attr editor for node values.

    Provides a button for setting the value of
    all variants at once based on the scene selection.
    Each variant value will be set to a single node,
    and the order of the selection matters.

    The number of variants in the batch action is
    automatically adjusted to match the number of
    selected nodes.
    """

    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)

        h_layout = QtWidgets.QHBoxLayout(parent)
        h_layout.setContentsMargins(0, 0, 0, 0)

        self.pick_button = QtWidgets.QToolButton(parent)
        self.pick_button.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        self.pick_button.setStatusTip("Assign the selected nodes, one per variant.")
        self.pick_button.setFixedSize(TOOL_ICON_SIZE)
        self.pick_button.clicked.connect(self.setFromSelection)
        h_layout.addWidget(self.pick_button)
        h_layout.setAlignment(self.pick_button, QtCore.Qt.AlignTop)
        # body spacer
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        h_layout.addItem(spacer)

        self.set_default_form_layout(h_layout)

    def setFromSelection(self):
        """
        Set the node value for this attribute for each variant
        based on the selected list of nodes. Increases the variant
        list size if necessary to match the selection.
        """
        action_proxy = self.get_action_proxy()
        if not action_proxy:
            return

        self.set_variant_values(pm.selected())


BatchAttrForm.add_form_type(BuildActionAttributeType.NODE, NodeBatchAttrForm)


class DefaultBatchAttrForm(BatchAttrForm):
    def setup_ui(self, parent):
        self.setup_default_form_ui(parent)


BatchAttrForm.add_form_type(BuildActionAttributeType.UNKNOWN, DefaultBatchAttrForm)
