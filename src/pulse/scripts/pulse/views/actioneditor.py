
from functools import partial
from Qt import QtCore, QtWidgets, QtGui
import pymel.core as pm
import pymetanode as meta

import pulse
import pulse.names
from pulse.views.core import PulseWindow
from pulse.views import utils as viewutils
from pulse.views.actiontree import ActionTreeSelectionModel


__all__ = [
    'ActionAttrForm',
    'ActionEditorWidget',
    'ActionEditorWindow',
    'BatchActionEditorWidget',
    'BoolAttrForm',
    'BuildGroupEditorWidget',
    'BuildItemEditorWidget',
    'DefaultAttrForm',
    'NodeAttrForm',
    'OptionAttrForm',
]


ATTRFORM_TYPEMAP = {}


class ActionAttrForm(QtWidgets.QWidget):
    """
    The base class for all forms used to edit action attributes.
    Provides input validation and basic signals for keeping
    track of value changes.
    """

    LABEL_WIDTH = 150
    LABEL_HEIGHT = 20

    # valueChanged(newValue, isValueValid)
    valueChanged = QtCore.Signal(object, bool)

    @staticmethod
    def createAttrForm(attr, attrValue, parent=None):
        """
        Create a new ActionAttrForm of the appropriate
        type based on a BuildAction attribute.

        Args:
            attr: A dict representing the config of a BuildAction attribute
            attrValue: The current value of the attribute
        """
        attrType = attr['type']
        if attrType in ATTRFORM_TYPEMAP:
            return ATTRFORM_TYPEMAP[attrType](attr, attrValue, parent=parent)
        # fallback to the default widget
        return DefaultAttrForm(attr, attrValue)

    def __init__(self, attr, attrValue, parent=None):
        super(ActionAttrForm, self).__init__(parent=parent)
        # the config data of the attribute being edited
        self.attr = attr
        # the current value of the attribute
        self.attrValue = attrValue
        # build the ui
        self.setupUi(self)
        # update the ui with the current attr value
        self._setFormValue(self.attrValue)
        # update current valid state after ui has been setup
        self.isValueValid = self._isValueValid(self.attrValue)
        self._setUiValidState(self.isValueValid)

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
            return True
        else:
            return False

    def setupUi(self, parent):
        """
        Build the appropriate ui for the attribute
        """
        raise NotImplementedError

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
            self.valueChanged.emit(self.attrValue, self.isValueValid)
        else:
            self._setUiValidState(False)

    def _setUiValidState(self, isValid):
        if hasattr(self, 'frame'):
            if isValid:
                self.frame.setStyleSheet('')
            else:
                self.frame.setStyleSheet('.QFrame{ background-color: rgb(255, 0, 0, 35); }')

    def setupDefaultFormUi(self, parent):
        """
        Optional UI setup that builds a standardized layout.
        Includes a form layout and a label with the attributes name.
        Should be called at the start of setupUi if desired.
        """
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QtWidgets.QFrame(parent)
        layout.addWidget(self.frame)

        self.formLayout = QtWidgets.QFormLayout(self.frame)
        # margin that will give us some visible area of
        # the frame that can change color based on valid state
        self.formLayout.setContentsMargins(2, 2, 2, 2)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        # attribute name
        self.label = QtWidgets.QLabel(self.frame)
        self.label.setMinimumSize(QtCore.QSize(self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignTop)
        # add some space above the label so it lines up
        self.label.setMargin(2)
        self.label.setText(pulse.names.toTitle(self.attr['name']))
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)

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
        self.textEdit.textChanged.connect(self._valueChanged)

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

ATTRFORM_TYPEMAP['option'] = OptionAttrForm



class BoolAttrForm(ActionAttrForm):
    """
    A simple checkbox attribute form
    """

    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self.checkbox = QtWidgets.QCheckBox(parent)
        self.checkbox.setMinimumHeight(self.LABEL_HEIGHT)
        self.checkbox.stateChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.checkbox)

    def _setFormValue(self, attrValue):
        self.checkbox.setChecked(attrValue)

    def _getFormValue(self):
        return self.checkbox.isChecked()

    def _isValueTypeValid(self, attrValue):
        return attrValue is True or attrValue is False

ATTRFORM_TYPEMAP['bool'] = BoolAttrForm


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
        hlayout.addWidget(self.listWidget)

        self.pickButton = QtWidgets.QPushButton(parent)
        self.pickButton.setIcon(viewutils.getIcon("select.png"))
        self.pickButton.setFixedSize(QtCore.QSize(20, 20))
        self.pickButton.clicked.connect(self.setFromSelection)
        hlayout.addWidget(self.pickButton)
        hlayout.setAlignment(self.pickButton, QtCore.Qt.AlignTop)

        self.setDefaultFormLayout(hlayout)

    def _setFormValue(self, attrValue):
        while self.listWidget.takeItem(0):
            pass
        if attrValue:
            self.listWidget.addItem(QtWidgets.QListWidgetItem(attrValue.nodeName()))

    def _getFormValue(self):
        return self.attrValue

    def _isValueTypeValid(self, attrValue):
        return attrValue is None or isinstance(attrValue, pm.nt.DependNode)

    def setFromSelection(self):
        sel = pm.selected()
        if sel:
            self.setAttrValue(sel[0])
            self.valueChanged.emit(self.attrValue, self.isValueValid)
        else:
            self.setAttrValue(None)


ATTRFORM_TYPEMAP['node'] = NodeAttrForm



class BuildItemEditorWidget(QtWidgets.QWidget):
    """
    Base class for a form for editing any type of BuildItem
    """

    @staticmethod
    def createItemWidget(buildItem, parent=None):
        if isinstance(buildItem, pulse.BuildGroup):
            return BuildGroupEditorWidget(buildItem, parent=parent)
        elif isinstance(buildItem, pulse.BuildAction):
            return ActionEditorWidget(buildItem, parent=parent)
        elif isinstance(buildItem, pulse.BatchBuildAction):
            return BatchActionEditorWidget(buildItem, parent=parent)
        return QtWidgets.QWidget(parent=parent)

    def __init__(self, buildItem, parent=None):
        super(BuildItemEditorWidget, self).__init__(parent=parent)
        self.buildItem = buildItem
        self.setupUi(self)

    def setupUi(self, parent):
        """
        Create the UI that is common to all BuildItem editors, including
        a basic header and layout.
        """
        # main layout containing header and body
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(12)

        # header frame
        headerFrame = QtWidgets.QFrame(parent)
        headerFrame.setStyleSheet(".QFrame{ background-color: rgba(255, 255, 255, 30); }")
        layout.addWidget(headerFrame)
        # header layout
        headerLay = QtWidgets.QHBoxLayout(headerFrame)
        # display name label
        font = QtGui.QFont()
        font.setWeight(75)
        font.setBold(True)
        self.displayNameLabel = QtWidgets.QLabel(headerFrame)
        self.displayNameLabel.setFont(font)
        self.displayNameLabel.setText(self.buildItem.getDisplayName())
        headerLay.addWidget(self.displayNameLabel)

        # body layout
        bodyLay = QtWidgets.QVBoxLayout(parent)
        layout.addLayout(bodyLay)
        # main body content layout
        self.layout = QtWidgets.QVBoxLayout(parent)
        # no spacing between attributes
        self.layout.setSpacing(0)
        bodyLay.addLayout(self.layout)
        # body spacer
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        bodyLay.addItem(spacer)

        self.setupContentUi(parent)

    def setupContentUi(self, parent):
        pass




class BuildGroupEditorWidget(BuildItemEditorWidget):
    pass


class ActionEditorWidget(BuildItemEditorWidget):
    def setupContentUi(self, parent):
        for attr in self.buildItem.config['attrs']:
            attrValue = getattr(self.buildItem, attr['name'])
            attrForm = ActionAttrForm.createAttrForm(attr, attrValue, parent=parent)
            attrForm.valueChanged.connect(partial(self.attrValueChanged, attrForm))
            self.layout.addWidget(attrForm)

    def attrValueChanged(self, attrForm, attrValue, isValueValid):
        setattr(self.buildItem, attrForm.attr['name'], attrValue)


class BatchActionEditorWidget(BuildItemEditorWidget):
    pass






class ActionEditorWindow(PulseWindow):

    OBJECT_NAME = 'pulseActionEditorWindow'

    def __init__(self, parent=None):
        super(ActionEditorWindow, self).__init__(parent=parent)

        self.setWindowTitle('Pulse Action Editor')

        self.buildItems = []

        widget = QtWidgets.QWidget(self)
        self.setCentralWidget(widget)
        self.setupUi(widget)

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

        self.layout = QtWidgets.QVBoxLayout(self.scrollWidget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.scrollWidget.setLayout(self.layout)

    def selectionChanged(self, selected, deselected):
        self.clearItemsUi()
        self.buildItems = [i.internalPointer().buildItem for i in self.selectionModel.selectedIndexes()]
        self.setupItemsUi(self.scrollWidget)

    def clearItemsUi(self):
        while True:
            item = self.layout.takeAt(0)
            if item:
                w = item.widget().setParent(None)
            else:
                break

    def setupItemsUi(self, parent):
        for buildItem in self.buildItems[:1]:
            itemWidget = BuildItemEditorWidget.createItemWidget(buildItem, parent=parent)
            self.layout.addWidget(itemWidget)
