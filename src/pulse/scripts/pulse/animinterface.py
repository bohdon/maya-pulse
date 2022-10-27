from .vendor import pymetanode as meta
from .vendor import yaml

ANIM_CTL_METACLASS = 'pulse_animcontrol'


def get_all_anim_ctls():
    """
    Return all animation controls in the scene
    """
    return meta.findMetaNodes(ANIM_CTL_METACLASS)


def get_rig_anim_interface(ctls, exclude_attrs=None):
    """
    Return the animation interface for a set of controls.
    Gathers information about the keyable attributes and
    default world transforms of each control, and returns
    it as a dict.

    Args:
        ctls (list of PyNode): A list of animation control nodes
        exclude_attrs (list of str): List of keyable attributes to exclude

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
    interface = {
        'ctls': {}
    }

    for ctl in ctls:
        ctl_name = ctl.nodeName()
        ctl_interface = get_anim_ctl_interface(ctl, exclude_attrs=exclude_attrs)
        interface['ctls'][ctl_name] = ctl_interface
    return interface


def get_anim_ctl_interface(ctl, exclude_attrs=None):
    """
    Return the animation interface for an animation control node.

    Args:
        ctl (PyNode): An animation control node
        exclude_attrs (list of str): List of keyable attributes to exclude

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
    interface = {
        # get world matrix, simplified
        'worldMatrix': get_approx_attr_value(ctl.wm),
        'attrs': {}
    }

    # get all keyable attribute info
    attrs = ctl.listAttr(keyable=True)
    for attr in attrs:
        attr_info = {}
        attr_name = attr.longName()
        if exclude_attrs:
            if attr_name in exclude_attrs:
                continue

        attr_info['type'] = attr.type()
        attr_info['default'] = get_approx_attr_value(attr)

        if attr.type() == 'enum':
            attr_info['enums'] = get_enum_dict_by_index(attr.getEnums())

        interface['attrs'][attr_name] = attr_info

    return interface


def get_enum_dict_by_index(enum_dict):
    """
    Return an EnumDict indexed by enum index, instead of
    by the enum name, since the index is the important value when animating.
    """
    return dict([(v, k) for k, v in enum_dict.items()])


def get_approx_attr_value(attr):
    """
    Return an approximate representation of an attribute value
    by rounding any numerical values to a fixed precision.

    Args:
        attr (Attribute): A PyNode attribute
    """
    attr_value = attr.get()
    return get_approx_value(attr_value)


def get_approx_value(value):
    """
    Return an approximate representation of any numerical value.
    Handles lists of values, and does not modify the value if it is not numerical.

    Args:
        value: Any object or value

    Returns:
        An approximate version of the value if it is numeric, or
        a list of numeric values (handles recursion), otherwise,
        the unmodified value.
    """
    if isinstance(value, (int, float)):
        approx_val = round(value, 3)
        return 0 if approx_val == 0 else approx_val
    elif hasattr(value, '__iter__'):
        return [get_approx_value(v) for v in value]
    else:
        return value


def save_rig_anim_interface(filepath, exclude_attrs=None, find_control_func=None):
    """
    Save the animation interface of a rig to a file.

    Args:
        filepath (str): The path to the file to write
        exclude_attrs (list of str): List of keyable attributes to exclude
        find_control_func (function): An optional function used to gather
            all animation controls. Must return a list of PyNodes.
    """
    if find_control_func is not None:
        ctls = find_control_func()
    else:
        ctls = get_all_anim_ctls()

    interface = get_rig_anim_interface(ctls, exclude_attrs=exclude_attrs)

    with open(filepath, 'w') as fp:
        yaml.safe_dump(interface, fp, default_flow_style=False)

    print(filepath)
