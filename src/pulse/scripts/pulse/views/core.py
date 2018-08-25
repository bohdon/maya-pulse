
import os
import logging
import maya.cmds as cmds
import pymel.core as pm
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymetanode as meta

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.core import Blueprint, BuildStep

__all__ = [
    'BlueprintUIModel',
    'BuildStepSelectionModel',
    'BuildStepTreeModel',
    'buttonCommand',
    'CollapsibleFrame',
    'PulseWindow',
]

LOG = logging.getLogger(__name__)


def buttonCommand(func, *args, **kwargs):
    """
    Return a function that can be called which will execute
    the given function with proper undo chunk handling.
    """

    def wrapper():
        cmds.undoInfo(openChunk=True)
        try:
            func(*args, **kwargs)
        except Exception as e:
            cmds.error(e)
        finally:
            cmds.undoInfo(closeChunk=True)

    return wrapper


class CollapsibleFrame(QtWidgets.QFrame):
    """
    A QFrame that can be collapsed when clicked.
    """

    collapsedChanged = QtCore.Signal(bool)

    def __init__(self, parent):
        super(CollapsibleFrame, self).__init__(parent)
        self._isCollapsed = False

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setIsCollapsed(not self._isCollapsed)
        else:
            return super(CollapsibleFrame, self).mouseReleaseEvent(QMouseEvent)

    def setIsCollapsed(self, newCollapsed):
        """
        Set the collapsed state of this frame.
        """
        self._isCollapsed = newCollapsed
        self.collapsedChanged.emit(self._isCollapsed)

    def isCollapsed(self):
        """
        Return True if the frame is currently collapsed.
        """
        return self._isCollapsed


class PulseWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):
    """
    A base class for any standalone window in the Pulse UI. Integrates
    the Maya builtin dockable mixin, and prevents multiple instances
    of the window.
    """

    OBJECT_NAME = None

    @classmethod
    def createAndShow(cls):
        cls.deleteInstances()
        window = cls()
        window.show()
        return window

    @classmethod
    def exists(cls):
        """
        Return True if an instance of this window exists
        """
        result = False
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            result = True
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            result = True
        if cmds.window(cls.OBJECT_NAME, q=True, ex=True):
            result = True
        return result

    @classmethod
    def deleteInstances(cls):
        """
        Delete existing instances of this window
        """
        result = False
        # close and delete an existing workspace control
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            cmds.workspaceControl(
                cls.getWorkspaceControlName(), e=True, close=True)
            result = True
        if cmds.workspaceControl(cls.getWorkspaceControlName(), q=True, ex=True):
            cmds.deleteUI(cls.getWorkspaceControlName(), control=True)
            result = True
        if cmds.window(cls.OBJECT_NAME, q=True, ex=True):
            cmds.deleteUI(cls.OBJECT_NAME, window=True)
            result = True
        return result

    @classmethod
    def getWorkspaceControlName(cls):
        return cls.OBJECT_NAME + 'WorkspaceControl'

    def __init__(self, parent=None):
        super(PulseWindow, self).__init__(parent=parent)
        self.setObjectName(self.OBJECT_NAME)
        self.setProperty('saveWindowPref', True)

    def show(self):
        """
        Show the PulseWindow.
        """
        super(PulseWindow, self).show(dockable=True, retain=False)


class BlueprintUIModel(QtCore.QObject):
    """
    The owner and manager of various models representing a Blueprint
    in the scene. All reading and writing for the Blueprint through
    the UI should be done using this model.
    """

    # shared instances, mapped by name
    INSTANCES = {}

    @classmethod
    def getDefaultModel(cls):
        return cls.getSharedModel(None)

    @classmethod
    def getSharedModel(cls, name):
        """
        Return a shared UI model by name, creating a new
        model if necessary. Will always return a valid
        BlueprintUIModel.
        """
        if name not in cls.INSTANCES:
            cls.INSTANCES[name] = cls(name)
        return cls.INSTANCES[name]

    @classmethod
    def deleteSharedModel(cls, name):
        if name in cls.INSTANCES:
            del cls.INSTANCES[name]

    # a config property on the blueprint changed
    # TODO: add more generic blueprint property data model
    rigNameChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(BlueprintUIModel, self).__init__(parent=parent)

        # the blueprint of this model
        self.blueprint = Blueprint()

        # the tree item model and selection model for BuildItems
        self.buildStepTreeModel = BuildStepTreeModel(self.blueprint)
        self.buildStepSelectionModel = BuildStepSelectionModel(
            self.buildStepTreeModel)

        # attempt to load from the scene
        self.loadFromFile(suppressWarnings=True)

    def isReadOnly(self):
        """
        Return True if the Blueprint is not able to be modified.
        """
        return False

    def getBlueprintFilepath(self):
        """
        Return the filepath for the Blueprint being edited
        """
        sceneName = pm.sceneName()
        if not sceneName:
            return None

        filepath = os.path.splitext(sceneName)[0] + '.yaml'
        return filepath

    def saveToFile(self, suppressWarnings=False):
        """
        Save the Blueprint data to the file associated with this model
        """
        filepath = self.getBlueprintFilepath()
        if not filepath:
            if not suppressWarnings:
                LOG.warning("Scene is not saved")
            return

        success = self.blueprint.saveToFile(filepath)
        if not success:
            LOG.error("Failed to save Blueprint to file: {0}".format(filepath))

    def loadFromFile(self, suppressWarnings=False):
        """
        Load the Blueprint from the file associated with this model
        """
        filepath = self.getBlueprintFilepath()
        if not filepath:
            if not suppressWarnings:
                LOG.warning("Scene is not saved")
            return

        success = self.blueprint.loadFromFile(filepath)
        self.emitAllModelResets()

        if not success:
            LOG.error(
                "Failed to load Blueprint from file: {0}".format(filepath))

    def emitAllModelResets(self):
        self.buildStepTreeModel.modelReset.emit()
        self.rigNameChanged.emit(self.getRigName())

    def getRigName(self):
        return self.blueprint.rigName

    def setRigName(self, newRigName):
        if not self.isReadOnly():
            self.blueprint.rigName = newRigName
            self.rigNameChanged.emit(self.blueprint.rigName)

    def initializeBlueprint(self):
        """
        Initialize the Blueprint to its default state.
        """
        self.blueprint.rootStep.clearChildren()
        self.blueprint.initializeDefaultActions()
        self.emitAllModelResets()

    def getActionDataForAttrPath(self, attrPath):
        """
        Return serialized data for an action represented
        by an attribute path.
        """
        stepPath, _ = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error(
                'getActionDataForAttrPath: {0} is not an action'.format(step))
            return

        return step.actionProxy.serialize()

    def setActionDataForAttrPath(self, attrPath, data):
        """
        Replace all values on an action represented by an
        attribute path by deserializng data.
        """
        stepPath, _ = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error(
                'setActionDataForAttrPath: {0} is not an action'.format(step))
            return

        step.actionProxy.deserialize(data)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])

    def getActionAttr(self, attrPath, variantIndex=-1):
        stepPath, attrName = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error('getActionAttr: {0} is not an action'.format(step))
            return

        if variantIndex >= 0:
            actionData = step.actionProxy.getVariant(variantIndex)
            return actionData.getAttrValue(attrName)
        else:
            return step.actionProxy.getAttrValue(attrName)

    def setActionAttr(self, attrPath, value, variantIndex=-1):
        """
        Set the value for an attribute on the Blueprint
        """
        if self.isReadOnly():
            return

        stepPath, attrName = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error('setActionAttr: {0} is not an action'.format(step))
            return

        if variantIndex >= 0:
            variant = step.actionProxy.getVariant(variantIndex)
            variant.setAttrValue(attrName, value)
        else:
            step.actionProxy.setAttrValue(attrName, value)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])

    def isActionAttrVariant(self, attrPath):
        stepPath, attrName = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error(
                "isActionAttrVariant: {0} is not an action".format(step))
            return

        return step.actionProxy.isVariantAttr(attrName)

    def setIsActionAttrVariant(self, attrPath, isVariant):
        """
        """
        if self.isReadOnly():
            return

        stepPath, attrName = attrPath.split('.')

        step = self.blueprint.getStepByPath(stepPath)
        if not step.isAction():
            LOG.error(
                "setIsActionAttrVariant: {0} is not an action".format(step))
            return

        step.actionProxy.setIsVariantAttr(attrName, isVariant)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])

    def moveStep(self, sourcePath, targetPath):
        """
        Move a BuildStep from source path to target path.

        Returns:
            The new path (str) of the build step, or None if
            the operation failed.
        """
        if self.isReadOnly():
            return

        step = self.blueprint.getStepByPath(sourcePath)
        if not step:
            LOG.error("moveStep: failed to find step: {0}".format(sourcePath))
            return

        if step == self.blueprint.rootStep:
            LOG.error("moveStep: cannot move root step")
            return

        index = self.buildStepTreeModel.indexByStepPath(sourcePath)

        # TODO: handle moving between new parents
        newName = targetPath.split('/')[-1]
        step.setName(newName)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])
        return step.getFullPath()


class BuildStepTreeModel(QtCore.QAbstractItemModel):
    """
    A Qt tree model for viewing and modifying the BuildStep
    hierarchy of a Blueprint.
    """

    def __init__(self, blueprint=None, parent=None):
        super(BuildStepTreeModel, self).__init__(parent=parent)
        self._blueprint = blueprint

    def setBlueprint(self, newBlueprint):
        """
        Set a new Blueprint for this model, causing a full full model reset.
        """
        if self._blueprint is not newBlueprint:
            self.beginResetModel()
            self._blueprint = newBlueprint
            self.endResetModel()

    def step(self, row, column, parent=QtCore.QModelIndex()):
        """
        Return the BuildStep for a row, column, and parent index.
        """
        return self.stepForIndex(self.index(row, column, parent))

    def stepForIndex(self, index):
        """
        Return the BuildStep of a QModelIndex.
        """
        if index.isValid():
            stepFromPtr = index.internalPointer()
            if not isinstance(stepFromPtr, pulse.BuildStep):
                import traceback
                traceback.print_stack()
            return stepFromPtr

        if self._blueprint:
            return self._blueprint.rootStep

    def indexByStepPath(self, path):
        """
        Return a QModelIndex for a step by path
        """
        # TODO: debug, this is not working
        if self._blueprint:
            step = self._blueprint.getStepByPath(path)
            if step:
                childIndeces = []
                while step.parent:
                    childIndeces.append(step.indexInParent())
                    step = step.parent
                # print(childIndeces)
                parentIndex = QtCore.QModelIndex()
                for childIndex in childIndeces:
                    index = self.index(childIndex, 0, parentIndex)
                    parentIndex = index
                return index

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Create a QModelIndex for a row, column, and parent index
        """
        if parent.isValid() and column != 0:
            return QtCore.QModelIndex()

        parentStep = self.stepForIndex(parent)
        if parentStep and parentStep.canHaveChildren:
            step = parentStep.getChildAt(row)
            return self.createIndex(row, column, step)

        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        parentStep = self.stepForIndex(index).parent
        if parentStep == self._blueprint.rootStep:
            return QtCore.QModelIndex()

        return self.createIndex(parentStep.indexInParent(), 0, parentStep)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled

        flags = QtCore.Qt.ItemIsEnabled \
            | QtCore.Qt.ItemIsSelectable \
            | QtCore.Qt.ItemIsDragEnabled \
            | QtCore.Qt.ItemIsEditable

        if self.stepForIndex(index).canHaveChildren:
            flags |= QtCore.Qt.ItemIsDropEnabled

        return flags

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        step = self.stepForIndex(parent)
        return step.numChildren() if step else 0

    def insertRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        step = self.stepForIndex(parent)
        for _ in range(count):
            step.insertChild(row, BuildStep())
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        step = self.stepForIndex(parent)
        step.removeChildren(row, count)
        self.endRemoveRows()
        return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        step = self.stepForIndex(index)

        if role == QtCore.Qt.DisplayRole:
            return step.getDisplayName()

        elif role == QtCore.Qt.EditRole:
            return step.name

        elif role == QtCore.Qt.DecorationRole:
            iconFile = step.getIconFile()
            if iconFile:
                return QtGui.QIcon(iconFile)

        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(0, 20)

        elif role == QtCore.Qt.ForegroundRole:
            color = step.getColor()
            if color:
                return QtGui.QColor(*[c * 255 for c in color])

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False

        if role != QtCore.Qt.EditRole:
            return False

        step = self.stepForIndex(index)

        stepPath = step.getFullPath()
        stepNewPath = os.path.dirname(stepPath) + '/' + value
        cmds.pulseMoveStep(stepPath, stepNewPath)
        # oldName = step.name
        # step.setName(value)
        # if step.name != oldName:
        #     self.dataChanged.emit(index, index, [])

        return False

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        result = QtCore.QMimeData()

        def getSingleItemData(index):
            step = self.stepForIndex(index)
            data = step.serialize()
            if 'children' in data:
                del data['children']
            return data

        stepDataList = [getSingleItemData(index) for index in indexes]
        datastr = meta.encodeMetaData(stepDataList)
        result.setData('text/plain', datastr)
        print(datastr)
        return result

    def canDropMimeData(self, data, action, row, column, parent):
        try:
            stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except Exception:
            return False
        else:
            return isinstance(stepDataList, list)

    def dropMimeData(self, data, action, row, column, parent):
        result = super(BuildStepTreeModel, self).dropMimeData(
            data, action, row, column, parent)

        if not result:
            return False

        try:
            stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except Exception as e:
            print(e)
        else:
            print(stepDataList, data, action, row, column, parent)

            count = len(stepDataList)
            for i in range(count):
                index = self.index(row + i, 0, parent)
                step = self.stepForIndex(index)
                if step:
                    step.deserialize(stepDataList[i])
                    # self.dataChanged.emit(index, index, [])

        return True


class BuildStepSelectionModel(QtCore.QItemSelectionModel):
    """
    The selection model for the BuildItems of a Blueprint. Allows
    a singular selection that is shared across all UI for the Blueprint.
    An instance of this model should be acquired by going through
    the BlueprintUIModel for a specific Blueprint.
    """

    def getSelectedItems(self):
        """
        Return the currently selected BuildItems
        """
        indexes = self.selectedIndexes()
        items = []
        for index in indexes:
            if index.isValid():
                buildItem = index.internalPointer()
                if buildItem:
                    items.append(buildItem)
        return list(set(items))

    def getSelectedGroups(self):
        """
        Return indexes of the selected BuildItems that can have children
        """
        indexes = self.selectedIndexes()
        indeces = []
        for index in indexes:
            if index.isValid():
                buildItem = index.internalPointer()
                if buildItem and buildItem.canHaveChildren:
                    indeces.append(index)
                # TODO: get parent until we have an item that supports children
        return list(set(indeces))

    def getSelectedAction(self):
        """
        Return the currently selected BuildAction, if any.
        """
        items = self.getSelectedItems()
        return [i for i in items if isinstance(i, pulse.BuildAction)]

    def getSelectedItemPaths(self):
        """
        Return the full paths of the selected BuildItems
        """
        items = self.getSelectedItems()
        return [i.getFullPath() for i in items]

    def setSelectedItemPaths(self, paths):
        """
        Set the selection using BuildItem paths
        """
        model = self.model()
        if not model or not hasattr(model, 'blueprint'):
            return

        # blueprint = model.blueprint
        # items = [blueprint.getStepByPath(p) for p in paths]
        # indeces = [model.indexForItem(i) for i in items if i]
        # self.clear()
        # for index in indeces:
        #     if index.isValid():
        #         self.select(index, QtCore.QItemSelectionModel.Select)
