import logging
from enum import IntEnum

import pymel.core as pm

from . import nodes

LOG = logging.getLogger(__name__)

IS_MATRIX_PLUGIN_LOADED = False
IS_QUAT_PLUGIN_LOADED = False

# Map of utility node types to default output attribute names.
# Used to determine which attribute to return by default when creating utility nodes.
OUTPUT_ATTR_NAMES = {
    "addDoubleLinear": "output",
    "aimMatrix": "outputMatrix",
    "angleBetween": "angle",
    "blendColors": "output",
    "blendMatrix": "outputMatrix",
    "choice": "output",
    "clamp": "output",
    "composeMatrix": "outputMatrix",
    "condition": "outColor",
    "distanceBetween": "distance",
    "floatMath": "outFloat",
    "inverseMatrix": "outputMatrix",
    "multMatrix": "matrixSum",
    "multiplyDivide": "output",
    "reverse": "output",
    "setRange": "outValue",
    "vectorProduct": "output",
}

# Map of node types to functions used to retrieve the output attribute names.
# If the function is a string, attempts to resolve it from globals().
OUTPUT_ATTR_NAME_FUNCS = {"plusMinusAverage": "get_plus_minus_average_output_attr"}


class PlusMinusAverageOperation(IntEnum):
    NO_OPERATION = 0
    SUM = 1
    SUBTRACT = 2
    AVERAGE = 3


class MultiplyDivideOperation(IntEnum):
    NO_OPERATION = 0
    MULTIPLY = 1
    DIVIDE = 2
    POWER = 3


class FloatMathOperation(IntEnum):
    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    MIN = 4
    MAX = 5
    POWER = 6


class ConditionOperation(IntEnum):
    EQUAL = 0
    NOT_EQUAL = 1
    GREATER_THAN = 2
    GREATER_OR_EQUAL = 3
    LESS_THAN = 4
    LESS_OR_EQUAL = 5


class VectorProductOperation(IntEnum):
    NO_OPERATION = 0
    DOT_PRODUCT = 1
    CROSS_PRODUCT = 2
    VECTOR_MATRIX_PRODUCT = 3
    POINT_MATRIX_PRODUCT = 4


class AlignMatrixPrimaryMode(IntEnum):
    LOCK_AXIS = 0
    AIM = 1
    ALIGN = 2


class AlignMatrixSecondaryMode(IntEnum):
    NONE = 0
    AIM = 1
    ALIGN = 2


def load_matrix_plugin():
    global IS_MATRIX_PLUGIN_LOADED
    if not IS_MATRIX_PLUGIN_LOADED:
        try:
            pm.loadPlugin("matrixNodes", quiet=True)
            IS_MATRIX_PLUGIN_LOADED = True
        except:
            pass


def load_quat_plugin():
    global IS_QUAT_PLUGIN_LOADED
    if not IS_QUAT_PLUGIN_LOADED:
        try:
            pm.loadPlugin("quatNodes", quiet=True)
            IS_QUAT_PLUGIN_LOADED = True
        except:
            pass


def get_constraint_weight_attr(leader, constraint):
    """
    Return the weight attribute from a constraint that
    corresponds to a specific leader node.

    Args:
        leader (PyNode): A node that is one of the leaders of a constraint.
        constraint (PyNode): A constraint node.
    """
    for i, target in enumerate(constraint.getTargetList()):
        if leader == target:
            return constraint.getWeightAliasList()[i]


def get_output_attr(input):
    """
    Return the output attr of a utility node.

    Most of the time this is a standard output based on the node type,
    but some nodes have more than one output attr, and one is selected
    based on the input.

    Matches the dimension of the input (if its an attribute),
    e.g. if inputX is given, outputX will be returned.

    Examples:
        multiplyDivide.input1 -> multiplyDivide.output1
        multiplyDivide.input1X -> multiplyDivide.output1X
        setRange.min -> setRange.outValue
        condition.colorIfTrueR -> condition.outColorR
        plusMinusAverage.input2D[0].input2Dx -> plusMinusAverage.output2Dx

    Args:
        input: A PyNode or Attribute for which to return an output.

    Returns:
        An Attribute that matches the input, or None if the input is unhandled
    """

    def resolve_output_func(func):
        if callable(func):
            return func
        elif func in globals():
            return globals()[func]
        return None

    output_funcs = {name: resolve_output_func(func) for name, func in OUTPUT_ATTR_NAME_FUNCS.items()}
    output_funcs = {name: func for name, func in output_funcs.items() if func}

    node = input.node()
    node_type = node.nodeType()
    if node_type not in OUTPUT_ATTR_NAMES and node_type not in output_funcs:
        LOG.warning("No output found for utility type '%s'", node_type)
        return None

    if node_type in output_funcs:
        fnc = output_funcs[node_type]
        return fnc(input)

    elif node_type in OUTPUT_ATTR_NAMES:
        output_attr_name = OUTPUT_ATTR_NAMES[node_type]
        output_attr = nodes.safe_get_attr(node, output_attr_name)

        if output_attr and output_attr.isCompound():
            if isinstance(input, pm.Attribute) and input.isChild():
                # input and output are both compound, return
                # child of output at the same child index
                index = nodes.get_compound_attr_index(input)
                return output_attr.getChildren()[index]

        return output_attr


def get_plus_minus_average_output_attr(input):
    """
    Return the output attr of a plusMinusAverage node.
    Returns the output that matches the dimension of the input (if it's an attribute),
    otherwise returns the 1D output.

    Args:
        input: A PyNode or Attribute for which to return an output

    Returns:
        An Attribute of the node, which could be one of output1D, output2D, output3D or any children.
        Returns output1D if the given input is the node and not an attribute.
    """
    input_node = input.node()

    if not isinstance(input, pm.Attribute):
        return input_node.output1D

    num_children = 0
    if input.isCompound():
        num_children = input.numChildren()
    elif input.isChild():
        num_children = input.getParent().numChildren()

    if num_children > 0:
        # get output of same dimension (1D, 2D, or 3D)
        output_attr = input_node.attr("output{0}D".format(num_children))

        if input.isChild():
            # return a matching child attribute
            index = nodes.get_compound_attr_index(input)
            return output_attr.getChildren()[index]

        return output_attr

    # if all else fails
    return input_node.output1D


def get_largest_dimension_attr(attrs):
    """
    Return the attr that has the largest dimension.

    Args:
        attrs: A list of Attributes
    """
    largest_dim = 0
    largest_attr = None
    for attr in attrs:
        dim = nodes.get_attr_dimension(attr)
        if dim > largest_dim:
            largest_dim = dim
            largest_attr = attr
    return largest_attr


def _filter_for_best_input_attrs(attrs):
    """
    Return a list of attrs that represents
    only the attrs that correspond to specific
    output attrs.

    If none of the attrs correspond to an output,
    the original attrs list will be returned.
    """
    non_input_attr_names = [
        "firstTerm",
        "secondTerm",
    ]
    # TODO: check node type
    filtered_attrs = [a for a in attrs if a.longName() not in non_input_attr_names]
    if filtered_attrs:
        return filtered_attrs
    else:
        return attrs


def _get_output_attr_from_largest(attrs):
    """
    Return the output attr of a utility node using the
    attr with the largest dimension.

    Args:
        attrs: A list of Attributes
    """
    largest = get_largest_dimension_attr(attrs)
    return get_output_attr(largest)


def get_input_connections(input_val, dest_attr):
    """
    Return a list of (src, dst) tuples representing connections to be made between an
    input and destination attribute. Input can be a simple value or an Attribute,
    and the results are intended for use with `set_or_connect_attr`.

    More than one connection tuple may be returned in situations where
    the input and destination dimensions don't match.
    e.g. ([1, 2], input) -> (1, inputX), (2, inputY)

    Args:
        input_val: An Attribute or value to set or connect to the destination attribute.
        dest_attr (Attribute): The attribute that will receive the input value.
    """
    if input_val is None:
        return []

    def _child(obj, index):
        """
        Return the child of an object whether it's a list-like object or compound attribute.
        If the dimension of obj is 1, returns obj.
        """
        if nodes.get_attr_or_value_dimension(obj) == 1:
            return obj
        if isinstance(obj, pm.Attribute):
            return obj.getChildren()[index]
        else:
            return obj[index]

    # simplify the input if possible
    if isinstance(input_val, (list, tuple)):
        if len(input_val) == 1:
            input_val = input_val[0]

    input_dim = nodes.get_attr_or_value_dimension(input_val)
    dest_attr_dim = nodes.get_attr_dimension(dest_attr)

    # get the overlapping dimension
    dim = min(input_dim, dest_attr_dim)

    if input_dim == dest_attr_dim:
        # TODO: only do this if input is an Attribute?
        # direct connection is allowed
        return [(input_val, dest_attr)]
    else:
        # this represents n to m dimension attr/values and
        # all other odd associations
        ins = [_child(input_val, i) for i in range(dim)]
        ats = [_child(dest_attr, i) for i in range(dim)]
        return list(zip(ins, ats))


def set_or_connect_attr(attr, val):
    """
    Set or connect the given value into the given attribute.
    Handles finding the correct inputs on the target utility
    node automatically, as well as plugging n-dimension inputs
    into m-dimension attributes.

    Args:
        attr: A Attribute to set or connect
        val: A PyNode, Attribute or value

    Returns:
        A list of Attributes that were set or connected
    """
    cons = get_input_connections(val, attr)
    for srcVal, dstAttr in cons:
        if isinstance(srcVal, pm.Attribute):
            srcVal >> dstAttr
        else:
            dstAttr.set(srcVal)
    return [con[1] for con in cons]


def add(*inputs):
    """Return an attribute that represents the given inputs added together."""
    return plus_minus_average(inputs, PlusMinusAverageOperation.SUM)


def subtract(*inputs):
    """
    Return an attribute that represents the given inputs subtracted in
    sequential order.
    Eg. input[0] - input[1] - ... - input[n]
    All inputs can be either attributes or values.
    """
    return plus_minus_average(inputs, PlusMinusAverageOperation.SUBTRACT)


def average(*inputs):
    """Return an attribute that represents the average of the given inputs."""
    return plus_minus_average(inputs, PlusMinusAverageOperation.AVERAGE)


def plus_minus_average(inputs, operation):
    node = pm.shadingNode("plusMinusAverage", asUtility=True)
    node.operation.set(operation)

    if len(inputs) > 0:
        input_dim = nodes.get_attr_or_value_dimension(inputs[0])
        if input_dim == 1:
            multi_attr = node.input1D
        elif input_dim == 2:
            multi_attr = node.input2D
        elif input_dim == 3:
            multi_attr = node.input3D
        else:
            raise ValueError("Input dimension is not 1D, 2D, or 3D: {0}".format(inputs))
        for i, input in enumerate(inputs):
            # hook up inputs
            set_or_connect_attr(multi_attr[i], input)
        return get_output_attr(multi_attr)
    else:
        return get_output_attr(node)


# TODO: move internal functions to another module so these functions can shadow builtin names


def min_float(a, b):
    """
    Return an attribute that represents min(a, b).
    Only supports float values.
    """
    return _create_utility_and_return_output("floatMath", floatA=a, floatB=b, operation=FloatMathOperation.MIN)


def max_float(a, b):
    """
    Return an attribute that represents max(a, b).
    Only supports float values.
    """
    return _create_utility_and_return_output("floatMath", floatA=a, floatB=b, operation=FloatMathOperation.MAX)


def multiply(a, b):
    """Return an attribute that represents a * b."""
    return multiply_divide(a, b, MultiplyDivideOperation.MULTIPLY)


def divide(a, b):
    """Return an attribute that represents a / b."""
    return multiply_divide(a, b, MultiplyDivideOperation.DIVIDE)


def pow(a, b):
    """Return an attribute that represents a ^ b."""
    return multiply_divide(a, b, MultiplyDivideOperation.POWER)


def sqrt(a):
    """Return an attribute that represents the square root of a."""
    return multiply_divide(a, 0.5, MultiplyDivideOperation.POWER)


def multiply_divide(input1, input2, operation=MultiplyDivideOperation.DIVIDE):
    return _create_utility_and_return_output("multiplyDivide", input1=input1, input2=input2, operation=operation)


def reverse(input):
    return _create_utility_and_return_output("reverse", input=input)


def clamp(input, min, max):
    """
    Return an attribute that represents the given input clamped in the range
    [min, max].
    All inputs can be either attributes or values.
    """
    return _create_utility_and_return_output("clamp", input=input, min=min, max=max)


def set_range(value, min, max, old_min, old_max):
    """
    Return an attribute that represents the given input mapped from the range
    [old_min, old_max] to the range [min, max].
    All inputs can be either attributes or values.
    """
    return _create_utility_and_return_output("setRange", value=value, min=min, max=max, oldMin=old_min, oldMax=old_max)


def blend2(a, b, blender):
    """
    Given two inputs of 1D, 2D, or 3D using a blender value, create a blend node and return
    the output attribute. If 1D, returns the outputX, if 2D or 3D, returns the output.
    """
    # clamp blender
    if not isinstance(blender, pm.Attribute):
        blender = max(min(blender, 1), 0)
    return _create_utility_and_return_output("blendColors", color1=a, color2=b, blender=blender)


def distance(a, b, ws=True, make_local=True):
    """
    Return an attribute on a distance node that represents the distance
    between nodes A and B.

    Args:
        a: Node A
        b: Node B
        ws: Use world space matrices
        make_local: If True, makes both matrix inputs to the distance utils be matrices local to node A.
    """
    node_type = "distanceBetween"
    in_matrix1 = a.node().wm if ws and not make_local else a.node().m
    in_matrix2 = b.node().wm if ws or make_local else b.node().m
    if make_local:
        mult = pm.createNode("multMatrix")
        in_matrix2 >> mult.matrixIn[0]
        a.node().pim >> mult.matrixIn[1]
        in_matrix2 = mult.matrixSum
    n = create_utility_node(node_type=node_type, inMatrix1=in_matrix1, inMatrix2=in_matrix2)
    return n.distance


def equal(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a == b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.EQUAL)


def not_equal(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a != b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.NOT_EQUAL)


def greater_than(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a > b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.GREATER_THAN)


def greater_or_equal(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a >= b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.GREATER_OR_EQUAL)


def less_than(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a < b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.LESS_THAN)


def less_or_equal(a, b, true_val, false_val):
    """
    Return an attribute that represents true_val if a <= b else false_val.
    Inputs can be either attributes or values.
    """
    return condition(a, b, true_val, false_val, ConditionOperation.LESS_OR_EQUAL)


def condition(first_term, second_term, true_val, false_val, operation):
    """
    Create a condition that returns either true_val or false_val based
    on the comparison of first_term and second_term.

    Args:
        first_term: The first term to compare against.
        second_term: The second term to compare against.
        true_val: The value or attribute to use if the condition is true.
        false_val: The value or attribute to use if the condition is false.
        operation (ConditionOperation): The condition node operation to use
    """
    return _create_utility_and_return_output(
        "condition",
        firstTerm=first_term,
        secondTerm=second_term,
        colorIfTrue=true_val,
        colorIfFalse=false_val,
        operation=operation,
    )


def choice(selector, *inputs) -> pm.Attribute:
    """
    Create a choice node that selects an input based on a selector.

    Args:
        selector: The selector value or attribute.
        *inputs: The array of input values or attributes to select based on the selector.
    """
    choice_node = pm.shadingNode("choice", asUtility=True)
    set_or_connect_attr(choice_node.selector, selector)
    for i, input in enumerate(inputs):
        set_or_connect_attr(choice_node.input[i], input)
    return choice_node.output


def dot(a, b) -> pm.Attribute:
    """
    Calculate the dot product of two vectors using a `vectorProduct` node

    Args:
        a: A vector value or attribute
        b: A vector value or attribute
    """
    return _create_utility_and_return_output(
        "vectorProduct", input1=a, input2=b, operation=VectorProductOperation.DOT_PRODUCT
    )


def cross(a, b) -> pm.Attribute:
    """
    Calculate the cross product of two vectors using a `vectorProduct` node

    Args:
        a: A vector value or attribute
        b: A vector value or attribute
    """
    return _create_utility_and_return_output(
        "vectorProduct", input1=a, input2=b, operation=VectorProductOperation.CROSS_PRODUCT
    )


def matrix_multiply_vector(matrix, vector) -> pm.Attribute:
    """
    Multiply a direction vector by a matrix using a `vectorProduct` node

    Args:
        matrix: A transformation matrix value or attribute
        vector: A vector value or attribute representing a direction
    """
    return _create_utility_and_return_output(
        "vectorProduct", input1=vector, matrix=matrix, operation=VectorProductOperation.VECTOR_MATRIX_PRODUCT
    )


def matrix_multiply_point(matrix, point) -> pm.Attribute:
    """
    Multiply a point vector by a matrix using a `vectorProduct` node

    Args:
        matrix: A transformation matrix value or attribute
        point: A vector value or attribute representing a location
    """
    return _create_utility_and_return_output(
        "vectorProduct", input1=point, matrix=matrix, operation=VectorProductOperation.POINT_MATRIX_PRODUCT
    )


def mult_matrix(*matrices):
    load_matrix_plugin()
    mmtx = pm.shadingNode("multMatrix", asUtility=True)
    for i, matrix in enumerate(matrices):
        set_or_connect_attr(mmtx.matrixIn[i], matrix)
    return mmtx.matrixSum


def inverse_matrix(matrix) -> pm.Attribute:
    """
    Invert a matrix using a `inverseMatrix` node

    Args:
        matrix: A matrix value or attribute
    """
    return _create_utility_and_return_output("inverseMatrix", inputMatrix=matrix)


def compose_matrix(translate=None, rotate=None, scale=None) -> pm.Attribute:
    """
    Compose a matrix using separate translate, rotate, and scale values using a `composeMatrix` utility node

    Args:
        translate: A translation vector or attribute
        rotate: A euler rotation vector or attribute
        scale: A scale vector or attribute
    """
    kwargs = {}
    if translate is not None:
        kwargs["inputTranslate"] = translate
    if rotate is not None:
        kwargs["inputRotate"] = rotate
    if scale is not None:
        kwargs["inputScale"] = scale
    return _create_utility_and_return_output("composeMatrix", useEulerRotation=True, **kwargs)


def decompose_matrix(matrix):
    """
    Create a `decomposeMatrix` utility node.

    Returns:
        The `decomposeMatrix` node (not output attributes).
    """
    load_matrix_plugin()
    return create_utility_node("decomposeMatrix", inputMatrix=matrix)


# TODO: add aimMatrix functions


def align_matrix_to_direction(matrix, keep_axis, align_axis, align_direction, align_matrix) -> pm.Attribute:
    """
    Align a matrix by pointing a secondary axis in a direction, while preserving a primary axis.

    Args:
        matrix: A transformation matrix value or attribute
        keep_axis: A vector value or attribute representing the primary aim axis to keep locked
        align_axis: A vector value or attribute representing the secondary align axis to try to adjust
        align_direction: The direction vector value or attribute that the secondary axis should align to
        align_matrix: A matrix applied to the direction vector
    """
    return _create_utility_and_return_output(
        "aimMatrix",
        inputMatrix=matrix,
        primaryInputAxis=keep_axis,
        primaryMode=AlignMatrixPrimaryMode.LOCK_AXIS,
        secondaryInputAxis=align_axis,
        secondaryMode=AlignMatrixSecondaryMode.ALIGN,
        secondaryTargetVector=align_direction,
        secondaryTargetMatrix=align_matrix,
    )


def align_matrix_to_point(matrix, keep_axis, align_axis, align_target_point, align_matrix):
    """
    Align a matrix by pointing a secondary axis at a location, while preserving a primary axis.

    Args:
        matrix: A transformation matrix value or attribute
        keep_axis: A vector value or attribute representing the primary aim axis to keep locked
        align_axis: A vector value or attribute representing the secondary align axis to try to adjust
        align_target_point: The point value or attribute that the secondary axis should aim at
        align_matrix: A matrix applied to the align_target_point

    Returns:
    """
    return _create_utility_and_return_output(
        "aimMatrix",
        inputMatrix=matrix,
        primaryInputAxis=keep_axis,
        primaryMode=AlignMatrixPrimaryMode.LOCK_AXIS,
        secondaryInputAxis=align_axis,
        secondaryMode=AlignMatrixSecondaryMode.AIM,
        secondaryTargetVector=align_target_point,
        secondaryTargetMatrix=align_matrix,
    )


def blend_matrix(input_matrix, target_matrix, weight):
    """
    Args:
        input_matrix: A matrix value or attribute
        target_matrix: A matrix value or attribute
        weight: A weight value or attribute (0..1)
    """
    return blend_matrix_multi(input_matrix, (target_matrix, weight))


def blend_matrix_multi(input_matrix, *targets_and_weights):
    """
    Blend a matrix towards one or more target matrices using a `blendMatrix` node.
    The order matters, since blends are calculated in a stack, i.e. the results of
    the previous blend get blended with next target and so on.

    Args:
        input_matrix: A transformation matrix value or attribute
        *targets_and_weights: A list of tuples containing (target matrix, weight) values or attributes
    """
    blend = pm.shadingNode("blendMatrix", asUtility=True)
    set_or_connect_attr(blend.inputMatrix, input_matrix)
    for i, (matrix, weight) in enumerate(targets_and_weights):
        set_or_connect_attr(blend.target[i].targetMatrix, matrix)
        set_or_connect_attr(blend.target[i].weight, weight)
    return blend.outputMatrix


def create_utility_node(node_type, **kwargs):
    """
    Create and return a utility node.
    Sets or connects any attributes defined by kwargs.
    """
    node = pm.shadingNode(node_type, asUtility=True)
    for key, value in kwargs.items():
        set_or_connect_attr(node.attr(key), value)
    return node


def _create_utility_and_return_output(node_type, **kwargs):
    """
    Create and return a utility node, as well as the attrs
    on the node that were set or connected to based on kwargs.
    """
    node = pm.shadingNode(node_type, asUtility=True)
    all_dst_attrs = []
    for key, value in kwargs.items():
        dst_attrs = set_or_connect_attr(node.attr(key), value)
        all_dst_attrs.extend(dst_attrs)
    input_attrs = _filter_for_best_input_attrs(all_dst_attrs)
    return _get_output_attr_from_largest(input_attrs)
