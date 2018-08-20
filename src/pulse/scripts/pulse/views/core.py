
import os
import logging
import maya.cmds as cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymetanode as meta

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.core import BlueprintLifecycleEvents, BlueprintChangeEvents, BuildStep

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

    BlueprintUIModels can exist without the Blueprint node in the
    scene. In this case the model won't be functional, but will
    automatically update if the same named Blueprint node is created.

    The model maintains a list of subscribers used to properly manage
    and cleanup Maya callbacks, so any QWidgets should call addSubscriber
    and removeSubscriber on the model during show and hide events (or similar).
    """

    # shared instances, mapped by blueprint node name
    INSTANCES = {}

    @classmethod
    def getDefaultModel(cls):
        return cls.getSharedModel(pulse.BLUEPRINT_NODENAME)

    @classmethod
    def getSharedModel(cls, blueprintNodeName):
        """
        Return a shared model for a specific Blueprint node,
        creating a new model if necessary. Will always return
        a valid BlueprintUIModel.
        """
        if blueprintNodeName not in cls.INSTANCES:
            cls.INSTANCES[blueprintNodeName] = cls(blueprintNodeName)
        return cls.INSTANCES[blueprintNodeName]

    @classmethod
    def deleteSharedModel(cls, blueprintNodeName):
        if blueprintNodeName in cls.INSTANCES:
            del cls.INSTANCES[blueprintNodeName]

    # the blueprint node was created
    blueprintCreated = QtCore.Signal()

    # the blueprint node was deleted
    blueprintDeleted = QtCore.Signal()

    # the blueprint node was modified from loading
    blueprintNodeChanged = QtCore.Signal()

    # a config property on the blueprint changed
    rigNameChanged = QtCore.Signal(str)

    def __init__(self, blueprintNodeName, parent=None):
        super(BlueprintUIModel, self).__init__(parent=parent)

        # the blueprint node this model is associated with
        self.blueprintNodeName = blueprintNodeName

        # the blueprint of this model
        self.blueprint = None
        # if cmds.objExists(self.blueprintNodeName):
        #     # load from existing node
        #     self.blueprint = pulse.Blueprint.fromNode(self.blueprintNodeName)

        # the tree item model and selection model for BuildItems
        self.buildStepTreeModel = BuildStepTreeModel(self.blueprint)
        self.buildStepTreeModel.dataChanged.connect(self._onItemModelChanged)
        self.buildStepTreeModel.rowsInserted.connect(self._onItemModelChanged)
        self.buildStepTreeModel.rowsMoved.connect(self._onItemModelChanged)
        self.buildStepTreeModel.rowsRemoved.connect(self._onItemModelChanged)
        self.buildStepSelectionModel = BuildStepSelectionModel(
            self.buildStepTreeModel)

        self._modelSubscribers = []

        self._isSaving = False

        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.appendUnique(self._onBlueprintCreated)
        lifeEvents.onBlueprintDeleted.appendUnique(self._onBlueprintDeleted)

    def __del__(self):
        super(BlueprintUIModel, self).__del__()
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.removeAll(self._onBlueprintCreated)
        lifeEvents.onBlueprintDeleted.removeAll(self._onBlueprintDeleted)

    def _subscribeToBlueprintNodeChanges(self):
        changeEvents = BlueprintChangeEvents.getShared(self.blueprintNodeName)
        if changeEvents:
            changeEvents.onBlueprintNodeChanged.appendUnique(
                self._onBlueprintNodeChanged)
            changeEvents.addSubscriber(self)
            LOG.debug('subscribed to blueprint node changes')

    def _setBlueprint(self, newBlueprint):
        self.blueprint = newBlueprint
        self.buildStepTreeModel.setBlueprint(self.blueprint)
        self.rigNameChanged.emit(self.getRigName())

    def blueprintExists(self):
        """
        Return True if the Blueprint node exists for this model.
        """
        return self.blueprint is not None

    def addSubscriber(self, subscriber):
        """
        Add a subscriber to this model. Will enable Maya callbacks
        if this is the first subscriber.
        """
        if subscriber not in self._modelSubscribers:
            self._modelSubscribers.append(subscriber)
        # if any subscribers, subscribe to maya callbacks
        if self._modelSubscribers:
            lifeEvents = BlueprintLifecycleEvents.getShared()
            lifeEvents.addSubscriber(self)
            changeEvents = BlueprintChangeEvents.getShared(
                self.blueprintNodeName)
            if changeEvents:
                changeEvents.addSubscriber(self)

        return
        # we may have missed events since last subscribed,
        # so make sure blueprint exists == node exists
        # if cmds.objExists(self.blueprintNodeName):
        #     if self.blueprint is None:
        #         self._setBlueprint(
        #             pulse.Blueprint.fromNode(self.blueprintNodeName))
        # else:
        #     if self.blueprint is not None:
        #         self._setBlueprint(None)

    def removeSubscriber(self, subscriber):
        """
        Remove a subscriber from this model. Will disable
        Maya callbacks if no subscribers remain.
        """
        if subscriber in self._modelSubscribers:
            self._modelSubscribers.remove(subscriber)
        # if no subscribers, unsubscribe from maya callbacks
        if not self._modelSubscribers:
            lifeEvents = BlueprintLifecycleEvents.getShared()
            lifeEvents.removeSubscriber(self)
            changeEvents = BlueprintChangeEvents.getShared(
                self.blueprintNodeName)
            if changeEvents:
                changeEvents.removeSubscriber(self)

    def _onBlueprintCreated(self, node):
        return
        # if node.nodeName() == self.blueprintNodeName:
        #     self._setBlueprint(
        #         pulse.Blueprint.fromNode(self.blueprintNodeName))
        #     self._subscribeToBlueprintNodeChanges()
        #     self.blueprintCreated.emit()

    def _onBlueprintDeleted(self, node):
        return
        # if node.nodeName() == self.blueprintNodeName:
        #     self._setBlueprint(None)
        #     # doing some cleanup since we can here
        #     BlueprintChangeEvents.cleanupSharedInstances()
        #     self.blueprintDeleted.emit()
        #     self.buildStepTreeModel.setBlueprint(None)

    def _onBlueprintNodeChanged(self, node):
        """
        The blueprint node has changed, reload its data
        """
        return
        # if not self._isSaving:
        #     selectedPaths = self.buildStepSelectionModel.getSelectedItemPaths()
        #     self.load()
        #     self.blueprintNodeChanged.emit()
        #     self.buildStepSelectionModel.setSelectedItemPaths(selectedPaths)

    def _onItemModelChanged(self):
        self.save()

    def isReadOnly(self):
        """
        Return True if the Blueprint is not able to be modified.
        This will be True if the Blueprint doesn't exist.
        """
        return self.blueprint is None

    def getBlueprint(self):
        """
        Return the Blueprint represented by this model.
        """
        return self.blueprint

    def getRigName(self):
        # TODO: better solve for blueprint meta data
        if self.blueprint:
            return self.blueprint.rigName

    def setRigName(self, newRigName):
        if not self.isReadOnly():
            self.blueprint.rigName = newRigName
            self.rigNameChanged.emit(self.blueprint.rigName)
            self.save()

    def setBlueprintAttr(self, name, value):
        """
        Set the value for an attribute on the Blueprint
        """
        print('setattr', name, value)
        if self.isReadOnly() or not self.blueprintExists():
            return

        step = self.blueprint.getStepByPath('Hand/Bind Skin')
        step.actionProxy.setAttrValue('maxInfluences', value)
        self.buildStepTreeModel.modelReset.emit()

    def moveStep(self, sourcePath, targetPath):
        """
        Move a BuildStep from source path to target path.

        Returns:
            The new path (str) of the build step, or None if
            the operation failed.
        """
        if self.isReadOnly() or not self.blueprintExists():
            return

        step = self.blueprint.getStepByPath(sourcePath)
        if not step:
            LOG.error("moveStep: failed to find step: {0}".format(sourcePath))
            return

        if step == self.blueprint.rootStep:
            LOG.error("moveStep: cannot move root step")
            return

        # TODO: handle moving between new parents
        newName = targetPath.split('/')[-1]
        step.setName(newName)

        # TODO: find index of step and emit data change instead of reset
        self.buildStepTreeModel.modelReset.emit()
        return step.getFullPath()

    def saveToSceneFile(self):
        """
        Save the Blueprint data to a file paired with the current scene
        """
        if self.blueprint:
            self.blueprint.saveToSceneFile()

    def loadFromSceneFile(self):
        blueprint = pulse.Blueprint.fromSceneFile()
        if blueprint:
            self._setBlueprint(blueprint)
            self.buildStepTreeModel.modelReset.emit()

    def save(self):
        """
        Save the Blueprint data to the blueprint node
        """
        return
        self._isSaving = True
        # TODO: save after the deferred call instead of on every call?
        self.blueprint.saveToNode(self.blueprintNodeName)
        cmds.evalDeferred(self._saveFinishedDeferred)

    def _saveFinishedDeferred(self):
        self._isSaving = False
        # TODO: fire a signal

    def load(self):
        """
        Load the Blueprint data from the blueprint node
        """
        return
        LOG.debug('loading...')
        # TODO: preserve selection by item path
        if (cmds.objExists(self.blueprintNodeName) and
                pulse.Blueprint.isBlueprintNode(self.blueprintNodeName)):
            # node exists and is a valid blueprint
            if self.blueprint is None:
                self._setBlueprint(
                    pulse.Blueprint.fromNode(self.blueprintNodeName))
            else:
                self.blueprint.loadFromNode(self.blueprintNodeName)
                self.buildStepTreeModel.modelReset.emit()
            # attempt to preserve selection
            LOG.debug('load finished.')

        else:
            # attempted to load from non-existent or invalid node
            self._setBlueprint(None)
            LOG.debug('load failed.')

    def createNode(self):
        """
        Delete the blueprint node of this model
        """
        if not cmds.objExists(self.blueprintNodeName):
            pulse.Blueprint.createNode(self.blueprintNodeName)

    def deleteNode(self):
        """
        Delete the blueprint node of this model
        """
        if cmds.objExists(self.blueprintNodeName):
            cmds.delete(self.blueprintNodeName)


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
