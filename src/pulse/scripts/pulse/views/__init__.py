
import maya.cmds as cmds

from .core import *
from .blueprinteditor import *
from .actiontree import *
from .actioneditor import *
from .actionattrform import *
from .pulseeditor import *


def togglePulseUI():
    """
    Toggle the Pulse UI on / off
    """
    if isPulseUIShowing():
        hidePulseUI()
    else:
        showPulseUI()

def isPulseUIShowing():
    return PulseEditorWindow.exists()

def showPulseUI():
    if isPulseUIShowing():
        return
    
    PulseEditorWindow().createAndShow()

def hidePulseUI():
    if not isPulseUIShowing():
        return
    
    PulseEditorWindow.deleteInstances()
