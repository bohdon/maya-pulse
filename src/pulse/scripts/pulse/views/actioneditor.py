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


class BuildActionProxyForm(QtWidgets.QWidget):
    """
    Form for editing BuildActionProxys.
    Displays an attr form for every attribute on the action,
    and provides UI for managing variants.
    """

    def __init__(self, index, parent=None):
        super(BuildActionProxyForm, self).__init__(parent=parent)
        self.index = QtCore.QPersistentModelIndex(index)
        self.setupUi(self)
        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def onModelDataChanged(self):
        if not self.index.isValid():
            self.hide()
            return

        step = self.step()
        if not step:
            return

        # update attr forms to represent the current
        # variant attr state and count
        self.setupConstantsUi(self)
        self.setupVariantsUi(self)

    def step(self):
        """
        Return the BuildStep being edited by this form
        """
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def actionProxy(self):
        """
        Return the BuildActionProxy being edited by this form
        """
        step = self.step()
        if step and step.isAction():
            return step.actionProxy

    def setupUi(self, parent):
        """
        Build the content ui for this BatchBuildAction.
        Creates ui to manage the array of variant attributes.
        """

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(4)
        layout.setMargin(0)

        # constants main layout
        self.constantAttrForms = {}
        self.constantsLayout = QtWidgets.QVBoxLayout(parent)
        self.constantsLayout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.constantsLayout)

        spacer = QtWidgets.QSpacerItem(
            20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

        actionProxy = self.actionProxy()
        if actionProxy and actionProxy.numAttrs() > 0:
            self.setupVariantsHeaderUi(parent, layout)

    def setupVariantsHeaderUi(self, parent, layout):
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

        # variant list main layout
        self.variantAttrForms = []
        self.variantLayout = QtWidgets.QVBoxLayout(parent)
        self.variantLayout.setContentsMargins(0, 0, 0, 0)
        self.variantLayout.setSpacing(4)
        layout.addLayout(self.variantLayout)

        self.setupConstantsUi(parent)
        self.setupVariantsUi(parent)

    def setupConstantsUi(self, parent):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        # create form container for all attrs
        for attr in actionProxy.getAttrs():
            if attr['name'] in self.constantAttrForms:
                # form already setup
                continue

            form = {}

            # make an HBox with a button to toggle variant state
            attrHLayout = QtWidgets.QHBoxLayout(parent)
            attrHLayout.setSpacing(10)
            attrHLayout.setMargin(0)
            form['layout'] = attrHLayout
            self.constantsLayout.addLayout(attrHLayout)

            # button to toggle variant
            toggleVariantBtn = QtWidgets.QPushButton(parent)
            toggleVariantBtn.setText("⋮")
            toggleVariantBtn.setFixedSize(QtCore.QSize(14, 20))
            toggleVariantBtn.setCheckable(True)
            form['toggleVariantBtn'] = toggleVariantBtn
            attrHLayout.addWidget(toggleVariantBtn)
            attrHLayout.setAlignment(toggleVariantBtn, QtCore.Qt.AlignTop)
            toggleVariantBtn.clicked.connect(
                partial(self.toggleIsVariantAttr, attr['name']))

            self.constantAttrForms[attr['name']] = form

        # update all form containers to match the current variant state
        for attr in actionProxy.getAttrs():
            isVariant = actionProxy.isVariantAttr(attr['name'])

            # update attr form variant state
            form = self.constantAttrForms[attr['name']]
            form['toggleVariantBtn'].setChecked(isVariant)

            if not isVariant:
                self.createOrShowConstantAttrForm(attr, form)
                self.hideVariantMainAttrForm(form)
            else:
                self.createOrShowVariantMainAttrForm(attr, form)
                self.hideConstantAttrForm(form)

    def createOrShowConstantAttrForm(self, attr, form):
        if 'constantForm' not in form:
            newForm = self.createConstantAttrForm(self, attr)
            if newForm:
                form['layout'].addWidget(newForm)
                form['constantForm'] = newForm
        else:
            form['constantForm'].setVisible(True)

    def hideConstantAttrForm(self, form):
        if 'constantForm' in form:
            form['constantForm'].setVisible(False)

    def createOrShowVariantMainAttrForm(self, attr, form):
        if 'variantForm' not in form:
            newForm = self.createVariantMainAttrForm(self, attr)
            if newForm:
                form['layout'].addWidget(newForm)
                form['variantForm'] = newForm
        else:
            form['variantForm'].setVisible(True)

    def hideVariantMainAttrForm(self, form):
        if 'variantForm' in form:
            form['variantForm'].setVisible(False)

    def createConstantAttrForm(self, parent, attr):
        attrForm = ActionAttrForm.createForm(
            self.index, attr, parent=parent)
        return attrForm

    def createVariantMainAttrForm(self, parent, attr):
        """
        Creates an attr form in the constant attr area,
        but for an attribute marked as variant. By default
        this will just show the attribute label as a
        placeholder to accompany the variant toggle,
        but some attributes support custom forms for
        batch editing multiple variant values.
        """
        batchForm = BatchAttrForm.createForm(
            self.index, attr, parent=parent)
        return batchForm

    def setupVariantsUi(self, parent):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        viewutils.clearLayout(self.variantLayout)

        self.variantsLabel.setText(
            "Variants: {0}".format(actionProxy.numVariants()))

        for i in range(actionProxy.numVariants()):
            self._createVariantForm(parent, i, actionProxy)

    def _createVariantForm(self, parent, variantIndex, actionProxy):
        """
        Build a form for editing the variant attribute values
        at the variant index.
        """
        if variantIndex > 0:
            # divider line
            dividerLine = QtWidgets.QFrame(parent)
            dividerLine.setStyleSheet(
                ".QFrame{ background-color: rgb(0, 0, 0, 15); border-radius: 2px }")
            dividerLine.setMinimumHeight(2)
            self.variantLayout.addWidget(dividerLine)

        variantHLayout = QtWidgets.QHBoxLayout(parent)

        # remove variant button
        removeVariantBtn = QtWidgets.QPushButton(parent)
        removeVariantBtn.setText('x')
        removeVariantBtn.setFixedSize(QtCore.QSize(20, 20))
        removeVariantBtn.clicked.connect(
            partial(self.removeVariantAtIndex, variantIndex))
        variantHLayout.addWidget(removeVariantBtn)

        # create attr form for all variant attributes
        variantVLayout = QtWidgets.QVBoxLayout(parent)
        variantVLayout.setSpacing(0)
        variantHLayout.addLayout(variantVLayout)

        if actionProxy.isVariantAction():
            for attr in actionProxy.getAttrs():
                if not actionProxy.isVariantAttr(attr['name']):
                    continue
                attrForm = ActionAttrForm.createForm(
                    self.index, attr, variantIndex, parent=parent)
                variantVLayout.addWidget(attrForm)
        else:
            noAttrsLabel = QtWidgets.QLabel(parent)
            noAttrsLabel.setText("No variant attributes")
            noAttrsLabel.setMinimumHeight(24)
            noAttrsLabel.setContentsMargins(10, 0, 0, 0)
            noAttrsLabel.setEnabled(False)
            variantVLayout.addWidget(noAttrsLabel)

        self.variantLayout.addLayout(variantHLayout)

    def toggleIsVariantAttr(self, attrName):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        step = self.step()
        if not step:
            return

        attrPath = '{0}.{1}'.format(step.getFullPath(), attrName)

        isVariant = actionProxy.isVariantAttr(attrName)
        cmds.pulseSetIsVariantAttr(attrPath, not isVariant)

    def addVariant(self):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        actionProxy.addVariant()
        self.setupVariantsUi(self)

    def removeVariantAtIndex(self, index):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        actionProxy.removeVariantAt(index)
        self.setupVariantsUi(self)

    def removeVariantFromEnd(self):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        actionProxy.removeVariantAt(-1)
        self.setupVariantsUi(self)


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

        widget = ActionEditorWidget(self)
        widget.setMinimumSize(400, 300)
        self.setCentralWidget(widget)
