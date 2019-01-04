
import os
import logging
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMayaUI as mui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymetanode as meta

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.core import Blueprint, BuildStep
from .utils import dpiScale

__all__ = [
    'BlueprintUIModel',
    'BuildStepSelectionModel',
    'BuildStepTreeModel',
    'PulseWindow',
]

LOG = logging.getLogger(__name__)


class PulseWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    """
    A base class for any standalone window in the Pulse UI. Integrates
    the Maya builtin dockable mixin, and prevents multiple instances
    of the window.
    """

    OBJECT_NAME = None
    PREFERRED_SIZE = QtCore.QSize(200, 400)
    STARTING_SIZE = QtCore.QSize(200, 400)
    MINIMUM_SIZE = QtCore.QSize(200, 400)

    # the name of the module in which this window class can be found
    # used to build the UI_SCRIPT and CLOSE_SCRIPT
    WINDOW_MODULE = None

    # a string of python code to run when the workspace control is shown
    UI_SCRIPT = 'from {module} import {cls}\n{cls}.createWindow(restore=True)'

    # a string of python code to run when the workspace control is closed
    CLOSE_SCRIPT = 'from {module} import {cls}\n{cls}.windowClosed()'

    REQUIRED_PLUGINS = ['pulse']

    # reference to singleton instance
    INSTANCE = None

    @classmethod
    def createWindow(cls, restore=False):
        if restore:
            parent = mui.MQtUtil.getCurrentParent()

        # create instance if it doesn't exists
        if not cls.INSTANCE:

            # load required plugins
            if cls.REQUIRED_PLUGINS:
                for plugin in cls.REQUIRED_PLUGINS:
                    pm.loadPlugin(plugin, quiet=True)

            cls.INSTANCE = cls()

        if restore:
            mixinPtr = mui.MQtUtil.findControl(cls.INSTANCE.objectName())
            mui.MQtUtil.addWidgetToMayaLayout(long(mixinPtr), long(parent))
        else:
            uiScript = cls.UI_SCRIPT.format(
                module=cls.WINDOW_MODULE, cls=cls.__name__)
            closeScript = cls.CLOSE_SCRIPT.format(
                module=cls.WINDOW_MODULE, cls=cls.__name__)

            cls.INSTANCE.show(dockable=True,
                              uiScript=uiScript,
                              closeCallback=closeScript,
                              requiredPlugin=cls.REQUIRED_PLUGINS)

        return cls.INSTANCE

    @classmethod
    def destroyWindow(cls):
        if cls.windowExists():
            cls.hideWindow()
            cmds.deleteUI(cls.getWorkspaceControlName(), control=True)

    @classmethod
    def showWindow(cls):
        if cls.windowExists():
            cmds.workspaceControl(
                cls.getWorkspaceControlName(), e=True, vis=True)
        else:
            cls.createWindow()

    @classmethod
    def hideWindow(cls):
        """
        Close the window, if it exists
        """
        if cls.windowExists():
            cmds.workspaceControl(
                cls.getWorkspaceControlName(), e=True, vis=False)

    @classmethod
    def toggleWindow(cls):
        if cls.windowVisible():
            cls.hideWindow()
        else:
            cls.showWindow()

    @classmethod
    def windowClosed(cls):
        cls.INSTANCE = None

    @classmethod
    def windowExists(cls):
        """
        Return True if an instance of this window exists
        """
        return cmds.workspaceControl(
            cls.getWorkspaceControlName(), q=True, ex=True)

    @classmethod
    def windowVisible(cls):
        return cls.windowExists() and cmds.workspaceControl(
            cls.getWorkspaceControlName(), q=True, vis=True)

    @classmethod
    def getWorkspaceControlName(cls):
        return cls.OBJECT_NAME + 'WorkspaceControl'

    def __init__(self, parent=None):
        super(PulseWindow, self).__init__(parent=parent)

        self.setObjectName(self.OBJECT_NAME)

        self.preferredSize = self.PREFERRED_SIZE
        self.resize(dpiScale(self.STARTING_SIZE))

    def setSizeHint(self, size):
        self.preferredSize = size

    def sizeHint(self):
        return self.preferredSize

    def minimumSizeHint(self):
        return self.MINIMUM_SIZE


class BlueprintUIModel(QtCore.QObject):
    """
    The owner and manager of various models representing a Blueprint
    in the scene. All reading and writing for the Blueprint through
    the UI should be done using this model.

    Blueprints edited though the UI are saved to yaml files
    associated with a maya scene file. This model is also responsible
    for loading and saving the blueprint yaml file.
    """

    # shared instances, mapped by name
    INSTANCES = {}

    @classmethod
    def getDefaultModel(cls):
        # type: (class) -> BlueprintUIModel
        """
        Return the default model instance used by editor views.
        """
        return cls.getSharedModel(None)

    @classmethod
    def getSharedModel(cls, name):
        # type: (class, str) -> BlueprintUIModel
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
        self._blueprint = Blueprint()

        # the tree item model and selection model for BuildSteps
        self.buildStepTreeModel = BuildStepTreeModel(self.blueprint)
        self.buildStepSelectionModel = BuildStepSelectionModel(
            self.buildStepTreeModel)

        # attempt to load from the scene
        self.load(suppressWarnings=True)

    @property
    def blueprint(self):
        """
        The Blueprint object represented by this Model.
        """
        return self._blueprint

    def isReadOnly(self):
        """
        Return True if the Blueprint is not able to be modified.
        """
        return False

    def getBlueprintFilepath(self):
        """
        Return the filepath for the Blueprint being edited
        """
        sceneName = None
        isRigScene = len(pulse.getAllRigs()) > 0

        if isRigScene:
            # get filepath from rig
            rig = pulse.getAllRigs()[0]
            rigdata = meta.getMetaData(rig, pulse.RIG_METACLASS)
            sceneName = rigdata.get('blueprintFile')
        else:
            sceneName = pm.sceneName()

        if sceneName:
            filepath = os.path.splitext(sceneName)[0] + '.yaml'
            return filepath

    def save(self, suppressWarnings=False):
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

    def load(self, suppressWarnings=False):
        """
        Load the Blueprint from the file associated with this model
        """
        filepath = self.getBlueprintFilepath()
        if not filepath:
            if not suppressWarnings:
                LOG.warning("Scene is not saved")

            self.initializeBlueprint()
            return

        self.buildStepTreeModel.beginResetModel()
        success = self.blueprint.loadFromFile(filepath)
        self.buildStepTreeModel.endModelReset()
        self.rigNameChanged.emit(self.getRigName())

        if not success:
            LOG.error(
                "Failed to load Blueprint from file: {0}".format(filepath))

    def getRigName(self):
        return self.blueprint.rigName

    def setRigName(self, newRigName):
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        self.blueprint.rigName = newRigName
        self.rigNameChanged.emit(self.blueprint.rigName)

    def initializeBlueprint(self):
        """
        Initialize the Blueprint to an empty state.
        """
        self.buildStepTreeModel.beginResetModel()
        self.blueprint.rigName = None
        self.blueprint.rootStep.clearChildren()
        self.buildStepTreeModel.endResetModel()

    def initializeBlueprintToDefaultActions(self):
        """
        Initialize the Blueprint to its default state based
        on the current blueprint config.
        """
        self.buildStepTreeModel.beginResetModel()
        self.blueprint.rootStep.clearChildren()
        self.blueprint.initializeDefaultActions()
        self.buildStepTreeModel.endResetModel()

    def createStep(self, parentPath, childIndex, data):
        """
        Create a new BuildStep

        Args:
            parentPath (str): The path to the parent step
            childIndex (int): The index at which to insert the new step
            data (str): The serialized data for the BuildStep to create

        Returns:
            The newly created BuildStep, or None if the operation failed.
        """
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        parentStep = self.blueprint.getStepByPath(parentPath)
        if not parentStep:
            LOG.error("createStep: failed to find parent step: %s", parentPath)
            return

        parentIndex = self.buildStepTreeModel.indexByStep(parentStep)
        self.buildStepTreeModel.beginInsertRows(
            parentIndex, childIndex, childIndex)

        step = BuildStep.fromData(data)
        parentStep.insertChild(childIndex, step)

        self.buildStepTreeModel.endInsertRows()
        return step

    def deleteStep(self, stepPath):
        """
        Delete a BuildStep

        Returns:
            True if the step was deleted successfully
        """
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return False

        step = self.blueprint.getStepByPath(stepPath)
        if not step:
            LOG.error("deleteStep: failed to find step: %s", stepPath)
            return False

        stepIndex = self.buildStepTreeModel.indexByStep(step)
        self.buildStepTreeModel.beginRemoveRows(
            stepIndex.parent(), stepIndex.row(), stepIndex.row())

        step.removeFromParent()

        self.buildStepTreeModel.endRemoveRows()
        return True

    def moveStep(self, sourcePath, targetPath):
        """
        Move a BuildStep from source path to target path.

        Returns:
            The new path (str) of the build step, or None if
            the operation failed.
        """
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        step = self.blueprint.getStepByPath(sourcePath)
        if not step:
            LOG.error("moveStep: failed to find step: %s", sourcePath)
            return

        if step == self.blueprint.rootStep:
            LOG.error("moveStep: cannot move root step")
            return

        self.buildStepTreeModel.layoutAboutToBeChanged.emit()

        sourceParentPath = os.path.dirname(sourcePath)
        targetParentPath = os.path.dirname(targetPath)
        if sourceParentPath != targetParentPath:
            step.setParent(self.blueprint.getStepByPath(targetParentPath))
        targetName = os.path.basename(targetPath)
        step.setName(targetName)

        self.buildStepTreeModel.layoutChanged.emit()

        return step.getFullPath()

    def getStep(self, stepPath):
        """
        Return the BuildStep at a path
        """
        return self.blueprint.getStepByPath(stepPath)

    def getStepData(self, stepPath):
        """
        Return the serialized data for a step at a path
        """
        step = self.getStep(stepPath)
        if step:
            return step.serialize()

    def getActionData(self, stepPath):
        """
        Return serialized data for a BuildActionProxy
        """
        step = self.getStep(stepPath)
        if not step:
            return

        if not step.isAction():
            LOG.error(
                'getActionData: %s step is not an action', step)
            return

        return step.actionProxy.serialize()

    def setActionData(self, stepPath, data):
        """
        Replace all attribute values on a BuildActionProxy.
        """
        step = self.getStep(stepPath)
        if not step:
            return

        if not step.isAction():
            LOG.error(
                'setActionData: %s step is not an action', step)
            return

        step.actionProxy.deserialize(data)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])

    def getActionAttr(self, attrPath, variantIndex=-1):
        """
        Return the value of an attribute of a BuildAction

        Args:
            attrPath (str): The full path to an action attribute, e.g. 'My/Action.myAttr'
            variantIndex (int): The index of the variant to retrieve, if the action has variants

        Returns:
            The attribute value, of varying types
        """
        stepPath, attrName = attrPath.split('.')

        step = self.getStep(stepPath)
        if not step:
            return

        if not step.isAction():
            LOG.error('getActionAttr: %s is not an action', step)
            return

        if variantIndex >= 0:
            if step.actionProxy.numVariants() > variantIndex:
                actionData = step.actionProxy.getVariant(variantIndex)
                return actionData.getAttrValue(attrName)
        else:
            return step.actionProxy.getAttrValue(attrName)

    def setActionAttr(self, attrPath, value, variantIndex=-1):
        """
        Set the value for an attribute on the Blueprint
        """
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        stepPath, attrName = attrPath.split('.')

        step = self.getStep(stepPath)
        if not step:
            return

        if not step.isAction():
            LOG.error('setActionAttr: %s is not an action', step)
            return

        if variantIndex >= 0:
            variant = step.actionProxy.getOrCreateVariant(variantIndex)
            variant.setAttrValue(attrName, value)
        else:
            step.actionProxy.setAttrValue(attrName, value)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])

    def isActionAttrVariant(self, attrPath):
        stepPath, attrName = attrPath.split('.')

        step = self.getStep(stepPath)
        if not step.isAction():
            LOG.error(
                "isActionAttrVariant: {0} is not an action".format(step))
            return

        return step.actionProxy.isVariantAttr(attrName)

    def setIsActionAttrVariant(self, attrPath, isVariant):
        """
        """
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        stepPath, attrName = attrPath.split('.')

        step = self.getStep(stepPath)
        if not step:
            return

        if not step.isAction():
            LOG.error(
                "setIsActionAttrVariant: {0} is not an action".format(step))
            return

        step.actionProxy.setIsVariantAttr(attrName, isVariant)

        index = self.buildStepTreeModel.indexByStepPath(stepPath)
        self.buildStepTreeModel.dataChanged.emit(index, index, [])


class BuildStepTreeModel(QtCore.QAbstractItemModel):
    """
    A Qt tree model for viewing and modifying the BuildStep
    hierarchy of a Blueprint.
    """

    def __init__(self, blueprint=None, parent=None):
        super(BuildStepTreeModel, self).__init__(parent=parent)
        self._blueprint = blueprint

    def stepForIndex(self, index):
        """
        Return the BuildStep of a QModelIndex.
        """
        if index.isValid():
            return index.internalPointer()
        if self._blueprint:
            return self._blueprint.rootStep

    def indexByStep(self, step):
        if step and step != self._blueprint.rootStep:
            return self.createIndex(step.indexInParent(), 0, step)
        return QtCore.QModelIndex()

    def indexByStepPath(self, path):
        """
        Return a QModelIndex for a step by path
        """
        if self._blueprint:
            step = self._blueprint.getStepByPath(path)
            return self.indexByStep(step)
        return QtCore.QModelIndex()

    def index(self, row, column, parent=QtCore.QModelIndex()):
        """
        Create a QModelIndex for a row, column, and parent index
        """
        if parent.isValid() and column != 0:
            return QtCore.QModelIndex()

        parentStep = self.stepForIndex(parent)
        if parentStep and parentStep.canHaveChildren:
            childStep = parentStep.getChildAt(row)
            if childStep:
                return self.createIndex(row, column, childStep)

        return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childStep = self.stepForIndex(index)
        if childStep:
            parentStep = childStep.parent
        else:
            return QtCore.QModelIndex()

        if parentStep is None or parentStep == self._blueprint.rootStep:
            return QtCore.QModelIndex()

        return self.createIndex(parentStep.indexInParent(), 0, parentStep)

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsDropEnabled

        flags = QtCore.Qt.ItemIsEnabled \
            | QtCore.Qt.ItemIsSelectable \
            | QtCore.Qt.ItemIsDragEnabled \
            | QtCore.Qt.ItemIsEditable

        step = self.stepForIndex(index)
        if step and step.canHaveChildren:
            flags |= QtCore.Qt.ItemIsDropEnabled

        return flags

    # def supportedDropActions(self):
    #     return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        step = self.stepForIndex(parent)
        return step.numChildren() if step else 0

    # def insertRows(self, row, count, parent=QtCore.QModelIndex()):
    #     self.beginInsertRows(parent, row, row + count - 1)
    #     step = self.stepForIndex(parent)
    #     for _ in range(count):
    #         step.insertChild(row, BuildStep())
    #     self.endInsertRows()
    #     return True

    # def removeRows(self, row, count, parent=QtCore.QModelIndex()):
    #     self.beginRemoveRows(parent, row, row + count - 1)
    #     step = self.stepForIndex(parent)
    #     cmds.pulseDeleteStep(step.getFullPath())
    #     self.endRemoveRows()
    #     return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return

        step = self.stepForIndex(index)
        if not step:
            return

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
        return True

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

    # def canDropMimeData(self, data, action, row, column, parent):
    #     try:
    #         stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
    #     except Exception:
    #         return False
    #     else:
    #         return isinstance(stepDataList, list)

    # def dropMimeData(self, data, action, row, column, parent):
    #     result = super(BuildStepTreeModel, self).dropMimeData(
    #         data, action, row, column, parent)

    #     if not result:
    #         return False

    #     try:
    #         stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
    #     except Exception as e:
    #         print(e)
    #     else:
    #         print(stepDataList, data, action, row, column, parent)

    #         count = len(stepDataList)
    #         for i in range(count):
    #             index = self.index(row + i, 0, parent)
    #             step = self.stepForIndex(index)
    #             if step:
    #                 step.deserialize(stepDataList[i])
    #                 # self.dataChanged.emit(index, index, [])

    #     return True


class BuildStepSelectionModel(QtCore.QItemSelectionModel):
    """
    The selection model for the BuildSteps of a Blueprint. Allows
    a singular selection that is shared across all UI for the Blueprint.
    An instance of this model should be acquired by going through
    the BlueprintUIModel for a specific Blueprint.
    """

    def getSelectedItems(self):
        """
        Return the currently selected BuildSteps
        """
        indexes = self.selectedIndexes()
        items = []
        for index in indexes:
            if index.isValid():
                buildStep = self.model.stepForIndex(index)
                # buildStep = index.internalPointer()
                if buildStep:
                    items.append(buildStep)
        return list(set(items))

    def getSelectedGroups(self):
        """
        Return indexes of the selected BuildSteps that can have children
        """
        indexes = self.selectedIndexes()
        indeces = []
        for index in indexes:
            if index.isValid():
                buildStep = self.model.stepForIndex(index)
                # buildStep = index.internalPointer()
                if buildStep and buildStep.canHaveChildren:
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
        Return the full paths of the selected BuildSteps
        """
        items = self.getSelectedItems()
        return [i.getFullPath() for i in items]

    def setSelectedItemPaths(self, paths):
        """
        Set the selection using BuildStep paths
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
