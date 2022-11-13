import logging
from functools import partial
from typing import Optional, cast

from ...build_items import BuildActionProxy, BuildStep
from ...vendor.Qt import QtCore, QtWidgets, QtGui
from ..core import BuildStepTreeModel
from .build_action_data_form import MainBuildActionDataForm, BuildActionDataForm

logger = logging.getLogger(__name__)


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
