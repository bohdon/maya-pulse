
from functools import partial
from Qt import QtCore, QtWidgets, QtGui
import pymetanode as meta

import pulse
import pulse.names
from pulse.views.core import PulseWindow
from pulse.views.actiontree import ActionTreeSelectionModel


__all__ = [
    'ActionAttrForm',
    'ActionEditorWidget',
    'ActionEditorWindow',
    'BatchActionEditorWidget',
    'BuildGroupEditorWidget',
    'BuildItemEditorWidget',
    'DefaultAttrForm',
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
            self.valueChanged.emit(self.attrValue, self.isValueValid)

    def setupDefaultFormUi(self, parent):
        """
        Optional UI setup that builds a standardized layout.
        Includes a form layout and a label with the attributes name.
        Should be called at the start of setupUi if desired.
        """
        self.formLayout = QtWidgets.QFormLayout(parent)
        self.formLayout.setContentsMargins(0,0,0,0)
        self.formLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop|QtCore.Qt.AlignTrailing)
        self.formLayout.setHorizontalSpacing(10)

        # attribute name
        self.label = QtWidgets.QLabel(parent)
        self.label.setMinimumSize(QtCore.QSize(self.LABEL_WIDTH, self.LABEL_HEIGHT))
        self.label.setText(pulse.names.toTitle(self.attr['name']))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)

    def setDefaultFormWidget(self, widget):
        """
        Set the attribute field widget for the default form layout.
        Requires `setupDefaultFormUi` to be used.
        """
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, widget)




class DefaultAttrForm(ActionAttrForm):
    """
    A catchall attribute widget that can handle any attribute type
    by leveraging pymetanode serialization. Provides a text field
    where values can typed representing serialized string data.
    """
    def setupUi(self, parent):
        self.setupDefaultFormUi(parent)

        self._didFailDecode = False

        self.textEdit = QtWidgets.QLineEdit(parent)
        self.textEdit.setStyleSheet('font: 8pt "Consolas Spaced";')
        self.textEdit.textChanged.connect(self._valueChanged)

        self.setDefaultFormWidget(self.textEdit)

    def _setFormValue(self, attrValue):
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
        # spacing between attributes
        self.layout.setSpacing(4)
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
        print(self.buildItems)
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
