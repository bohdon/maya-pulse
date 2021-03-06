"""
UI model classes, and base classes for common widgets.
"""


from pulse.views.utils import CollapsibleFrame
from pulse.vendor.Qt import QtWidgets, QtGui
import os
import logging
import pymel.core as pm
import maya.cmds as cmds
import maya.OpenMaya as api
import maya.OpenMayaUI as mui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymetanode as meta

import pulse
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.core import Blueprint, BuildStep, serializeAttrValue
from pulse.prefs import optionVarProperty
from .utils import dpiScale

__all__ = [
    'BlueprintUIModel',
    'BuildStepSelectionModel',
    'BuildStepTreeModel',
    'PulsePanelWidget',
    'PulseWindow',
]

LOG = logging.getLogger(__name__)
LOG.level = logging.DEBUG

BLUEPRINT_FILE_EXT = 'yml'


class PulsePanelWidget(QtWidgets.QWidget):
    """
    Base widget for any simple panel in the editor ui.

    Provides functionality for building a consistent
    ui across all pulse editor views.
    """

    def __init__(self, parent):
        super(PulsePanelWidget, self).__init__(parent=parent)

        self.setupUi(self)
        self.setupPanelUi(self.panelWidget)

    def getPanelDisplayName(self):
        """
        Return the display name for this panel
        """
        raise NotImplementedError

    def getPanelColor(self):
        return [0, 0, 0]

    def setupUi(self, parent):
        """
        Build a collapsible panel ui that can be used
        by all design panels.

        All panel widgets should be attached to `self.panelWidget`
        """
        self.mainLayout = QtWidgets.QVBoxLayout(parent)
        self.mainLayout.setMargin(0)
        self.mainLayout.setSpacing(3)

        # header frame
        self.headerFrame = CollapsibleFrame(parent)
        headerColor = 'rgba({0}, {1}, {2}, 40)'.format(*self.getPanelColor())
        self.headerFrame.setStyleSheet(
            ".CollapsibleFrame{{ background-color: {color}; border-radius: 2px; }}".format(color=headerColor))
        self.headerFrame.collapsedChanged.connect(self.onCollapsedChanged)
        # header layout
        self.headerLayout = QtWidgets.QHBoxLayout(self.headerFrame)
        self.headerLayout.setContentsMargins(10, 2, 2, 2)
        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(self.headerFrame)
        self.displayNameLabel.setMinimumHeight(18)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(self.getPanelDisplayName())
        self.headerLayout.addWidget(self.displayNameLabel)

        self.mainLayout.addWidget(self.headerFrame)

        self.panelWidget = QtWidgets.QWidget(parent)
        self.mainLayout.addWidget(self.panelWidget)

    def setupPanelUi(self, parent):
        """
        Setup the ui for the contents of the panel
        """
        raise NotImplementedError

    def onCollapsedChanged(self, isCollapsed):
        self.panelWidget.setVisible(not isCollapsed)

    @staticmethod
    def createPanelFrame(parent):
        """
        Create a QFrame with consistent styling for a design view panel
        """
        frame = QtWidgets.QFrame(parent)
        frame.setObjectName("panelFrame")
        frame.setStyleSheet(
            ".QFrame#panelFrame{ background-color: rgba(255, 255, 255, 5); }")
        return frame


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

    Blueprints represented in this model are saved and loaded using yaml
    files which are paired with a maya scene file.
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
            cls.INSTANCES[name].onDelete()
            del cls.INSTANCES[name]

    @classmethod
    def deleteAllSharedModels(cls):
        keys = cls.INSTANCES.keys()
        for key in keys:
            cls.INSTANCES[key].onDelete()
            del cls.INSTANCES[key]

    # a config property on the blueprint changed
    # TODO: add more generic blueprint property data model
    rigNameChanged = QtCore.Signal(str)

    # called when the blueprint filepath has changed
    # occurs on maya open scene, or new scene
    fileChanged = QtCore.Signal()

    # called just before a blueprint file is loaded
    # args: (filepath)
    preFileLoad = QtCore.Signal(str)

    # called when the blueprint file has changed
    postFileLoad = QtCore.Signal()

    rigExistsChanged = QtCore.Signal()

    autoSave = optionVarProperty('pulse.editor.autoSave', True)
    autoLoad = optionVarProperty('pulse.editor.autoLoad', True)

    # called when the read-only state of the blueprint has changed
    readOnlyChanged = QtCore.Signal(bool)

    def setAutoSave(self, value):
        self.autoSave = value

    def setAutoLoad(self, value):
        self.autoLoad = value

    def __init__(self, parent=None):
        super(BlueprintUIModel, self).__init__(parent=parent)

        # the blueprint of this model
        self._blueprint = Blueprint()

        # the tree item model and selection model for BuildSteps
        self.buildStepTreeModel = BuildStepTreeModel(self.blueprint, self)
        self.buildStepSelectionModel = BuildStepSelectionModel(
            self.buildStepTreeModel, self)

        # keeps track of whether a rig is currently in the scene,
        # which will affect the ability to edit the Blueprint
        self.rigExists = False
        self.refreshRigExists()

        # attempt to load from the scene
        if self.autoLoad:
            self.load(suppressWarnings=True)

        # register maya scene callbacks that can be used
        # for auto-saving the Blueprint
        self._callbackIds = []
        self.addSceneCallbacks()

    def onDelete(self):
        self.removeSceneCallbacks()

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
        return self.rigExists

    def getBlueprintFilepath(self):
        """
        Return the filepath for the Blueprint being edited
        """
        sceneName = None

        if self.rigExists:
            # get filepath from rig
            rig = pulse.getAllRigs()[0]
            rigdata = meta.getMetaData(rig, pulse.RIG_METACLASS)
            sceneName = rigdata.get('blueprintFile')
        else:
            sceneName = pm.sceneName()

        if sceneName:
            baseName = os.path.splitext(sceneName)[0]
            filepath = '%s.%s' % (baseName, BLUEPRINT_FILE_EXT)
            return filepath

    def getBlueprintFilename(self):
        """
        Return the filename for the Blueprint being edited
        """
        filepath = self.getBlueprintFilepath()
        if filepath:
            return os.path.basename(filepath)

    def addSceneCallbacks(self):
        if not self._callbackIds:
            saveId = api.MSceneMessage.addCallback(
                api.MSceneMessage.kBeforeSave, self.onBeforeSaveScene)
            openId = api.MSceneMessage.addCallback(
                api.MSceneMessage.kAfterOpen, self.onAfterOpenScene)
            newId = api.MSceneMessage.addCallback(
                api.MSceneMessage.kAfterNew, self.onAfterNewScene)
            self._callbackIds.append(saveId)
            self._callbackIds.append(openId)
            self._callbackIds.append(newId)
        LOG.debug(
            'BlueprintUIModel: added scene callbacks')

    def removeSceneCallbacks(self):
        if self._callbackIds:
            while self._callbackIds:
                cbid = self._callbackIds.pop()
                api.MMessage.removeCallback(cbid)
            LOG.debug(
                'BlueprintUIModel: removed scene callbacks')

    def onBeforeSaveScene(self, clientData=None):
        if self.shouldAutoSaveBlueprint():
            LOG.debug('Auto-saving Pulse Blueprint...')
            self.save()

    def onAfterOpenScene(self, clientData=None):
        if self.autoLoad:
            self.load(suppressWarnings=True)
        self.fileChanged.emit()

    def onAfterNewScene(self, clientData=None):
        self.initializeBlueprint()
        self.fileChanged.emit()

    def save(self, suppressWarnings=False):
        """
        Save the Blueprint data to the file associated with this model
        """
        self.refreshRigExists()

        if self.isReadOnly():
            return

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
        self.refreshRigExists()
        filepath = self.getBlueprintFilepath()
        if not filepath:
            if not suppressWarnings:
                LOG.warning("Scene is not saved")
            return

        if not os.path.isfile(filepath):
            if not suppressWarnings:
                LOG.warning(
                    "Blueprint file does not exist: {0}".format(filepath))
            return

        self.preFileLoad.emit(filepath)
        self.buildStepTreeModel.beginResetModel()
        success = self.blueprint.loadFromFile(filepath)
        self.buildStepTreeModel.endResetModel()
        self.rigNameChanged.emit(self.getRigName())
        self.postFileLoad.emit()

        if not success:
            LOG.error(
                "Failed to load Blueprint from file: {0}".format(filepath))

    def doesBlueprintPairFileExist(self):
        """
        Return True if a Blueprint yaml file exists that is
        paired to the current maya scene file.
        """
        filepath = self.getBlueprintFilepath()
        if filepath:
            return os.path.isfile(filepath)
        return False

    def refreshRigExists(self):
        oldReadOnly = self.isReadOnly()
        self.rigExists = len(pulse.getAllRigs()) > 0
        self.rigExistsChanged.emit()

        if oldReadOnly != self.isReadOnly():
            self.readOnlyChanged.emit(self.isReadOnly())

    def shouldAutoSaveBlueprint(self):
        if not self.autoSave:
            return False
        if not self.doesBlueprintPairFileExist():
            return False
        self.refreshRigExists()
        if self.isReadOnly():
            return False
        return True

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
        self.rigNameChanged.emit(self.blueprint.rigName)

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

        try:
            step = BuildStep.fromData(data)
        except ValueError as e:
            LOG.error("Failed to create build step: %s" % e, exc_info=True)
            return

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

    def renameStep(self, stepPath, targetName):
        if self.isReadOnly():
            LOG.error('Cannot edit readonly Blueprint')
            return

        step = self.blueprint.getStepByPath(stepPath)
        if not step:
            LOG.error("moveStep: failed to find step: %s", stepPath)
            return

        if step == self.blueprint.rootStep:
            LOG.error("moveStep: cannot rename root step")
            return

        oldName = step.name
        step.setName(targetName)

        if step.name != oldName:
            index = self.buildStepTreeModel.indexByStep(step)
            self.buildStepTreeModel.dataChanged.emit(index, index, [])

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

        # used to keep track of drag move actions since
        # we don't have enough data within one function
        # to group undo chunks completely
        self.isMoveActionOpen = False
        # hacky, but used to rename dragged steps back to their
        # original names since they will get new names due to
        # conflicts from both source and target steps existing
        # at the same time briefly
        self.dragRenameQueue = []

    def isReadOnly(self):
        parent = QtCore.QObject.parent(self)
        if parent and hasattr(parent, 'isReadOnly'):
            return parent.isReadOnly()
        return False

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
            if not self.isReadOnly():
                return QtCore.Qt.ItemIsDropEnabled
            else:
                return 0

        flags = QtCore.Qt.ItemIsEnabled \
            | QtCore.Qt.ItemIsSelectable \

        if not self.isReadOnly():
            flags |= QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEditable

        step = self.stepForIndex(index)
        if step and step.canHaveChildren:
            flags |= QtCore.Qt.ItemIsDropEnabled

        return flags

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def rowCount(self, parent=QtCore.QModelIndex()):
        step = self.stepForIndex(parent)
        return step.numChildren() if step else 0

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
            # dim color if step is disabled
            if step.isDisabledInHierarchy():
                color = [c * 0.4 for c in color]
            return QtGui.QColor(*[c * 255 for c in color])

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if self.isReadOnly():
            return False
        if not index.isValid():
            return False

        step = self.stepForIndex(index)

        if role == QtCore.Qt.EditRole:
            if not value:
                value = ''
            stepPath = step.getFullPath()
            cmds.pulseRenameStep(stepPath, value)
            return True

        elif role == QtCore.Qt.CheckStateRole:
            step.isDisabled = True if value else False
            self.dataChanged.emit(index, index, [])
            self._emitDataChangedOnAllChildren(index, [])
            # emit data changed on all children
            return True

        return False

    def _emitDataChangedOnAllChildren(self, parent=QtCore.QModelIndex(), roles=None):
        if not parent.isValid():
            return
        rowCount = self.rowCount(parent)
        if rowCount == 0:
            return

        firstChild = self.index(0, 0, parent)
        lastChild = self.index(rowCount - 1, 0, parent)

        # emit one event for all child indexes of parent
        self.dataChanged.emit(firstChild, lastChild, roles)

        # recursively emit on all children
        for i in range(rowCount):
            childIndex = self.index(i, 0, parent)
            self._emitDataChangedOnAllChildren(childIndex, roles)

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        result = QtCore.QMimeData()

        # TODO: this block of getting topmost steps is redundantly
        #       used in deleting steps, need to consolidate
        steps = []
        for index in indexes:
            step = self.stepForIndex(index)
            if step:
                steps.append(step)
        steps = pulse.BuildStep.getTopmostSteps(steps)

        stepDataList = [step.serialize() for step in steps]
        datastr = meta.encodeMetaData(stepDataList)
        result.setData('text/plain', datastr)
        return result

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction | QtCore.Qt.MoveAction

    def canDropMimeData(self, data, action, row, column, parentIndex):
        try:
            stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except Exception:
            return False
        else:
            return isinstance(stepDataList, list)

    def dropMimeData(self, data, action, row, column, parentIndex):
        if not self.canDropMimeData(data, action, row, column, parentIndex):
            return False

        if action == QtCore.Qt.IgnoreAction:
            return True

        try:
            stepDataList = meta.decodeMetaData(str(data.data('text/plain')))
        except Exception as e:
            LOG.error(e)
            return False

        print('dropData', stepDataList, data, action, row, column, parentIndex)

        beginRow = 0
        parentPath = None

        if parentIndex.isValid():
            parentStep = self.stepForIndex(parentIndex)
            if parentStep:
                if parentStep.canHaveChildren:
                    # drop into step group
                    beginRow = parentStep.numChildren()
                    parentPath = parentStep.getFullPath()
                else:
                    # drop next to step
                    beginRow = parentIndex.row()
                    parentPath = os.path.dirname(parentStep.getFullPath())

        if not parentPath:
            parentPath = ''
            beginRow = self.rowCount(QtCore.QModelIndex())
        if row != -1:
            beginRow = row

        cmds.undoInfo(openChunk=True, chunkName='Drag Pulse Actions')
        self.isMoveActionOpen = True
        cmds.evalDeferred(self._deferredMoveUndoClose)

        # create dropped steps
        count = len(stepDataList)
        for i in range(count):
            stepDataStr = serializeAttrValue(stepDataList[i])
            newStepPath = cmds.pulseCreateStep(
                parentPath, beginRow + i, stepDataStr)
            if newStepPath:
                newStepPath = newStepPath[0]

                if action == QtCore.Qt.MoveAction:
                    # create queue of renames to perform after source
                    # steps have been removed
                    targetName = stepDataList[i].get('name', '')
                    self.dragRenameQueue.append((newStepPath, targetName))

        return True

    def removeRows(self, row, count, parent):
        indexes = []
        for i in range(row, row + count):
            index = self.index(i, 0, parent)
            indexes.append(index)

        # TODO: provide better api for deleting groups of steps
        steps = []
        for index in indexes:
            step = self.stepForIndex(index)
            if step:
                steps.append(step)
        steps = pulse.BuildStep.getTopmostSteps(steps)

        paths = []
        for step in steps:
            path = step.getFullPath()
            if path:
                paths.append(path)

        if not self.isMoveActionOpen:
            cmds.undoInfo(openChunk=True, chunkName='Delete Pulse Actions')

        for path in paths:
            cmds.pulseDeleteStep(path)

        if not self.isMoveActionOpen:
            cmds.undoInfo(closeChunk=True)

    def _deferredMoveUndoClose(self):
        """
        Called after a drag move operation has finished in order
        to capture all cmds into one undo chunk.
        """
        if self.isMoveActionOpen:
            self.isMoveActionOpen = False

            # rename dragged steps back to their original names
            # since they were changed due to conflicts during drop
            while self.dragRenameQueue:
                path, name = self.dragRenameQueue.pop()
                cmds.pulseRenameStep(path, name)

            cmds.undoInfo(closeChunk=True)


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
        if not self.model() or not hasattr(self.model(), '_blueprint'):
            return

        blueprint = self.model()._blueprint
        steps = [blueprint.getStepByPath(p) for p in paths]
        indexes = [self.model().indexByStep(s) for s in steps if s]
        self.clearSelection()
        for index in indexes:
            if index.isValid():
                self.select(index, QtCore.QItemSelectionModel.Select)
