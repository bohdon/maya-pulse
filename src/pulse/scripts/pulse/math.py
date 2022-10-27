import pymel.core as pm


def make_matrix_from_xy(x_axis, y_axis):
    """
    Return a matrix with given X and Y axes.
    X will remain fixed, Y may be changed minimally to enforce orthogonality.
    Z will be computed. Inputs need not be normalized.
    """
    # if almost the same, pick a new normal vector
    new_x = pm.dt.Vector(x_axis).normal()
    normal = pm.dt.Vector(y_axis).normal()

    if new_x.dot(normal) >= 0.9999:
        # don't pick the same vector as newX
        if new_x.z < 0.9999:
            normal = pm.dt.Vector(0, 0, 1)
        else:
            normal = pm.dt.Vector(1, 0, 0)

    new_z = new_x.cross(normal).normal()
    new_y = new_z.cross(new_z)
    return pm.dt.Matrix(new_x, new_y, new_z)


def make_matrix_from_xz(x_axis, z_axis):
    """
    Return a matrix with given X and Z axes.
    X will remain fixed, Z may be changed minimally to enforce orthogonality.
    Y will be computed. Inputs need not be normalized.
    """
    # if almost the same, pick a new normal vector
    new_x = pm.dt.Vector(x_axis).normal()
    normal = pm.dt.Vector(z_axis).normal()

    if new_x.dot(normal) >= 0.9999:
        # don't pick the same vector as newX
        if new_x.z < 0.9999:
            normal = pm.dt.Vector(0, 0, 1)
        else:
            normal = pm.dt.Vector(1, 0, 0)

    new_y = normal.cross(new_x).normal()
    new_z = new_x.cross(new_y)
    return pm.dt.Matrix(new_x, new_y, new_z)


def lerp_vector(a, b, alpha):
    return a + (b - a) * alpha


def lerp_rotation(a, b, alpha):
    return a + (b - a) * alpha


def lerp_matrix(a: pm.dt.Matrix, b: pm.dt.Matrix, alpha: float) -> pm.dt.Matrix:
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
    mtx.setTranslation(lerp_vector(a_t, b_t, alpha), space='world')
    # TODO: troubleshoot rotation interpolation, doesn't seem to work correctly
    mtx.setRotation(lerp_rotation(a_r, b_r, alpha))
    mtx.setScale(lerp_vector(a_s, b_s, alpha), space='world')
    return mtx
