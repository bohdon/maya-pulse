import logging
from functools import partial
from typing import cast, Dict
from maya import cmds
from ...vendor.Qt import QtCore, QtWidgets, QtGui

from ...build_items import BuildActionProxy, BuildStep, BuildActionData, BuildActionAttribute
from ..actionattrform import ActionAttrForm, BatchAttrForm, ActionAttrFormBase
from ..core import BuildStepTreeModel
from ..gen.build_action_data_form import Ui_BuildActionDataForm

logger = logging.getLogger(__name__)


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
        if variant_index < 0:
            self.ui.remove_btn.setVisible(False)

        # the map of all attr forms, indexed by attr name
        self._attr_forms: Dict[str, ActionAttrFormBase] = {}
        self.update_attr_form_list()

        self.ui.remove_btn.clicked.connect(self._on_remove_clicked)
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
