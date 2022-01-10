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


def lerpVector(a, b, alpha):
    return a + (b - a) * alpha


def lerpRotation(a, b, alpha):
    return a + (b - a) * alpha


def lerpMatrix(a: pm.dt.Matrix, b: pm.dt.Matrix, alpha: float) -> pm.dt.Matrix:
    """
    Return a linear interpolation between two matrices.

    Args:
        a (Matrix): A matrix
        b (Matrix): A second matrix
        alpha (float): A 0..1 float used to blend between matrix A (0) and B (1)

    Returns:
        A matrix blended from A to B
    """
    a_trans = pm.dt.TransformationMatrix(a)
    b_trans = pm.dt.TransformationMatrix(b)
    a_t = a_trans.getTranslation(space='world')
    a_r = a_trans.getRotation()
    a_s = pm.dt.Vector(a_trans.getScale(space='world'))
    b_t = b_trans.getTranslation(space='world')
    b_r = b_trans.getRotation()
    b_s = pm.dt.Vector(b_trans.getScale(space='world'))

    mtx = pm.dt.TransformationMatrix()
    mtx.setTranslation(lerpVector(a_t, b_t, alpha), space='world')
    # TODO: troubleshoot rotation interpolation, doesn't seem to work correctly
    mtx.setRotation(lerpRotation(a_r, b_r, alpha))
    mtx.setScale(lerpVector(a_s, b_s, alpha), space='world')
    return mtx
