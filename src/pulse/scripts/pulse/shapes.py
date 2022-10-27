import logging

import pymel.core as pm

LOG = logging.getLogger(__name__)


def rotate_components(shape, rotation):
    """
    Rotate the components of a shape.

    Args:
        shape: A Mesh or NurbsCurve node
        rotation: A vector rotation in euler angles
    """
    if isinstance(shape, pm.nt.Mesh):
        pm.rotate(shape.vtx, rotation, objectSpace=True)
    elif isinstance(shape, pm.nt.NurbsCurve):
        pm.rotate(shape.cv, rotation, objectSpace=True)
    else:
        LOG.error("%s is not a valid shape", shape)


def combine_shapes(transforms):
    """
    Combine multiple shape nodes into one transform with all the shapes.

    Args:
        transforms: A list of transform nodes with shapes to combine

    Returns:
        The combined transform node containing all the shapes
    """
    # get first transform, and all shapes
    target = transforms[0]
    shapes = []
    for t in transforms:
        shapes.extend(t.getShapes())

    # re-parent shapes to first transform
    for shape in shapes:
        pm.parent(shape, target, shape=True, relative=True)

    # delete empty remaining transforms
    nodes_to_delete = []
    for t in transforms:
        if not t.getChildren():
            nodes_to_delete.append(t)
    pm.delete(nodes_to_delete)

    return target
