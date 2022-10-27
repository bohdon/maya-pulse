"""
Tree widget for displaying the build step hierarchy of a blueprint.
"""

import logging
from functools import partial
from typing import Optional, Dict, List

import maya.cmds as cmds

from ..vendor.Qt import QtCore, QtWidgets, QtGui
from ..serializer import serialize_attr_value
from ..buildItems import BuildStep, BuildActionRegistry, BuildActionSpec, BuildActionAttribute
from .. import sym
from .core import BlueprintUIModel
from .core import PulseWindow
from .gen.action_tree import Ui_ActionTree

LOG = logging.getLogger(__name__)


class ActionTreeStyledItemDelegate(QtWidgets.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(ActionTreeStyledItemDelegate, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem, index: QtCore.QModelIndex):
        super(ActionTreeStyledItemDelegate, self).paint(painter, option, index)


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
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

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

        steps: List[BuildStep] = []
        for index in indexes:
            step: BuildStep = self.model().stepForIndex(index)
            if step:
                steps.append(step)
        steps = BuildStep.get_topmost_steps(steps)

        paths = []
        for step in steps:
            path = step.get_full_path()
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

        steps: List[BuildStep] = []
        for index in indexes:
            step: BuildStep = self.model().stepForIndex(index)
            if step:
                steps.append(step)

        mirrorUtil = MirrorActionUtil(self.blueprintModel)
        for step in steps:
            if step.is_action():
                mirrorUtil.mirrorAction(step)


class ActionTree(QtWidgets.QWidget):
    """
    A widget that displays all Build Actions in a Blueprint.
    Items can be selected, and the shared selection model can then be used to
    display info about selected BuildActions in other UI.
    """

    def __init__(self, parent=None):
        super(ActionTree, self).__init__(parent=parent)

        # get shared models
        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.model = self.blueprintModel.buildStepTreeModel
        self._selection_model = self.blueprintModel.buildStepSelectionModel

        self.ui = Ui_ActionTree()
        self.ui.setupUi(self)

        # add action tree view
        self.action_tree_view = ActionTreeView(self.blueprintModel, self)
        self.action_tree_view.setModel(self.model)
        self.action_tree_view.setSelectionModel(self._selection_model)
        self.action_tree_view.expandAll()
        self.ui.main_layout.addWidget(self.action_tree_view)

        # connect signals
        self.model.modelReset.connect(self._on_model_reset)
        self.blueprintModel.changeSceneFinished.connect(self._onChangeSceneFinished)
        self.blueprintModel.fileChanged.connect(self._onFileChanged)

        self._onFileChanged()

    def _onChangeSceneFinished(self):
        self._onFileChanged()

    def _onFileChanged(self):
        # don't update until after scene change is finished
        if self.blueprintModel.isChangingScenes:
            return

        if self.blueprintModel.isFileOpen():
            self.ui.main_stack.setCurrentWidget(self.ui.active_page)
        else:
            self.ui.main_stack.setCurrentWidget(self.ui.inactive_page)

    def _on_model_reset(self):
        self.action_tree_view.expandAll()

    def setupActionsMenu(self, parent: Optional[QtCore.QObject], menu_bar: QtWidgets.QMenuBar):
        """
        Set up the Actions menu on a menu bar.
        """
        actions_menu = menu_bar.addMenu("Actions")

        add_defaults_action = QtWidgets.QAction("Add Default Actions", parent)
        add_defaults_action.setStatusTip("Add the default set of actions.")
        add_defaults_action.triggered.connect(self.blueprintModel.addDefaultActions)
        actions_menu.addAction(add_defaults_action)

        actions_menu.addSeparator()

        allActionSpecs: List[BuildActionSpec] = BuildActionRegistry.get().get_all_actions()

        grp_action = QtWidgets.QAction("Group", parent)
        grp_action.triggered.connect(self.blueprintModel.createGroup)
        actions_menu.addAction(grp_action)

        # create action sub menu for each category
        categories = [spec.category for spec in allActionSpecs]
        categories = list(set(categories))
        cat_menus: Dict[str, QtWidgets.QMenu] = {}

        for cat in sorted(categories):
            cat_menu = actions_menu.addMenu(cat)
            cat_menus[cat] = cat_menu

        for actionSpec in allActionSpecs:
            actionId = actionSpec.id
            actionCategory = actionSpec.category
            description = actionSpec.description

            action = QtWidgets.QAction(actionSpec.display_name, parent)
            if description:
                action.setStatusTip(description)
            action.triggered.connect(partial(self.blueprintModel.createAction, actionId))

            cat_menus[actionCategory].addAction(action)


class ActionTreeWindow(PulseWindow):
    """
    A standalone window that contains an Action Tree.
    """

    OBJECT_NAME = 'pulseActionTreeWindow'
    WINDOW_MODULE = 'pulse.ui.actiontree'
    WINDOW_TITLE = 'Pulse Action Tree'
    WIDGET_CLASS = ActionTree

    def __init__(self, parent=None):
        super(ActionTreeWindow, self).__init__(parent)

        # setup main menu bar
        self.menu_bar = QtWidgets.QMenuBar(self)
        self.layout().setMenuBar(self.menu_bar)

        self.main_widget.setupActionsMenu(self, self.menu_bar)


# Action Mirroring
# ----------------

# TODO: move this outside of a ui module, should be core functionality

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
            self._config = self.blueprintModel.blueprint.get_config()
        return self._config

    def getMirroredStepName(self, stepName: str) -> Optional[str]:
        """
        Return the mirrored name of a BuildStep.

        Returns:
            The mirrored step name, or None if it cannot be mirrored
        """
        destName = sym.get_mirrored_name(stepName, self.getConfig())
        if destName != stepName:
            return destName

    def canMirrorStep(self, sourceStep: BuildStep):
        """
        Return True if a BuildStep can be mirrored
        """
        return sourceStep.is_action() and self.getMirroredStepName(sourceStep.name) is not None

    def getMirroredStepPath(self, sourceStep: BuildStep):
        """
        Return the full path to a BuildStep by mirroring a steps name.
        """
        destStepName = self.getMirroredStepName(sourceStep.name)
        if destStepName:
            parentPath = sourceStep.get_parent_path()
            if parentPath:
                return parentPath + '/' + destStepName
            return destStepName

    def getPairedStep(self, sourceStep) -> BuildStep:
        """
        Return the BuildStep that is paired with a step, if any
        """
        destStepPath = self.getMirroredStepPath(sourceStep)
        if destStepPath:
            return self.blueprintModel.getStep(destStepPath)

    def getOrCreatePairedStep(self, sourceStep: BuildStep) -> BuildStep:
        """
        Return the BuildStep that is paired with a step,
        creating a new BuildStep if necessary.
        """
        destStepPath = self.getMirroredStepPath(sourceStep)
        if destStepPath:
            destStep = self.blueprintModel.getStep(destStepPath)
            if not destStep:
                childIndex = sourceStep.index_in_parent() + 1
                newStepData = sourceStep.serialize()
                newStepData['name'] = self.getMirroredStepName(sourceStep.name)
                dataStr = serialize_attr_value(newStepData)
                cmds.pulseCreateStep(sourceStep.get_parent_path(), childIndex, dataStr)
                return self.blueprintModel.getStep(destStepPath)
            else:
                return destStep

    def mirrorAction(self, sourceStep: BuildStep):
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

        sourceAction = sourceStep.action_proxy
        destAction = destStep.action_proxy

        if not destAction or destAction.action_id != sourceAction.action_id:
            # action was set up incorrectly
            LOG.warning("Cannot mirror %s -> %s, destination action"
                        "is not tye same type", sourceStep, destStep)
            return False

        destStepPath = destStep.get_full_path()

        # match up variant attrs
        for _, attr in sourceAction.get_attrs().items():
            isVariant = sourceAction.is_variant_attr(attr.name)
            destAttrPath = f'{destStepPath}.{attr.name}'
            if destAction.is_variant_attr(attr.name) != isVariant:
                cmds.pulseSetIsVariantAttr(destAttrPath, isVariant)

        # match up variant lengths
        while sourceAction.num_variants() < destAction.num_variants():
            destAction.remove_variant_at(-1)
        while sourceAction.num_variants() > destAction.num_variants():
            destAction.add_variant()

        #  mirror invariant attr values
        for _, attr in sourceAction.get_attrs().items():
            if not sourceAction.is_variant_attr(attr.name):
                value = attr.get_value()
                mirroredValue = self.mirrorActionValue(attr, value)
                destAttrPath = f'{destStepPath}.{attr.name}'
                mirroredValueStr = serialize_attr_value(mirroredValue)
                LOG.debug('%s -> %s', value, mirroredValue)
                cmds.pulseSetActionAttr(destAttrPath, mirroredValueStr)

        # mirror variant attr values
        for i, variant in enumerate(sourceAction.get_variants()):
            for _, attr in variant.get_attrs().items():
                value = attr.get_value()
                mirroredValue = self.mirrorActionValue(attr, value)
                destAttrPath = f'{destStepPath}.{attr.name}'
                mirroredValueStr = serialize_attr_value(mirroredValue)
                LOG.debug('%s -> %s', value, mirroredValue)
                cmds.pulseSetActionAttr(destAttrPath, mirroredValueStr, v=i)

        cmds.undoInfo(closeChunk=True)

        return True

    def mirrorActionValue(self, attr: BuildActionAttribute, value):
        """
        Return a mirrored value of an attribute, taking into account attribute types and config.

        Args:
            attr: BuildActionAttribute
                The attribute to mirror.
            value:
                The attribute value to mirror.
        """
        if not attr.config.get('canMirror', True):
            # don't mirror the attributes value, just copy it
            return value

        def getPairedNodeOrSelf(node):
            """
            Return the paired node of a node, if one exists, otherwise return the node.
            """
            paired_node = sym.get_paired_node(node)
            if paired_node:
                return paired_node
            return node

        if not value:
            return value

        # TODO: move mirror logic into BuildActionAttribute and type-specific subclasses?

        if attr.type == 'node':
            return getPairedNodeOrSelf(value)

        elif attr.type == 'nodelist':
            return [getPairedNodeOrSelf(node) for node in value]

        elif attr.type == 'string':
            return sym.get_mirrored_name(value, self.getConfig())

        elif attr.type == 'stringlist':
            return [sym.get_mirrored_name(v, self.getConfig()) for v in value]

        return value
