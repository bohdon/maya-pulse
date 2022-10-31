"""
Form ui classes for any type of action attribute, e.g.
float forms, node and node list forms, combo box forms, etc.
"""
import logging
from typing import Optional

import maya.cmds as cmds
import pymel.core as pm

from ..build_items import BuildStep, BuildActionProxy, BuildActionAttribute
from ..vendor import pymetanode as meta
from ..serializer import serialize_attr_value
from ..vendor.Qt import QtCore, QtGui, QtWidgets
from .. import names
from . import utils

LOG = logging.getLogger(__name__)

SELECT_ICON_PATH = ':/icon/circle_left.svg'
RESET_ICON_PATH = ':/icon/reset.svg'
TOOL_ICON_SIZE = QtCore.QSize(20, 20)


class ActionAttrForm(QtWidgets.QFrame):
    """
    The base class for all forms used to edit action attributes.
    Provides input validation and basic signals for keeping
    track of value changes.
    """

    # map of attribute types to form widget classes
    TYPE_MAP: dict[Optional[str], type['ActionAttrForm']] = {}

    LABEL_WIDTH = 120
    LABEL_HEIGHT = 20
    FORM_WIDTH_SMALL = 80

    @staticmethod
    def createForm(index, attr: BuildActionAttribute, variantIndex=-1, parent=None):
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            index:
                A QModelIndex pointing to the BuildStep being edited
            attr:
                The attribute being edited.
        """
        if attr.type is None:
            LOG.error(f"Attribute has no type: {attr}")
            # TODO: create a generic attribute form that just displays the error

        if attr.type in ActionAttrForm.TYPE_MAP:
            return ActionAttrForm.TYPE_MAP[attr.type](index, attr, variantIndex, parent=parent)

        # type not found, fallback to None type
        if None in ActionAttrForm.TYPE_MAP:
            return ActionAttrForm.TYPE_MAP[None](index, attr, variantIndex, parent=parent)

    @classmethod
    def addFormType(cls, typeName: Optional[str], formClass: type['ActionAttrForm']):
        cls.TYPE_MAP[typeName] = formClass

    def __init__(self, index, attr: BuildActionAttribute, variantIndex: int, parent=None):
        super(ActionAttrForm, self).__init__(parent=parent)
        self.setObjectName('formFrame')

        self.index = QtCore.QPersistentModelIndex(index)
        # the attribute being edited
        self.attr = attr
        # the index of the variant being edited
        self.variantIndex = variantIndex

        # build the ui
        self.resetValueBtn = None
        self.setupUi(self)

        # update valid state, check both type and value here
        # because the current value may be of an invalid type
        self._updateValidState()
        self._updateResetVisible()

        # listen to model change events
        self.index.model().dataChanged.connect(self.onModelDataChanged)

    def _updateValidState(self):
        """
        Update the state of the ui to represent whether the attribute value is currently valid.
        """
        # if false, the input is not acceptable, e.g. badly formatted
        isFormValid = self._isFormValueValid()

        # if false, the type might be wrong, value out of range, or missing a required input
        self.attr.validate()
        isValueValid = self._isFormValueValid() and self.attr.is_value_valid()

        self._setUiValidState(isValueValid, isFormValid)

    def _updateResetVisible(self):
        if self.resetValueBtn:
            self.resetValueBtn.setVisible(self.isValueSet())

    def onModelDataChanged(self):
        """
        """
        # TODO: only update if the change affected this attribute
        if not self.index.isValid():
            self.hide()
            return

        actionProxy = self.getActionProxy()
        if not actionProxy:
            self.hide()
            return

        # update form
        self._setFormValue(self.getAttrValue())
        self._updateResetVisible()
        self._updateValidState()

    def isVariant(self):
        return self.variantIndex >= 0

    def getAttrValue(self):
        return self.attr.get_value()

    def setAttrValue(self, newValue):
        """
        Set the current value of the attribute in this form.
        Performs partial validation and prevents actually setting
        the attribute value if it's type is invalid.
        """
        if not self.attr.is_acceptable_value(newValue):
            # invalid type or otherwise unacceptable value
            return

        attrPath = self.getAttrPath()
        if not attrPath:
            return

        strValue = serialize_attr_value(newValue)
        cmds.pulseSetActionAttr(attrPath, strValue, v=self.variantIndex)
        # refresh form to the new value in case it was cleaned up or processed
        self._setFormValue(self.attr.get_value())

    def isValueSet(self) -> bool:
        """
        Return true if the attribute has been set to a non-default value.
        """
        return self.attr.is_value_set() or self._getFormValue() != self.getAttrValue()

    def resetValueToDefault(self):
        self.setAttrValue(self.attr.default_value)

    def setupUi(self, parent):
        """
        Build the appropriate ui for the attribute
        """
        raise NotImplementedError

    def getStep(self) -> BuildStep:
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self) -> BuildActionProxy:
        step = self.getStep()
        if step and step.is_action():
            return step.action_proxy

    def getAttrPath(self):
        step = self.getStep()
        if not step:
            return

        return f"{step.get_full_path()}.{self.attr.name}"

    def _setFormValue(self, attrValue):
        """
        Set the current value displayed in the UI form
        """
        raise NotImplementedError

    def _getFormValue(self):
        """
        Return the current value entered into the form.
        It may not be an acceptable or valid attribute value.
        """
        # default implementation has no separate form value
        return self.getAttrValue()

    def _isFormValueValid(self):
        """
        Return True if the current form contains valid data.
        The attribute value will not be set unless the form has valid data to prevent a bad state.
        """
        return self.attr.is_acceptable_value(self._getFormValue())

    def _onValueEdited(self):
        """
        Called when the value represented in the form has been edited by the user.
        Try to set the attribute to the new value, or update the valid state of the form.
        """
        if self._isFormValueValid():
            # update the attributes value
            self.setAttrValue(self._getFormValue())
        else:
            # cant set the attribute, but indicate invalid state
            self._updateValidState()
            self._updateResetVisible()

    def _setUiValidState(self, isValid, isFormValid):
        if isValid:
            self.label.setToolTip('')
            self.setProperty('cssClasses', '')
        elif isFormValid:
            reason = self.attr.get_invalid_reason()
            self.label.setToolTip(f'Invalid: {reason}')
            self.setProperty('cssClasses', 'warning')
        else:
            self.label.setToolTip('Invalid input')
            self.setProperty('cssClasses', 'error')

        # force a styling refresh to make use of cssClasses
        self.setStyleSheet('')

    def setupDefaultFormUi(self, parent):
        """
        Optional UI setup that builds a standardized layout.
        Includes a form layout and a label with the attributes name.
        Should be called at the start of setupUi if desired.
        """
        self.mainLayout = QtWidgets.QHBoxLayout(parent)
        # margin that will give us some visible area of
        # the frame that can change color based on valid state
        self.mainLayout.setMargin(2)

        self.formLayout = QtWidgets.QFormLayout(parent)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop | QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        self.labelLayout = QtWidgets.QHBoxLayout(parent)

        # attribute name label
        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignTop)
        # add some space above the label, so it lines up
        self.label.setMargin(2)
        self.label.setText(names.to_title(self.attr.name))
        # set description tooltips
        description = self.attr.description
        if description:
            self.label.setStatusTip(description)

        self.labelLayout.addWidget(self.label)

        self.formLayout.setLayout(0, QtWidgets.QFormLayout.LabelRole, self.labelLayout)

        self.mainLayout.addLayout(self.formLayout)

        # add reset value button
        self.resetValueBtn = QtWidgets.QToolButton(parent)
        self.resetValueBtn.setIcon(QtGui.QIcon(RESET_ICON_PATH))
        self.resetValueBtn.setFixedSize(TOOL_ICON_SIZE)
        utils.setRetainSizeWhenHidden(self.resetValueBtn, True)
        self.resetValueBtn.setStatusTip('Reset value to default')
        self.resetValueBtn.clicked.connect(self.resetValueToDefault)
        self.mainLayout.addWidget(self.resetValueBtn)
        self.mainLayout.setAlignment(self.resetValueBtn, QtCore.Qt.AlignTop)

    def setDefaultFormWidget(self, widget):
        """
        Set the widget to be used as the field in the default form layout
        Requires `setupDefaultFormUi` to be used.
        """
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, widget)

    def setDefaultFormLayout(self, layout):
        """
        Set the layout to be used as the field in the default form layout.
        Requires `setupDefaultFormUi` to be used.
        """
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, layout)


class BatchAttrForm(QtWidgets.QFrame):
    """
    The base class for an attribute form designed to bulk edit all variants
    of an attribute on an action proxy. This appears where the default attr
    form usually appears when the attribute is marked as variant.
    """

    TYPE_MAP: dict[Optional[str], type['BatchAttrForm']] = {}

    LABEL_WIDTH = ActionAttrForm.LABEL_WIDTH
    LABEL_HEIGHT = ActionAttrForm.LABEL_HEIGHT
    FORM_WIDTH_SMALL = ActionAttrForm.FORM_WIDTH_SMALL

    @staticmethod
    def doesFormExist(attr: BuildActionAttribute):
        return attr.type in BatchAttrForm.TYPE_MAP

    @staticmethod
    def createForm(index, attr: BuildActionAttribute, parent=None):
        """
        Create a new ActionAttrForm of the appropriate type based on a BuildAction attribute.
        """
        if attr.type in BatchAttrForm.TYPE_MAP:
            return BatchAttrForm.TYPE_MAP[attr.type](index, attr, parent=parent)

        # type not found, fallback to None type
        if None in BatchAttrForm.TYPE_MAP:
            return BatchAttrForm.TYPE_MAP[None](index, attr, parent=parent)

    @classmethod
    def addFormType(cls, attrType: Optional[str], formClass: type['BatchAttrForm']):
        cls.TYPE_MAP[attrType] = formClass

    def __init__(self, index, attr: BuildActionAttribute, parent=None):
        super(BatchAttrForm, self).__init__(parent=parent)
        self.setObjectName('formFrame')

        self.index = QtCore.QPersistentModelIndex(index)
        self.attr = attr

        self.setupUi(self)

    def onModelDataChanged(self):
        pass

    def setupUi(self, parent):
        raise NotImplementedError

    # TODO: share this functionality with the non-batch attr form
    def setupDefaultFormUi(self, parent):
        """
        Optional UI setup that builds a standardized layout.
        Includes a form layout and a label with the attributes name.
        Should be called at the start of setupUi if desired.
        """
        self.formLayout = QtWidgets.QFormLayout(parent)

        # margin that will give us some visible area of
        # the frame that can change color based on valid state
        self.formLayout.setMargin(2)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTop | QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        self.labelLayout = QtWidgets.QHBoxLayout(parent)

        # attribute name label
        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignTop)
        # add some space above the label so it lines up
        self.label.setMargin(2)
        self.label.setEnabled(False)
        self.label.setText(names.to_title(self.attr.name))
        # set description tooltips
        description = self.attr.description
        if description:
            self.label.setStatusTip(description)

        self.labelLayout.addWidget(self.label)

        self.formLayout.setLayout(0, QtWidgets.QFormLayout.LabelRole, self.labelLayout)

    def setDefaultFormWidget(self, widget):
        """
        Set the widget to be used as the field in the default form layout
        Requires `setupDefaultFormUi` to be used.
        """
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, widget)

    def setDefaultFormLayout(self, layout):
        """
        Set the layout to be used as the field in the default form layout.
        Requires `setupDefaultFormUi` to be used.
        """
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.FieldRole, layout)

    def getStep(self) -> BuildStep:
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self) -> BuildActionProxy:
        step = self.getStep()
        if step and step.is_action():
            return step.action_proxy

    def getAttrPath(self):
        step = self.getStep()
        if not step:
            return

        return f'{step.get_full_path()}.{self.attr.name}'

    def setVariantValues(self, values):
        attrPath = self.getAttrPath()
        if not attrPath:
            return

        for i, value in enumerate(values):
            strValue = serialize_attr_value(value)
            cmds.pulseSetActionAttr(attrPath, strValue, v=i)


class DefaultAttrForm(ActionAttrForm):
    """
    A catchall attribute form that can handle any attribute type by leveraging pymetanode serialization.
    Provides a text field where values can be typed in serialized string form.
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self._didFailDecode = False

        self.textEdit = QtWidgets.QLineEdit(parent)
        # TODO: use cssClasses
        self.textEdit.setStyleSheet('font: 8pt "Consolas";')

        self._setFormValue(self.getAttrValue())

        self.textEdit.editingFinished.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.textEdit)

    def _setFormValue(self, attrValue):
        if isinstance(attrValue, str):
            self.textEdit.setText(repr(attrValue))
        else:
            self.textEdit.setText(meta.encodeMetaData(attrValue))

    def _hasSyntaxErrors(self) -> bool:
        """
        Return true if the current form value has syntax errors that prevent
        it from being able to decode.
        """
        try:
            meta.decodeMetaData(self.textEdit.text())
            return True
        except:
            return False

    def _getFormValue(self):
        try:
            return meta.decodeMetaData(self.textEdit.text())
        except:
            return None

    def _isFormValueValid(self):
        try:
            meta.decodeMetaData(self.textEdit.text())
        except Exception as e:
            return False
        return super(DefaultAttrForm, self)._isFormValueValid()

    def _onValueEdited(self):
        """
        If the form text is empty, but the value is not acceptable, reset the attribute to the default
        value for the type. Useful for list or complex data types where typing the default value would be tedious.

        Note that that's not the same as the default value that may be set in the config, e.g. an empty list
        instead of potentially a list with config-defined default values in it.
        """
        if not self._isFormValueValid():
            if not self.textEdit.text().strip(' '):
                self.setAttrValue(self.attr.get_type_default_value())
                self._updateValidState()
                return

        super(DefaultAttrForm, self)._onValueEdited()


ActionAttrForm.addFormType(None, DefaultAttrForm)


class BoolAttrForm(ActionAttrForm):
    """
    A simple checkbox attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.checkbox = QtWidgets.QCheckBox(parent)
        self._setFormValue(self.getAttrValue())
        self.checkbox.setMinimumHeight(self.LABEL_HEIGHT)
        self.checkbox.stateChanged.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.checkbox)

    def _setFormValue(self, attrValue):
        self.checkbox.setChecked(attrValue)

    def _getFormValue(self):
        return self.checkbox.isChecked()


# TODO: put attribute type names in an enum class
ActionAttrForm.addFormType('bool', BoolAttrForm)


class IntAttrForm(ActionAttrForm):
    """
    A simple integer attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.spinBox = QtWidgets.QSpinBox(parent)
        self.spinBox.setMinimumHeight(self.LABEL_HEIGHT)
        self.spinBox.setMinimumWidth(self.FORM_WIDTH_SMALL)
        self.spinBox.setRange(self.attr.config.get('min', 0), self.attr.config.get('max', 100))
        self._setFormValue(self.getAttrValue())
        self.spinBox.valueChanged.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.spinBox)

    def _setFormValue(self, attrValue):
        self.spinBox.setValue(attrValue)

    def _getFormValue(self):
        return self.spinBox.value()


ActionAttrForm.addFormType('int', IntAttrForm)


class FloatAttrForm(ActionAttrForm):
    """
    A simple float attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.spinBox = QtWidgets.QDoubleSpinBox(parent)
        self.spinBox.setMinimumHeight(self.LABEL_HEIGHT)
        self.spinBox.setMinimumWidth(self.FORM_WIDTH_SMALL)
        self.spinBox.setDecimals(self.attr.config.get('decimals', 3))
        self.spinBox.setSingleStep(self.attr.config.get('stepSize', 0.1))
        self.spinBox.setRange(self.attr.config.get('min', 0), self.attr.config.get('max', 100))
        self._setFormValue(self.getAttrValue())
        self.spinBox.valueChanged.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.spinBox)

    def _setFormValue(self, attrValue):
        self.spinBox.setValue(attrValue)

    def _getFormValue(self):
        return self.spinBox.value()


ActionAttrForm.addFormType('float', FloatAttrForm)


class StringAttrForm(ActionAttrForm):
    """
    A simple string attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.lineEdit = QtWidgets.QLineEdit(parent)
        self.lineEdit.setMinimumHeight(self.LABEL_HEIGHT)
        self._setFormValue(self.getAttrValue())
        self.lineEdit.editingFinished.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.lineEdit)

    def _setFormValue(self, attrValue):
        self.lineEdit.setText(attrValue)

    def _getFormValue(self):
        return self.lineEdit.text().strip(' ')


ActionAttrForm.addFormType('string', StringAttrForm)


class OptionAttrForm(ActionAttrForm):
    """
    An options list form that uses a combo box
    to display options and keeps data stored as an int value
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.combo = QtWidgets.QComboBox(parent)
        for option in self.attr.config.get('options', []):
            self.combo.addItem(option)
        self._setFormValue(self.getAttrValue())
        self.combo.currentIndexChanged.connect(self._onValueEdited)

        self.setDefaultFormWidget(self.combo)

    def _setFormValue(self, attrValue):
        self.combo.setCurrentIndex(attrValue)

    def _getFormValue(self):
        return self.combo.currentIndex()


ActionAttrForm.addFormType('option', OptionAttrForm)


class NodeAttrForm(ActionAttrForm):
    """
    A special form that allows picking nodes from the scene.
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        hlayout = QtWidgets.QHBoxLayout(parent)
        hlayout.setSpacing(4)

        self.listWidget = QtWidgets.QListWidget(parent)
        self.listWidget.setFixedHeight(20)
        self.listWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.listWidget.setSortingEnabled(True)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listWidget.itemSelectionChanged.connect(self.onItemSelectionChanged)
        hlayout.addWidget(self.listWidget)

        self.pickButton = QtWidgets.QToolButton(parent)
        self.pickButton.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        self.pickButton.setStatusTip("Assign the selected node. "
                                     "Ctrl + click to pop the assigned node from the selection.")
        self.pickButton.setFixedSize(TOOL_ICON_SIZE)
        self.pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(self.pickButton)
        hlayout.setAlignment(self.pickButton, QtCore.Qt.AlignTop)

        self._setFormValue(self.getAttrValue())

        self.setDefaultFormLayout(hlayout)

    def _setFormValue(self, attrValue):
        while self.listWidget.takeItem(0):
            pass
        if attrValue:
            item = QtWidgets.QListWidgetItem(attrValue.nodeName())
            uuid = meta.getUUID(attrValue)
            item.setData(QtCore.Qt.UserRole, uuid)
            self.listWidget.addItem(item)

    def _shouldPopSelection(self):
        """
        Return true if the first selected node should be popped from the selection
        when assigning from selection. True when holding the control key.
        """
        return QtWidgets.QApplication.instance().keyboardModifiers() & QtCore.Qt.ControlModifier

    def setFromSelection(self):
        sel = pm.selected()
        if sel:
            self.setAttrValue(sel[0])
        else:
            self.setAttrValue(None)
        if self._shouldPopSelection():
            pm.select(sel[1:])

    def onItemSelectionChanged(self):
        items = self.listWidget.selectedItems()
        nodes = []
        for item in items:
            node = meta.findNodeByUUID(item.data(QtCore.Qt.UserRole))
            if node:
                nodes.append(node)
        if nodes:
            pm.select(nodes)


ActionAttrForm.addFormType('node', NodeAttrForm)


class NodeListAttrForm(ActionAttrForm):
    """
    A special form that allows picking nodes from the scene.
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        hlayout = QtWidgets.QHBoxLayout(parent)
        hlayout.setSpacing(4)

        self.listWidget = QtWidgets.QListWidget(parent)
        self.listWidget.setSortingEnabled(True)
        self.listWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listWidget.itemSelectionChanged.connect(self.onItemSelectionChanged)
        hlayout.addWidget(self.listWidget)

        self.pickButton = QtWidgets.QToolButton(parent)
        self.pickButton.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        self.pickButton.setStatusTip('Assign the selected nodes.')
        self.pickButton.setFixedSize(TOOL_ICON_SIZE)
        self.pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(self.pickButton)
        hlayout.setAlignment(self.pickButton, QtCore.Qt.AlignTop)

        self.setDefaultFormLayout(hlayout)

        self._setFormValue(self.getAttrValue())

    def _setFormValue(self, attrValue):
        while self.listWidget.takeItem(0):
            pass
        for node in attrValue:
            if node:
                item = QtWidgets.QListWidgetItem(node.nodeName())
                uuid = meta.getUUID(node)
                item.setData(QtCore.Qt.UserRole, uuid)
                self.listWidget.addItem(item)
            else:
                self.listWidget.addItem('(missing)')
        # 13px line height per item, clamped in range 40..120, added 8px buffer
        newHeight = max(40, min(120, 8 + 13 * self.listWidget.count()))
        self.listWidget.setFixedHeight(newHeight)

    def setFromSelection(self):
        self.setAttrValue(pm.selected())

    def onItemSelectionChanged(self):
        items = self.listWidget.selectedItems()
        nodes = []
        for item in items:
            node = meta.findNodeByUUID(item.data(QtCore.Qt.UserRole))
            if node:
                nodes.append(node)
        if nodes:
            pm.select(nodes)


ActionAttrForm.addFormType('nodelist', NodeListAttrForm)


class NodeBatchAttrForm(BatchAttrForm):
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
        self.setupDefaultFormUi(parent)

        hlayout = QtWidgets.QHBoxLayout(parent)
        hlayout.setContentsMargins(0, 0, 0, 0)

        pickButton = QtWidgets.QToolButton(parent)
        pickButton.setIcon(QtGui.QIcon(SELECT_ICON_PATH))
        pickButton.setStatusTip('Assign the selected nodes, one per variant.')
        pickButton.setFixedSize(TOOL_ICON_SIZE)
        pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(pickButton)
        hlayout.setAlignment(pickButton, QtCore.Qt.AlignTop)
        # body spacer
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        hlayout.addItem(spacer)

        self.setDefaultFormLayout(hlayout)

    def setFromSelection(self):
        """
        Set the node value for this attribute for each variant
        based on the selected list of nodes. Increases the variant
        list size if necessary to match the selection.
        """
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        self.setVariantValues(pm.selected())


BatchAttrForm.addFormType('node', NodeBatchAttrForm)


class DefaultBatchAttrForm(BatchAttrForm):

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)


BatchAttrForm.addFormType(None, DefaultBatchAttrForm)
