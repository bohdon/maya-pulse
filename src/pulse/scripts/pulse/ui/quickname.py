"""
Widget for quickly naming nodes using preset lists of
keywords, prefixes, and suffixes
"""

from functools import partial

import pymel.core as pm

from ..vendor.Qt import QtCore, QtWidgets
from .. import names
from .core import PulseWindow, BlueprintUIModel
from .gen.quick_name_editor import Ui_QuickNameEditor


class QuickNameWidget(QtWidgets.QWidget):
    """
    Widget for quickly naming nodes using preset lists of
    keywords, prefixes, and suffixes
    """

    def __init__(self, parent=None):
        super(QuickNameWidget, self).__init__(parent=parent)

        self.blueprint_model = BlueprintUIModel.getDefaultModel()

        # the blueprint config
        self.config = self._get_config()
        # the section of the config that contains naming keywords
        self.names_config = self.config.get('names', {})

        self.active_keyword = None

        self.prefix_btns: dict[str, QtWidgets.QPushButton] = {}
        self.keyword_btns: dict[str, QtWidgets.QPushButton] = {}
        self.suffix_btns: dict[str, QtWidgets.QPushButton] = {}

        self.ui = Ui_QuickNameEditor()
        self.ui.setupUi(self)
        self.setup_prefixes_ui(parent, self.ui.prefixes_vbox)
        self.setup_keywords_ui(parent, self.ui.keywords_vbox)
        self.setup_suffixes_ui(parent, self.ui.suffixes_vbox)

        self.ui.set_name_btn.clicked.connect(self._on_preview_btn_clicked)

        self.refresh_preview_label()
        self._update_help_text()

    def _update_help_text(self):
        msg_config = "Edit the blueprint config to modify naming keywords"
        msg_no_bp = "No Blueprint exists, using the default config"
        msg_no_config = "No Blueprint config was found"

        # TODO(bsayre): check whether the config is actually available and valid
        self.ui.help_label.setText(msg_config)

    def _get_config(self):
        config = self.blueprint_model.blueprint.get_config()
        return config if config else {}

    def setup_prefixes_ui(self, parent, layout):
        """
        Build the prefixes layout and button grid.
        Returns the layout.
        """
        prefixes = self.names_config.get('prefixes', {})

        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setObjectName("prefixBtnGrid")

        if prefixes:
            # create button for all prefixes
            x = 0
            y = 0
            for prefix in prefixes:
                name = prefix['name']
                btn = QtWidgets.QPushButton()
                btn.setText(name)
                btn.setCheckable(True)
                btn.clicked.connect(self._on_prefix_or_suffix_clicked)
                btn_grid.addWidget(btn, y, x, 1, 1)
                self.prefix_btns[name] = btn

                x += 1
                if x > 1:
                    x = 0
                    y += 1

            layout.addLayout(btn_grid)

        else:
            no_names_label = QtWidgets.QLabel(parent)
            no_names_label.setText('no prefixes')
            no_names_label.setProperty('cssClasses', 'help')
            layout.addWidget(no_names_label)

    def setup_suffixes_ui(self, parent, layout):
        """
        Build the suffixes layout and button grid.
        Returns the layout.
        """
        suffixes = self.names_config.get('suffixes', {})

        btn_grid = QtWidgets.QGridLayout()
        btn_grid.setObjectName("suffixBtnGrid")

        if suffixes:
            # create button for all suffixes
            x = 0
            y = 0
            for suffix in suffixes:
                name = suffix['name']
                btn = QtWidgets.QPushButton()
                btn.setText(name)
                btn.setCheckable(True)
                btn.clicked.connect(self._on_prefix_or_suffix_clicked)
                btn_grid.addWidget(btn, y, x, 1, 1)
                self.suffix_btns[name] = btn

                x += 1
                if x > 1:
                    x = 0
                    y += 1

            layout.addLayout(btn_grid)

        else:
            no_names_label = QtWidgets.QLabel(parent)
            no_names_label.setText('no suffixes')
            no_names_label.setProperty('cssClasses', 'help')
            layout.addWidget(no_names_label)

    def setup_keywords_ui(self, parent, layout):
        """
        Build the keywords layout and all categories and button grids.
        Returns the layout.
        """
        keywords = self.names_config.get('keywords', {})

        if keywords:
            cats_layout = QtWidgets.QHBoxLayout(parent)

            # create category and btn grid for all keywords
            cat_names = sorted(keywords.keys())
            for catName in cat_names:
                cat_keywords = keywords[catName]
                cat_layout = self.setupKeywordCategoryUi(parent, catName, cat_keywords)
                cats_layout.addLayout(cat_layout)

            layout.addLayout(cats_layout)

        else:
            no_names_label = QtWidgets.QLabel(parent)
            no_names_label.setText('no keywords')
            no_names_label.setProperty('cssClasses', 'help')
            layout.addWidget(no_names_label)

    def setupKeywordCategoryUi(self, parent, name: str, keywords: list[str]):
        """
        Build a keyword category layout and button grid.
        Returns the layout.

        Args:
            name: A string name of the category
            keywords: A list of string names of the keywords in the category
        """
        layout = QtWidgets.QVBoxLayout(parent)
        layout.setSpacing(2)

        cat_label = QtWidgets.QLabel(parent)
        cat_label.setText(names.toTitle(name))
        cat_label.setProperty('cssClasses', 'section-title')
        layout.addWidget(cat_label)

        # create button for all keywords
        for name in keywords:
            btn = QtWidgets.QPushButton()
            btn.setObjectName('keywordBtn_' + name)
            btn.setText(name)
            btn.setCheckable(True)
            btn.installEventFilter(self)
            btn.clicked.connect(partial(self._on_keyword_clicked, name))
            layout.addWidget(btn)
            self.keyword_btns[name] = btn

        spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        layout.addItem(spacer)

        return layout

    def eventFilter(self, widget, event):
        # if (event.type() == QtCore.QEvent.Enter and
        #         widget.objectName().startswith('keywordBtn_')):
        #     self.setActiveKeyword(widget.objectName()[11:])
        #     self.refreshPreviewLabel()
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def set_active_keyword(self, new_keyword):
        self.active_keyword = new_keyword
        self.refresh_preview_label()
        # color the clicked btn
        for btnKey, btn in self.keyword_btns.items():
            if btnKey == self.active_keyword:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

    def refresh_preview_label(self):
        """
        Update the name preview label to match the name
        that would be applied to a node.
        """
        self.ui.set_name_btn.setText(self.evaluate_name())

    def sort_ordered_names(self, names, category):
        """
        Sort a list of names using the defined orders in the config

        Args:
            names (list of str): A list of names
            category (str): The name category, e.g. 'prefixes'
        """
        cat_items = self.names_config.get(category, [])
        if not cat_items:
            return names

        name_pairs = []
        for name in names:
            is_found = False
            for item in cat_items:
                if item['name'] == name:
                    name_pairs.append((item['sort'], item['name']))
                    is_found = True
                    break
            if not is_found:
                # unknown name, sort order = 0
                name_pairs.append((0, name))
        name_pairs.sort()

        return [p[1] for p in name_pairs]

    def evaluate_prefix(self):
        """
        Return the combined prefix
        """
        # TODO: sort using config
        prefixes = []
        for name, btn in self.prefix_btns.items():
            if btn.isChecked():
                prefixes.append(name)
        prefixes = self.sort_ordered_names(prefixes, 'prefixes')
        return '_'.join(prefixes)

    def evaluate_suffix(self):
        """
        Return the combined suffix
        """
        # TODO: sort using config
        suffixes = []
        for name, btn in self.suffix_btns.items():
            if btn.isChecked():
                suffixes.append(name)
        suffixes = self.sort_ordered_names(suffixes, 'suffixes')
        return '_'.join(suffixes)

    def evaluate_name(self, include_number=False):
        """
        Return the fully combined name, including suffixes and prefixes
        """
        components = []
        # prefix
        prefix = self.evaluate_prefix()
        if prefix:
            components.append(prefix)
        # keyword
        keyword = self.active_keyword if self.active_keyword else '*'
        if include_number:
            num_fmt = self.names_config.get('numberFormat', '_{num:02}')
            keyword += num_fmt
        components.append(keyword)
        # suffix
        suffix = self.evaluate_suffix()
        if suffix:
            components.append(suffix)
        return '_'.join(components)

    def _on_prefix_or_suffix_clicked(self, *args, **kwargs):
        """
        Called when a prefix or suffix is clicked. Refreshes the preview.
        """
        self.refresh_preview_label()

    def _on_keyword_clicked(self, keyword):
        """
        Called when a keyword is clicked. Performs actual renaming of nodes.
        """
        # save the active keyword
        self.set_active_keyword(keyword)
        # rename the nodes
        self.rename_selected_nodes()

    def _on_preview_btn_clicked(self):
        """
        Called when the preview button is clicked. Performs renaming of nodes
        using the last used keyword. Does nothing if no keyword is set.
        """
        self.rename_selected_nodes()

    def rename_selected_nodes(self):
        """
        Perform the renaming of all selected nodes based on the
        active prefix, suffix, and selected keyword.
        """
        if self.active_keyword:
            sel = pm.selected()
            is_multiple_nodes = len(sel) > 1
            name = self.evaluate_name(include_number=is_multiple_nodes)
            for i, s in enumerate(pm.selected()):
                s.rename(name.format(num=i + 1))


class QuickNameWindow(PulseWindow):
    OBJECT_NAME = 'pulseQuickNameWindow'
    WINDOW_MODULE = 'pulse.ui.quickname'

    def __init__(self, parent=None):
        super(QuickNameWindow, self).__init__(parent=parent)

        self.setWindowTitle('Quick Name Editor')

        layout = QtWidgets.QVBoxLayout(self)
        layout.setMargin(0)
        self.setLayout(layout)

        widget = QuickNameWidget(self)
        layout.addWidget(widget)
