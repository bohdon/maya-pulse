
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
