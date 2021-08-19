import logging

import maya.cmds as cmds
import pymel.core as pm

from . import nodes

LOG = logging.getLogger(__name__)

IS_MATRIX_PLUGIN_LOADED = False
IS_QUAT_PLUGIN_LOADED = False


def loadMatrixPlugin():
    global IS_MATRIX_PLUGIN_LOADED
    if not IS_MATRIX_PLUGIN_LOADED:
        try:
            pm.loadPlugin('matrixNodes', quiet=True)
            IS_MATRIX_PLUGIN_LOADED = True
        except:
            pass


def loadQuatPlugin():
    global IS_QUAT_PLUGIN_LOADED
    if not IS_QUAT_PLUGIN_LOADED:
        try:
            pm.loadPlugin('quatNodes', quiet=True)
            IS_QUAT_PLUGIN_LOADED = True
        except:
            pass


def getConstraintWeightAttr(leader, constraint):
    """
    Return the weight attribute from a constraint that
    corresponds to a specific leader node.

    Args:
        leader (PyNode): A node that is one of the leaders of a constraint
        constraint (PyNode): A constraint node
    """
    for i, target in enumerate(constraint.getTargetList()):
        if leader == target:
            return constraint.getWeightAliasList()[i]


def getOutputAttr(input):
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
    # map of node types to special output retrieval functions
    outputFuncs = {
        'plusMinusAverage': getPlusMinusAverageOutputAttr
    }

    # map of node types to output attribute names
    outputAttrs = {
        'addDoubleLinear': 'output',
        'angleBetween': 'angle',
        'blendColors': 'output',
        'choice': 'output',
        'clamp': 'output',
        'condition': 'outColor',
        'distanceBetween': 'distance',
        'multiplyDivide': 'output',
        'reverse': 'output',
        'setRange': 'outValue',
        'vectorProduct': 'output',
        'floatMath': 'outFloat',
    }

    node = input.node()
    nodeType = node.nodeType()
    if nodeType not in outputAttrs and nodeType not in outputFuncs:
        LOG.warning(
            "No output found for utility type '{0}'".format(nodeType))
        return None

    if nodeType in outputFuncs:
        fnc = outputFuncs[nodeType]
        return fnc(input)

    elif nodeType in outputAttrs:
        outputAttrName = outputAttrs[nodeType]
        outputAttr = nodes.safeGetAttr(node, outputAttrName)

        if outputAttr and outputAttr.isCompound():
            if isinstance(input, pm.Attribute) and input.isChild():
                # input and output are both compound, return
                # child of output at the same child index
                index = nodes.getCompoundAttrIndex(input)
                return outputAttr.getChildren()[index]

        return outputAttr


def getPlusMinusAverageOutputAttr(input):
    """
    Return the output attr of a plusMinusAverage node.
    Returns the output that matches the dimension of the input
    (if its an attribute), otherwise returns the 1D output.

    Args:
        input: A PyNode or Attribute for which to return an output

    Returns:
        An Attribute of the node, which could be one of
        output1D, output2D, output3D or any children.
        Returns output1D if the given input is the node and not an attribute.
    """
    inputNode = input.node()

    if not isinstance(input, pm.Attribute):
        return inputNode.output1D

    numChildren = 0
    if input.isCompound():
        numChildren = input.numChildren()
    elif input.isChild():
        numChildren = input.getParent().numChildren()

    if numChildren > 0:
        # get output of same dimension (1D, 2D, or 3D)
        outputAttr = inputNode.attr('output{0}D'.format(numChildren))

        if input.isChild():
            # return a matching child attribute
            index = nodes.getCompoundAttrIndex(input)
            return outputAttr.getChildren()[index]

        return outputAttr

    # if all else fails
    return inputNode.output1D


def getLargestDimensionAttr(attrs):
    """
    Return the attr that has the largest dimension.

    Args:
        attrs: A list of Attributes
    """
    largestDim = 0
    largestAttr = None
    for attr in attrs:
        dim = nodes.getAttrDimension(attr)
        if dim > largestDim:
            largestDim = dim
            largestAttr = attr
    return largestAttr


def _filterForBestInputAttrs(attrs):
    """
    Return a list of attrs that represents
    only the attrs that correspond to specific
    output attrs.

    If none of the attrs correspond to an output,
    the original attrs list will be returned.
    """
    nonInputAttrNames = [
        'firstTerm',
        'secondTerm',
    ]
    # TODO: check node type
    filteredAttrs = [a for a in attrs if a.longName() not in nonInputAttrNames]
    if filteredAttrs:
        return filteredAttrs
    else:
        return attrs


def _getOutputAttrFromLargest(attrs):
    """
    Return the output attr of a utility node using the
    attr with the largest dimension.

    Args:
        attrs: A list of Attributes
    """
    largest = getLargestDimensionAttr(attrs)
    return getOutputAttr(largest)


def getInputConnections(inputVal, destAttr):
    """
    Return a list of (src, dst) tuples representing connections to be made
    between an input and destAttr. Input can be an Attribute or just
    a value, and the results are intended for use with `setOrConnectAttr`.

    More than one connection tuple may be returned in situations where
    the input and destination dimensions don't match.
    e.g. ([1, 2], input) -> (1, inputX), (2, inputY)

    Args:
        inputVal: An Attribute or value to set or connect to destAttr
        destAttr (Attribute): The attribute that to receive the inputVal
    """
    if not inputVal:
        return []

    def _child(obj, index):
        """
        Return the child of an object whether
        its a list-like object or compound attribute.
        If the dimension of obj is 1, returns obj.
        """
        if nodes.getAttrOrValueDimension(obj) == 1:
            return obj
        if isinstance(obj, pm.Attribute):
            return obj.getChildren()[index]
        else:
            return obj[index]

    # simplify the input if possible
    if isinstance(inputVal, (list, tuple)):
        if len(inputVal) == 1:
            inputVal = inputVal[0]

    inputDim = nodes.getAttrOrValueDimension(inputVal)
    destAttrDim = nodes.getAttrDimension(destAttr)

    # get the overlapping dimension
    dim = min(inputDim, destAttrDim)

    if inputDim == destAttrDim:
        # TODO: only do this if input is an Attribute?
        # direct connection is allowed
        return [(inputVal, destAttr)]
    else:
        # this represents n to m dimension attr/values and
        # all other odd associations
        ins = [_child(inputVal, i) for i in range(dim)]
        ats = [_child(destAttr, i) for i in range(dim)]
        return list(zip(ins, ats))


def setOrConnectAttr(attr, val):
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
    cons = getInputConnections(val, attr)
    for srcVal, dstAttr in cons:
        if isinstance(srcVal, pm.Attribute):
            srcVal >> dstAttr
        else:
            dstAttr.set(srcVal)
    return [con[1] for con in cons]


def add(*inputs):
    """ Return an attribute that represents the given inputs added together. """
    return plusMinusAverage(inputs, 1)


def subtract(*inputs):
    """
    Return an attribute that represents the given inputs subtracted in
    sequential order.
    Eg. input[0] - input[1] - ... - input[n]
    All inputs can be either attributes or values.
    """
    return plusMinusAverage(inputs, 2)


def average(*inputs):
    """ Return an attribute that represents the average of the given inputs. """
    return plusMinusAverage(inputs, 3)


def plusMinusAverage(inputs, operation):
    node = pm.shadingNode('plusMinusAverage', asUtility=True)
    node.operation.set(operation)

    if len(inputs) > 0:
        inputDim = nodes.getAttrOrValueDimension(inputs[0])
        if inputDim == 1:
            multiattr = node.input1D
        elif inputDim == 2:
            multiattr = node.input2D
        elif inputDim == 3:
            multiattr = node.input3D
        else:
            raise ValueError(
                "Input dimension is not 1D, 2D, or 3D: {0}".format(inputs))
        for i, input in enumerate(inputs):
            # hook up inputs
            setOrConnectAttr(multiattr[i], input)
        return getOutputAttr(multiattr)
    else:
        return getOutputAttr(node)


# TODO: move internal functions to another module so these functions can shadow builtin names

def min_float(a, b):
    """
    Return an attribute that represents min(a, b).
    Only supports float values.
    """
    return _createUtilityAndReturnOutput(
        'floatMath', floatA=a, floatB=b, operation=4)


def max_float(a, b):
    """
    Return an attribute that represents max(a, b).
    Only supports float values.
    """
    return _createUtilityAndReturnOutput(
        'floatMath', floatA=a, floatB=b, operation=5)


def multiply(a, b):
    """ Return an attribute that represents a * b. """
    return multiplyDivide(a, b, 1)


def divide(a, b):
    """ Return an attribute that represents a / b. """
    return multiplyDivide(a, b, 2)


def pow(a, b):
    """ Return an attribute that represents a ^ b. """
    return multiplyDivide(a, b, 3)


def sqrt(a):
    """ Return an attribute that represents the square root of a. """
    return multiplyDivide(a, 0.5, 3)


def multiplyDivide(input1, input2, operation=1):
    return _createUtilityAndReturnOutput(
        'multiplyDivide', input1=input1, input2=input2, operation=operation)


def reverse(input):
    return _createUtilityAndReturnOutput('reverse', input=input)


def clamp(input, min, max):
    """
    Return an attribute that represents the given input clamped in the range
    [min, max].
    All inputs can be either attributes or values.
    """
    return _createUtilityAndReturnOutput('clamp', input=input, min=min, max=max)


def setRange(value, min, max, oldMin, oldMax):
    """
    Return an attribute that represents the given input mapped from the range
    [oldMin, oldMax] to the range [min, max].
    All inputs can be either attributes or values.
    """
    return _createUtilityAndReturnOutput(
        'setRange', value=value, min=min, max=max, oldMin=oldMin, oldMax=oldMax)


def blend2(a, b, blender):
    """
    Given two inputs of 1D, 2D, or 3D using a blender value, create a blend node and return
    the output attribute. If 1D, returns the outputX, if 2D or 3D, returns the output.
    """
    # clamp blender
    if not isinstance(blender, pm.Attribute):
        blender = max(min(blender, 1), 0)
    return _createUtilityAndReturnOutput(
        'blendColors', color1=a, color2=b, blender=blender)


def distance(a, b, ws=True, makeLocal=True):
    """
    Return an attribute on a distance node that represents the distance
    between nodes A and B.

    `a` -- node A
    `b` -- node B
    `ws` -- use worldspace matrices
    `makeLocal` -- if True, makes both matrix inputs to the
        distance utils be matrices local to node A
    """
    nodetype = 'distanceBetween'
    inMatrix1 = a.node().wm if ws and not makeLocal else a.node().m
    inMatrix2 = b.node().wm if ws or makeLocal else b.node().m
    if makeLocal:
        mult = pm.createNode('multMatrix')
        inMatrix2 >> mult.matrixIn[0]
        a.node().pim >> mult.matrixIn[1]
        inMatrix2 = mult.matrixSum
    n = createUtilityNode(nodeType=nodetype, inMatrix1=inMatrix1,
                          inMatrix2=inMatrix2)
    return n.distance


def equal(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a == b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 0)


def notEqual(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a != b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 1)


def greaterThan(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a > b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 2)


def greaterOrEqual(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a >= b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 3)


def lessThan(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a < b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 4)


def lessOrEqual(a, b, trueVal, falseVal):
    """
    Return an attribute that represents trueVal if a <= b else falseVal.
    Inputs can be either attributes or values.
    """
    return condition(a, b, trueVal, falseVal, 5)


def condition(firstTerm, secondTerm, trueVal, falseVal, operation):
    """
    Create a condition that returns either trueVal or falseVal based
    on the comparison of firstTerm and secondTerm.

    Args:
        operaiton (int): An int value representing the type of comparison:
            0 - Equal
            1 - Not Equal
            2 - Greater Than
            3 - Greater or Equal
            4 - Less Than
            5 - Less or Equal
    """
    return _createUtilityAndReturnOutput(
        'condition', firstTerm=firstTerm, secondTerm=secondTerm,
        colorIfTrue=trueVal, colorIfFalse=falseVal, operation=operation)


def choice(selector, *inputs):
    choiceNode = pm.shadingNode('choice', asUtility=True)
    setOrConnectAttr(choiceNode.selector, selector)
    for i, input in enumerate(inputs):
        setOrConnectAttr(choiceNode.input[i], input)
    return choiceNode.output


def multMatrix(*matrices):
    loadMatrixPlugin()
    mmtx = pm.shadingNode('multMatrix', asUtility=True)
    for i, matrix in enumerate(matrices):
        setOrConnectAttr(mmtx.matrixIn[i], matrix)
    return mmtx.matrixSum


def decomposeMatrix(matrix):
    """
    Create a `decomposeMatrix` utility node.

    Returns:
        The `decomposeMatrix` node (not output attributes).
    """
    loadMatrixPlugin()
    return createUtilityNode(
        'decomposeMatrix', inputMatrix=matrix)


def decomposeMatrixAndConnect(matrix, transform):
    """
    Decompose a matrix and connect it to the translate, rotate,
    and scales of a transform node.

    Args:
        matrix (Attribute): A matrix attribute
        transform (PyNode): A transform node

    Returns:
        the decomposeMatrix node
    """
    decomp = decomposeMatrix(matrix)
    decomp.outputTranslate >> transform.translate
    decomp.outputRotate >> transform.rotate
    decomp.outputScale >> transform.scale
    return decomp


def connectMatrix(matrix, transform):
    """
    A generalized function for connecting a matrix to a transform.
    For Maya 2020 and higher this uses offsetParentMatrix connections.
    For Maya 2019 and below this uses a decompose matrix node and
    connections to translate, rotate, and scale. Assumes the connect
    is world space, and will disable inheritsTransform on the target.
    """
    if cmds.about(api=True) >= 20200000:
        transform.t.set(0, 0, 0)
        transform.r.set(0, 0, 0)
        transform.s.set(1, 1, 1)
        nodes.connectOffsetMatrix(
            matrix, transform, preservePosition=False, preserveTransformValues=False)
    else:
        transform.inheritsTransform.set(False)
        decomposeMatrixAndConnect(matrix, transform)


def createUtilityNode(nodeType, **kwargs):
    """
    Create and return a utility node.
    Sets or connects any attributes defined by kwargs.
    """
    node = pm.shadingNode(nodeType, asUtility=True)
    for key, value in kwargs.items():
        setOrConnectAttr(node.attr(key), value)
    return node


def _createUtilityAndReturnOutput(nodeType, **kwargs):
    """
    Create and return a utility node, as well as the attrs
    on the node that were set or connected to based on kwargs.
    """
    node = pm.shadingNode(nodeType, asUtility=True)
    allDstAttrs = []
    for key, value in kwargs.items():
        dstAttrs = setOrConnectAttr(node.attr(key), value)
        allDstAttrs.extend(dstAttrs)
    inputAttrs = _filterForBestInputAttrs(allDstAttrs)
    return _getOutputAttrFromLargest(inputAttrs)
