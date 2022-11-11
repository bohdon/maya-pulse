# coding=utf-8
"""
Editor widgets for inspecting and editing BuildSteps and BuildActions.
"""

import logging
import os
import traceback
from functools import partial
from typing import Optional, cast, Dict

import maya.cmds as cmds

from .. import source_editor
from ..build_items import BuildActionProxy, BuildStep, BuildActionData, BuildActionAttribute
from ..vendor.Qt import QtCore, QtWidgets, QtGui
from .actionattrform import ActionAttrForm, BatchAttrForm, ActionAttrFormBase
from .core import BlueprintUIModel, BuildStepTreeModel
from .core import PulseWindow

from .gen.action_editor import Ui_ActionEditor

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = "PYLOG_%s" % LOG.name.split(".")[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, "INFO").upper())


class BuildStepNotificationsList(QtWidgets.QWidget):
    """
    Displays the current list of notifications, warnings, and errors for an action.
    """

    def __init__(self, step: BuildStep, parent=None):
        super(BuildStepNotificationsList, self).__init__(parent=parent)
        self.setObjectName("formFrame")

        self.step = step

        self.setup_ui(self)

    def setup_ui(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setMargin(0)

        has_notifications = False
        for validate_result in self.step.get_validate_results():
            label = QtWidgets.QLabel(parent)
            label.setProperty("cssClasses", "notification error")
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setText(str(validate_result))
            label.setToolTip(self.format_error_text(validate_result))
            self.layout.addWidget(label)
            has_notifications = True

        self.setVisible(has_notifications)

    def format_error_text(self, exc: Exception):
        lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return "".join(lines).strip()


class BuildStepForm(QtWidgets.QWidget):
    """
    A form for editing a BuildStep
    """

    def __init__(self, index: QtCore.QModelIndex, parent=None):
        """
        Args:
            index (QModelIndex): The index of the BuildStep
        """
        super(BuildStepForm, self).__init__(parent=parent)
        self.display_name_label = None
        self.action_form = None

        self.index = QtCore.QPersistentModelIndex(index)

        self.setup_ui(self)

        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def on_model_data_changed(self):
        # TODO: refresh displayed values
        if not self.index.isValid():
            self.hide()
            return

        step = self.get_step()
        if not step:
            return

        if self.display_name_label:
            self.display_name_label.setText(self.get_step_display_name(step))

    def get_step(self) -> BuildStep:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_step_display_name(self, step: BuildStep):
        parent_path = step.get_parent_path()
        if parent_path:
            return f"{step.get_parent_path()}/{step.get_display_name()}".replace("/", " / ")
        else:
            return step.get_display_name()

    def setup_ui(self, parent):
        """
        Create a basic header and body layout to contain the generic
        or action proxy forms.
        """
        step = self.get_step()
        if not step:
            return

        # main layout containing header and body
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setSpacing(2)
        self.main_layout.setMargin(0)

        # title / header
        self.setup_header_ui(self)

        # notifications
        notifications = BuildStepNotificationsList(step, parent)
        self.main_layout.addWidget(notifications)

        # body
        self.setup_body_ui(self)
        self.setLayout(self.main_layout)

    def setup_header_ui(self, parent):
        """
        Build the header UI for this build step. Includes the step name and
        a button for quick-editing the action's python script if this step is an action.
        """
        step = self.get_step()
        color = step.get_color()
        color_str = color.as_style()

        bg_color = color * 0.15
        bg_color.a = 0.5
        bg_color_str = bg_color.as_style()

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setMargin(0)

        self.display_name_label = QtWidgets.QLabel(parent)
        self.display_name_label.setText(self.get_step_display_name(step))
        self.display_name_label.setProperty("cssClasses", "section-title")
        self.display_name_label.setStyleSheet(f"color: {color_str}; background-color: {bg_color_str}")
        layout.addWidget(self.display_name_label)

        if step.is_action():
            edit_btn = QtWidgets.QToolButton(parent)
            edit_btn.setIcon(QtGui.QIcon(":/icon/file_pen.svg"))
            edit_btn.setStatusTip("Edit this action's python script.")
            edit_btn.clicked.connect(self._open_action_script_in_source_editor)
            layout.addWidget(edit_btn)

        self.main_layout.addLayout(layout)

    def setup_body_ui(self, parent):
        """
        Build the body UI for this build step.

        If this step is an action, create a BuildActionProxyForm widget, possibly using the custom
        `editor_form_cls` defined on the action.
        """
        step = self.get_step()
        if step.is_action() and step.action_proxy.is_valid():
            custom_form_cls = step.action_proxy.spec.editor_form_cls
            if not custom_form_cls:
                # use default form
                custom_form_cls = BuildActionProxyForm
            self.action_form = custom_form_cls(self.index, parent)
            self.main_layout.addWidget(self.action_form)

    def _open_action_script_in_source_editor(self):
        """
        Open the python file for this action in a source editor.
        """
        step = self.get_step()
        if step.is_action() and step.action_proxy.spec:
            source_editor.open_module(step.action_proxy.spec.module)


class Ui_BuildActionDataForm(object):
    def setupUi(self, parent):
        self.main_layout = QtWidgets.QHBoxLayout(parent)
        self.main_layout.setMargin(0)

        self.frame = QtWidgets.QFrame(parent)
        self.frame.setProperty("cssClasses", "block")

        self.h_layout = QtWidgets.QHBoxLayout(self.frame)
        self.h_layout.setMargin(0)

        self.attr_list_layout = QtWidgets.QVBoxLayout(self.frame)
        self.attr_list_layout.setMargin(0)
        self.attr_list_layout.setSpacing(0)
        self.h_layout.addLayout(self.attr_list_layout)

        self.main_layout.addWidget(self.frame)

    def setup_remove_variant_ui(self, parent):
        """
        Add an X button for removing this variant.
        """
        self.remove_btn = QtWidgets.QToolButton(parent)
        # button uses its own margin to get correct spacing on the left and right,
        # so the real size is 20x20 after the margin of 4px
        self.remove_btn.setFixedSize(QtCore.QSize(26, 26))
        self.remove_btn.setStyleSheet("margin: 3px; padding: 3px")
        self.remove_btn.setStatusTip("Remove this variant.")
        self.remove_btn.setIcon(QtGui.QIcon(":/icon/xmark.svg"))

        self.h_layout.insertWidget(0, self.remove_btn)
        self.h_layout.setAlignment(self.remove_btn, QtCore.Qt.AlignTop)


class BuildActionDataForm(QtWidgets.QWidget):
    """
    Form for editing all attributes of a BuildActionData instance.

    This form is used for both invariant and variant attribute editing, and handles
    building the list of ActionAttrForms for each attribute.
    """

    # called when the remove-variant button is clicked
    on_removed = QtCore.Signal()

    def __init__(self, index, variant_index=-1, parent=None):
        super(BuildActionDataForm, self).__init__(parent=parent)

        self.index = QtCore.QPersistentModelIndex(index)
        self.variant_index = variant_index

        self.missing_label = None
        self.ui = Ui_BuildActionDataForm()
        self.ui.setupUi(self)

        # if variant, add a button to delete this variant
        if variant_index >= 0:
            self.ui.setup_remove_variant_ui(self)
            self.ui.remove_btn.clicked.connect(self._on_remove_clicked)

        # the map of all attr forms, indexed by attr name
        self._attr_forms: Dict[str, ActionAttrFormBase] = {}
        self.update_attr_form_list()

        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def _on_remove_clicked(self):
        self.on_removed.emit()

    def on_model_data_changed(self):
        if not self.index.isValid():
            self.hide()
            return

        self.update_attr_form_list()

    def get_step(self) -> BuildStep:
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_action_data(self) -> BuildActionData:
        """
        Return the BuildActionData being edited by this form
        """
        step = self.get_step()
        if step and step.is_action():
            action_proxy = step.action_proxy
            if self.variant_index >= 0:
                if action_proxy.num_variants() > self.variant_index:
                    return action_proxy.get_variant(self.variant_index)
            else:
                return action_proxy

    def update_attr_form_list(self):
        """
        Update the current attr forms to reflect
        the action data. Can be called whenever the
        action data's list of attributes changes
        """
        action_data = self.get_action_data()
        if not action_data:
            return

        if action_data.is_missing_spec():
            # add warning that the action config was not found
            if not self.missing_label:
                self.missing_label = QtWidgets.QLabel(self)
                self.missing_label.setText(f"Unknown action: '{action_data.action_id}'")
                self.ui.attr_list_layout.addWidget(self.missing_label)
            return
        else:
            # remove missing label if it existed previously
            if self.missing_label:
                self.ui.attr_list_layout.removeWidget(self.missing_label)
                self.missing_label = None

        parent = self

        # remove forms for non-existent attrs
        for attrName, attr_form in list(self._attr_forms.items()):
            if not action_data.has_attr(attrName):
                self.ui.attr_list_layout.removeWidget(attr_form)
                attr_form.setParent(None)
                del self._attr_forms[attrName]

        for i, attr in enumerate(action_data.get_attrs().values()):

            # the current attr form, if any
            attr_form = self._attr_forms.get(attr.name, None)

            # the old version of the form.
            # if set, will be replaced with a new attr form
            old_form = None
            if self.should_recreate_attr_form(action_data, attr, attr_form):
                old_form = attr_form
                attr_form = None

            if not attr_form:
                # create the attr form
                attr_form = self.create_attr_form(action_data, attr, parent)

                if old_form:
                    self.ui.attr_list_layout.replaceWidget(old_form, attr_form)
                    old_form.setParent(None)
                else:
                    self.ui.attr_list_layout.insertWidget(i, attr_form)

                self._attr_forms[attr.name] = attr_form

            self.update_attr_form(action_data, attr, attr_form)

    def create_attr_form(self, action_data: BuildActionData, attr: BuildActionAttribute, parent) -> ActionAttrForm:
        """
        Create the form widget for an attribute
        """
        return ActionAttrForm.create_form(self.index, attr, self.variant_index, parent=parent)

    def should_recreate_attr_form(
        self, action_data: BuildActionData, attr: BuildActionAttribute, attr_form: ActionAttrFormBase
    ):
        return False

    def update_attr_form(self, action_data: BuildActionData, attr: BuildActionAttribute, attr_form: ActionAttrFormBase):
        """
        Called when updating the attr form list, on an
        attr form that already exists.
        """
        attr_form.on_model_data_changed()

    @staticmethod
    def is_variant_attr(action_data: BuildActionData, attr_name: str) -> bool:
        """
        Return true if an attribute is variant on the given build action.
        Can only be true if the action_data is a BuildActionProxy.
        """
        if isinstance(action_data, BuildActionProxy):
            return action_data.is_variant_attr(attr_name)


class MainBuildActionDataForm(BuildActionDataForm):
    """
    The form for the main set of BuildActionData of a BuildActionProxy.
    Contains additional buttons for toggling the variant state of attributes,
    and uses BatchAttrForms for variant attributes.
    """

    def create_attr_form(self, action_data: BuildActionData, attr: BuildActionAttribute, parent):
        is_variant = self.is_variant_attr(action_data, attr.name)

        attr_form: ActionAttrFormBase
        if is_variant:
            attr_form = BatchAttrForm.create_form(self.index, attr, parent=parent)
        else:
            attr_form = ActionAttrForm.create_form(self.index, attr, self.variant_index, parent=parent)

        # add toggle variant button to label layout
        toggle_variant_btn = QtWidgets.QToolButton(parent)
        toggle_variant_btn.setCheckable(True)
        toggle_variant_btn.setFixedSize(QtCore.QSize(20, 20))
        toggle_variant_btn.setStyleSheet("padding: 4px;")
        toggle_variant_btn.setStatusTip(
            "Toggle this attribute between singular and variant. Variants allow multiple "
            "actions to be defined in one place, with a mix of different properties."
        )

        attr_form.label_layout.insertWidget(0, toggle_variant_btn)
        attr_form.label_layout.setAlignment(toggle_variant_btn, QtCore.Qt.AlignTop)
        toggle_variant_btn.clicked.connect(partial(self.toggle_is_variant_attr, attr.name))

        attr_form.toggleVariantBtn = toggle_variant_btn
        return attr_form

    def should_recreate_attr_form(
        self, action_data: BuildActionData, attr: BuildActionAttribute, attr_form: ActionAttrFormBase
    ):
        if isinstance(action_data, BuildActionProxy) and action_data.is_variant_attr(attr.name):
            # ensure it's a batch attribute form
            return not isinstance(attr_form, BatchAttrForm)
        else:
            # ensure it's a normal attribute form
            return not isinstance(attr_form, ActionAttrForm)

    def update_attr_form(self, action_data: BuildActionData, attr: BuildActionAttribute, attr_form):
        is_variant = self.is_variant_attr(action_data, attr.name)

        attr_form.toggleVariantBtn.setChecked(is_variant)

        if is_variant:
            attr_form.toggleVariantBtn.setIcon(QtGui.QIcon(":/icon/bars_staggered.svg"))
        else:
            attr_form.toggleVariantBtn.setIcon(QtGui.QIcon(":/icon/minus.svg"))

        super(MainBuildActionDataForm, self).update_attr_form(action_data, attr, attr_form)

    def toggle_is_variant_attr(self, attr_name: str):
        step = self.get_step()
        if not step:
            return

        attr_path = f"{step.get_full_path()}.{attr_name}"
        is_variant = self.is_variant_attr(self.get_action_data(), attr_name)
        cmds.pulseSetIsVariantAttr(attr_path, not is_variant)


class BuildActionProxyForm(QtWidgets.QWidget):
    """
    Form for editing BuildActionProxy objects.
    Displays an attr form for every attribute on the action,
    and provides UI for managing variants.
    """

    def __init__(self, index, parent=None):
        super(BuildActionProxyForm, self).__init__(parent=parent)
        self.variants_label = None
        self.variant_list_layout = None

        self.index = QtCore.QPersistentModelIndex(index)
        self.has_variants_ui = False

        self.setup_ui(self)
        self.update_variant_form_list()

        self.index.model().dataChanged.connect(self.on_model_data_changed)

    def on_model_data_changed(self):
        if not self.index.isValid():
            self.hide()
            return

        # TODO: get specific changes necessary to insert or remove indeces
        self.update_variant_form_list()

    def get_step(self) -> Optional[BuildStep]:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return cast(BuildStepTreeModel, self.index.model()).step_for_index(self.index)

    def get_action_proxy(self) -> Optional[BuildActionProxy]:
        """
        Return the BuildActionProxy being edited by this form
        """
        step = self.get_step()
        if step and step.is_action():
            return step.action_proxy

    def should_setup_variants_ui(self):
        action_proxy = self.get_action_proxy()
        return action_proxy and action_proxy.num_attrs() > 0

    def setup_ui(self, parent):
        """
        Build the ui for this form, includes both the variant and invariant attributes.
        """
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setSpacing(2)
        self.main_layout.setMargin(0)

        self.setup_layout_header(parent, self.main_layout)

        # invariant attributes
        main_attr_form = MainBuildActionDataForm(self.index, parent=parent)
        self.main_layout.addWidget(main_attr_form)

        # variant attributes
        if self.should_setup_variants_ui():
            self.setup_variants_ui(parent, self.main_layout)
            self.has_variants_ui = True

    def setup_layout_header(self, parent, layout):
        """
        Called after the main layout has been created, before the
        main action data form or variants forms have been added to the layout.
        Intended for use in BuildActionProxyForm subclasses to add custom ui before the main form.
        """
        pass

    def setup_variants_ui(self, parent, layout):
        # variant header
        self.variant_header = QtWidgets.QFrame(parent)
        self.variant_header.setStyleSheet(".QFrame{ background-color: rgb(0, 0, 0, 10%); border-radius: 2px }")
        layout.addWidget(self.variant_header)

        variant_header_layout = QtWidgets.QHBoxLayout(self.variant_header)
        variant_header_layout.setMargin(5)
        variant_header_layout.setSpacing(4)

        # add variant button
        add_variant_btn = QtWidgets.QToolButton(self.variant_header)
        add_variant_btn.setFixedSize(QtCore.QSize(20, 20))
        add_variant_btn.setStyleSheet("padding: 4px")
        add_variant_btn.setStatusTip("Add a variant to this action.")
        add_variant_btn.setIcon(QtGui.QIcon(":/icon/plus.svg"))
        add_variant_btn.clicked.connect(self.add_variant)
        variant_header_layout.addWidget(add_variant_btn)

        self.variants_label = QtWidgets.QLabel(self.variant_header)
        self.variants_label.setText("Variants: ")
        self.variants_label.setProperty("cssClasses", "help")
        variant_header_layout.addWidget(self.variants_label)

        # variant list layout
        self.variant_list_layout = QtWidgets.QVBoxLayout(parent)
        self.variant_list_layout.setContentsMargins(0, 0, 0, 0)
        self.variant_list_layout.setSpacing(2)
        layout.addLayout(self.variant_list_layout)

    def create_variant_action_data_form(self, variant_index, parent):
        """
        Create a widget that wraps a BuildActionDataForm widget
        for use in the variants list. Adds a button to remove the variant.
        """
        data_form = BuildActionDataForm(self.index, variant_index, parent=parent)
        data_form.on_removed.connect(partial(self.remove_variant_at_index, variant_index))
        return data_form

    def update_variant_form_list(self):
        if not self.has_variants_ui:
            return

        action_proxy = self.get_action_proxy()
        if not action_proxy:
            return

        self.variant_header.setVisible(action_proxy.is_variant_action())
        self.variants_label.setText(f"Variants: {action_proxy.num_variants()}")

        while self.variant_list_layout.count() < action_proxy.num_variants():
            self.insert_variant_form(self.variant_list_layout.count())

        while self.variant_list_layout.count() > action_proxy.num_variants():
            self.remove_variant_form(-1)

        for i in range(self.variant_list_layout.count()):
            item = self.variant_list_layout.itemAt(i)
            data_form = cast(BuildActionDataForm, item.widget())
            if data_form:
                data_form.variant_index = i
                data_form.update_attr_form_list()

    def insert_variant_form(self, index=-1):
        """
        Insert a new variant action data form into the variants list.
        """
        if not self.has_variants_ui:
            return

        if index >= 0:
            variant_index = index
        else:
            variant_index = self.variant_list_layout.count() + index
        attr_form = self.create_variant_action_data_form(variant_index, parent=self)
        self.variant_list_layout.insertWidget(index, attr_form)

    def remove_variant_form(self, index):
        """
        Remove a variant action data form from the variants list.
        """
        if not self.has_variants_ui:
            return

        if index < 0:
            index = self.variant_list_layout.count() + index
        if 0 <= index < self.variant_list_layout.count():
            attr_form_item = self.variant_list_layout.takeAt(index)
            attr_form = attr_form_item.widget()
            if attr_form:
                attr_form.setParent(None)

    def add_variant(self):
        action_proxy = self.get_action_proxy()
        if not action_proxy:
            return

        action_proxy.add_variant()
        self.update_variant_form_list()

    def remove_variant_at_index(self, index):
        action_proxy = self.get_action_proxy()
        if not action_proxy:
            return

        # TODO: implement plugin command
        # step = self.get_step()
        # step_path = step.get_full_path()
        # cmds.pulseRemoveVariant(step_path, self.variant_index)

        action_proxy.remove_variant_at(index)
        self.update_variant_form_list()

    def remove_variant_from_end(self):
        action_proxy = self.get_action_proxy()
        if not action_proxy:
            return

        action_proxy.remove_variant_at(-1)
        self.update_variant_form_list()


class ActionEditor(QtWidgets.QWidget):
    """
    The main widget for inspecting and editing BuildActions.

    Uses the shared action tree selection model to automatically
    display editors for the selected actions.
    """

    def __init__(self, parent=None):
        super(ActionEditor, self).__init__(parent=parent)

        self.ui = Ui_ActionEditor()
        self.ui.setupUi(self)

        self.blueprintModel = BlueprintUIModel.get_default_model()
        self.blueprintModel.read_only_changed.connect(self.on_read_only_changed)
        self.model = self.blueprintModel.build_step_tree_model
        self.model.dataChanged.connect(self.on_model_data_changed)
        self.model.modelReset.connect(self.on_model_reset)
        self.selectionModel = self.blueprintModel.build_step_selection_model
        self.selectionModel.selectionChanged.connect(self._on_selection_changed)

        self.setEnabled(not self.blueprintModel.is_read_only())

        self.setup_items_ui_for_selection()

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        self.setup_items_ui_for_selection()

    def on_model_data_changed(self):
        # TODO: refresh displayed build step forms if applicable
        pass

    def on_model_reset(self):
        self.setup_items_ui_for_selection()

    def on_read_only_changed(self, is_read_only):
        self.setEnabled(not is_read_only)

    def clear_items_ui(self):
        while True:
            item = self.ui.items_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            else:
                break

    def setup_items_ui(self, item_indexes, parent):
        self.clear_items_ui()

        for index in item_indexes:
            item_widget = BuildStepForm(index, parent=parent)
            self.ui.items_layout.addWidget(item_widget)

    def setup_items_ui_for_selection(self):
        if self.selectionModel.hasSelection():
            self.ui.main_stack.setCurrentWidget(self.ui.content_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.help_page)

        self.setup_items_ui(self.selectionModel.selectedIndexes(), self.ui.scroll_area_widget)


class ActionEditorWindow(PulseWindow):
    OBJECT_NAME = "pulseActionEditorWindow"
    WINDOW_MODULE = "pulse.ui.actioneditor"
    WINDOW_TITLE = "Pulse Action Editor"
    WIDGET_CLASS = ActionEditor
