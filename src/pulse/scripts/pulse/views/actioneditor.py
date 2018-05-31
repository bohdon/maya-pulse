
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
    'ActionForm',
    'BatchActionForm',
    'BuildItemForm',
]



class BuildItemForm(QtWidgets.QWidget):
    """
    Base class for a form for editing any type of BuildItem
    """

    "The BuildItem of this form has been modified by the form"
    buildItemChanged = QtCore.Signal()

    @staticmethod
    def createItemWidget(buildItem, parent=None):
        if isinstance(buildItem, pulse.BuildAction):
            return ActionForm(buildItem, parent=parent)
        elif isinstance(buildItem, pulse.BatchBuildAction):
            return BatchActionForm(buildItem, parent=parent)
        else:
            return BuildItemForm(buildItem, parent=parent)
        return QtWidgets.QWidget(parent=parent)

    def __init__(self, buildItem, parent=None):
        super(BuildItemForm, self).__init__(parent=parent)
        self.buildItemPath = buildItem.getFullPath()
        self.buildItem = buildItem
        self.setupUi(self)
        self.setupContentUi(self)

    def getItemDisplayName(self):
        return self.buildItem.getDisplayName()

    def getItemIcon(self):
        iconFile = self.buildItem.getIconFile()
        if iconFile:
            return QtGui.QIcon(iconFile)

    def getItemColor(self):
        color = self.buildItem.getColor()
        if color:
            return [int(c * 255) for c in color]
        else:
            return [255, 255, 255]

    def setupUi(self, parent):
        """
        Create the UI that is common to all BuildItem editors, including
        a basic header and layout.
        """
        # main layout containing header and body
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(4)
        layout.setMargin(0)

        # header frame
        self.headerFrame = QtWidgets.QFrame(parent)
        headerColor = 'rgba({0}, {1}, {2}, 40)'.format(*self.getItemColor())
        self.headerFrame.setStyleSheet(".QFrame{{ background-color: {color}; border-radius: 2px; }}".format(color=headerColor))
        layout.addWidget(self.headerFrame)
        # header layout
        self.headerLayout = QtWidgets.QHBoxLayout(self.headerFrame)
        self.headerLayout.setContentsMargins(10, 4, 4, 4)
        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(self.headerFrame)
        self.displayNameLabel.setMinimumHeight(18)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(self.getItemDisplayName())
        self.headerLayout.addWidget(self.displayNameLabel)

        # body layout
        bodyFrame = QtWidgets.QFrame(parent)
        bodyFrame.setObjectName("bodyFrame")
        bodyColor = 'rgba(255, 255, 255, 5)'.format(*self.getItemColor())
        bodyFrame.setStyleSheet(".QFrame#bodyFrame{{ background-color: {color}; }}".format(color=bodyColor))
        layout.addWidget(bodyFrame)

        self.mainLayout = QtWidgets.QVBoxLayout(bodyFrame)
        self.mainLayout.setMargin(6)
        self.mainLayout.setSpacing(0)

    def setupContentUi(self, parent):
        pass


class ActionForm(BuildItemForm):
    """
    Form for editing Actions that displays an attr form
    for every attribute on the action.
    """

    convertToBatchClicked = QtCore.Signal()

    def setupUi(self, parent):
        super(ActionForm, self).setupUi(parent)

        # add batch conversion button to header
        convertToBatchBtn = QtWidgets.QPushButton(parent)
        convertToBatchBtn.setIcon(viewutils.getIcon("convertActionToBatch.png"))
        convertToBatchBtn.setFixedSize(QtCore.QSize(18, 18))
        convertToBatchBtn.clicked.connect(self.convertToBatchClicked.emit)
        self.headerLayout.addWidget(convertToBatchBtn)

    def setupContentUi(self, parent):
        for attr in self.buildItem.config['attrs']:
            attrValue = getattr(self.buildItem, attr['name'])
            attrForm = ActionAttrForm.createForm(attr, attrValue, parent=parent)
            attrForm.valueChanged.connect(partial(self.attrValueChanged, attrForm))
            self.mainLayout.addWidget(attrForm)

    def attrValueChanged(self, attrForm, attrValue, isValueValid):
        setattr(self.buildItem, attrForm.attr['name'], attrValue)
        self.buildItemChanged.emit()



class BatchActionForm(BuildItemForm):
    """
    Form for editing Batch Actions. Very similar
    to the standard ActionForm, with a few key
    differences.

    Each attribute has a toggle that controls
    whether the attribute is variant or not.

    All variants are displayed in a list, with the ability
    to easily add and remove variants. If a BatchAttrForm
    exists for a variant attribute type, it will be displayed
    in place of the normal AttrEditor form (only when that
    attribute is marked as variant).
    """

    convertToActionClicked = QtCore.Signal()

    def setupUi(self, parent):
        super(BatchActionForm, self).setupUi(parent)

        # add action conversion button to header
        convertToActionBtn = QtWidgets.QPushButton(parent)
        convertToActionBtn.setIcon(viewutils.getIcon("convertBatchToAction.png"))
        convertToActionBtn.setFixedSize(QtCore.QSize(18, 18))
        convertToActionBtn.clicked.connect(self.convertToActionClicked.emit)
        self.headerLayout.addWidget(convertToActionBtn)

    def setupContentUi(self, parent):
        """
        Build the content ui for this BatchBuildAction.
        Creates ui to manage the array of variant attributes.
        """

        # constants main layout
        self.constantsLayout = QtWidgets.QVBoxLayout(parent)
        self.constantsLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.constantsLayout)

        spacer = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.mainLayout.addItem(spacer)

        # variant header
        variantHeader = QtWidgets.QFrame(parent)
        variantHeader.setStyleSheet(".QFrame{ background-color: rgb(255, 255, 255, 15); border-radius: 2px }")
        self.mainLayout.addWidget(variantHeader)

        variantHeaderLayout = QtWidgets.QHBoxLayout(variantHeader)
        variantHeaderLayout.setContentsMargins(10, 4, 4, 4)
        variantHeaderLayout.setSpacing(4)

        self.variantsLabel = QtWidgets.QLabel(variantHeader)
        self.variantsLabel.setText("Variants: {0}".format(len(self.buildItem.variantValues)))
        variantHeaderLayout.addWidget(self.variantsLabel)

        spacer = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.mainLayout.addItem(spacer)

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
        self.mainLayout.addLayout(self.variantLayout)

        self.setupConstantsUi(parent)
        self.setupVariantsUi(parent)

    def setupConstantsUi(self, parent):
        viewutils.clearLayout(self.constantsLayout)

        # create attr form all constant attributes
        for attr in self.buildItem.actionClass.config['attrs']:
            isConstant = (attr['name'] in self.buildItem.constantValues)
            # make an HBox with a button to toggle variant state
            attrHLayout = QtWidgets.QHBoxLayout(parent)
            attrHLayout.setSpacing(10)
            attrHLayout.setMargin(0)
            self.constantsLayout.addLayout(attrHLayout)

            if isConstant:
                # constant value, make an attr form
                attrValue = self.buildItem.constantValues[attr['name']]
                context = self.buildItem.constantValues
                attrForm = ActionAttrForm.createForm(attr, attrValue, parent=parent)
                attrForm.valueChanged.connect(partial(self.attrValueChanged, context, attrForm))
                attrHLayout.addWidget(attrForm)
            else:
                # variant value, check for batch editor, or just display a label
                attrLabel = QtWidgets.QLabel(parent)
                # extra 2 to account for the left-side frame padding that occurs in the ActionAttrForm
                attrLabel.setFixedSize(QtCore.QSize(ActionAttrForm.LABEL_WIDTH + 2, ActionAttrForm.LABEL_HEIGHT))
                attrLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignTop)
                attrLabel.setMargin(2)
                attrLabel.setText(pulse.names.toTitle(attr['name']))
                attrLabel.setEnabled(False)
                attrHLayout.addWidget(attrLabel)

                if BatchAttrForm.doesFormExist(attr):
                    batchEditor = BatchAttrForm.createForm(self.buildItem, attr, parent=parent)
                    batchEditor.valuesChanged.connect(self.batchEditorValuesChanged)
                    attrHLayout.addWidget(batchEditor)
                else:
                    spacer = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
                    attrHLayout.addItem(spacer)

            # not a constant value, add a line with button to make it constant
            # button to toggle variant
            toggleVariantBtn = QtWidgets.QPushButton(parent)
            toggleVariantBtn.setText("v")
            toggleVariantBtn.setFixedSize(QtCore.QSize(20, 20))
            toggleVariantBtn.setCheckable(True)
            toggleVariantBtn.setChecked(not isConstant)
            attrHLayout.addWidget(toggleVariantBtn)
            attrHLayout.setAlignment(toggleVariantBtn, QtCore.Qt.AlignTop)
            toggleVariantBtn.clicked.connect(partial(self.setIsVariantAttr, attr['name'], isConstant))


    def setupVariantsUi(self, parent):
        viewutils.clearLayout(self.variantLayout)

        self.variantsLabel.setText("Variants: {0}".format(len(self.buildItem.variantValues)))
        for i, variant in enumerate(self.buildItem.variantValues):

            if i > 0:
                # divider line
                dividerLine = QtWidgets.QFrame(parent)
                dividerLine.setStyleSheet(".QFrame{ background-color: rgb(0, 0, 0, 15); border-radius: 2px }")
                dividerLine.setMinimumHeight(2)
                self.variantLayout.addWidget(dividerLine)

            variantHLayout = QtWidgets.QHBoxLayout(parent)

            # remove variant button
            removeVariantBtn = QtWidgets.QPushButton(parent)
            removeVariantBtn.setText('x')
            removeVariantBtn.setFixedSize(QtCore.QSize(20, 20))
            removeVariantBtn.clicked.connect(partial(self.removeVariantAtIndex, i))
            variantHLayout.addWidget(removeVariantBtn)

            # create attr form for all variant attributes
            variantVLayout = QtWidgets.QVBoxLayout(parent)
            variantVLayout.setSpacing(0)
            variantHLayout.addLayout(variantVLayout)

            if self.buildItem.variantAttributes:
                for attr in self.buildItem.actionClass.config['attrs']:
                    if attr['name'] not in self.buildItem.variantAttributes:
                        continue
                    attrValue = variant[attr['name']]
                    # context = variant
                    attrForm = ActionAttrForm.createForm(attr, attrValue, parent=parent)
                    attrForm.valueChanged.connect(partial(self.attrValueChanged, variant, attrForm))
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
        if isVariant:
            self.buildItem.addVariantAttr(attrName)
        else:
            self.buildItem.removeVariantAttr(attrName)
        self.setupConstantsUi(self)
        self.setupVariantsUi(self)

    def addVariant(self):
        self.buildItem.addVariant()
        self.setupVariantsUi(self)
        self.buildItemChanged.emit()

    def removeVariantAtIndex(self, index):
        self.buildItem.removeVariantAt(index)
        self.setupVariantsUi(self)
        self.buildItemChanged.emit()

    def removeVariantFromEnd(self):
        self.buildItem.removeVariantAt(-1)
        self.setupVariantsUi(self)
        self.buildItemChanged.emit()

    def attrValueChanged(self, context, attrForm, attrValue, isValueValid):
        """
        Args:
            context: A dict representing the either constantValues object or
                a variant within the batch action
        """
        attrName = attrForm.attr['name']
        # prevent adding new keys to the context dict
        if attrName in context:
            context[attrName] = attrValue
            self.buildItemChanged.emit()

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

        self.buildItems = []

        self.setupUi(self)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildItemTreeModel
        self.selectionModel = self.blueprintModel.buildItemSelectionModel
        self.selectionModel.selectionChanged.connect(self.selectionChanged)

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

        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.scrollLayout.addItem(spacer)

        self.scrollWidget.setLayout(self.scrollLayout)


    def selectionChanged(self, selected, deselected):
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
            buildItem = index.internalPointer()
            itemWidget = BuildItemForm.createItemWidget(buildItem, parent=parent)
            itemWidget.buildItemChanged.connect(partial(self.buildItemChanged, itemWidget))
            if isinstance(itemWidget, ActionForm):
                itemWidget.convertToBatchClicked.connect(partial(self.convertActionToBatch, index))
            elif isinstance(itemWidget, BatchActionForm):
                itemWidget.convertToActionClicked.connect(partial(self.convertBatchToAction, index))
            self.mainLayout.addWidget(itemWidget)

    def setupItemsUiForSelection(self):
        self.setupItemsUi(self.selectionModel.selectedIndexes(), self.scrollWidget)

    def buildItemChanged(self, itemWidget):
        self.blueprintModel.save()

    def convertActionToBatch(self, itemModelIndex):
        # create new BatchBuildAction
        oldAction = itemModelIndex.internalPointer()
        newAction = pulse.BatchBuildAction.fromAction(oldAction)
        # replace the item in the model
        parentIndex = itemModelIndex.parent()
        row = itemModelIndex.row()
        self.model.removeRows(row, 1, parentIndex)
        self.model.insertBuildItems(row, [newAction], parentIndex)
        # select new item
        self.selectionModel.select(self.model.index(row, 0, parentIndex), QtCore.QItemSelectionModel.Select)

    def convertBatchToAction(self, itemModelIndex):
        # create new BuildAction
        oldAction = itemModelIndex.internalPointer()
        newAction = pulse.BuildAction.fromBatchAction(oldAction)
        # replace the item in the model
        parentIndex = itemModelIndex.parent()
        row = itemModelIndex.row()
        self.model.removeRows(row, 1, parentIndex)
        self.model.insertBuildItems(row, [newAction], parentIndex)
        # select new item
        self.selectionModel.select(self.model.index(row, 0, parentIndex), QtCore.QItemSelectionModel.Select)



class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        widget = ActionEditorWidget(self)
        widget.setMinimumSize(400, 300)
        self.setCentralWidget(widget)

