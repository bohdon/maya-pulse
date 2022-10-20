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

from .. import sourceeditor
from ..buildItems import BuildActionProxy, BuildStep, BuildActionData, BuildActionAttribute
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
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(2)
        layout.setMargin(0)

        # header frame
        headerFrame = QtWidgets.QFrame(parent)
        self.setupHeaderUi(headerFrame)
        layout.addWidget(headerFrame)

        # notifications
        notifications = BuildStepNotificationsList(step, parent)
        layout.addWidget(notifications)

        # body layout
        bodyFrame = QtWidgets.QFrame(parent)
        bodyFrame.setObjectName("bodyFrame")
        bodyColorStr = LinearColor(1, 1, 1, 0.02).as_style()
        bodyFrame.setStyleSheet(f".QFrame#bodyFrame{{ background-color: {bodyColorStr}; }}")
        layout.addWidget(bodyFrame)

        self.setupBodyUi(bodyFrame)

    def setupHeaderUi(self, parent):
        step = self.getStep()
        color = step.get_color()
        colorStr = color.as_style()

        bgColor = color * 0.15
        bgColor.a = 0.5
        bgColorStr = bgColor.as_style()

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setMargin(0)

        self.displayNameLabel = QtWidgets.QLabel(parent)
        self.displayNameLabel.setText(self.getStepDisplayName(step))
        self.displayNameLabel.setProperty('cssClasses', 'section-title')
        self.displayNameLabel.setStyleSheet(f"color: {colorStr}; background-color: {bgColorStr}")
        layout.addWidget(self.displayNameLabel)

        if step.is_action():
            editBtn = QtWidgets.QToolButton(parent)
            editBtn.setIcon(QtGui.QIcon(':/icon/file_pen.svg'))
            editBtn.setStatusTip('Edit this actions python script.')
            editBtn.clicked.connect(self._openActionScriptInSourceEditor)
            layout.addWidget(editBtn)

    def setupBodyUi(self, parent):
        step = self.getStep()

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(6)
        layout.setSpacing(0)

        if step.is_action() and step.action_proxy.is_valid():
            formCls = step.action_proxy.spec.editor_form_cls
            if not formCls:
                formCls = BuildActionProxyForm
            self.actionForm = formCls(self.index, parent)
            layout.addWidget(self.actionForm)

    def _openActionScriptInSourceEditor(self):
        """
        Open the python file for this action in a source editor.
        """
        step = self.getStep()
        if step.is_action() and step.action_proxy.spec:
            sourceeditor.open_module(step.action_proxy.spec.module)


class BuildActionDataForm(QtWidgets.QWidget):
    """
    Form for editing all attributes of a BuildActionData instance.
    """

    def __init__(self, index, variantIndex=-1, parent=None):
        super(BuildActionDataForm, self).__init__(parent=parent)

        self.index = QtCore.QPersistentModelIndex(index)
        self.variantIndex = variantIndex
        self.setupUi(self)

        # the map of all attr forms, indexed by attr name
        self._attrForms = {}
        self.updateAttrFormList()

        self.index.model().dataChanged.connect(self.onModelDataChanged)

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
            actionProxy = step.action_proxy
            if self.variantIndex >= 0:
                if actionProxy.num_variants() > self.variantIndex:
                    return actionProxy.get_variant(self.variantIndex)
            else:
                return actionProxy

    def setupUi(self, parent):
        self.layout = QtWidgets.QHBoxLayout(parent)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

        self.attrListLayout = QtWidgets.QVBoxLayout(parent)
        self.attrListLayout.setMargin(0)
        self.attrListLayout.setSpacing(0)
        self.layout.addLayout(self.attrListLayout)

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
                self.attrListLayout.addWidget(self.missingLabel)
            return
        else:
            # remove missing label if it existed previously
            if self.missingLabel:
                self.attrListLayout.removeWidget(self.missingLabel)
                self.missingLabel = None

        parent = self

        # remove forms for non-existent attrs
        for attrName, attrForm in list(self._attrForms.items()):
            if not actionData.has_attr(attrName):
                self.attrListLayout.removeWidget(attrForm)
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
                    self.attrListLayout.replaceWidget(oldForm, attrForm)
                    oldForm.setParent(None)
                else:
                    self.attrListLayout.insertWidget(i, attrForm)

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
    The form for the main set of BuildActionData of a
    BuildActionProxy. Contains additional buttons for
    toggling the variant state of attributes, and uses
    BatchAttrForms for variant attributes.
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
        Build the content ui for this BatchBuildAction.
        Creates ui to manage the array of variant attributes.
        """
        self.layout = QtWidgets.QVBoxLayout(parent)
        self.layout.setSpacing(4)
        self.layout.setMargin(0)

        self.setupLayoutHeader(parent, self.layout)

        # form for all main / invariant attributes
        mainAttrForm = MainBuildActionDataForm(self.index, parent=parent)
        self.layout.addWidget(mainAttrForm)

        spacer = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.layout.addItem(spacer)

        # variant form list
        if self.shouldSetupVariantsUi():
            self.setupVariantsUi(parent, self.layout)
            self.hasVariantsUi = True

    def setupLayoutHeader(self, parent, layout):
        """
        Called after the main layout has been created, before the
        main action data form or variants forms have been added to the layout.
        """
        pass

    def setupVariantsUi(self, parent, layout):
        # variant header
        self.variantHeader = QtWidgets.QFrame(parent)
        self.variantHeader.setStyleSheet(".QFrame{ background-color: rgb(0, 0, 0, 10%); border-radius: 2px }")
        layout.addWidget(self.variantHeader)

        variantHeaderLayout = QtWidgets.QHBoxLayout(self.variantHeader)
        variantHeaderLayout.setContentsMargins(10, 4, 4, 4)
        variantHeaderLayout.setSpacing(4)

        self.variantsLabel = QtWidgets.QLabel(self.variantHeader)
        self.variantsLabel.setText("Variants: ")
        self.variantsLabel.setProperty('cssClasses', 'help')
        variantHeaderLayout.addWidget(self.variantsLabel)

        spacer = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

        # add variant button
        addVariantBtn = QtWidgets.QToolButton(self.variantHeader)
        addVariantBtn.setFixedSize(QtCore.QSize(40, 20))
        addVariantBtn.setStyleSheet('padding: 4px')
        addVariantBtn.setStatusTip('Add a variant to this action.')
        addVariantBtn.setIcon(QtGui.QIcon(":/icon/plus.svg"))
        addVariantBtn.clicked.connect(self.addVariant)
        variantHeaderLayout.addWidget(addVariantBtn)

        # variant list layout
        self.variantListLayout = QtWidgets.QVBoxLayout(parent)
        self.variantListLayout.setContentsMargins(0, 0, 0, 0)
        self.variantListLayout.setSpacing(4)
        layout.addLayout(self.variantListLayout)

    def createVariantActionDataForm(self, variantIndex, parent):
        """
        Create a widget that wraps a BuildActionDataForm widget
        for use in the variants list. Adds a button to remove the variant.
        """
        dataForm = BuildActionDataForm(self.index, variantIndex, parent=parent)

        # add remove variant button
        removeVariantBtn = QtWidgets.QToolButton(parent)
        removeVariantBtn.setFixedSize(QtCore.QSize(20, 20))
        removeVariantBtn.setStyleSheet('padding: 4px')
        removeVariantBtn.setStatusTip('Remove this variant.')
        removeVariantBtn.setIcon(QtGui.QIcon(":/icon/xmark.svg"))
        removeVariantBtn.clicked.connect(partial(self.removeVariantAtIndex, variantIndex))
        dataForm.layout.insertWidget(0, removeVariantBtn)

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
