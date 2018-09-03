"""
Links are used to ensure that nodes update to
match each others' positions when doing rig layout.

They are like parent constraints that exist without
any additional nodes or connections between nodes,
and are only updated when requested by the designer.

Link information is stored in the scene on each node
using meta data.
"""

import pymel.core as pm
import pymetanode as meta

import pulse.nodes

__all__ = [
    'cleanupLinks',
    'getAllLinkedNodes',
    'getLink',
    'link',
    'snapToLink',
    'unlink',
]

LINK_METACLASS = 'pulse_link'


def link(leader, follower):
    """
    Link the follower to a leader
    """
    meta.setMetaData(follower, className=LINK_METACLASS, data=leader)


def unlink(node):
    """
    Remove a link from a node
    """
    meta.removeMetaData(node, className=LINK_METACLASS)


def getLink(node):
    """
    Return the leader that a node is linked to
    """
    return meta.getMetaData(node, className=LINK_METACLASS)


def getAllLinkedNodes():
    """
    Return all nodes in the scene that are linked
    """
    return meta.findMetaNodes(className=LINK_METACLASS)


def cleanupLinks():
    """
    Cleanup all nodes in the scene that have broken links
    """
    nodes = meta.findMetaNodes(className=LINK_METACLASS)
    for node in nodes:
        if not getLink(node):
            unlink(node)


def snapToLink(node, translate=True, rotate=True, scale=True):
    """
    Update a node to match its followers position
    """
    leader = getLink(node)
    if leader:
        wm = pulse.nodes.getWorldMatrix(leader)
        pulse.nodes.setWorldMatrix(
            node, wm,
            translate=translate,
            rotate=rotate,
            scale=scale)
