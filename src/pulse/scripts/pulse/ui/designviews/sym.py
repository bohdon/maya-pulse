from .. import utils as viewutils
from ..core import PulsePanelWidget
from ..utils import undoAndRepeatPartial as cmd
from ... import editorutils
from ...prefs import optionVarProperty
from ...vendor.Qt import QtWidgets


class SymmetryPanel(PulsePanelWidget):
    mirrorRecursive = optionVarProperty(
        'pulse.editor.mirrorRecursive', True)
    mirrorTransforms = optionVarProperty(
        'pulse.editor.mirrorTransforms', True)
    mirrorParenting = optionVarProperty(
        'pulse.editor.mirrorParenting', True)
    mirrorLinks = optionVarProperty(
        'pulse.editor.mirrorLinks', True)
    mirrorAppearance = optionVarProperty(
        'pulse.editor.mirrorAppearance', True)
    mirrorCurveShapes = optionVarProperty(
        'pulse.editor.mirrorCurveShapes', True)
    mirrorAllowCreate = optionVarProperty(
        'pulse.editor.mirrorAllowCreate', True)

    def setMirrorRecursive(self, value):
        self.mirrorRecursive = True if value > 0 else False

    def setMirrorTransforms(self, value):
        self.mirrorTransforms = True if value > 0 else False

    def setMirrorParenting(self, value):
        self.mirrorParenting = True if value > 0 else False

    def setMirrorLinks(self, value):
        self.mirrorLinks = True if value > 0 else False

    def setMirrorAppearance(self, value):
        self.mirrorAppearance = True if value > 0 else False

    def setMirrorCurveShapes(self, value):
        self.mirrorCurveShapes = True if value > 0 else False

    def setMirrorAllowCreate(self, value):
        self.mirrorAllowCreate = True if value > 0 else False

    def __init__(self, parent):
        super(SymmetryPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Symmetry"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        self.setupContentUi(frame)

    def setupContentUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        # mirror settings
        # ---------------

        settingsGrid = QtWidgets.QGridLayout(parent)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Include All Children")
        check.setStatusTip(
            "Recursively mirror the selected nodes and all of their children")
        check.setChecked(self.mirrorRecursive)
        check.stateChanged.connect(
            self.setMirrorRecursive)
        settingsGrid.addWidget(check, 0, 0, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Allow Node Creation")
        check.setStatusTip(
            "Allow the creation of nodes when mirroring recursively")
        check.setChecked(self.mirrorAllowCreate)
        check.stateChanged.connect(
            self.setMirrorAllowCreate)
        settingsGrid.addWidget(check, 1, 0, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Transforms")
        check.setStatusTip(
            "Mirror the transform matrices of the nodes")
        check.setChecked(self.mirrorTransforms)
        check.stateChanged.connect(
            self.setMirrorTransforms)
        settingsGrid.addWidget(check, 2, 0, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Parenting")
        check.setStatusTip(
            "Mirror the parenting structure of the nodes")
        check.setChecked(self.mirrorParenting)
        check.stateChanged.connect(
            self.setMirrorParenting)
        settingsGrid.addWidget(check, 3, 0, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Links")
        check.setStatusTip(
            "Mirror the layout links of the nodes, allowing mirrored nodes to snap to their linked mirror nodes")
        check.setChecked(self.mirrorLinks)
        check.stateChanged.connect(
            self.setMirrorLinks)
        settingsGrid.addWidget(check, 4, 0, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Appearance")
        check.setStatusTip(
            "Mirror the name and color of the nodes")
        check.setChecked(self.mirrorAppearance)
        check.stateChanged.connect(
            self.setMirrorAppearance)
        settingsGrid.addWidget(check, 0, 1, 1, 1)

        check = QtWidgets.QCheckBox(parent)
        check.setText("Curve Shapes")
        check.setStatusTip(
            "Mirror curve shapes")
        check.setChecked(self.mirrorCurveShapes)
        check.stateChanged.connect(
            self.setMirrorCurveShapes)
        settingsGrid.addWidget(check, 1, 1, 1, 1)
        layout.addLayout(settingsGrid)

        # mirror axis

        # mirror mode toggle

        # mirror actions
        # --------------
        gridLayout = QtWidgets.QGridLayout(parent)
        gridLayout.setMargin(0)
        gridLayout.setSpacing(2)

        pairBtn = QtWidgets.QPushButton(parent)
        pairBtn.setText("Pair")
        pairBtn.setStatusTip(
            "Pair the two selected nodes as mirroring counterparts")
        pairBtn.clicked.connect(cmd(editorutils.pairSelected))

        unpairBtn = QtWidgets.QPushButton(parent)
        unpairBtn.setText("Unpair")
        unpairBtn.setStatusTip(
            "Unpair the selected node or nodes (can be many at once)")
        unpairBtn.clicked.connect(cmd(editorutils.unpairSelected))

        mirrorBtn = QtWidgets.QPushButton(parent)
        mirrorBtn.setText("Mirror")
        mirrorBtn.setStatusTip(
            "Mirror the selected nodes using the current options")
        mirrorBtn.clicked.connect(self.mirrorSelected)

        gridItems = [
            [pairBtn, unpairBtn],
        ]
        viewutils.addItemsToGrid(gridLayout, gridItems)
        gridLayout.addWidget(mirrorBtn, 2, 0, 1, 2)
        layout.addLayout(gridLayout)

    def mirrorSelected(self):
        kw = dict(
            recursive=self.mirrorRecursive,
            create=self.mirrorAllowCreate,
            curveShapes=self.mirrorCurveShapes,
            links=self.mirrorLinks,
            reparent=self.mirrorParenting,
            transform=self.mirrorTransforms,
            appearance=self.mirrorAppearance,
        )
        cmd(editorutils.mirrorSelected, **kw)()
