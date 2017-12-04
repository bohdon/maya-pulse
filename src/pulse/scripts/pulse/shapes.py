
import pymel.core as pm


__all__ = [
    'rotateComponents',
    'rotateSelectedComponentsAroundAxis',
]


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
        pm.error("{0} is not a valid shape".format(shape))


def rotateSelectedComponentsAroundAxis(axis, degrees=90):
    """
    Rotate the components of a shape by 90 degrees along one axis

    Args:
        axis: A int representing which axis to rotate around
            X = 0, Y = 1, Z = 2
        degrees: A float, how many degrees to rotate the components on that axis
            default is 90
    """
    rotation = pm.dt.Vector()
    rotation[axis] = degrees
    for node in pm.selected():
        for shape in node.getShapes():
            rotateComponents(shape, rotation)
