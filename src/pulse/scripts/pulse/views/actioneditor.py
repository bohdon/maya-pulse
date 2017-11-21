
from functools import partial
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.names
from .core import PulseWindow
from . import utils as viewutils
from .actiontree import ActionTreeItemModel, ActionTreeSelectionModel
from .actionattrform import ActionAttrForm


__all__ = [
    'ActionEditorWidget',
    'ActionEditorWindow',
    'ActionForm',
    'BatchActionForm',
    'BuildGroupForm',
    'BuildItemForm',
]




class BatchAttrEditor(QtWidgets.QWidget):
    """
    The base class for an attribute form designed to
    bulk edit all variants in a batch action.
    This appears where the default attr form usually appears
    when the attribute is marked as variant.
    
    BatchAttrForms should only exist if they provide an
    easy way to bulk set different values for all variants,
    as its pointless to provide functionality for setting all
    variants to the same value (would make the attribute constant).
    """

    TYPEMAP = {}
    
    valuesChanged = QtCore.Signal()
    variantCountChanged = QtCore.Signal()

    @staticmethod
    def doesEditorExist(attr):
        return attr['type'] in BatchAttrEditor.TYPEMAP

    @staticmethod
    def createEditor(action, attr, parent=None):
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            attr: A dict representing the config of a BuildAction attribute
        """
        attrType = attr['type']
        if attrType in BatchAttrEditor.TYPEMAP:
            return BatchAttrEditor.TYPEMAP[attrType](action, attr, parent=parent)

    def __init__(self, batchAction, attr, parent=None):
        super(BatchAttrEditor, self).__init__(parent=parent)
        self.batchAction = batchAction
        self.attr = attr
        self.setupUi(self)

    def setupUi(self, parent):
        raise NotImplementedError



class NodeBatchAttrEditor(BatchAttrEditor):
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

    def setupUi(self, parent):
        hlayout = QtWidgets.QHBoxLayout(parent)
        hlayout.setContentsMargins(2, 2, 2, 2)

        pickButton = QtWidgets.QPushButton(parent)
        pickButton.setIcon(viewutils.getIcon("select.png"))
        pickButton.setFixedSize(QtCore.QSize(20, 20))
        pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(pickButton)
        hlayout.setAlignment(pickButton, QtCore.Qt.AlignTop)
        # body spacer
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacer)

    def setFromSelection(self):
        """
        Set the node value for this attribute for each variant
        based on the selected list of nodes. Increases the variant
        list size if necessary to match the selection.
        """
        sel = pm.selected()
        # resize variant list to match selection
        didCountChange = False
        while len(self.batchAction.variantValues) < len(sel):
            self.batchAction.addVariant()
            didCountChange = True

        for i, node in enumerate(sel):
            self.batchAction.variantValues[i][self.attr['name']] = sel[i]
        self.valuesChanged.emit()
        if didCountChange:
            self.variantCountChanged.emit()


BatchAttrEditor.TYPEMAP['node'] = NodeBatchAttrEditor




class BuildItemForm(QtWidgets.QWidget):
    """
    Base class for a form for editing any type of BuildItem
    """

    buildItemChanged = QtCore.Signal()

    @staticmethod
    def createItemWidget(buildItem, parent=None):
        if isinstance(buildItem, pulse.BuildGroup):
            return BuildGroupForm(buildItem, parent=parent)
        elif isinstance(buildItem, pulse.BuildAction):
            return ActionForm(buildItem, parent=parent)
        elif isinstance(buildItem, pulse.BatchBuildAction):
            return BatchActionForm(buildItem, parent=parent)
        return QtWidgets.QWidget(parent=parent)

    def __init__(self, buildItem, parent=None):
        super(BuildItemForm, self).__init__(parent=parent)
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
        layout.setSpacing(12)

        # header frame
        self.headerFrame = QtWidgets.QFrame(parent)
        colorstr = 'rgba({0}, {1}, {2}, 30)'.format(*self.getItemColor())
        self.headerFrame.setStyleSheet(".QFrame{{ background-color: {color}; }}".format(color=colorstr))
        layout.addWidget(self.headerFrame)
        # header layout
        self.headerLayout = QtWidgets.QHBoxLayout(self.headerFrame)
        self.headerLayout.setContentsMargins(10, 4, 4, 4)
        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(self.headerFrame)
        self.displayNameLabel.setMinimumHeight(20)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(self.getItemDisplayName())
        self.headerLayout.addWidget(self.displayNameLabel)

        # body layout
        bodyLay = QtWidgets.QVBoxLayout(parent)
        layout.addLayout(bodyLay)
        # main body content layout
        self.mainLayout = QtWidgets.QVBoxLayout(parent)
        # no spacing between attributes
        self.mainLayout.setSpacing(0)
        bodyLay.addLayout(self.mainLayout)
        # body spacer
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        bodyLay.addItem(spacer)

    def setupContentUi(self, parent):
        pass




class BuildGroupForm(BuildItemForm):

    def getItemDisplayName(self):
        return '{0} ({1})'.format(self.buildItem.getDisplayName(), self.buildItem.getChildCount())


class ActionForm(BuildItemForm):
    """
    Editor widget for both BuildActions and BatchBuildActions.
    Creates an ActionAttrForm for all attributes of the action.
    """

    convertToBatchClicked = QtCore.Signal()

    def setupUi(self, parent):
        super(ActionForm, self).setupUi(parent)

        # add batch conversion button to header
        convertToBatchBtn = QtWidgets.QPushButton(parent)
        convertToBatchBtn.setIcon(viewutils.getIcon("convertActionToBatch.png"))
        convertToBatchBtn.setFixedSize(QtCore.QSize(20, 20))
        convertToBatchBtn.clicked.connect(self.convertToBatchClicked.emit)
        self.headerLayout.addWidget(convertToBatchBtn)

    def setupContentUi(self, parent):
        for attr in self.buildItem.config['attrs']:
            attrValue = getattr(self.buildItem, attr['name'])
            attrForm = ActionAttrForm.createAttrForm(attr, attrValue, parent=parent)
            attrForm.valueChanged.connect(partial(self.attrValueChanged, attrForm))
            self.mainLayout.addWidget(attrForm)

    def attrValueChanged(self, attrForm, attrValue, isValueValid):
        setattr(self.buildItem, attrForm.attr['name'], attrValue)
        self.buildItemChanged.emit()



class BatchActionForm(BuildItemForm):
    """
    The main editor for Batch Actions. Very similar
    to the standard ActionForm, with a few key
    differences.

    Each attribute has a toggle that controls
    whether the attribute is variant or not.

    All variants are displayed in a list, with the ability
    to easily add and remove variants. If a BatchAttrEditor
    exists for a variant attribute type, it will be displayed
    in place of the normal AttrEditor form.
    """

    convertToActionClicked = QtCore.Signal()

    def getItemDisplayName(self):
        return 'Batch {0} (x{1})'.format(self.buildItem.getDisplayName(), self.buildItem.getActionCount())

    def setupUi(self, parent):
        super(BatchActionForm, self).setupUi(parent)

        # add action conversion button to header
        convertToActionBtn = QtWidgets.QPushButton(parent)
        convertToActionBtn.setIcon(viewutils.getIcon("convertBatchToAction.png"))
        convertToActionBtn.setFixedSize(QtCore.QSize(20, 20))
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

        spacer = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.mainLayout.addItem(spacer)

        # variant header
        variantHeader = QtWidgets.QFrame(parent)
        variantHeader.setStyleSheet(".QFrame{ background-color: rgb(255, 255, 255, 20); }")
        self.mainLayout.addWidget(variantHeader)

        variantHeaderLayout = QtWidgets.QHBoxLayout(variantHeader)
        variantHeaderLayout.setContentsMargins(10, 4, 4, 4)
        variantHeaderLayout.setSpacing(4)

        self.variantsLabel = QtWidgets.QLabel(variantHeader)
        self.variantsLabel.setText("Variants: {0}".format(len(self.buildItem.variantValues)))
        variantHeaderLayout.addWidget(self.variantsLabel)

        addBtn = QtWidgets.QPushButton(variantHeader)
        addBtn.setText('+')
        addBtn.setFixedSize(QtCore.QSize(20, 20))
        addBtn.clicked.connect(self.addVariant)
        variantHeaderLayout.addWidget(addBtn)

        removeBtn = QtWidgets.QPushButton(variantHeader)
        removeBtn.setText('-')
        removeBtn.setFixedSize(QtCore.QSize(20, 20))
        removeBtn.clicked.connect(self.removeVariantFromEnd)
        variantHeaderLayout.addWidget(removeBtn)

        # variant list main layout
        self.variantLayout = QtWidgets.QVBoxLayout(parent)
        self.variantLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.variantLayout)

        self.setupConstantsUi(parent)
        self.setupVariantsUi(parent)

    def setupConstantsUi(self, parent):
        viewutils.clearLayout(self.constantsLayout)

        # create attr form all constant attributes
        for attr in self.buildItem.actionClass.config['attrs']:
            isConstant = (attr['name'] in self.buildItem.constantValues)
            # always make an HBox with a button to toggle variant state
            attrHLayout = QtWidgets.QHBoxLayout(parent)
            attrHLayout.setSpacing(10)
            attrHLayout.setContentsMargins(0, 0, 0, 0)
            self.constantsLayout.addLayout(attrHLayout)

            if isConstant:
                # constant value, make an attr form
                attrValue = self.buildItem.constantValues[attr['name']]
                context = self.buildItem.constantValues
                attrForm = ActionAttrForm.createAttrForm(attr, attrValue, parent=parent)
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

                if BatchAttrEditor.doesEditorExist(attr):
                    batchEditor = BatchAttrEditor.createEditor(self.buildItem, attr, parent=parent)
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

            layout = QtWidgets.QVBoxLayout(parent)
            self.variantLayout.addLayout(layout)

            label = QtWidgets.QLabel(parent)
            label.setText("{0}:".format(i))
            layout.addWidget(label)

            # create attr form for all variant attributes
            for attr in self.buildItem.actionClass.config['attrs']:
                if attr['name'] not in self.buildItem.variantAttributes:
                    continue
                attrValue = variant[attr['name']]
                # context = variant
                attrForm = ActionAttrForm.createAttrForm(attr, attrValue, parent=parent)
                attrForm.valueChanged.connect(partial(self.attrValueChanged, variant, attrForm))
                layout.addWidget(attrForm)


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

    def removeVariantFromEnd(self):
        self.buildItem.removeVariantAt(-1)
        self.setupVariantsUi(self)

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

        self.model = ActionTreeItemModel.getSharedModel()
        self.selectionModel = ActionTreeSelectionModel.getSharedModel()
        self.selectionModel.selectionChanged.connect(self.selectionChanged)

    def setupUi(self, parent):
        outerLayout = QtWidgets.QVBoxLayout(parent)
        outerLayout.setContentsMargins(0, 0, 0, 0)

        self.scrollArea = QtWidgets.QScrollArea(parent)
        self.scrollArea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        outerLayout.addWidget(self.scrollArea)

        self.scrollWidget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.scrollWidget)

        self.mainLayout = QtWidgets.QVBoxLayout(self.scrollWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.scrollWidget.setLayout(self.mainLayout)

    def selectionChanged(self, selected, deselected):
        self.clearItemsUi()
        self.setupItemsUi(self.selectionModel.selectedIndexes(), self.scrollWidget)

    def clearItemsUi(self):
        while True:
            item = self.mainLayout.takeAt(0)
            if item:
                w = item.widget().setParent(None)
            else:
                break

    def setupItemsUi(self, itemIndexes, parent):
        for index in itemIndexes[:1]:
            buildItem = index.internalPointer().buildItem
            itemWidget = BuildItemForm.createItemWidget(buildItem, parent=parent)
            itemWidget.buildItemChanged.connect(partial(self.buildItemChanged, itemWidget))
            if isinstance(itemWidget, ActionForm):
                itemWidget.convertToBatchClicked.connect(partial(self.convertActionToBatch, index))
            elif isinstance(itemWidget, BatchActionForm):
                itemWidget.convertToActionClicked.connect(partial(self.convertBatchToAction, index))
            self.mainLayout.addWidget(itemWidget)

    def buildItemChanged(self, itemWidget):
        self.model.blueprint.saveToDefaultNode()

    def convertActionToBatch(self, itemModelIndex):
        # create new BatchBuildAction
        oldAction = itemModelIndex.internalPointer().buildItem
        newAction = pulse.BatchBuildAction.fromAction(oldAction)
        # replace the item in the model
        parentIndex = itemModelIndex.parent()
        row = itemModelIndex.row()
        self.model.removeRows(row, 1, parentIndex)
        self.model.insertBuildItems(row, [newAction], parentIndex)
        self.model.blueprint.saveToDefaultNode()
        # select new item
        self.selectionModel.select(self.model.index(row, 0, parentIndex), QtCore.QItemSelectionModel.Select)

    def convertBatchToAction(self, itemModelIndex):
        # create new BuildAction
        oldAction = itemModelIndex.internalPointer().buildItem
        newAction = pulse.BuildAction.fromBatchAction(oldAction)
        # replace the item in the model
        parentIndex = itemModelIndex.parent()
        row = itemModelIndex.row()
        self.model.removeRows(row, 1, parentIndex)
        self.model.insertBuildItems(row, [newAction], parentIndex)
        self.model.blueprint.saveToDefaultNode()
        # select new item
        self.selectionModel.select(self.model.index(row, 0, parentIndex), QtCore.QItemSelectionModel.Select)



class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        widget = ActionEditorWidget(self)
        self.setCentralWidget(widget)

