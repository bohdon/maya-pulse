from __future__ import print_function

import pymetanode as meta
import pulse.vendor.yaml as yaml

__all__ = [
    'getAllAnimControls',
    'getAnimControlInterface',
    'getApproximateValue',
    'getRigAnimInterface',
    'saveRigAnimInterface',
]


def getAllAnimControls():
    """
    Return all animation controls in the scene
    """
    return meta.findMetaNodes('pulse_animcontrol')


def getRigAnimInterface(ctls, excludeAttrs=None):
    """
    Return the animation interface for a set of controls.
    Gathers information about the keyable attributes and
    default world transforms of each control, and returns
    it as a dict.

    Args:
        ctls (list of PyNode): A list of animation control nodes
        excludeAttrs (list of str): List of keyable attributes to exclude

    Returns:
        Dict containing info about each control, and each keyable
        attribute on those controls. See `gteAnimControlInterface`
        for an example of a specific control interface.

        Example:
        {
            'ctls': {
                'my_ctl': {
                    ...
                },
                'my_other_ctl': {
                    ...
                },
                ...
            }
        }
    """
    interface = {}

    interface['ctls'] = {}
    for ctl in ctls:
        ctlName = ctl.nodeName()
        ctlInterface = getAnimControlInterface(ctl, excludeAttrs=excludeAttrs)
        interface['ctls'][ctlName] = ctlInterface
    return interface


def getAnimControlInterface(ctl, excludeAttrs=None):
    """
    Return the animation interface for an animation control node.

    Args:
        ctl (PyNode): An animation control node
        excludeAttrs (list of str): List of keyable attributes to exclude

    Returns:
        Example:
            {
                'worldMatrix': [
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0],
                    [0, 0, 0, 0]
                ],
                'attrs': {
                    'translateX': {
                        'type': 'doubleLinear',
                        'default': '123.456',
                        ...
                    },
                    'space': {
                        'type': 'enum',
                        'default': 0
                        'enums': [
                            'root',
                            'world'
                        ]
                    }
                }
            }
    """
    interface = {}

    # get world matrix, simplified
    interface['worldMatrix'] = getApproximateAttrValue(ctl.wm)

    # get all keyable attribute info
    interface['attrs'] = {}
    attrs = ctl.listAttr(keyable=True)
    for attr in attrs:
        attrInfo = {}
        attrName = attr.longName()
        if excludeAttrs:
            if attrName in excludeAttrs:
                continue

        attrInfo['type'] = attr.type()
        attrInfo['default'] = getApproximateAttrValue(attr)

        if attr.type() == 'enum':
            attrInfo['enums'] = getEnumDictByIndex(attr.getEnums())

        interface['attrs'][attrName] = attrInfo

    return interface


def getEnumDictByIndex(enumDict):
    """
    Return an EnumDict indexed by enum index, instead of
    by the enum name, since the index is the important value when animating.
    """
    return dict([(v, k) for k, v in enumDict.items()])


def getApproximateAttrValue(attr):
    """
    Return an approximate representation of an attribute value
    by rounding any numerical values to a fixed precision.

    Args:
        attr (Attribute): A PyNode attribute
    """
    attrValue = attr.get()
    return getApproximateValue(attrValue)


def getApproximateValue(value):
    """
    Return an approximate representation of any numerical value.
    Handles lists of values, and does not modify the value if it
    is not numerical.

    Args:
        value: Any object or value

    Returns:
        An approximate version of the value if it is numeric, or
        a list of numeric values (handles recursion), otherwise,
        the unmodified value.
    """
    if isinstance(value, (int, float)):
        approxVal = round(value, 3)
        return 0 if approxVal == 0 else approxVal
    elif hasattr(value, '__iter__'):
        return [getApproximateValue(v) for v in value]
    else:
        return value


def saveRigAnimInterface(filepath, excludeAttrs=None, findControlFunc=None):
    """
    Save the animation interface of a rig to a file.

    Args:
        filepath (str): The path to the file to write
        excludeAttrs (list of str): List of keyable attributes to exclude
        findControlFunc (function): An optional function used to gather
            all animation controls. Must return a list of PyNodes.
    """
    if findControlFunc is not None:
        ctls = findControlFunc()
    else:
        ctls = getAllAnimControls()

    interface = getRigAnimInterface(ctls, excludeAttrs=excludeAttrs)

    with open(filepath, 'w') as fp:
        yaml.safe_dump(interface, fp, default_flow_style=False)

    print(filepath)
