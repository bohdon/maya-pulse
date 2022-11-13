#! /bin/bash

PROJECT_NAME="maya-pulse"
PACKAGE_NAME="pulse"


if [[ ! "$MAYA_MODULES_INSTALL_PATH" ]]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        MAYA_MODULES_INSTALL_PATH="$HOME/Library/Preferences/Autodesk/maya/modules"
    elif [[ "$(expr substr $(uname -s) 1 5)" == "Linux" ]]; then
        MAYA_MODULES_INSTALL_PATH="/usr/autodesk/userconfig/maya/modules"
    elif [[ "$(expr substr $(uname -s) 1 5)" == "MINGW" ]]; then
        IS_WINDOWS=1
        MAYA_MODULES_INSTALL_PATH="$HOME/Documents/maya/modules"
    fi
fi



build() {
    echo "Building..."
    mkdir -p build
    cp -R src/$PACKAGE_NAME build/
    cp -R src/$PACKAGE_NAME.mod build/
}

clean() {
    echo "Cleaning..."
    rm -Rf build
}

dev() {
    uninstall
    clean
    echo "Installing for development..."
    link `pwd`/src/$PACKAGE_NAME.mod $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME.mod
    link `pwd`/src/$PACKAGE_NAME $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME
}

test() {
    build
    echo "Running tests..."
    mayapy tests build/$PACKAGE_NAME
}

install() {
    uninstall
    clean
    build
    echo "Installing..."
    cp -v build/$PACKAGE_NAME.mod $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME.mod
    cp -R build/$PACKAGE_NAME $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME
}

uninstall() {
    echo "Uninstalling..."
    rm -v $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME.mod || true
    rm -R $MAYA_MODULES_INSTALL_PATH/$PACKAGE_NAME || true
}


ALL_COMMANDS="build, clean, dev, test, install, uninstall"



# Template setup.sh utils
# -----------------------


# simple cross-platform symlink util
link() {
    # use mklink if on windows
    if [[ -n "$WINDIR" ]]; then
        # determine if the link is a directory
        # also convert '/' to '\'
        if [[ -d "$1" ]]; then
            cmd <<< "mklink /D \"`cygpath -w \"$2\"`\" \"`cygpath -w \"$1\"`\"" > /dev/null
        else
            cmd <<< "mklink \"`cygpath -w \"$2\"`\" \"`cygpath -w \"$1\"`\"" > /dev/null
        fi
    else
        ln -sf "$1" "$2"
    fi
}

# run command by name
if [[ "$1" ]]; then
    cd $(dirname "$0")
    $1
else
    echo -e "usage: setup.sh [COMMAND]\n  $ALL_COMMANDS"
fi
