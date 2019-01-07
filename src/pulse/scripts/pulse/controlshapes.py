
import os
import pulse.vendor.yaml as yaml
from fnmatch import fnmatch
import pymel.core as pm
import pymetanode as meta

import pulse.nodes
import pulse.links

__all__ = [
    'addShapes',
    'createControl',
    'createControlsForSelected',
    'getControlShapes',
    'getShapeData',
    'loadControlShapesFromDirectory',
    'removeShapes',
    'replaceShapes',
    'saveControlShapeToFile',
]

CONTROLSHAPE_METACLASS = 'pulse_controlshape'
BUILTIN_CONTROLSHAPES_LOADED = False
CONTROLSHAPES = {}


# Control Shape Registration
# --------------------------

def getControlShapes():
    """
    Return all available control shapes
    """
    def sort(a, b):
        result = cmp(a.get('sort', 999), b.get('sort', 999))
        if result == 0:
            result = cmp(a['name'], b['name'])
        return result

    return sorted(CONTROLSHAPES.values(), sort)


def registerControlShape(name, shape):
    """
    Register a new control shape.

    Args:
        name: A string name to register the shape under, will
            replace existing shapes and can be used to remove shapes
        shape: A dict containing control shape data
    """
    global CONTROLSHAPES
    CONTROLSHAPES[name] = shape


def unregisterControlShape(name):
    """
    Unregister a control shape.

    Args:
        name: A string name that the shape is registered under
    """
    global CONTROLSHAPES
    if name in CONTROLSHAPES:
        del CONTROLSHAPES[name]


def loadControlShapesFromDirectory(startDir, pattern='*_control.yaml'):
    """
    Return control shape data for all controls found by searching
    a directory. Search is performed recursively for
    any yaml files matching a pattern.

    Args:
        startDir: A str path of the directory to search
        pattern: A fnmatch pattern to filter which files to load
    """
    if '~' in startDir:
        startDir = os.path.expanduser(startDir)

    result = []

    paths = os.listdir(startDir)
    for path in paths:
        fullPath = os.path.join(startDir, path)

        if os.path.isfile(fullPath):
            if fnmatch(path, pattern):
                with open(fullPath, 'rb') as fp:
                    data = yaml.load(fp.read())
                name = data.get('name')
                if name:
                    result.append(data)
                else:
                    pm.warning("Invalid control shape: {0}".format(fullPath))

        elif os.path.isdir(fullPath):
            result.extend(loadControlShapesFromDirectory(fullPath, pattern))

    return result


def loadBuiltinControlShapes():
    """
    Load all built-in pulse control shapes.
    """
    global BUILTIN_CONTROLSHAPES_LOADED
    if not BUILTIN_CONTROLSHAPES_LOADED:
        controlsDir = os.path.join(os.path.dirname(__file__), 'controls')
        shapes = loadControlShapesFromDirectory(controlsDir)
        for s in shapes:
            registerControlShape(s['name'], s)
        BUILTIN_CONTROLSHAPES_LOADED = True


def saveControlShapeToFile(name, icon, curve, filePath):
    """
    Save a control curve to a yaml file.

    Args:
        curve (PyNode): A curve transform node containing one or
            more curve shapes.
    """
    data = {
        'name': name,
        'icon': icon,
        'sort': 100,
        'curves': getShapeData(curve),
    }
    with open(filePath, 'wb') as fp:
        yaml.dump(data, fp)


# Control Creation
# ----------------


def createControl(shapeData, name=None, targetNode=None,
                  link=False, parent=None):
    """
    Create a control at the given target with the given shape data.

    Args:
        shapeData: A dict containing control shape data
        name: A string name of the control created
        targetNode: An optional transform node to position the
            control at upon creation
        link (bool): If true, link the control to the targetNode
        parent: An optional transform node to parent the control to
    """
    if targetNode and not isinstance(targetNode, pm.nt.Transform):
        raise TypeError('targetNode must be a Transform node')
    if name is None:
        name = 'ctl1'
    # create control transform
    ctl = pm.group(em=True, n=name)
    addShapes(ctl, shapeData)
    if targetNode:
        # match target node transform settings
        ctl.setAttr('rotateOrder', targetNode.getAttr('rotateOrder'))
        pulse.nodes.matchWorldMatrix(targetNode, ctl)
        if link:
            pulse.links.link(targetNode, ctl)
    # group to main ctls group
    if parent:
        ctl.setParent(parent)
    # apply meta data to keep track of control shapes
    meta.setMetaData(ctl, CONTROLSHAPE_METACLASS, {})
    return ctl


def createControlsForSelected(shapeData, link=True):
    """
    Create or update control shapes for each selected node.

    Args:
        shapeData: A dict containing control shape data
        link (bool): If true, link the controls to the target nodes
    """
    result = []
    sel = pm.selected()
    if not sel:
        ctl = createControl(shapeData)
        result.append(ctl)
    else:
        for node in sel:
            if meta.hasMetaClass(node, CONTROLSHAPE_METACLASS):
                # update shape
                replaceShapes(node, shapeData)
                result.append(node)
            else:
                # create new control
                ctl = createControl(shapeData, targetNode=node, link=link)
                result.append(ctl)
    pm.select(result)
    return result


def addShapes(node, shapeData):
    """
    Add all shapes for the given shape data to the given node.
    Returns the new shape nodes.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(
            'Expected a Transform node, got {0}'.format(type(node).__name__))
    result = []
    for curveData in shapeData['curves']:
        curve = pm.curve(**curveData)
        shape = curve.getShape()
        pm.parent(shape, node, s=True, r=True)
        pm.delete(curve)
        result.append(shape)
    return result


def removeShapes(node):
    """
    Remove the shape nodes from the given transform.
    Only works for meshes, curves, and nurbs surfaces.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(
            'Expected a Transform node, got {0}'.format(type(node).__name__))
    for s in node.getShapes():
        if s.nodeType() in ('mesh', 'nurbsCurve', 'nurbsSurface'):
            pm.delete(s)


def replaceShapes(node, shapeData):
    """
    Replace the shapes on the given control node with the given shape data.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(
            'Expected a Transform node, got {0}'.format(type(node).__name__))

    color = pulse.nodes.getOverrideColor(node)
    removeShapes(node)
    addShapes(node, shapeData)
    if color:
        pulse.nodes.setOverrideColor(node, color)


def getShapeData(node):
    """
    Return curve shape data for a node.

    Args:
        node (PyNode): A transform containing one or more curve shapes
    """
    result = []
    shapes = node.getShapes(type='nurbsCurve')
    for shape in shapes:
        shapeData = {
            'degree': shape.degree(),
            'periodic': shape.form() == pm.nt.NurbsCurve.Form.periodic,
            'knot': shape.getKnots(),
            'point': [p.tolist() for p in shape.getCVs()],
        }
        result.append(shapeData)
    return result
