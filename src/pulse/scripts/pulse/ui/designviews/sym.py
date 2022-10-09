from ...vendor.Qt import QtWidgets
from ...prefs import optionVarProperty
from ... import editorutils
from ..utils import undoAndRepeatPartial as cmd

from ..gen.designpanel_symmetry import Ui_SymmetryDesignPanel


class SymmetryDesignPanel(QtWidgets.QWidget):
    include_children = optionVarProperty('pulse.editor.mirrorIncludeChildren', True)
    mirror_transforms = optionVarProperty('pulse.editor.mirrorTransforms', True)
    mirror_parenting = optionVarProperty('pulse.editor.mirrorParenting', True)
    mirror_links = optionVarProperty('pulse.editor.mirrorLinks', True)
    mirror_appearance = optionVarProperty('pulse.editor.mirrorAppearance', True)
    mirror_curve_shapes = optionVarProperty('pulse.editor.mirrorCurveShapes', True)
    allow_create = optionVarProperty('pulse.editor.mirrorAllowCreate', True)

    def set_include_children(self, value):
        self.include_children = True if value > 0 else False

    def set_mirror_transforms(self, value):
        self.mirror_transforms = True if value > 0 else False

    def set_mirror_parenting(self, value):
        self.mirror_parenting = True if value > 0 else False

    def set_mirror_links(self, value):
        self.mirror_links = True if value > 0 else False

    def set_mirror_appearance(self, value):
        self.mirror_appearance = True if value > 0 else False

    def set_mirror_curve_shapes(self, value):
        self.mirror_curve_shapes = True if value > 0 else False

    def set_allow_create(self, value):
        self.allow_create = True if value > 0 else False

    def __init__(self, parent):
        super(SymmetryDesignPanel, self).__init__(parent)

        self.ui = Ui_SymmetryDesignPanel()
        self.ui.setupUi(self)

        self.ui.include_children_check.setChecked(self.include_children)
        self.ui.allow_create_check.setChecked(self.allow_create)
        self.ui.transforms_check.setChecked(self.mirror_transforms)
        self.ui.parenting_check.setChecked(self.mirror_parenting)
        self.ui.links_check.setChecked(self.mirror_links)
        self.ui.appearance_check.setChecked(self.mirror_appearance)
        self.ui.curve_shapes_check.setChecked(self.mirror_curve_shapes)

        self.ui.include_children_check.stateChanged.connect(self.set_include_children)
        self.ui.allow_create_check.stateChanged.connect(self.set_allow_create)
        self.ui.transforms_check.stateChanged.connect(self.set_mirror_transforms)
        self.ui.parenting_check.stateChanged.connect(self.set_mirror_parenting)
        self.ui.links_check.stateChanged.connect(self.set_mirror_links)
        self.ui.appearance_check.stateChanged.connect(self.set_mirror_appearance)
        self.ui.curve_shapes_check.stateChanged.connect(self.set_mirror_curve_shapes)

        self.ui.pair_btn.clicked.connect(cmd(editorutils.pairSelected))
        self.ui.unpair_btn.clicked.connect(cmd(editorutils.unpairSelected))
        self.ui.mirror_btn.clicked.connect(self.mirror_selected)

    def mirror_selected(self):
        kw = dict(
            recursive=self.include_children,
            create=self.allow_create,
            curveShapes=self.mirror_curve_shapes,
            links=self.mirror_links,
            reparent=self.mirror_parenting,
            transform=self.mirror_transforms,
            appearance=self.mirror_appearance,
        )
        cmd(editorutils.mirrorSelected, **kw)()