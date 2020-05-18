
import logging
import pymel.core as pm


__all__ = [
    'rotateComponents',
]

LOG = logging.getLogger(__name__)


# Component Editing
# -----------------

def rotateComponents(shape, rotation):
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
        LOG.error("{0} is not a valid shape".format(shape))


def combineShapes(transforms):
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

    # reparent shapes to first transform
    for shape in shapes:
        pm.parent(shape, target, shape=True, relative=True)

    # delete empty remaining transforms
    nodesToDelete = []
    for t in transforms:
        if not t.getChildren():
            nodesToDelete.append(t)
    pm.delete(nodesToDelete)

    return target
