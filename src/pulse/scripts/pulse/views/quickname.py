"""
Widget for quickly naming nodes using preset lists of
keywords, prefixes, and suffixes
"""


from functools import partial
import pymel.core as pm
from pulse.vendor.Qt import QtCore, QtWidgets, QtGui

import pulse.core
import pulse.names
from .core import PulseWindow, BlueprintUIModel
from .utils import undoAndRepeatPartial as cmd
from . import style

__all__ = [
    "QuickNameWidget",
    "QuickNameWindow",
]


class QuickNameWidget(QtWidgets.QWidget):
    """
    Widget for quickly naming nodes using preset lists of
    keywords, prefixes, and suffixes
    """

    def __init__(self, parent=None):
        super(QuickNameWidget, self).__init__(parent=parent)

        self.blueprintModel = BlueprintUIModel.getDefaultModel()

        # the blueprint config
        self.config = self._getConfig()
        # the section of the config that contains naming keywoards
        self.namesConfig = self.config.get('names', {})

        self.activeKeyword = None
        self.activeKeywordColor = style.UIColors.DARKGRAY

        self.setupUi(self)
        self.refreshPreviewLabel()

        if True:  # TODO: replace with 'is blueprint initialized' or similar
            self.helpText.setText(
                "Edit the Blueprint Config to modify naming keywords")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.HELPTEXT))
        elif self.config:
            self.helpText.setText(
                "No Blueprint exists, using the default config")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.WARNING))
        else:
            self.helpText.setText(
                "No Blueprint config was found")
            self.helpText.setStyleSheet(
                style.UIColors.asFGColor(style.UIColors.ERROR))

    def _getConfig(self):
        # if self.blueprintModel.blueprintExists():
        if True:
            config = self.blueprintModel.blueprint.getConfig()
        else:
            config = pulse.core.blueprints.loadDefaultConfig()
        return config if config else {}

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
        self.namePreviewBtn.setStatusTip(
            "The current constructed name. "
            "Click to apply to the selected node")
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

        # help text
        self.helpText = QtWidgets.QLabel()
        self.helpText.setFont(style.UIFonts.getHelpTextFont())
        layout.addWidget(self.helpText)

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
        prefixes = self.namesConfig.get('prefixes', {})
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
        suffixes = self.namesConfig.get('suffixes', {})
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
        keywords = self.namesConfig.get('keywords', {})
        categoryNames = sorted(keywords.keys())
        for catName in categoryNames:
            catKeywords = keywords[catName]
            catLayout = self.setupKeywordCategoryUi(
                scrollWidget, catName, catKeywords)
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
        label.setStyleSheet(
            'background-color: rgba(0, 0, 0, 40); border-radius: 2px')
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
                btn.setStyleSheet(
                    style.UIColors.asBGColor(self.activeKeywordColor))
            else:
                btn.setStyleSheet('')

    def refreshPreviewLabel(self):
        """
        Update the name preview label to match the name
        that would be applied to a node.
        """
        self.namePreviewBtn.setText(self.evaluateName())

    def sortOrderedNames(self, names, category):
        """
        Sort a list of names using the defined orders in the config

        Args:
            names (list of str): A list of names
            category (str): The name category, e.g. 'prefixes'
        """
        categoryItems = self.namesConfig.get(category, [])
        if not categoryItems:
            return names

        namePairs = []
        for name in names:
            isFound = False
            for item in categoryItems:
                if item['name'] == name:
                    namePairs.append((item['sort'], item['name']))
                    isFound = True
                    break
            if not isFound:
                # unknown name, sort order = 0
                namePairs.append((0, name))
        namePairs.sort()

        return [p[1] for p in namePairs]

    def evaluatePrefix(self):
        """
        Return the combined prefix
        """
        # TODO: sort using config
        prefixes = []
        for name, btn in self.prefixBtns.iteritems():
            if btn.isChecked():
                prefixes.append(name)
        prefixes = self.sortOrderedNames(prefixes, 'prefixes')
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
        suffixes = self.sortOrderedNames(suffixes, 'suffixes')
        return '_'.join(suffixes)

    def evaluateName(self, includeNumber=False):
        """
        Return the fully combined name, including suffixes and prefixes
        """
        components = []
        # prefix
        prefix = self.evaluatePrefix()
        if prefix:
            components.append(prefix)
        # keyword
        keyword = self.activeKeyword if self.activeKeyword else '*'
        if includeNumber:
            keyword += '{num}'
        components.append(keyword)
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
            sel = pm.selected()
            isMultipleNodes = len(sel) > 1
            name = self.evaluateName(includeNumber=isMultipleNodes)
            for i, s in enumerate(pm.selected()):
                s.rename(name.format(num=i+1))


class QuickNameWindow(PulseWindow):

    OBJECT_NAME = 'pulseQuickNameWindow'
    PREFERRED_SIZE = QtCore.QSize(400, 300)
    STARTING_SIZE = QtCore.QSize(400, 300)
    MINIMUM_SIZE = QtCore.QSize(400, 300)

    WINDOW_MODULE = 'pulse.views.quickname'

    def __init__(self, parent=None):
        super(QuickNameWindow, self).__init__(parent=parent)

        self.setWindowTitle('Quick Name Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = QuickNameWidget(self)
        layout.addWidget(widget)
