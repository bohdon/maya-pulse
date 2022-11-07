import functools
import os
from fnmatch import fnmatch

import pymel.core as pm

from .vendor import pymetanode as meta
from .vendor import yaml
from . import links
from . import nodes
from . import util_nodes

CONTROL_SHAPE_METACLASS = "pulse_controlshape"
BUILTIN_CONTROL_SHAPES_LOADED = False
CONTROL_SHAPES = {}


def create_line_shape(start_node, end_node, parent_node=None):
    """
    Create a curve shape that draws a straight line between
    two nodes.

    Args:
        start_node (PyNode): A transform node.
        end_node (PyNode): A transform node.
        parent_node (PyNode): A transform node to use as the parent
            of the newly created shape. Default is None, which creates
            a new transform for the curve.
    """
    curve_transform = pm.curve(d=1, p=[(0, 0, 0), (0, 0, 0)], k=[0, 1])
    curve_shape = curve_transform.getShape()

    if parent_node:
        pm.parent(curve_shape, parent_node, shape=True, relative=True)
        pm.delete(curve_transform)
        curve_transform = None

    # if a parent node is used, we don't need to connect the control point,
    # it can stay at relative location (0, 0, 0)
    if start_node != parent_node:
        connect_node_to_control_point(start_node, curve_shape, 0)
    if end_node != parent_node:
        connect_node_to_control_point(end_node, curve_shape, 1)

    return curve_shape


def connect_node_to_control_point(node, curve_shape, point_index):
    """
    Connect the world location of a node to the world location of a
    control point on a curve shape. Assumes that the curveShape is
    not a child of the node (in which case this is unnecessary).

    Args:
        node (PyNode): A transform node.
        curve_shape (Curve): A curve shape.
        point_index (int): The index of a control point on the curve shape.
    """
    # TODO: name the utility nodes
    mmtx = util_nodes.mult_matrix(node.wm, curve_shape.pim)
    decomp = util_nodes.decompose_matrix(mmtx)
    decomp.outputTranslate >> curve_shape.controlPoints[point_index]


# Control Shape Registration
# --------------------------


def get_control_shapes():
    """
    Return all available control shapes
    """

    def cmp(a, b):
        return (a > b) - (a < b)

    def sort_func(a, b):
        result = cmp(a.get("sort", 999), b.get("sort", 999))
        if result == 0:
            result = cmp(a["name"], b["name"])
        return result

    return sorted(CONTROL_SHAPES.values(), key=functools.cmp_to_key(sort_func))


def register_control_shape(name, shape):
    """
    Register a new control shape.

    Args:
        name: A string name to register the shape under, will
            replace existing shapes and can be used to remove shapes.
        shape: A dict containing control shape data.
    """
    global CONTROL_SHAPES
    CONTROL_SHAPES[name] = shape


def unregister_control_shape(name):
    """
    Unregister a control shape.

    Args:
        name: A string name that the shape is registered under
    """
    global CONTROL_SHAPES
    if name in CONTROL_SHAPES:
        del CONTROL_SHAPES[name]


def load_control_shapes_from_directory(start_dir, pattern="*_control.yaml"):
    """
    Return control shape data for all controls found by searching
    a directory. Search is performed recursively for
    any yaml files matching a pattern.

    Args:
        start_dir: A str path of the directory to search
        pattern: A fnmatch pattern to filter which files to load
    """
    if "~" in start_dir:
        start_dir = os.path.expanduser(start_dir)

    result = []

    paths = os.listdir(start_dir)
    for path in paths:
        full_path = os.path.join(start_dir, path)

        if os.path.isfile(full_path):
            if fnmatch(path, pattern):
                with open(full_path, "r") as fp:
                    data = yaml.load(fp.read())
                name = data.get("name")
                if name:
                    result.append(data)
                else:
                    pm.warning(f"Invalid control shape: {full_path}")

        elif os.path.isdir(full_path):
            result.extend(load_control_shapes_from_directory(full_path, pattern))

    return result


def load_builtin_control_shapes():
    """
    Load all built-in pulse control shapes.
    """
    global BUILTIN_CONTROL_SHAPES_LOADED
    if not BUILTIN_CONTROL_SHAPES_LOADED:
        controls_dir = os.path.join(os.path.dirname(__file__), "controls")
        shapes = load_control_shapes_from_directory(controls_dir)
        for s in shapes:
            register_control_shape(s["name"], s)
        BUILTIN_CONTROL_SHAPES_LOADED = True


def save_control_shape_to_file(name, icon, curve, file_path):
    """
    Save a control curve to a yaml file.

    Args:
        name: The display name of the curve.
        icon: The path to an icon for the curve.
        curve (PyNode): A curve transform node containing one or more curve shapes.
        file_path: The path to the file where the shape should be saved.
    """
    data = {
        "name": name,
        "icon": icon,
        "sort": 100,
        "curves": get_shape_data(curve),
    }
    with open(file_path, "w") as fp:
        yaml.dump(data, fp)


# Control Creation
# ----------------


def create_control(shape_data, name=None, target_node=None, link=False, parent=None):
    """
    Create a control at the given target with the given shape data.

    Args:
        shape_data: A dict containing control shape data.
        name: A string name of the control created.
        target_node: An optional transform node to position the control at upon creation.
        link (bool): If true, link the control to the target_node.
        parent: An optional transform node to parent the control to.
    """
    if target_node and not isinstance(target_node, pm.nt.Transform):
        raise TypeError("target_node must be a Transform node")
    if name is None:
        name = "ctl1"
    # create control transform
    ctl = pm.group(em=True, n=name)
    add_shapes(ctl, shape_data)
    if target_node:
        # match target node transform settings
        ctl.setAttr("rotateOrder", target_node.getAttr("rotateOrder"))
        nodes.match_world_matrix(target_node, ctl)
        if link:
            links.create_default_link(ctl, target_node)
    # group to main ctls group
    if parent:
        ctl.setParent(parent)
    # apply metadata to keep track of control shapes
    meta.setMetaData(ctl, CONTROL_SHAPE_METACLASS, {})
    return ctl


def create_controls_for_selected(shape_data, link=True):
    """
    Create or update control shapes for each selected node.

    Args:
        shape_data: A dict containing control shape data.
        link (bool): If true, link the controls to the target nodes.
    """
    result = []
    sel = pm.selected()
    if not sel:
        ctl = create_control(shape_data)
        result.append(ctl)
    else:
        for node in sel:
            if meta.hasMetaClass(node, CONTROL_SHAPE_METACLASS):
                # update shape
                replace_shapes(node, shape_data)
                result.append(node)
            else:
                # create new control
                ctl = create_control(shape_data, target_node=node, link=link)
                result.append(ctl)
    pm.select(result)
    return result


def add_shapes(node, shape_data):
    """
    Add all shapes for the given shape data to the given node.
    Returns the new shape nodes.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(f"Expected a Transform node, got {type(node).__name__}")
    result = []
    for curveData in shape_data["curves"]:
        curve = pm.curve(**curveData)
        shape = curve.getShape()
        pm.parent(shape, node, s=True, r=True)
        pm.delete(curve)
        result.append(shape)
    return result


def remove_shapes(node):
    """
    Remove the shape nodes from the given transform.
    Only works for meshes, curves, and nurbs surfaces.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(f"Expected a Transform node, got {type(node).__name__}")
    for s in node.getShapes():
        if s.nodeType() in ("mesh", "nurbsCurve", "nurbsSurface"):
            pm.delete(s)


def replace_shapes(node, shape_data):
    """
    Replace the shapes on the given control node with the given shape data.
    """
    if not isinstance(node, pm.nt.Transform):
        raise TypeError(f"Expected a Transform node, got {type(node).__name__}")

    color = nodes.get_override_color(node)
    remove_shapes(node)
    add_shapes(node, shape_data)
    if color:
        nodes.set_override_color(node, color)


def get_shape_data(node):
    """
    Return curve shape data for a node.

    Args:
        node (PyNode): A transform containing one or more curve shapes
    """
    result = []
    shapes = node.getShapes(type="nurbsCurve")
    for shape in shapes:
        shape_data = {
            "degree": shape.degree(),
            "periodic": shape.form() == pm.nt.NurbsCurve.Form.periodic,
            "knot": shape.getKnots(),
            "point": [p.tolist() for p in shape.getCVs()],
        }
        result.append(shape_data)
    return result
