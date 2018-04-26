
from functools import partial
import pymel.core as pm

import pulse.names
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui
from pulse.views.core import buttonCommand
from pulse.views.core import PulseWindow
from pulse.views.core import BlueprintUIModel
from pulse.views.style import UIColors
from .core import DesignViewPanel

__all__ = [
    "NamesPanel",
]


class NamesPanel(DesignViewPanel):

    def __init__(self, parent):
        super(NamesPanel, self).__init__(parent=parent)

    def getPanelDisplayName(self):
        return "Names"

    def setupPanelUi(self, parent):
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setMargin(0)

        frame = self.createPanelFrame(parent)
        layout.addWidget(frame)

        btnLayout = QtWidgets.QVBoxLayout(frame)
        btnLayout.setMargin(0)
        btnLayout.setSpacing(2)

        quickNameWindowBtn = QtWidgets.QPushButton(frame)
        quickNameWindowBtn.setText("Quick Name Editor")
        quickNameWindowBtn.clicked.connect(buttonCommand(QuickNameEditor.createAndShow))
        btnLayout.addWidget(quickNameWindowBtn)


class QuickNameWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(QuickNameWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()
        self.loadConfig()

        self.activeKeyword = None

        if self.config:
            self.setupUi(self)
            self.refreshPreviewLabel()

    def loadConfig(self):
        if self.blueprintModel.blueprint is not None:
            self.config = self.blueprintModel.blueprint.loadBlueprintConfig()
            print(self.blueprintModel.blueprint.configFile)
        else:
            self.config = None

    def setupUi(self, parent):
        """
        Build the UI for the main body of the window
        """
        layout = QtWidgets.QVBoxLayout(parent)

        # preview text
        self.namePreviewBtn = QtWidgets.QPushButton(parent)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setBold(True)
        self.namePreviewBtn.setFont(font)
        # self.namePreviewBtn.setAlignment(QtCore.Qt.AlignCenter)
        self.namePreviewBtn.setContentsMargins(10, 10, 10, 10)
        # self.namePreviewBtn.setStyleSheet(
        #     'background-color: rgba(0, 0, 0, 40); border-radius: 2px')
        self.namePreviewBtn.clicked.connect(self.onPreviewBtnClicked)
        layout.addWidget(self.namePreviewBtn)

        # prefixes / suffixes
        self.prefixSuffixLayout = QtWidgets.QHBoxLayout()

        prefixLayout = self.setupPrefixesUi(parent)
        self.prefixSuffixLayout.addLayout(prefixLayout)

        suffixLayout = self.setupSuffixesUi(parent)
        self.prefixSuffixLayout.addLayout(suffixLayout)

        layout.addLayout(self.prefixSuffixLayout)

        # keywords
        keywordsLayout = self.setupKeywordsUi(parent)
        layout.addLayout(keywordsLayout)

        layout.setStretch(2, 1)

    def setupPrefixesUi(self, parent):
        """
        Build the prefixes layout and button grid.
        Returns the layout.
        """
        prefixLayout = QtWidgets.QVBoxLayout(parent)

        prefixesLabel = self.createLabel(parent, "Prefixes", bold=True)
        prefixLayout.addWidget(prefixesLabel)

        self.prefixBtnGrid = QtWidgets.QGridLayout()
        self.prefixBtnGrid.setObjectName("prefixBtnGrid")

        # create button for all prefixes
        self.prefixBtns = {}
        prefixes = self.config['names']['prefixes']
        x = 0
        y = 0
        for prefix in prefixes:
            name = prefix['name']
            btn = QtWidgets.QPushButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.clicked.connect(self.onPrefixOrSuffixClicked)
            self.prefixBtnGrid.addWidget(btn, y, x, 1, 1)
            self.prefixBtns[name] = btn

            x += 1
            if x > 1:
                x = 0
                y += 1

        prefixLayout.addLayout(self.prefixBtnGrid)

        spacerItem = QtWidgets.QSpacerItem(
            0, 2, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        prefixLayout.addItem(spacerItem)

        return prefixLayout

    def setupSuffixesUi(self, parent):
        """
        Build the suffixes layout and button grid.
        Returns the layout.
        """
        suffixLayout = QtWidgets.QVBoxLayout(parent)

        suffixesLabel = self.createLabel(parent, "Suffixes", bold=True)
        suffixLayout.addWidget(suffixesLabel)

        self.suffixBtnGrid = QtWidgets.QGridLayout()
        self.suffixBtnGrid.setObjectName("suffixBtnGrid")

        # create button for all suffixes
        self.suffixBtns = {}
        suffixes = self.config['names']['suffixes']
        x = 0
        y = 0
        for suffix in suffixes:
            name = suffix['name']
            btn = QtWidgets.QPushButton()
            btn.setText(name)
            btn.setCheckable(True)
            btn.clicked.connect(self.onPrefixOrSuffixClicked)
            self.suffixBtnGrid.addWidget(btn, y, x, 1, 1)
            self.suffixBtns[name] = btn

            x += 1
            if x > 1:
                x = 0
                y += 1

        suffixLayout.addLayout(self.suffixBtnGrid)

        spacerItem = QtWidgets.QSpacerItem(
            0, 2, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        suffixLayout.addItem(spacerItem)

        return suffixLayout

    def setupKeywordsUi(self, parent):
        """
        Build the keywords layout and all categories and button grids.
        Returns the layout.
        """
        keywordsLayout = QtWidgets.QVBoxLayout(parent)

        keywordsLabel = self.createLabel(parent, "Names", bold=True)
        keywordsLayout.addWidget(keywordsLabel)

        scrollArea = QtWidgets.QScrollArea(parent)
        scrollArea.setFrameShape(QtWidgets.QScrollArea.NoFrame)
        scrollArea.setWidgetResizable(True)
        scrollWidget = QtWidgets.QWidget()

        scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)

        # create category and btn grid for all keywords
        self.keywordBtns = {}
        keywords = self.config['names']['keywords']
        categoryNames = sorted(keywords.keys())
        for catName in categoryNames:
            catKeywords = keywords[catName]
            catLayout = self.setupKeywordCategoryUi(scrollWidget, catName, catKeywords)
            scrollLayout.addLayout(catLayout)

        keywordsSpacer = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        scrollLayout.addItem(keywordsSpacer)

        scrollArea.setWidget(scrollWidget)
        keywordsLayout.addWidget(scrollArea)

        return keywordsLayout

    def setupKeywordCategoryUi(self, parent, name, keywords):
        """
        Build a keyword category layout and button grid.
        Returns the layout.

        Args:
            name: A string name of the category
            keywords: A list of string names of the keywords in the category
        """
        layout = QtWidgets.QVBoxLayout(parent)

        catLabel = self.createLabel(parent, pulse.names.toTitle(name))
        catLabel.setStyleSheet(
            'background-color: rgba(255, 255, 255, 5); border-radius: 2px')
        layout.addWidget(catLabel)

        catBtnGrid = QtWidgets.QGridLayout()

        # create button for all keywords
        x = 0
        y = 0
        for name in keywords:
            btn = QtWidgets.QPushButton()
            btn.setObjectName('keywordBtn_' + name)
            btn.setText(name)
            catBtnGrid.addWidget(btn, y, x, 1, 1)
            self.keywordBtns[name] = btn
            btn.installEventFilter(self)
            btn.clicked.connect(partial(self.onKeywordClicked, name))

            x += 1
            if x > 3:
                x = 0
                y += 1

        if y == 0:
            while x <= 3:
                spacer = QtWidgets.QLabel()
                catBtnGrid.addWidget(spacer, y, x, 1, 1)
                x += 1

        layout.addLayout(catBtnGrid)
        return layout

    def createLabel(self, parent, text, bold=False):
        label = QtWidgets.QLabel(parent)
        label.setText(text)
        if bold:
            font = QtGui.QFont()
            font.setWeight(75)
            font.setBold(True)
            label.setFont(font)
        label.setMinimumHeight(20)
        label.setContentsMargins(10, 2, 2, 2)
        label.setStyleSheet('background-color: rgba(0, 0, 0, 40); border-radius: 2px')
        return label

    def eventFilter(self, widget, event):
        # if (event.type() == QtCore.QEvent.Enter and
        #         widget.objectName().startswith('keywordBtn_')):
        #     self.setActiveKeyword(widget.objectName()[11:])
        #     self.refreshPreviewLabel()
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def setActiveKeyword(self, newKeyword):
        self.activeKeyword = newKeyword
        self.refreshPreviewLabel()
        # color the clicked btn
        for btnKey, btn in self.keywordBtns.iteritems():
            if btnKey == self.activeKeyword:
                btn.setStyleSheet(UIColors.asBGColor(UIColors.GREEN))
            else:
                btn.setStyleSheet('')

    def refreshPreviewLabel(self):
        """
        Update the name preview label to match the name
        that would be applied to a node.
        """
        self.namePreviewBtn.setText(self.evaluateName())

    def evaluatePrefix(self):
        """
        Return the combined prefix
        """
        # TODO: sort using config
        prefixes = []
        for name, btn in self.prefixBtns.iteritems():
            if btn.isChecked():
                prefixes.append(name)
        return '_'.join(prefixes)

    def evaluateSuffix(self):
        """
        Return the combined suffix
        """
        # TODO: sort using config
        suffixes = []
        for name, btn in self.suffixBtns.iteritems():
            if btn.isChecked():
                suffixes.append(name)
        return '_'.join(suffixes)

    def evaluateName(self):
        """
        Return the fully combined name, including suffixes and prefixes
        """
        components = []
        # prefix
        prefix = self.evaluatePrefix()
        if prefix:
            components.append(prefix)
        # keyword
        components.append(self.activeKeyword if self.activeKeyword else '*')
        # suffix
        suffix = self.evaluateSuffix()
        if suffix:
            components.append(suffix)
        return '_'.join(components)

    def onPrefixOrSuffixClicked(self, *args, **kwargs):
        """
        Called when a prefix or suffix is clicked. Refreshes the preview.
        """
        self.refreshPreviewLabel()

    def onKeywordClicked(self, keyword):
        """
        Called when a keyword is clicked. Performs actual renaming of nodes.
        """
        # save the active keyword
        self.setActiveKeyword(keyword)
        # rename the nodes
        self.renameSelectedNodes()

    def onPreviewBtnClicked(self):
        """
        Called when the preview button is clicked. Performs renaming of nodes
        using the last used keyword. Does nothing if no keyword is set.
        """
        self.renameSelectedNodes()

    def renameSelectedNodes(self):
        """
        Perform the renaming of all selected nodes based on the
        active prefix, suffix, and selected keyword.
        """
        if self.activeKeyword:
            name = self.evaluateName()
            for s in pm.selected():
                s.rename(name)


class QuickNameEditor(PulseWindow):

    OBJECT_NAME = 'pulseQuickNameEditor'

    def __init__(self, parent=None):
        super(QuickNameEditor, self).__init__(parent=parent)

        self.setWindowTitle('Quick Name Editor')

        widget = QuickNameWidget(self)
        widget.setMinimumSize(400, 300)
        self.setCentralWidget(widget)
