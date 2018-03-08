
from functools import partial
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
import maya.cmds as cmds
import maya.OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymetanode as meta

import pulse
from pulse.events import BlueprintLifecycleEvents

__all__ = [
    'BlueprintUIModel',
    'BuildItemSelectionModel',
    'BuildItemTreeModel',
    'buttonCommand',
    'CollapsibleFrame',
    'PulseWindow',
    'TreeModelBuildItem',
    'UIEventMixin',
]

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
            print(e)
        finally:
            cmds.undoInfo(closeChunk=True)
    
    return wrapper


class CollapsibleFrame(QtWidgets.QFrame):

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
        self._isCollapsed = newCollapsed
        self.collapsedChanged.emit(self._isCollapsed)
    
    def isCollapsed(self):
        return self._isCollapsed


class UIEventMixin(object):
    """
    A mixin for listening to shared events related
    to pulse scene changes, such as the creation or
    deletion of a Blueprint.
    """

    # the list of currently active ui objects listening for events
    _LISTENERS = []
    # is the mixin globally registered with maya callbacks?
    _IS_REGISTERED = False
    # the MCallbackIDs of registered messages
    _MSGIDS = []
    # flags for preventing redundant deferred event calls
    _NODES_DIRTY = False
    _BLUEPRINT_DIRTY = False
    # MCallbackID for the blueprint attribute change message
    _MSGID_BLUEPRINTCHANGE = None
    
    @staticmethod
    def _registerUIEventCallbacks():
        """
        Add MMessage callbacks for necessary Maya events
        """
        if not UIEventMixin._IS_REGISTERED:
            UIEventMixin._IS_REGISTERED = True
            msgIds = []
            msgIds.append(om.MDGMessage.addNodeAddedCallback(UIEventMixin._onNodesChanged, 'network'))
            msgIds.append(om.MDGMessage.addNodeRemovedCallback(UIEventMixin._onNodesChanged, 'network'))
            msgIds.append(om.MDGMessage.addNodeAddedCallback(UIEventMixin._onNodesChanged, 'transform'))
            msgIds.append(om.MDGMessage.addNodeRemovedCallback(UIEventMixin._onNodesChanged, 'transform'))
            UIEventMixin._MSGIDS = msgIds
    
    @staticmethod
    def _unregisterUIEventCallbacks():
        """
        Remove all registered MMessage callbacks
        """
        if UIEventMixin._IS_REGISTERED:
            UIEventMixin._IS_REGISTERED = False
            if UIEventMixin._MSGIDS:
                for id in UIEventMixin._MSGIDS:
                    om.MMessage.removeCallback(id)
                UIEventMixin._MSGIDS = []

    @staticmethod
    def _nodeAdded(node, *args):
        UIEventMixin._onNodesChanged()

    @staticmethod
    def _onNodesChanged(node, *args):
        # queue deferred change event only once per scene changes
        if not UIEventMixin._NODES_DIRTY:
            UIEventMixin._NODES_DIRTY = True
            cmds.evalDeferred(UIEventMixin._onNodesChangedDeferred)
    
    @staticmethod
    def _onNodesChangedDeferred():
        """
        Called when relevant nodes are added or removed.
        Used to check for changes in blueprints or rigs.
        """
        UIEventMixin._NODES_DIRTY = False
        blueprintExists = pulse.Blueprint.doesDefaultNodeExist()
        if blueprintExists:
            UIEventMixin._registerBlueprintChangeCallbacks()
        else:
            UIEventMixin._unregisterBlueprintChangeCallbacks()
        rigExists = len(pulse.getAllRigs()) > 0
        for listener in UIEventMixin._LISTENERS:
            listener.setBlueprintExists(blueprintExists)
            listener.setRigExists(rigExists)
    
    @staticmethod
    def _registerBlueprintChangeCallbacks():
        blueprintNode = pulse.Blueprint.getDefaultNode()
        if (UIEventMixin._MSGID_BLUEPRINTCHANGE is None) and blueprintNode:
            msgId = om.MNodeMessage.addAttributeChangedCallback(blueprintNode.__apimobject__(), UIEventMixin._onBlueprintAttrChanged)
            UIEventMixin._MSGID_BLUEPRINTCHANGE = msgId
    
    @staticmethod
    def _unregisterBlueprintChangeCallbacks():
        if not (UIEventMixin._MSGID_BLUEPRINTCHANGE is None):
            om.MMessage.removeCallback(UIEventMixin._MSGID_BLUEPRINTCHANGE)
            UIEventMixin._MSGID_BLUEPRINTCHANGE = None
    
    @staticmethod
    def _onBlueprintAttrChanged(changeType, srcPlug, dstPlug, clientData):
        if srcPlug.partialName() == 'pyMetaData' and not UIEventMixin._BLUEPRINT_DIRTY:
            UIEventMixin._BLUEPRINT_DIRTY = True
            cmds.evalDeferred(UIEventMixin._onBlueprintChangedDeferred)
    
    @staticmethod
    def _onBlueprintChangedDeferred():
        UIEventMixin._BLUEPRINT_DIRTY = False
        for listener in UIEventMixin._LISTENERS:
            listener.onBlueprintChanged()
    
    def initUIEventMixin(self):
        self.blueprintExists = pulse.Blueprint.doesDefaultNodeExist()
        self.rigExists = len(pulse.getAllRigs()) > 0
    
    def enableUIMixinEvents(self):
        """
        Enable events on this object
        """
        if self not in UIEventMixin._LISTENERS:
            UIEventMixin._LISTENERS.append(self)
        UIEventMixin._registerUIEventCallbacks()
        UIEventMixin._registerBlueprintChangeCallbacks()
    
    def disableUIMixinEvents(self):
        """
        Disable events on this object
        """
        if self in UIEventMixin._LISTENERS:
            UIEventMixin._LISTENERS.remove(self)
        if not UIEventMixin._LISTENERS:
            UIEventMixin._unregisterUIEventCallbacks()
            UIEventMixin._unregisterBlueprintChangeCallbacks()
    
    def setBlueprintExists(self, newExists):
        if newExists != self.blueprintExists:
            self.blueprintExists = newExists
            if self.blueprintExists:
                self.onBlueprintCreated()
            else:
                self.onBlueprintDeleted()
            self.onPulseNodesChanged()
    
    def setRigExists(self, newExists):
        if newExists != self.rigExists:
            self.rigExists = newExists
            if self.rigExists:
                self.onRigCreated()
            else:
                self.onRigDeleted()
            self.onPulseNodesChanged()
    
    def onPulseNodesChanged(self):
        """
        Called whenever a blueprint or rig is created or deleted.
        """
        pass
    
    def onBlueprintCreated(self):
        pass
    
    def onBlueprintChanged(self):
        """
        Called whenever the serialized Blueprint has changed.
        This may not be as granular as expected depending on how
        the attr form reports and applies Blueprint edits.
        """
        pass
    
    def onBlueprintDeleted(self):
        pass
    
    def onRigCreated(self):
        pass
    
    def onRigDeleted(self):
        pass


class PulseWindow(MayaQWidgetDockableMixin, QtWidgets.QMainWindow):

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
            cmds.workspaceControl(cls.getWorkspaceControlName(), e=True, close=True)
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
    automatically update if the matching Blueprint node is created.

    The model uses subscription notify calls to properly manage
    and cleanup Maya callbacks, so any QWidgets should call
    notifySubscriberAdded / notifySubscriberRemoved on the model
    during show and hide events (or similar).
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


    blueprintCreated = QtCore.Signal()
    blueprintDeleted = QtCore.Signal()
    rigNameChanged = QtCore.Signal(str)

    def __init__(self, blueprintNodeName, parent=None):
        super(BlueprintUIModel, self).__init__(parent=parent)

        # the blueprint node this model is associated with
        self.blueprintNodeName = blueprintNodeName

        # the blueprint of this model
        self.blueprint = None
        if cmds.objExists(self.blueprintNodeName):
            # load from existing node
            self.blueprint = pulse.Blueprint.fromNode(self.blueprintNodeName)
        
        # the tree item model and selection model for BuildItems
        self.buildItemTreeModel = BuildItemTreeModel(self.blueprint)
        self.buildItemSelectionModel = BuildItemSelectionModel(self.buildItemTreeModel)

        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.appendUnique(self._onBlueprintCreated)
        lifeEvents.onBlueprintDeleted.appendUnique(self._onBlueprintDeleted)
    
    def __del__(self):
        super(BlueprintUIModel, self).__del__()
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.onBlueprintCreated.removeAll(self._onBlueprintCreated)
        lifeEvents.onBlueprintDeleted.removeAll(self._onBlueprintDeleted)
    
    def _setBlueprint(self, newBlueprint):
        self.blueprint = newBlueprint
        self.buildItemTreeModel.setBlueprint(self.blueprint)
        self.rigNameChanged.emit(self.getRigName())
    
    def notifySubscriberAdded(self, subscriber):
        # pass through to the events dispatchers
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.notifySubscriberAdded(subscriber)
        # we may have missed events since last subscribed,
        # so make sure blueprint exists == node exists
        if cmds.objExists(self.blueprintNodeName):
            if self.blueprint is None:
                self._setBlueprint(pulse.Blueprint.fromNode(self.blueprintNodeName))
        else:
            if self.blueprint is not None:
                self._setBlueprint(None)

    def notifySubscriberRemoved(self, subscriber):
        # pass through to the events dispatchers
        lifeEvents = BlueprintLifecycleEvents.getShared()
        lifeEvents.notifySubscriberRemoved(subscriber)
    
    def _onBlueprintCreated(self, node):
        if node.nodeName() == self.blueprintNodeName:
            self._setBlueprint(pulse.Blueprint.fromNode(self.blueprintNodeName))
            self.blueprintCreated.emit()
    
    def _onBlueprintDeleted(self, node):
        if node.nodeName() == self.blueprintNodeName:
            self._setBlueprint(None)
            self.blueprintDeleted.emit()
    
    def isReadOnly(self):
        return self.blueprint is None
    
    def exists(self):
        return self.blueprint is not None
    
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
    
    def save(self):
        """
        Save the Blueprint data to the blueprint node
        """
        self.blueprint.saveToNode(self.blueprintNodeName)
        # TODO: fire a signal
    
    def load(self):
        """
        Load the Blueprint data from the blueprint node
        """
        self.blueprint.loadFromNode(self.blueprintNodeName)
        self.buildItemTreeModel.modelReset.emit()



class TreeModelBuildItem(object):
    """
    A wrapper for BuildItem that makes it more usable
    in a Qt tree model. Designed for short uses, should not
    be stored or referenced after immediate use.

    Returns TreeModelBuildItem objects when retrieving
    parent or children BuildItems.
    """

    def __init__(self, buildItem):
        self.buildItem = buildItem

    def children(self):
        if self.isGroup():
            return [TreeModelBuildItem(c) for c in self.buildItem.children]
        else:
            return []

    def isGroup(self):
        return isinstance(self.buildItem, pulse.BuildGroup)

    def columnCount(self):
        return 1

    def childCount(self):
        return len(self.children())

    def child(self, row):
        return self.children()[row]

    def parent(self):
        if self.buildItem.parent:
            return TreeModelBuildItem(self.buildItem.parent)

    def row(self):
        if self.buildItem.parent:
            return self.buildItem.parent.children.index(self.buildItem)
        return 0

    def insertChildren(self, position, childBuildItems):
        if not self.isGroup():
            return False

        if position < 0:
            position = self.childCount()

        for childBuildItem in childBuildItems:
            self.buildItem.insertChild(position, childBuildItem)

        return True

    def removeChildren(self, position, count):
        if not self.isGroup():
            return False

        if position < 0 or position + count > self.childCount():
            return False

        for row in range(count):
            self.buildItem.removeChildAt(position)

        return True

    def setData(self, column, value):
        if not self.isGroup():
            return False

        self.buildItem.displayName = value

        return True


    def data(self, column, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if isinstance(self.buildItem, pulse.BuildGroup):
                return '{0} ({1})'.format(self.buildItem.getDisplayName(), self.buildItem.getChildCount())
            elif isinstance(self.buildItem, pulse.BatchBuildAction):
                return '{0} (x{1})'.format(self.buildItem.getDisplayName(), self.buildItem.getActionCount())
            else:
                return self.buildItem.getDisplayName()

        elif role == QtCore.Qt.EditRole:
            return self.buildItem.getDisplayName()

        elif role == QtCore.Qt.DecorationRole:
            iconFile = self.buildItem.getIconFile()
            if iconFile:
                return QtGui.QIcon(iconFile)

        elif role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(0, 20)

        elif role == QtCore.Qt.ForegroundRole:
            color = self.buildItem.getColor()
            if color:
                return QtGui.QColor(*[c * 255 for c in color])




class BuildItemTreeModel(QtCore.QAbstractItemModel):

    def __init__(self, blueprint=None, parent=None):
        super(BuildItemTreeModel, self).__init__(parent=parent)
        if blueprint:
            self.blueprint = blueprint
        else:
            self.blueprint = pulse.Blueprint()
    
    def setBlueprint(self, newBlueprint):
        if not newBlueprint:
            newBlueprint = pulse.Blueprint()
        self.blueprint = newBlueprint
        self.modelReset.emit()

    def item(self, index):
        """
        Return a new TreeModelBuildItem for a BuildItem of a QModelIndex.
        """
        if index.isValid():
            return TreeModelBuildItem(index.internalPointer())
        else:
            return TreeModelBuildItem(self.blueprint.rootItem)

    def index(self, row, column, parent=QtCore.QModelIndex()): # override
        """
        Create a QModelIndex for a row, column, and parent index
        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        
        childItem = self.item(parent).child(row)
        if childItem:
            return self.createIndex(row, column, childItem.buildItem)
        else:
            return QtCore.QModelIndex()

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled

        flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsDragEnabled
        if self.item(index).isGroup():
            flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsDropEnabled
        return flags

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def columnCount(self, parent=QtCore.QModelIndex()): # override
        return self.item(parent).columnCount()

    def rowCount(self, parent=QtCore.QModelIndex()): # override
        return self.item(parent).childCount()

    def parent(self, index): # override
        if not index.isValid():
            return QtCore.QModelIndex()

        parentItem = self.item(index).parent()
        if parentItem.buildItem == self.blueprint.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem.buildItem)

    def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
        raise RuntimeError("Cannot insert rows without data, use insertBuildItems instead")

    def insertBuildItems(self, position, childBuildItems, parent=QtCore.QModelIndex()):
        self.beginInsertRows(parent, position, position + len(childBuildItems) - 1)
        success = self.item(parent).insertChildren(position, childBuildItems)
        self.endInsertRows()
        return success

    def removeRows(self, position, rows, parent=QtCore.QModelIndex()):
        self.beginRemoveRows(parent, position, position + rows - 1)
        success = self.item(parent).removeChildren(position, rows)
        self.endRemoveRows()
        return success

    def data(self, index, role=QtCore.Qt.DisplayRole): # override
        if index.isValid():
            return self.item(index).data(index.column(), role)

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return False
        
        if role != QtCore.Qt.EditRole:
            return False

        result = self.item(index).setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        result = QtCore.QMimeData()
        # TODO: this is wrong because serialization will include
        #       children and we don't want that here
        itemDataList = [self.item(index).buildItem.serialize() for index in indexes]
        datastr = meta.encodeMetaData(itemDataList)
        result.setData('text/plain', datastr)
        return result

    def dropMimeData(self, data, action, row, column, parent):
        try:
            itemDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except Exception as e:
            print(e)
            return False
        else:
            newBuildItems = [pulse.BuildItem.create(itemData) for itemData in itemDataList]
            return self.insertBuildItems(row, newBuildItems, parent)



class BuildItemSelectionModel(QtCore.QItemSelectionModel):
    """
    The selection model for the BuildItems of a Blueprint. Allows
    a singular selection that is shared across all UI for the Blueprint.
    An instance of this model should be acquired by going through
    the BlueprintUIModel for a specific Blueprint.
    """

    def getSelectedGroups(self):
        """
        Return the currently selected BuildGroup indexes
        """
        indexes = self.selectedIndexes()
        grps = []
        for index in indexes:
            buildItem = index.internalPointer()
            if isinstance(buildItem, pulse.BuildGroup):
                grps.append(index)
            else:
                grps.append(index.parent())
        return list(set(grps))

    def getSelectedAction(self):
        """
        Return the currently selected BuildAction, if any.
        """
        pass

