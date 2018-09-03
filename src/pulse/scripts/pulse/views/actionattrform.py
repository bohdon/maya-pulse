
import pymel.core as pm
import maya.cmds as cmds
import pymetanode as meta

import pulse.names
from pulse.core import serializeAttrValue
from pulse.vendor.Qt import QtCore, QtWidgets
from . import utils as viewutils

__all__ = [
    'ActionAttrForm',
    'BatchAttrForm',
    'BoolAttrForm',
    'DefaultAttrForm',
    'DefaultBatchAttrForm',
    'FloatAttrForm',
    'IntAttrForm',
    'NodeAttrForm',
    'NodeBatchAttrForm',
    'NodeListAttrForm',
    'OptionAttrForm',
    'StringAttrForm',
]


class ActionAttrForm(QtWidgets.QFrame):
    """
    The base class for all forms used to edit action attributes.
    Provides input validation and basic signals for keeping
    track of value changes.
    """

    TYPEMAP = {}

    LABEL_WIDTH = 140
    LABEL_HEIGHT = 20
    FORM_WIDTH_SMALL = 80

    @staticmethod
    def createForm(index, attr, variantIndex=-1, parent=None):
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            index: A QModelIndex pointing to the BuildStep being edited
            attr: A dict representing the config of a BuildAction attribute
        """
        attrType = attr['type']
        if attrType in ActionAttrForm.TYPEMAP:
            return ActionAttrForm.TYPEMAP[attrType](
                index, attr, variantIndex, parent=parent)

        # type not found, fallback to None type
        if None in ActionAttrForm.TYPEMAP:
            return ActionAttrForm.TYPEMAP[None](
                index, attr, variantIndex, parent=parent)

    @classmethod
    def addFormType(cls, typeName, formClass):
        cls.TYPEMAP[typeName] = formClass

    def __init__(self, index, attr, variantIndex, parent=None):
        super(ActionAttrForm, self).__init__(parent=parent)
        self.setObjectName('actionAttrForm')

        self.index = QtCore.QPersistentModelIndex(index)
        # the config data of the attribute being edited
        self.attr = attr
        self.variantIndex = variantIndex
        # the cached value of the attribute
        self.attrValue = self.getAttrValue()
        # build the ui
        self.setupUi(self)
        # update valid state, check both type and value here
        # because the current value may be of an invalid type
        self.isValueValid = self._isValueTypeValid(
            self.attrValue) and self._isValueValid(self.attrValue)
        self._setUiValidState(self.isValueValid)
        # listen to model change events
        self.index.model().dataChanged.connect(self.onModelDataChanged)

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

        # update cached value and form
        self.attrValue = self.getAttrValue()
        self._setFormValue(self.attrValue)

    def isVariant(self):
        return self.variantIndex >= 0

    def getAttrValue(self):
        actionProxy = self.getActionProxy()
        if not actionProxy:
            return

        if self.isVariant():
            variant = actionProxy.getVariant(self.variantIndex)
            return variant.getAttrValueOrDefault(self.attr['name'])
        else:
            return actionProxy.getAttrValueOrDefault(self.attr['name'])

    def setAttrValue(self, newValue):
        """
        Set the current value of the attribute in this form.
        Performs partial validation and prevents setting
        the value if it's type is invalid.
        """
        # value doesn't need to be valid as long
        # as it has the right type
        if self._isValueTypeValid(newValue):
            self.attrValue = newValue
            self._setFormValue(newValue)
            self.isValueValid = self._isValueValid(newValue)
            self._setUiValidState(self.isValueValid)

            # TODO: clean up relationship between preview value and actual value
            attrPath = self.getAttrPath()
            if not attrPath:
                return

            strValue = serializeAttrValue(newValue)
            cmds.pulseSetActionAttr(attrPath, strValue, v=self.variantIndex)

    def setupUi(self, parent):
        """
        Build the appropriate ui for the attribute
        """
        raise NotImplementedError

    def getStep(self):
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self):
        step = self.getStep()
        if step and step.isAction():
            return step.actionProxy

    def getAttrPath(self):
        step = self.getStep()
        if not step:
            return

        return '{0}.{1}'.format(step.getFullPath(), self.attr['name'])

    def _setFormValue(self, attrValue):
        """
        Set the current value displayed in the UI form
        """
        raise NotImplementedError

    def _getFormValue(self):
        """
        Return the current attribute value from the UI form.
        The result must always be of a valid type for this attr,
        though the value itself can be invalid.
        """
        raise NotImplementedError

    def _isFormValid(self):
        """
        Return True if the current form contains valid data.
        """
        return True

    def _isValueTypeValid(self, attrValue):
        """
        Return True if a potential value for the attribute matches
        the type of attribute. Attributes of at least a valid
        type can be saved, even though they may cause issues if not
        fixed before building.
        """
        return True

    def _isValueValid(self, attrValue):
        """
        Return True if a potential value for the attribute is valid
        """
        return True

    def _valueChanged(self):
        """
        Update the current attrValue and isValueValid state.
        Should be called whenever relevant UI values change.
        The new value will be retrieved by using `_getFormValue`,
        and validated using `_isValueValid`
        """
        # only emit when form is valid
        if self._isFormValid():
            self.attrValue = self._getFormValue()
            self.isValueValid = self._isValueValid(self.attrValue)
            self._setUiValidState(self.isValueValid)
            self.setAttrValue(self.attrValue)
        else:
            self._setUiValidState(False)

    def _setUiValidState(self, isValid):
        if isValid:
            self.setStyleSheet('')
        else:
            self.setStyleSheet(
                'QFrame#actionAttrForm { background-color: rgb(255, 0, 0, 35); }')

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
        self.formLayout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(
            QtCore.Qt.AlignRight |
            QtCore.Qt.AlignTop |
            QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        # attribute name
        self.labelLayout = QtWidgets.QHBoxLayout(parent)

        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(
            self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(
            QtCore.Qt.AlignRight |
            QtCore.Qt.AlignTrailing |
            QtCore.Qt.AlignTop)
        # add some space above the label so it lines up
        self.label.setMargin(2)
        self.label.setText(pulse.names.toTitle(self.attr['name']))
        description = self.attr.get('description')
        if description:
            self.label.setStatusTip(description)
        self.labelLayout.addWidget(self.label)

        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.LabelRole, self.labelLayout)

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
    The base class for an attribute form designed to
    bulk edit all variants of an attribute on an action proxy.
    This appears where the default attr form usually appears
    when the attribute is marked as variant.
    """

    TYPEMAP = {}

    LABEL_WIDTH = 140
    LABEL_HEIGHT = 20
    FORM_WIDTH_SMALL = 80

    @staticmethod
    def doesFormExist(attr):
        return attr['type'] in BatchAttrForm.TYPEMAP

    @staticmethod
    def createForm(index, attr, parent=None):
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            attr: A dict representing the config of a BuildAction attribute
        """
        attrType = attr['type']
        if attrType in BatchAttrForm.TYPEMAP:
            return BatchAttrForm.TYPEMAP[attrType](index, attr, parent=parent)
        # type not found, fallback to None type
        if None in BatchAttrForm.TYPEMAP:
            return BatchAttrForm.TYPEMAP[None](index, attr, parent=parent)

    @classmethod
    def addFormType(cls, typeName, formClass):
        cls.TYPEMAP[typeName] = formClass

    def __init__(self, index, attr, parent=None):
        super(BatchAttrForm, self).__init__(parent=parent)
        self.index = QtCore.QPersistentModelIndex(index)
        self.attr = attr
        self.setupUi(self)

    def onModelDataChanged(self):
        pass

    def setupUi(self, parent):
        raise NotImplementedError

    # TODO: share this functionality with the main attr form
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
        self.formLayout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(
            QtCore.Qt.AlignRight |
            QtCore.Qt.AlignTop |
            QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        # attribute name
        self.labelLayout = QtWidgets.QHBoxLayout(parent)

        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(
            self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(
            QtCore.Qt.AlignRight |
            QtCore.Qt.AlignTrailing |
            QtCore.Qt.AlignTop)
        # add some space above the label so it lines up
        self.label.setMargin(2)
        self.label.setText(pulse.names.toTitle(self.attr['name']))
        self.labelLayout.addWidget(self.label)

        self.formLayout.setLayout(
            0, QtWidgets.QFormLayout.LabelRole, self.labelLayout)

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

    def getStep(self):
        if self.index.isValid():
            return self.index.model().stepForIndex(self.index)

    def getActionProxy(self):
        step = self.getStep()
        if step and step.isAction():
            return step.actionProxy

    def getAttrPath(self):
        step = self.getStep()
        if not step:
            return

        return '{0}.{1}'.format(step.getFullPath(), self.attr['name'])

    def setVariantValues(self, values):
        attrPath = self.getAttrPath()
        if not attrPath:
            return

        for i, value in enumerate(values):
            strValue = serializeAttrValue(value)
            cmds.pulseSetActionAttr(attrPath, strValue, v=i)


class DefaultAttrForm(ActionAttrForm):
    """
    A catchall attribute form that can handle any attribute type
    by leveraging pymetanode serialization. Provides a text field
    where values can typed representing serialized string data.
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self._didFailDecode = False

        self.textEdit = QtWidgets.QLineEdit(parent)
        self.textEdit.setStyleSheet('font: 8pt "Consolas";')
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.textEdit.editingFinished.connect(self._valueChanged)

        self.setDefaultFormWidget(self.textEdit)

    def _setFormValue(self, attrValue):
        if isinstance(attrValue, basestring):
            self.textEdit.setText(repr(attrValue))
        else:
            self.textEdit.setText(meta.encodeMetaData(attrValue))

    def _getFormValue(self):
        return meta.decodeMetaData(self.textEdit.text())

    def _isFormValid(self):
        try:
            meta.decodeMetaData(self.textEdit.text())
            return True
        except Exception as e:
            return False


ActionAttrForm.addFormType(None, DefaultAttrForm)


class BoolAttrForm(ActionAttrForm):
    """
    A simple checkbox attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.checkbox = QtWidgets.QCheckBox(parent)
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.checkbox.setMinimumHeight(self.LABEL_HEIGHT)
        self.checkbox.stateChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.checkbox)

    def _setFormValue(self, attrValue):
        self.checkbox.setChecked(attrValue)

    def _getFormValue(self):
        return self.checkbox.isChecked()

    def _isValueTypeValid(self, attrValue):
        return attrValue is True or attrValue is False


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
        self.spinBox.setRange(self.attr.get('min', 0),
                              self.attr.get('max', 100))
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.spinBox.valueChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.spinBox)

    def _setFormValue(self, attrValue):
        self.spinBox.setValue(attrValue)

    def _getFormValue(self):
        return self.spinBox.value()

    def _isValueTypeValid(self, attrValue):
        return isinstance(attrValue, (int, long))


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
        self.spinBox.setDecimals(self.attr.get('decimals', 3))
        self.spinBox.setSingleStep(self.attr.get('stepSize', 0.1))
        self.spinBox.setRange(self.attr.get('min', 0),
                              self.attr.get('max', 100))
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.spinBox.valueChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.spinBox)

    def _setFormValue(self, attrValue):
        self.spinBox.setValue(attrValue)

    def _getFormValue(self):
        return self.spinBox.value()

    def _isValueTypeValid(self, attrValue):
        return isinstance(attrValue, float)


ActionAttrForm.addFormType('float', FloatAttrForm)


class StringAttrForm(ActionAttrForm):
    """
    A simple string attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.lineEdit = QtWidgets.QLineEdit(parent)
        self.lineEdit.setMinimumHeight(self.LABEL_HEIGHT)
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.lineEdit.editingFinished.connect(self._valueChanged)

        self.setDefaultFormWidget(self.lineEdit)

    def _setFormValue(self, attrValue):
        self.lineEdit.setText(attrValue)

    def _getFormValue(self):
        return self.lineEdit.text()

    def _isValueTypeValid(self, attrValue):
        return isinstance(attrValue, basestring)


ActionAttrForm.addFormType('string', StringAttrForm)


class OptionAttrForm(ActionAttrForm):
    """
    A options list form that uses a combo box
    to display options and keeps data stored as an int value
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.combo = QtWidgets.QComboBox(parent)
        for option in self.attr['options']:
            self.combo.addItem(option)
        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)
        self.combo.currentIndexChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.combo)

    def _setFormValue(self, attrValue):
        self.combo.setCurrentIndex(attrValue)

    def _getFormValue(self):
        return self.combo.currentIndex()

    def _isValueTypeValid(self, attrValue):
        return isinstance(attrValue, (int, long))

    def _isValueValid(self, attrValue):
        return attrValue >= 0 and attrValue < len(self.attr['options'])


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
        self.listWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.listWidget.setSortingEnabled(True)
        self.listWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listWidget.itemSelectionChanged.connect(
            self.onItemSelectionChanged)
        hlayout.addWidget(self.listWidget)

        self.pickButton = QtWidgets.QPushButton(parent)
        self.pickButton.setIcon(viewutils.getIcon("select.png"))
        self.pickButton.setFixedSize(QtCore.QSize(20, 20))
        self.pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(self.pickButton)
        hlayout.setAlignment(self.pickButton, QtCore.Qt.AlignTop)

        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)

        self.setDefaultFormLayout(hlayout)

    def _setFormValue(self, attrValue):
        while self.listWidget.takeItem(0):
            pass
        if attrValue:
            item = QtWidgets.QListWidgetItem(attrValue.nodeName())
            uuid = meta.getUUID(attrValue)
            item.setData(QtCore.Qt.UserRole, uuid)
            self.listWidget.addItem(item)

    def _getFormValue(self):
        return self.attrValue

    def _isValueTypeValid(self, attrValue):
        return attrValue is None or isinstance(attrValue, pm.nt.DependNode)

    def setFromSelection(self):
        sel = pm.selected()
        if sel:
            self.setAttrValue(sel[0])
        else:
            self.setAttrValue(None)

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
        self.listWidget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.listWidget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.listWidget.itemSelectionChanged.connect(
            self.onItemSelectionChanged)
        hlayout.addWidget(self.listWidget)

        self.pickButton = QtWidgets.QPushButton(parent)
        self.pickButton.setIcon(viewutils.getIcon("select.png"))
        self.pickButton.setFixedSize(QtCore.QSize(20, 20))
        self.pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(self.pickButton)
        hlayout.setAlignment(self.pickButton, QtCore.Qt.AlignTop)

        self.setDefaultFormLayout(hlayout)

        if self._isValueTypeValid(self.attrValue):
            self._setFormValue(self.attrValue)

    def _setFormValue(self, attrValue):
        while self.listWidget.takeItem(0):
            pass
        for node in attrValue:
            item = QtWidgets.QListWidgetItem(node.nodeName())
            uuid = meta.getUUID(node)
            item.setData(QtCore.Qt.UserRole, uuid)
            self.listWidget.addItem(item)
        # 13px line height per item, clamped in range 40..120, added 8px buffer
        newHeight = max(40, min(120, 8 + 13 * self.listWidget.count()))
        self.listWidget.setFixedHeight(newHeight)

    def _getFormValue(self):
        return self.attrValue

    def _isValueTypeValid(self, attrValue):
        if not isinstance(attrValue, list):
            return False
        return all([isinstance(n, pm.nt.DependNode) for n in attrValue])

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

        pickButton = QtWidgets.QPushButton(parent)
        pickButton.setIcon(viewutils.getIcon("select.png"))
        pickButton.setFixedSize(QtCore.QSize(20, 20))
        pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(pickButton)
        hlayout.setAlignment(pickButton, QtCore.Qt.AlignTop)
        # body spacer
        spacer = QtWidgets.QSpacerItem(
            20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
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
