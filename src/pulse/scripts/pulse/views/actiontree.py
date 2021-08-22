"""
Tree widget for displaying the build step hierarchy of a blueprint.
"""

import logging

import maya.cmds as cmds

from .actionpalette import ActionPaletteWidget
from .core import BlueprintUIModel
from .core import PulseWindow
from .. import sym
from ..buildItems import BuildStep
from ..serializer import serializeAttrValue
from ..vendor.Qt import QtCore, QtWidgets, QtGui

LOG = logging.getLogger(__name__)


class ActionTreeStyledItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(ActionTreeStyledItemDelegate, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

    def paint(self, painter, option, index):
        opt = option
        self.initStyleOption(opt, index)
        opt.font.setItalic(self.shouldBeItalic(index))

        step = self.blueprintModel.buildStepTreeModel.stepForIndex(index)
        if (step):
            opt.font.setStrikeOut(step.isDisabled)

        super(ActionTreeStyledItemDelegate, self).paint(
            painter, opt, index)

    def shouldBeItalic(self, index):
        return self.blueprintModel.isReadOnly()


class ActionTreeView(QtWidgets.QTreeView):
    """
    A tree view for displaying BuildActions in a Blueprint
    """

    def __init__(self, blueprintModel=None, parent=None):
        super().__init__(parent=parent)

        self.blueprintModel = blueprintModel

        self.setItemDelegate(ActionTreeStyledItemDelegate(parent))
        self.setHeaderHidden(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setIndentation(14)

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key_Delete:
            self.deleteSelectedItems()
            return True

        elif key == QtCore.Qt.Key_D:
            self.toggleSelectedItemsDisabled()
            return True

        elif key == QtCore.Qt.Key_M:
            self.mirrorSelectedItems()
            return True

        return super().keyPressEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        # don't perform selection changes on middle mouse press
        if event.buttons() & QtCore.Qt.MiddleButton:
            return True

        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        # start dragging when using middle mouse
        if event.buttons() & QtCore.Qt.MiddleButton:
            self.startDrag(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction)
            return True

        return super().mouseMoveEvent(event)

    def deleteSelectedItems(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps = []
        for index in indexes:
            step = self.model().stepForIndex(index)
            if step:
                steps.append(step)
        steps = BuildStep.getTopmostSteps(steps)

        paths = []
        for step in steps:
            path = step.getFullPath()
            print(step, path)
            if path:
                paths.append(path)

        cmds.undoInfo(openChunk=True, chunkName='Delete Pulse Actions')
        for path in paths:
            cmds.pulseDeleteStep(path)
        cmds.undoInfo(closeChunk=True)

    def toggleSelectedItemsDisabled(self):
        """
        Toggle the disabled state of the selected items.
        If item disable states are mismatched, will disable all items.
        """
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps = []
        for index in indexes:
            step = self.model().stepForIndex(index)
            if step:
                steps.append((index, step))

        all_disabled = all([s.isDisabled for i, s in steps])
        newDisabled = False if all_disabled else True
        for index, step in steps:
            self.model().setData(index, newDisabled, QtCore.Qt.CheckStateRole)

    def mirrorSelectedItems(self):
        indexes = self.selectedIndexes()

        if not indexes:
            return

        steps = []
        for index in indexes:
            step = self.model().stepForIndex(index)
            if step:
                steps.append(step)

        mirrorUtil = MirrorActionUtil(self.blueprintModel)
        for step in steps:
            if step.isAction():
                mirrorUtil.mirrorAction(step)


class ActionTreeWidget(QtWidgets.QWidget):
    """
    A widget that displays a all BuildActions in a Blueprint.
    Items can be selected, and the shared selection model
    can then be used to display info about selected BuildActions
    in other UI.
    """

    def __init__(self, parent=None):
        super(ActionTreeWidget, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self.selectionModel = self.blueprintModel.buildStepSelectionModel

        self.setupUi(self)

        # connect signals
        self.model.modelReset.connect(self.onModelReset)

    def setupUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)

        self.treeView = ActionTreeView(self.blueprintModel, parent)
        self.treeView.setModel(self.model)
        self.treeView.setSelectionModel(self.selectionModel)
        self.treeView.expandAll()
        layout.addWidget(self.treeView)

    def onModelReset(self):
        self.treeView.expandAll()


class ActionTreeWindow(PulseWindow):
    """
    A standalone window that contains an ActionTreeWidget
    and an ActionPaletteWidget.
    """

    OBJECT_NAME = 'pulseActionTreeWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.actiontree'

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Tree')

        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)

        self.actionTree = ActionTreeWidget(self)
        layout.addWidget(self.actionTree)

        self.actionPalette = ActionPaletteWidget(self)
        layout.addWidget(self.actionPalette)

        layout.setStretch(layout.indexOf(self.actionTree), 2)
        layout.setStretch(layout.indexOf(self.actionPalette), 1)


# Action Mirroring
# ----------------

class MirrorActionUtil(object):
    """
    A util class for mirroring BuildAction data.
    """

    def __init__(self, blueprintModel):
        # type: (BlueprintUIModel) -> None
        self.blueprintModel = blueprintModel
        self._config = None

    def getConfig(self):
        if self._config is None:
            self._config = self.blueprintModel.blueprint.getConfig()
        return self._config

    def getMirroredStepName(self, stepName):
        """
        Return the mirrored name of a BuildStep.

        Returns:
            The mirrored step name, or None if it cannot be mirrored
        """
        destName = sym.getMirroredName(stepName, self.getConfig())
        if destName != stepName:
            return destName

    def canMirrorStep(self, sourceStep):
        """
        Return True if a BuildStep can be mirrored
        """
        return sourceStep.isAction() and self.getMirroredStepName(sourceStep.name) is not None

    def getMirroredStepPath(self, sourceStep):
        """
        Return the full path to a BuildStep by mirroring a steps name.
        """
        destStepName = self.getMirroredStepName(sourceStep.name)
        if destStepName:
            parentPath = sourceStep.getParentPath()
            if parentPath:
                return parentPath + '/' + destStepName
            return destStepName

    def getPairedStep(self, sourceStep):
        """
        Return the BuildStep that is paired with a step, if any
        """
        destStepPath = self.getMirroredStepPath(sourceStep)
        if destStepPath:
            return self.blueprintModel.getStep(destStepPath)

    def getOrCreatePairedStep(self, sourceStep):
        """
        Return the BuildStep that is paired with a step,
        creating a new BuildStep if necessary.
        """
        destStepPath = self.getMirroredStepPath(sourceStep)
        if destStepPath:
            destStep = self.blueprintModel.getStep(destStepPath)
            if not destStep:
                childIndex = sourceStep.indexInParent() + 1
                newStepData = sourceStep.serialize()
                newStepData['name'] = self.getMirroredStepName(sourceStep.name)
                dataStr = serializeAttrValue(newStepData)
                cmds.pulseCreateStep(
                    sourceStep.getParentPath(), childIndex, dataStr)
                return self.blueprintModel.getStep(destStepPath)
            else:
                return destStep

    def mirrorAction(self, sourceStep):
        """
        Mirror a BuildStep
        """
        if not self.canMirrorStep(sourceStep):
            LOG.warning("Cannot mirror %s, only actions with"
                        "symmetrical names can be mirrored", sourceStep)
            return False

        cmds.undoInfo(openChunk=True, chunkName='Mirror Action')

        destStep = self.getOrCreatePairedStep(sourceStep)
        if not destStep:
            return False

        sourceAction = sourceStep.actionProxy
        destAction = destStep.actionProxy

        if not destAction or destAction.getActionId() != sourceAction.getActionId():
            # action was setup incorrectly
            LOG.warning("Cannot mirror %s -> %s, destination action"
                        "is not tye same type", sourceStep, destStep)
            return False

        destStepPath = destStep.getFullPath()

        # match up variant attrs
        for attr in sourceAction.getAttrs():
            isVariant = sourceAction.isVariantAttr(attr['name'])
            attrPath = destStepPath + '.' + attr['name']
            if destAction.isVariantAttr(attr['name']) != isVariant:
                cmds.pulseSetIsVariantAttr(attrPath, isVariant)

        # match up variant lengths
        while sourceAction.numVariants() < destAction.numVariants():
            destAction.removeVariantAt(-1)
        while sourceAction.numVariants() > destAction.numVariants():
            destAction.addVariant()

        #  mirror invariant attr values
        for attr in sourceAction.getAttrs():
            if not sourceAction.isVariantAttr(attr['name']):
                value = sourceAction.getAttrValue(attr['name'])
                mirroredValue = self.mirrorActionValue(attr, value)
                attrPath = destStepPath + '.' + attr['name']
                mirroredValueStr = serializeAttrValue(mirroredValue)
                LOG.debug('%s -> %s', value, mirroredValue)
                cmds.pulseSetActionAttr(attrPath, mirroredValueStr)

        # mirror variant attr values
        for i in range(sourceAction.numVariants()):
            variant = sourceAction.getVariant(i)
            for attrName in sourceAction.getVariantAttrs():
                attr = variant.getAttrConfig(attrName)
                if not attr:
                    # possibly stale or removed attribute
                    continue
                value = variant.getAttrValue(attrName)
                mirroredValue = self.mirrorActionValue(attr, value)
                attrPath = destStepPath + '.' + attr['name']
                mirroredValueStr = serializeAttrValue(mirroredValue)
                LOG.debug('%s -> %s', value, mirroredValue)

                cmds.pulseSetActionAttr(attrPath, mirroredValueStr, v=i)

        cmds.undoInfo(closeChunk=True)

        return True

    def mirrorActionValue(self, attr, value):
        """
        Args:
            attr (dict): The attribute config
            value: The attribute value, of varying type
        """

        def getPairedNodeOrSelf(node):
            """
            Return the paired node of a node, if one exists, otherwise return the node.
            """
            paired_node = sym.getPairedNode(node)
            if paired_node:
                return paired_node
            return node

        if not value:
            return value

        if attr['type'] == 'node':
            return getPairedNodeOrSelf(value)

        elif attr['type'] == 'nodelist':
            return [getPairedNodeOrSelf(node) for node in value]

        elif attr['type'] == 'string':
            return sym.getMirroredName(value, self.getConfig())

        elif attr['type'] == 'stringlist':
            return [sym.getMirroredName(v, self.getConfig()) for v in value]

        return value
