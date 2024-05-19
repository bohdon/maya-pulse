#!/usr/bin/env bash

# Utility for compiling Qt uis and resources to python code.

# Requires pyside6-uic.exe and pyside6-rcc.exe which can be installed via:
#   pip install pyside6
# The exes will be installed to <python>/Scripts.

# Qt Designer is included with the pyside6 package:
#   site-packages/PySide6/designer.exe

script_dir=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

# the path to output build files to:
UI_PYTHON_PATH=$script_dir/../src/pulse/scripts/pulse/ui/gen
# the import path to use instead of 'PySide6'
QT_IMPORT="...vendor.Qt"

# helper function that also echoes the command being run
build_qt() {
    echo "Building " $2

    py_path="$UI_PYTHON_PATH/$3.py"
    $1 $script_dir/$2 > $py_path

    # convert imports to Qt.py
    sed -i -e "s/PySide6/${QT_IMPORT}/" $py_path
}

# compile a .ui to a .py
build_ui() {
    build_qt "pyside6-uic -g python --from-imports" "$1.ui" "$1"
}

# compile a .qrc to a .py
build_res() {
    build_qt "pyside6-rcc -g python" $1 $2
}

# build all UIs
echo "Building ui files..."
build_ui action_editor
build_ui action_palette
build_ui action_tree
build_ui build_action_data_form
build_ui build_step_form
build_ui design_toolkit
build_ui designpanel_general
build_ui designpanel_joint_orients
build_ui designpanel_joints
build_ui designpanel_layout
build_ui designpanel_symmetry
build_ui designpanel_weights
build_ui layout_link_editor
build_ui layout_link_info_widget
build_ui main_editor
build_ui main_settings
build_ui main_toolbar
build_ui quick_color_editor
build_ui quick_name_editor
# build anim UIs
build_ui anim_picker
build_ui anim_tools

# build all resources
echo "Building resource files..."
build_res icons/icons.qrc icons_rc
