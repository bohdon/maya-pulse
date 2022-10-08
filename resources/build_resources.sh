#!/usr/bin/env bash

# Utility for compiling Qt uis and resources to python code.

# Requires pyside2-uic and pyside2-rcc which can be installed via:
#   pip install pyside2

# Qt Designer can be installed with:
#   pip install qt5-tools
# and browsing to <python>\Lib\site-packages\qt5_applications\Qt\bin\designer.exe

# the path to output build files to:
UI_PYTHON_PATH=../src/pulse/scripts/pulse/ui/gen

# helper function that also echoes the command being run
build_qt() {
    echo "Building " $2

    $1 $2 >"$UI_PYTHON_PATH/$3.py"
}

# compile a .ui to a .py
build_ui() {
    build_qt "pyside2-uic --from-imports" "$1.ui" "$1"
}

# compile a .qrc to a .py
build_res() {
    build_qt "pyside2-rcc" "$1.qrc" "$1"
}

# build all UIs
echo "Building ui files..."
build_ui quick_name_editor
build_ui layout_link_editor

# build all resources
echo "Building resource files..."
