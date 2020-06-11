
import pymel.core as pm


def makeMatrixFromXY(xAxis, yAxis):
    """
    Return a matrix with given X and Y axes.
    X will remain fixed, Y may be changed minimally to enforce orthogonality.
    Z will be computed. Inputs need not be normalized.
    """
    # if almost the same, pick a new normal vector
    newX = pm.dt.Vector(xAxis).normal()
    normal = pm.dt.Vector(yAxis).normal()

    if newX.dot(normal) >= 0.9999:
        # don't pick the same vector as newX
        if newX.z < 0.9999:
            normal = pm.dt.Vector(0, 0, 1)
        else:
            normal = pm.dt.Vector(1, 0, 0)

    newZ = newX.cross(normal).normal()
    newY = newZ.cross(newZ)
    return pm.dt.Matrix(newX, newY, newZ)


def makeMatrixFromXZ(xAxis, zAxis):
    """
    Return a matrix with given X and Z axes.
    X will remain fixed, Z may be changed minimally to enforce orthogonality.
    Y will be computed. Inputs need not be normalized.
    """
    # if almost the same, pick a new normal vector
    newX = pm.dt.Vector(xAxis).normal()
    normal = pm.dt.Vector(zAxis).normal()

    if newX.dot(normal) >= 0.9999:
        # don't pick the same vector as newX
        if newX.z < 0.9999:
            normal = pm.dt.Vector(0, 0, 1)
        else:
            normal = pm.dt.Vector(1, 0, 0)

    newY = normal.cross(newX).normal()
    newZ = newX.cross(newY)
    return pm.dt.Matrix(newX, newY, newZ)
