# coding=utf-8

from functools import partial
import maya.cmds as cmds
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse
import pulse.names
from pulse.core import serializeAttrValue
from .core import PulseWindow
from .core import BlueprintUIModel
from . import utils as viewutils
from .actionattrform import ActionAttrForm, BatchAttrForm


__all__ = [
    'ActionEditorWidget',
    'ActionEditorWindow',
    'BuildActionDataForm',
    'MainBuildActionDataForm',
    'BuildActionProxyForm',
    'BuildStepForm',
]


class BuildStepForm(QtWidgets.QWidget):
    """
    A form for editing a BuildStep
    """

    def __init__(self, index, parent=None):
        """
        Args:
            index (QModelIndex): The index of the BuildStep
        """
        super(BuildStepForm, self).__init__(parent=parent)
        self.index = QtCore.QPersistentModelIndex(index)
        self.setupUi(self)
        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def onModelDataChanged(self):
        # TODO: refresh displayed values
        if not self.index.isValid():
            self.hide()
            return

        step = self.step()
        if not step:
            return

        self.displayNameLabel.setText(step.getDisplayName())

    def step(self):
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getStepColor(self, step):
        color = step.getColor()
        if color:
            return [int(c * 255) for c in color]
        else:
            return [255, 255, 255]

    def setupUi(self, parent):
        """
        Create a basic header and body layout to contain the generic
        or action proxy forms.
        """
        step = self.step()
        if not step:
            return

        # main layout containing header and body
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(4)
        layout.setMargin(0)

        # header frame
        headerFrame = QtWidgets.QFrame(parent)
        headerColor = "rgba({0}, {1}, {2}, 40)".format(
            *self.getStepColor(step))
        headerFrame.setStyleSheet(
            ".QFrame{{ background-color: {color}; "
            "border-radius: 2px; }}".format(color=headerColor))
        layout.addWidget(headerFrame)

        self.setupHeaderUi(headerFrame)

        # body layout
        bodyFrame = QtWidgets.QFrame(parent)
        bodyFrame.setObjectName("bodyFrame")
        bodyColor = "rgba(255, 255, 255, 5)"
        bodyFrame.setStyleSheet(
            ".QFrame#bodyFrame{{ background-color: {color}; }}".format(color=bodyColor))
        layout.addWidget(bodyFrame)

        self.setupBodyUi(bodyFrame)

    def setupHeaderUi(self, parent):
        step = self.step()

        layout = QtWidgets.QHBoxLayout(parent)
        layout.setContentsMargins(10, 4, 4, 4)

        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(parent)
        self.displayNameLabel.setMinimumHeight(18)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(step.getDisplayName())
        layout.addWidget(self.displayNameLabel)

    def setupBodyUi(self, parent):
        step = self.step()

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(6)
        layout.setSpacing(0)

        if step.isAction():
            self.actionForm = BuildActionProxyForm(self.index, parent)
            layout.addWidget(self.actionForm)


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

    def getStep(self):
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionData(self):
        """
        Return the BuildActionProxy being edited by this form
        """
        step = self.getStep()
        if step and step.isAction():
            actionProxy = step.actionProxy
            if self.variantIndex >= 0:
                if actionProxy.numVariants() > self.variantIndex:
                    return actionProxy.getVariant(self.variantIndex)
            else:
                return actionProxy

    def setupUi(self, parent):
        self.layout = QtWidgets.QHBoxLayout(parent)
        self.layout.setMargin(0)
        self.setLayout(self.layout)

        self.attrListLayout = QtWidgets.QVBoxLayout(parent)
        self.attrListLayout.setMargin(0)
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

        parent = self

        # remove forms for non existent attrs
        for attrName, attrForm in self._attrForms.items():
            if not actionData.hasAttr(attrName):
                self.attrListLayout.removeWidget(attrForm)
                attrForm.setParent(None)
                del self._attrForms[attrName]

        for i, attr in enumerate(actionData.getAttrs()):

            # the current attr form, if any
            attrForm = self._attrForms.get(attr['name'], None)

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

                self._attrForms[attr['name']] = attrForm

            self.updateAttrForm(actionData, attr, attrForm)

    def createAttrForm(self, actionData, attr, parent):
        """
        Create the form widget for an attribute
        """
        return ActionAttrForm.createForm(
            self.index, attr, self.variantIndex, parent=parent)

    def shouldRecreateAttrForm(self, actionData, attr, attrForm):
        return False

    def updateAttrForm(self, actionData, attr, attrForm):
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

    def createAttrForm(self, actionData, attr, parent):
        isVariant = False
        # duck type of actionProxy
        if hasattr(actionData, 'isVariantAttr'):
            isVariant = actionData.isVariantAttr(attr['name'])

        if isVariant:
            attrForm = BatchAttrForm.createForm(
                self.index, attr, parent=parent)
        else:
            attrForm = ActionAttrForm.createForm(
                self.index, attr, self.variantIndex, parent=parent)

        attrForm.isBatchForm = isVariant

        # add toggle variant button to label layout
        toggleVariantBtn = QtWidgets.QPushButton(parent)
        toggleVariantBtn.setText("⋮")
        toggleVariantBtn.setFixedSize(QtCore.QSize(14, 20))
        toggleVariantBtn.setCheckable(True)
        attrForm.labelLayout.insertWidget(0, toggleVariantBtn)
        attrForm.labelLayout.setAlignment(toggleVariantBtn, QtCore.Qt.AlignTop)
        toggleVariantBtn.clicked.connect(
            partial(self.toggleIsVariantAttr, attr['name']))

        attrForm.toggleVariantBtn = toggleVariantBtn
        return attrForm

    def shouldRecreateAttrForm(self, actionData, attr, attrForm):
        isVariant = False
        # duck type of actionProxy
        if hasattr(actionData, 'isVariantAttr'):
            isVariant = actionData.isVariantAttr(attr['name'])

        return getattr(attrForm, 'isBatchForm', False) != isVariant

    def updateAttrForm(self, actionData, attr, attrForm):
        # update variant state of the attribute
        isVariant = False
        # duck type of actionProxy
        if hasattr(actionData, 'isVariantAttr'):
            isVariant = actionData.isVariantAttr(attr['name'])

        attrForm.toggleVariantBtn.setChecked(isVariant)
        # attrForm.setIsVariant(isVariant)

        super(MainBuildActionDataForm, self).updateAttrForm(
            actionData, attr, attrForm)

    def toggleIsVariantAttr(self, attrName):
        step = self.getStep()
        if not step:
            return

        actionProxy = self.getActionData()
        if not actionProxy:
            return

        attrPath = '{0}.{1}'.format(step.getFullPath(), attrName)

        isVariant = actionProxy.isVariantAttr(attrName)
        cmds.pulseSetIsVariantAttr(attrPath, not isVariant)


class BuildActionProxyForm(QtWidgets.QWidget):
    """
    Form for editing BuildActionProxys.
    Displays an attr form for every attribute on the action,
    and provides UI for managing variants.
    """

    def __init__(self, index, parent=None):
        super(BuildActionProxyForm, self).__init__(parent=parent)
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

    def getStep(self):
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self):
        """
        Return the BuildActionProxy being edited by this form
        """
        step = self.getStep()
        if step and step.isAction():
            return step.actionProxy

    def shouldSetupVariantsUi(self):
        actionProxy = self.getActionProxy()
        return actionProxy and actionProxy.numAttrs() > 0

    def setupUi(self, parent):
        """
        Build the content ui for this BatchBuildAction.
        Creates ui to manage the array of variant attributes.
        """

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(4)
        layout.setMargin(0)

        # form for all main / invariant attributes
        mainAttrForm = MainBuildActionDataForm(self.index, parent=parent)
        layout.addWidget(mainAttrForm)

        spacer = QtWidgets.QSpacerItem(
            20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

        # variant form list
        if self.shouldSetupVariantsUi():
            self.setupVariantsUi(parent, layout)
            self.hasVariantsUi = True

    def setupVariantsUi(self, parent, layout):
        # variant header
        variantHeader = QtWidgets.QFrame(parent)
        variantHeader.setStyleSheet(
            ".QFrame{ background-color: rgb(255, 255, 255, 15); border-radius: 2px }")
        layout.addWidget(variantHeader)

        variantHeaderLayout = QtWidgets.QHBoxLayout(variantHeader)
        variantHeaderLayout.setContentsMargins(10, 4, 4, 4)
        variantHeaderLayout.setSpacing(4)

        self.variantsLabel = QtWidgets.QLabel(variantHeader)
        self.variantsLabel.setText("Variants: ")
        variantHeaderLayout.addWidget(self.variantsLabel)

        spacer = QtWidgets.QSpacerItem(
            20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

        # add variant button
        addVariantBtn = QtWidgets.QPushButton(variantHeader)
        addVariantBtn.setText('+')
        addVariantBtn.setFixedSize(QtCore.QSize(20, 20))
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
        dataForm = BuildActionDataForm(
            self.index, variantIndex, parent=parent)

        # add remove variant button
        removeVariantBtn = QtWidgets.QPushButton(parent)
        removeVariantBtn.setText('x')
        removeVariantBtn.setFixedSize(QtCore.QSize(20, 20))
        removeVariantBtn.clicked.connect(
            partial(self.removeVariantAtIndex, variantIndex))
        dataForm.layout.insertWidget(0, removeVariantBtn)

        return dataForm

    def updateVariantFormList(self):
        if not self.hasVariantsUi:
            return

        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        self.variantsLabel.setText(
            "Variants: {0}".format(actionProxy.numVariants()))

        while self.variantListLayout.count() < actionProxy.numVariants():
            self.insertVariantForm(self.variantListLayout.count())

        while self.variantListLayout.count() > actionProxy.numVariants():
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

        actionProxy.addVariant()
        self.updateVariantFormList()

    def removeVariantAtIndex(self, index):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        # TODO: implement plugin command
        # step = self.getStep()
        # stepPath = step.getFullPath()
        # cmds.pulseRemoveVariant(stepPath, self.variantIndex)

        actionProxy.removeVariantAt(index)
        self.updateVariantFormList()

    def removeVariantFromEnd(self):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        actionProxy.removeVariantAt(-1)
        self.updateVariantFormList()


class ActionEditorWidget(QtWidgets.QWidget):
    """
    The main widget for inspecting and editing BuildActions.

    Uses the shared action tree selection model to automatically
    display editors for the selected actions.
    """

    def __init__(self, parent=None):
        super(ActionEditorWidget, self).__init__(parent=parent)

        self.setupUi(self)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self.model.dataChanged.connect(self.onModelDataChanged)
        self.model.modelReset.connect(self.onModelReset)
        self.selectionModel = self.blueprintModel.buildStepSelectionModel
        self.selectionModel.selectionChanged.connect(self.onSelectionChanged)

        self.setupItemsUiForSelection()

    def setupUi(self, parent):
        outerLayout = QtWidgets.QVBoxLayout(parent)

        self.scrollArea = QtWidgets.QScrollArea(parent)
        self.scrollArea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        outerLayout.addWidget(self.scrollArea)

        self.scrollWidget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollWidget)

        # scroll layout contains the main layout and a spacer item
        self.scrollLayout = QtWidgets.QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setMargin(0)

        self.mainLayout = QtWidgets.QVBoxLayout(self.scrollWidget)
        self.mainLayout.setSpacing(12)
        self.mainLayout.setMargin(4)
        self.scrollLayout.addLayout(self.mainLayout)

        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.scrollLayout.addItem(spacer)

        self.scrollWidget.setLayout(self.scrollLayout)

    def onSelectionChanged(self, selected, deselected):
        self.setupItemsUiForSelection()

    def onModelDataChanged(self):
        # TODO: refresh displayed build step forms if applicable
        pass

    def onModelReset(self):
        self.setupItemsUiForSelection()

    def clearItemsUi(self):
        while True:
            item = self.mainLayout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()
            else:
                break

    def setupItemsUi(self, itemIndexes, parent):
        self.clearItemsUi()

        for index in itemIndexes:
            itemWidget = BuildStepForm(index, parent=parent)
            self.mainLayout.addWidget(itemWidget)

    def setupItemsUiForSelection(self):
        self.setupItemsUi(
            self.selectionModel.selectedIndexes(),
            self.scrollWidget
        )


class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.actioneditor'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        widget = ActionEditorWidget(self)
        layout.addWidget(widget)
