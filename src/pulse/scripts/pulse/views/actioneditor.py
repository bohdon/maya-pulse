# coding=utf-8

from functools import partial

import pulse
import pulse.names
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
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
        self.index = index
        self.setupUi(self)

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
        self.constantsLayout = QtWidgets.QVBoxLayout(parent)
        self.constantsLayout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.constantsLayout)

        spacer = QtWidgets.QSpacerItem(
            20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)

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

        viewutils.clearLayout(self.constantsLayout)

        # create attr form all constant attributes,
        # or batch attr forms for any variant attributes that support it
        for attr in actionProxy.getAttrs():
            isVariant = actionProxy.isVariantAttr(attr['name'])
            # make an HBox with a button to toggle variant state
            attrHLayout = QtWidgets.QHBoxLayout(parent)
            attrHLayout.setSpacing(10)
            attrHLayout.setMargin(0)
            self.constantsLayout.addLayout(attrHLayout)

            # button to toggle variant
            toggleVariantBtn = QtWidgets.QPushButton(parent)
            toggleVariantBtn.setText("⋮")
            toggleVariantBtn.setFixedSize(QtCore.QSize(14, 20))
            toggleVariantBtn.setCheckable(True)
            toggleVariantBtn.setChecked(isVariant)
            attrHLayout.addWidget(toggleVariantBtn)
            attrHLayout.setAlignment(toggleVariantBtn, QtCore.Qt.AlignTop)
            toggleVariantBtn.clicked.connect(
                partial(self.setIsVariantAttr, attr['name'], not isVariant))

            if not isVariant:
                # constant value, make an attr form
                attrValue = actionProxy.getAttrValueOrDefault(attr['name'])
                attrForm = ActionAttrForm.createForm(
                    attr, attrValue, parent=parent)
                attrForm.valueChanged.connect(
                    partial(self.onAttrValueChanged, -1, attrForm))
                attrHLayout.addWidget(attrForm)
            else:
                # variant value, check for batch editor, or just display a label
                attrLabel = QtWidgets.QLabel(parent)
                # extra 2 to account for the left-side frame padding that occurs in the ActionAttrForm
                attrLabel.setFixedSize(
                    QtCore.QSize(ActionAttrForm.LABEL_WIDTH + 2, ActionAttrForm.LABEL_HEIGHT))
                attrLabel.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignTop)
                attrLabel.setMargin(2)
                attrLabel.setText(pulse.names.toTitle(attr['name']))
                attrLabel.setEnabled(False)
                attrHLayout.addWidget(attrLabel)

                # TODO: replace passing of buildItem wit persistent index
                # if BatchAttrForm.doesFormExist(attr):
                if False:
                    batchEditor = BatchAttrForm.createForm(
                        self.buildItem, attr, parent=parent)
                    batchEditor.valuesChanged.connect(
                        self.batchEditorValuesChanged)
                    attrHLayout.addWidget(batchEditor)
                else:
                    spacer = QtWidgets.QSpacerItem(
                        24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
                    attrHLayout.addItem(spacer)

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
                attrValue = actionProxy.getVariantAttrValueOrDefault(
                    variantIndex, attr['name'])
                attrForm = ActionAttrForm.createForm(
                    attr, attrValue, parent=parent)
                attrForm.valueChanged.connect(
                    partial(self.onAttrValueChanged, variantIndex, attrForm))
                variantVLayout.addWidget(attrForm)
        else:
            noAttrsLabel = QtWidgets.QLabel(parent)
            noAttrsLabel.setText("No variant attributes")
            noAttrsLabel.setMinimumHeight(24)
            noAttrsLabel.setContentsMargins(10, 0, 0, 0)
            noAttrsLabel.setEnabled(False)
            variantVLayout.addWidget(noAttrsLabel)

        self.variantLayout.addLayout(variantHLayout)

    def setIsVariantAttr(self, attrName, isVariant):
        actionProxy = self.actionProxy()
        if not actionProxy:
            return

        if isVariant:
            actionProxy.addVariantAttr(attrName)
        else:
            actionProxy.removeVariantAttr(attrName)
        self.setupConstantsUi(self)
        self.setupVariantsUi(self)

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

    def onAttrValueChanged(self, variantIndex, attrForm, attrValue, isValueValid):
        """
        Args:
            variantIndex (int): The index of the variant attribute that was modified.
                If < 0, the attribute is not variant.
            attrForm (ActionAttrForm): The attribute form that caused the change
        """
        if not self.index.isValid():
            return

        step = self.step()
        if not step:
            return

        # TODO: set data through the model
        if variantIndex >= 0:
            step.actionProxy.setVariantAttrValue(
                variantIndex, attrForm.attr['name'], attrValue)
        else:
            step.actionProxy.setAttrValue(
                attrForm.attr['name'], attrValue)

        self.index.model().dataChanged.emit(
            self.index, self.index, QtCore.Qt.UserRole)

    def batchEditorValuesChanged(self):
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

    def showEvent(self, event):
        super(ActionEditorWidget, self).showEvent(event)
        self.blueprintModel.addSubscriber(self)

    def hideEvent(self, event):
        super(ActionEditorWidget, self).hideEvent(event)
        self.blueprintModel.removeSubscriber(self)

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

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        widget = ActionEditorWidget(self)
        widget.setMinimumSize(400, 300)
        self.setCentralWidget(widget)
