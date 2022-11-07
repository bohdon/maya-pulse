# coding=utf-8
"""
Editor widgets for inspecting and editing BuildSteps and BuildActions.
"""

import logging
import os
import traceback
from functools import partial
from typing import Optional

import maya.cmds as cmds

from .. import source_editor
from ..build_items import BuildActionProxy, BuildStep, BuildActionData, BuildActionAttribute
from ..vendor.Qt import QtCore, QtWidgets, QtGui
from ..colors import LinearColor
from .actionattrform import ActionAttrForm, BatchAttrForm
from .core import BlueprintUIModel
from .core import PulseWindow

from .gen.action_editor import Ui_ActionEditor

LOG = logging.getLogger(__name__)
LOG_LEVEL_KEY = 'PYLOG_%s' % LOG.name.split('.')[0].upper()
LOG.setLevel(os.environ.get(LOG_LEVEL_KEY, 'INFO').upper())


class BuildStepNotificationsList(QtWidgets.QWidget):
    """
    Displays the current list of notifications, warnings, and errors for an action.
    """

    def __init__(self, step: BuildStep, parent=None):
        super(BuildStepNotificationsList, self).__init__(parent=parent)
        self.setObjectName('formFrame')

        self.step = step

        self.setupUi(self)

    def setupUi(self, parent):
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setMargin(0)

        hasNotifications = False
        for validate_result in self.step.get_validate_results():
            label = QtWidgets.QLabel(parent)
            label.setProperty('cssClasses', 'notification error')
            label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse | QtCore.Qt.TextSelectableByMouse)
            label.setText(str(validate_result))
            label.setToolTip(self.formatErrorText(validate_result))
            self.layout.addWidget(label)
            hasNotifications = True

        self.setVisible(hasNotifications)

    def formatErrorText(self, exc: Exception):
        lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return ''.join(lines).strip()


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
        self.displayNameLabel = None
        self.actionForm = None

        self.index = QtCore.QPersistentModelIndex(index)

        self.setupUi(self)

        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def onModelDataChanged(self):
        # TODO: refresh displayed values
        if not self.index.isValid():
            self.hide()
            return

        step = self.getStep()
        if not step:
            return

        if self.displayNameLabel:
            self.displayNameLabel.setText(self.getStepDisplayName(step))

    def getStep(self) -> BuildStep:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getStepDisplayName(self, step: BuildStep):
        parentPath = step.get_parent_path()
        if parentPath:
            return f'{step.get_parent_path()}/{step.get_display_name()}'.replace('/', ' / ')
        else:
            return step.get_display_name()

    def setupUi(self, parent):
        """
        Create a basic header and body layout to contain the generic
        or action proxy forms.
        """
        step = self.getStep()
        if not step:
            return

        # main layout containing header and body
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setSpacing(2)
        self.main_layout.setMargin(0)

        # title / header
        self.setupHeaderUi(self)

        # notifications
        notifications = BuildStepNotificationsList(step, parent)
        self.main_layout.addWidget(notifications)

        # body
        self.setupBodyUi(self)
        self.setLayout(self.main_layout)

    def setupHeaderUi(self, parent):
        """
        Build the header UI for this build step. Includes the step name and
        a button for quick-editing the action's python script if this step is an action.
        """
        step = self.getStep()
        color = step.get_color()
        color_str = color.as_style()

        bg_color = color * 0.15
        bg_color.a = 0.5
        bg_color_str = bg_color.as_style()

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setMargin(0)

        self.displayNameLabel = QtWidgets.QLabel(parent)
        self.displayNameLabel.setText(self.getStepDisplayName(step))
        self.displayNameLabel.setProperty('cssClasses', 'section-title')
        self.displayNameLabel.setStyleSheet(f"color: {color_str}; background-color: {bg_color_str}")
        layout.addWidget(self.displayNameLabel)

        if step.is_action():
            edit_btn = QtWidgets.QToolButton(parent)
            edit_btn.setIcon(QtGui.QIcon(':/icon/file_pen.svg'))
            edit_btn.setStatusTip("Edit this action's python script.")
            edit_btn.clicked.connect(self._openActionScriptInSourceEditor)
            layout.addWidget(edit_btn)

        self.main_layout.addLayout(layout)

    def setupBodyUi(self, parent):
        """
        Build the body UI for this build step.

        If this step is an action, create a BuildActionProxyForm widget, possibly using the custom
        `editor_form_cls` defined on the action.
        """
        step = self.getStep()
        if step.is_action() and step.action_proxy.is_valid():
            custom_form_cls = step.action_proxy.spec.editor_form_cls
            if not custom_form_cls:
                # use default form
                custom_form_cls = BuildActionProxyForm
            self.actionForm = custom_form_cls(self.index, parent)
            self.main_layout.addWidget(self.actionForm)

    def _openActionScriptInSourceEditor(self):
        """
        Open the python file for this action in a source editor.
        """
        step = self.getStep()
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

    def setupRemoveVariantUi(self, parent):
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
    onRemoved = QtCore.Signal()

    def __init__(self, index, variantIndex=-1, parent=None):
        super(BuildActionDataForm, self).__init__(parent=parent)

        self.index = QtCore.QPersistentModelIndex(index)
        self.variantIndex = variantIndex
        self.ui = Ui_BuildActionDataForm()
        self.ui.setupUi(self)

        # if variant, add a button to delete this variant
        if variantIndex >= 0:
            self.ui.setupRemoveVariantUi(self)
            self.ui.remove_btn.clicked.connect(self._on_remove_clicked)

        # the map of all attr forms, indexed by attr name
        self._attrForms = {}
        self.updateAttrFormList()

        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def _on_remove_clicked(self):
        self.onRemoved.emit()

    def onModelDataChanged(self):
        if not self.index.isValid():
            self.hide()
            return

        self.updateAttrFormList()

    def getStep(self) -> BuildStep:
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionData(self) -> BuildActionData:
        """
        Return the BuildActionData being edited by this form
        """
        step = self.getStep()
        if step and step.is_action():
            action_proxy = step.action_proxy
            if self.variantIndex >= 0:
                if action_proxy.num_variants() > self.variantIndex:
                    return action_proxy.get_variant(self.variantIndex)
            else:
                return action_proxy

    def updateAttrFormList(self):
        """
        Update the current attr forms to reflect
        the action data. Can be called whenever the
        action data's list of attributes changes
        """
        actionData = self.getActionData()
        if not actionData:
            return

        if not hasattr(self, 'missingLabel'):
            self.missingLabel = None

        if actionData.is_missing_spec():
            # add warning that the action config was not found
            if not self.missingLabel:
                self.missingLabel = QtWidgets.QLabel(self)
                self.missingLabel.setText(f"Unknown action: '{actionData.action_id}'")
                self.ui.attr_list_layout.addWidget(self.missingLabel)
            return
        else:
            # remove missing label if it existed previously
            if self.missingLabel:
                self.ui.attr_list_layout.removeWidget(self.missingLabel)
                self.missingLabel = None

        parent = self

        # remove forms for non-existent attrs
        for attrName, attrForm in list(self._attrForms.items()):
            if not actionData.has_attr(attrName):
                self.ui.attr_list_layout.removeWidget(attrForm)
                attrForm.setParent(None)
                del self._attrForms[attrName]

        for i, attr in enumerate(actionData.get_attrs().values()):

            # the current attr form, if any
            attrForm = self._attrForms.get(attr.name, None)

            # the old version of the form.
            # if set, will be replaced with a new attr form
            oldForm = None
            if self.shouldRecreateAttrForm(actionData, attr, attrForm):
                oldForm = attrForm
                attrForm = None

            if not attrForm:
                # create the attr form
                attrForm = self.createAttrForm(actionData, attr, parent)

                if oldForm:
                    self.ui.attr_list_layout.replaceWidget(oldForm, attrForm)
                    oldForm.setParent(None)
                else:
                    self.ui.attr_list_layout.insertWidget(i, attrForm)

                self._attrForms[attr.name] = attrForm

            self.updateAttrForm(actionData, attr, attrForm)

    def createAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, parent):
        """
        Create the form widget for an attribute
        """
        return ActionAttrForm.createForm(self.index, attr, self.variantIndex, parent=parent)

    def shouldRecreateAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, attrForm):
        return False

    def updateAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, attrForm):
        """
        Called when updating the attr form list, on an
        attr form that already exists.
        """
        attrForm.onModelDataChanged()


class MainBuildActionDataForm(BuildActionDataForm):
    """
    The form for the main set of BuildActionData of a BuildActionProxy.
    Contains additional buttons for toggling the variant state of attributes,
    and uses BatchAttrForms for variant attributes.
    """

    def createAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, parent):
        isVariant = False
        # duck type of action proxy
        if hasattr(actionData, 'is_variant_attr'):
            isVariant = actionData.is_variant_attr(attr.name)

        if isVariant:
            attrForm = BatchAttrForm.createForm(self.index, attr, parent=parent)
        else:
            attrForm = ActionAttrForm.createForm(self.index, attr, self.variantIndex, parent=parent)

        attrForm.isBatchForm = isVariant

        # add toggle variant button to label layout
        toggleVariantBtn = QtWidgets.QToolButton(parent)
        toggleVariantBtn.setCheckable(True)
        toggleVariantBtn.setFixedSize(QtCore.QSize(20, 20))
        toggleVariantBtn.setStyleSheet('padding: 4px;')
        toggleVariantBtn.setStatusTip('Toggle this attribute between singular and variant. Variants allow multiple '
                                      'actions to be defined in one place, with a mix of different properties.')

        attrForm.labelLayout.insertWidget(0, toggleVariantBtn)
        attrForm.labelLayout.setAlignment(toggleVariantBtn, QtCore.Qt.AlignTop)
        toggleVariantBtn.clicked.connect(partial(self.toggleIsVariantAttr, attr.name))

        attrForm.toggleVariantBtn = toggleVariantBtn
        return attrForm

    def shouldRecreateAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, attrForm):
        isVariant = False
        # duck type of action proxy
        if hasattr(actionData, 'is_variant_attr'):
            isVariant = actionData.is_variant_attr(attr.name)

        return getattr(attrForm, 'isBatchForm', False) != isVariant

    def updateAttrForm(self, actionData: BuildActionData, attr: BuildActionAttribute, attrForm):
        # update variant state of the attribute
        isVariant = False
        # duck type of action proxy
        if hasattr(actionData, 'is_variant_attr'):
            isVariant = actionData.is_variant_attr(attr.name)

        attrForm.toggleVariantBtn.setChecked(isVariant)

        if isVariant:
            attrForm.toggleVariantBtn.setIcon(QtGui.QIcon(":/icon/bars_staggered.svg"))
        else:
            attrForm.toggleVariantBtn.setIcon(QtGui.QIcon(":/icon/minus.svg"))

        super(MainBuildActionDataForm, self).updateAttrForm(actionData, attr, attrForm)

    def toggleIsVariantAttr(self, attrName: str):
        step = self.getStep()
        if not step:
            return

        actionProxy: BuildActionProxy = self.getActionData()
        if not actionProxy:
            return

        attrPath = f'{step.get_full_path()}.{attrName}'

        isVariant = actionProxy.is_variant_attr(attrName)
        cmds.pulseSetIsVariantAttr(attrPath, not isVariant)


class BuildActionProxyForm(QtWidgets.QWidget):
    """
    Form for editing BuildActionProxys.
    Displays an attr form for every attribute on the action,
    and provides UI for managing variants.
    """

    def __init__(self, index, parent=None):
        super(BuildActionProxyForm, self).__init__(parent=parent)
        self.variantsLabel = None
        self.variantListLayout = None

        self.index = QtCore.QPersistentModelIndex(index)
        self.hasVariantsUi = False

        self.setupUi(self)
        self.updateVariantFormList()

        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def onModelDataChanged(self):
        if not self.index.isValid():
            self.hide()
            return

        # TODO: get specific changes necessary to insert or remove indeces
        self.updateVariantFormList()

    def getStep(self) -> Optional[BuildStep]:
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self) -> Optional[BuildActionProxy]:
        """
        Return the BuildActionProxy being edited by this form
        """
        step = self.getStep()
        if step and step.is_action():
            return step.action_proxy

    def shouldSetupVariantsUi(self):
        actionProxy = self.getActionProxy()
        return actionProxy and actionProxy.num_attrs() > 0

    def setupUi(self, parent):
        """
        Build the ui for this form, includes both the variant and invariant attributes.
        """
        self.main_layout = QtWidgets.QVBoxLayout(parent)
        self.main_layout.setSpacing(2)
        self.main_layout.setMargin(0)

        self.setupLayoutHeader(parent, self.main_layout)

        # invariant attributes
        mainAttrForm = MainBuildActionDataForm(self.index, parent=parent)
        self.main_layout.addWidget(mainAttrForm)

        # variant attributes
        if self.shouldSetupVariantsUi():
            self.setupVariantsUi(parent, self.main_layout)
            self.hasVariantsUi = True

    def setupLayoutHeader(self, parent, layout):
        """
        Called after the main layout has been created, before the
        main action data form or variants forms have been added to the layout.
        Intended for use in BuildActionProxyForm subclasses to add custom ui before the main form.
        """
        pass

    def setupVariantsUi(self, parent, layout):
        # variant header
        self.variantHeader = QtWidgets.QFrame(parent)
        self.variantHeader.setStyleSheet(".QFrame{ background-color: rgb(0, 0, 0, 10%); border-radius: 2px }")
        layout.addWidget(self.variantHeader)

        variantHeaderLayout = QtWidgets.QHBoxLayout(self.variantHeader)
        variantHeaderLayout.setMargin(5)
        variantHeaderLayout.setSpacing(4)

        # add variant button
        addVariantBtn = QtWidgets.QToolButton(self.variantHeader)
        addVariantBtn.setFixedSize(QtCore.QSize(20, 20))
        addVariantBtn.setStyleSheet('padding: 4px')
        addVariantBtn.setStatusTip('Add a variant to this action.')
        addVariantBtn.setIcon(QtGui.QIcon(":/icon/plus.svg"))
        addVariantBtn.clicked.connect(self.addVariant)
        variantHeaderLayout.addWidget(addVariantBtn)

        self.variantsLabel = QtWidgets.QLabel(self.variantHeader)
        self.variantsLabel.setText("Variants: ")
        self.variantsLabel.setProperty('cssClasses', 'help')
        variantHeaderLayout.addWidget(self.variantsLabel)

        # variant list layout
        self.variantListLayout = QtWidgets.QVBoxLayout(parent)
        self.variantListLayout.setContentsMargins(0, 0, 0, 0)
        self.variantListLayout.setSpacing(2)
        layout.addLayout(self.variantListLayout)

    def createVariantActionDataForm(self, variantIndex, parent):
        """
        Create a widget that wraps a BuildActionDataForm widget
        for use in the variants list. Adds a button to remove the variant.
        """
        dataForm = BuildActionDataForm(self.index, variantIndex, parent=parent)
        dataForm.onRemoved.connect(partial(self.removeVariantAtIndex, variantIndex))
        return dataForm

    def updateVariantFormList(self):
        if not self.hasVariantsUi:
            return

        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        self.variantHeader.setVisible(actionProxy.is_variant_action())
        self.variantsLabel.setText(f"Variants: {actionProxy.num_variants()}")

        while self.variantListLayout.count() < actionProxy.num_variants():
            self.insertVariantForm(self.variantListLayout.count())

        while self.variantListLayout.count() > actionProxy.num_variants():
            self.removeVariantForm(-1)

        for i in range(self.variantListLayout.count()):
            item = self.variantListLayout.itemAt(i)
            dataForm = item.widget()
            if dataForm:
                dataForm.variantIndex = i
                dataForm.updateAttrFormList()

    def insertVariantForm(self, index=-1):
        """
        Insert a new variant action data form into the variants list.
        """
        if not self.hasVariantsUi:
            return

        if index >= 0:
            variantIndex = index
        else:
            variantIndex = self.variantListLayout.count() + index
        attrForm = self.createVariantActionDataForm(variantIndex, parent=self)
        self.variantListLayout.insertWidget(index, attrForm)

    def removeVariantForm(self, index):
        """
        Remove a variant action data form from the variants list.
        """
        if not self.hasVariantsUi:
            return

        if index < 0:
            index = self.variantListLayout.count() + index
        if index >= 0 and index < self.variantListLayout.count():
            attrFormItem = self.variantListLayout.takeAt(index)
            attrForm = attrFormItem.widget()
            if attrForm:
                attrForm.setParent(None)

    def addVariant(self):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        actionProxy.add_variant()
        self.updateVariantFormList()

    def removeVariantAtIndex(self, index):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        # TODO: implement plugin command
        # step = self.getStep()
        # stepPath = step.get_full_path()
        # cmds.pulseRemoveVariant(stepPath, self.variantIndex)

        actionProxy.remove_variant_at(index)
        self.updateVariantFormList()

    def removeVariantFromEnd(self):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        actionProxy.remove_variant_at(-1)
        self.updateVariantFormList()


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

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.blueprintModel.readOnlyChanged.connect(self.onReadOnlyChanged)
        self.model = self.blueprintModel.buildStepTreeModel
        self.model.dataChanged.connect(self.onModelDataChanged)
        self.model.modelReset.connect(self.onModelReset)
        self.selectionModel = self.blueprintModel.buildStepSelectionModel
        self.selectionModel.selectionChanged.connect(self._on_selection_changed)

        self.setEnabled(not self.blueprintModel.isReadOnly())

        self.setupItemsUiForSelection()

    def _on_selection_changed(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        self.setupItemsUiForSelection()

    def onModelDataChanged(self):
        # TODO: refresh displayed build step forms if applicable
        pass

    def onModelReset(self):
        self.setupItemsUiForSelection()

    def onReadOnlyChanged(self, isReadOnly):
        self.setEnabled(not isReadOnly)

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

    def setup_items_ui(self, itemIndexes, parent):
        self.clear_items_ui()

        for index in itemIndexes:
            item_widget = BuildStepForm(index, parent=parent)
            self.ui.items_layout.addWidget(item_widget)

    def setupItemsUiForSelection(self):
        if self.selectionModel.hasSelection():
            self.ui.main_stack.setCurrentWidget(self.ui.content_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.help_page)

        self.setup_items_ui(self.selectionModel.selectedIndexes(), self.ui.scroll_area_widget)


class ActionEditorWindow(PulseWindow):
    OBJECT_NAME = 'pulseActionEditorWindow'
    WINDOW_MODULE = 'pulse.ui.actioneditor'
    WINDOW_TITLE = 'Pulse Action Editor'
    WIDGET_CLASS = ActionEditor
