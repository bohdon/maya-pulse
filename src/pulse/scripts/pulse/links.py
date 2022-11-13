"""
Links are used to ensure that nodes update to match each other's positions when doing rig layout.

They are like parent constraints that exist without any additional nodes
or connections between nodes, and are only updated when requested by the designer.

Link information is stored in the scene on each node using metadata.
"""

import logging
import operator

import pymel.core as pm

from .vendor import pymetanode as meta
from . import joints, math
from . import nodes

LOG = logging.getLogger(__name__)

LINK_METACLASS = "pulse_link"

# map of link types to positioner classes
POSITIONER_CLASS_MAP = {}


class LinkType(object):
    # the linked object will follow the target's position
    DEFAULT = "default"
    # the linked object will be placed automatically
    # based on an ik pole vector, and target distance
    IK_POLE = "ikpole"
    # the linked object will be placed at weighted position between targets
    WEIGHTED = "weighted"


def create_default_link(follower, leader, keep_offset=False):
    positioner = DefaultLinkPositioner()
    positioner.keepOffset = keep_offset
    positioner.create_link(follower, [leader])


def recreate_link(node, keep_offset=False):
    """
    Recreate the link for a node, updating or removing its offsets if necessary.
    """
    link_data = get_link_meta_data(node)
    if link_data:
        positioner = get_positioner(link_data.get("type", LinkType.DEFAULT))
        positioner.keepOffset = keep_offset
        positioner.recreate_link(node, link_data)


def unlink(node):
    """
    Remove a link from a node
    """
    meta.remove_metadata(node, className=LINK_METACLASS)
    LOG.info("Unlinked %s", node)


def is_linked(node):
    return meta.has_metaclass(node, className=LINK_METACLASS)


def get_linked_nodes(node):
    """
    Return all leaders a node is linked to.
    """
    link_data = get_link_meta_data(node)
    positioner = get_positioner(link_data.get("type", LinkType.DEFAULT))
    positioner.get_target_nodes(link_data)


def get_link_meta_data(node):
    """
    Return all link metadata for a node
    """
    result = meta.get_metadata(node, className=LINK_METACLASS)
    if not result:
        return {}

    return result


def get_positioner(link_type) -> "LinkPositioner":
    """
    Create and return a new positioner instance for a link type.
    """
    # get positioner class by link type
    positioner_cls = POSITIONER_CLASS_MAP.get(link_type)
    if not positioner_cls:
        raise ValueError(f"Could not find a LinkPositioner for type: {link_type}")

    positioner = positioner_cls()
    return positioner


def set_link_meta_data(node, link_data):
    """
    Set the metadata for a linked node
    """
    meta.set_metadata(node, className=LINK_METACLASS, data=link_data)


def get_all_linked_nodes():
    """
    Return all nodes in the scene that are linked
    """
    return meta.find_meta_nodes(className=LINK_METACLASS)


def cleanup_links():
    """
    Cleanup all nodes in the scene that have broken links
    """
    link_nodes = meta.find_meta_nodes(className=LINK_METACLASS)
    for node in link_nodes:
        if not get_linked_nodes(node):
            unlink(node)


def apply_link_position(node, quiet=False):
    link_data = get_link_meta_data(node)

    if not link_data:
        if not quiet:
            LOG.warning("Node is not linked to anything: %s", node)
        return

    positioner = get_positioner(link_data.get("type", LinkType.DEFAULT))
    positioner.apply_link_position(node, link_data)


class LinkPositioner(object):
    """
    Handles updating the transform of a linked object
    to match its target.
    """

    # The unique name of the link type represented by this positioner.
    linkType = None

    def __init__(self):
        # if true, maintain the followers current offset when creating a link
        self.keepOffset = False

    def set_link_meta_data(self, node, link_data):
        """
        Set the metadata for a linked node
        """
        link_data["type"] = self.linkType
        meta.set_metadata(node, className=LINK_METACLASS, data=link_data)

    def create_link(self, follower, target_nodes):
        """
        Create a link between a follower and other nodes.
        Default implementation just stores the given target nodes, and optionally calculates offsets.

        Args:
            follower (PyNode): The node to be linked such that it can be positioned later automatically
            target_nodes: The nodes to link to the follower.
        """
        link_data = {
            "targetNodes": target_nodes,
        }

        if self.keepOffset:
            target_mtx = self.calculate_target_matrix(follower, target_nodes, link_data)
            offsets = self.calculate_offsets(follower, target_mtx)
            link_data.update(offsets)

        self.set_link_meta_data(follower, link_data)

    def recreate_link(self, node, link_data):
        """
        Re-create the link between a follower and other nodes.
        Useful for updating offsets.
        """
        self.create_link(node, self.get_target_nodes(link_data))

    def calculate_offsets(self, follower, target_mtx):
        """
        Calculate the offset translate, rotate, and scale for a follower and target matrix.
        """
        precision = 5
        offsets = {}

        # get local matrix of follower relative to leader
        # for some reason TransformationMatrix is not invertible
        offset_mtx = pm.dt.TransformationMatrix(follower.wm.get() * pm.dt.Matrix(target_mtx).inverse())

        # translate
        offsets["offsetTranslate"] = [round(v, precision) for v in offset_mtx.getTranslation("world")]

        # rotate
        rot = offset_mtx.getRotation()
        rot.setDisplayUnit("degrees")
        offsets["offsetRotate"] = [round(v, precision) for v in rot]

        # scale
        offsets["offsetScale"] = [round(v, precision) for v in offset_mtx.getScale("world")]

        return offsets

    def get_offset_matrix(self, link_data):
        """
        Return the offset matrix to apply using any offsets
        defined in the link's metadata.
        """
        t_offset = link_data.get("offsetTranslate")
        r_offset = link_data.get("offsetRotate")
        s_offset = link_data.get("offsetScale")
        mtx = pm.dt.TransformationMatrix()
        if s_offset:
            mtx.setScale(s_offset, "world")
        if r_offset:
            mtx.setRotation(r_offset)
        if t_offset:
            mtx.setTranslation(t_offset, "world")
        return mtx

    def apply_link_position(self, follower, link_data):
        """
        Update the transform of follower using its link data
        """
        target_nodes = self.get_target_nodes(link_data)
        target_mtx = self.calculate_target_matrix(follower, target_nodes, link_data)
        self.set_follower_matrix_with_offset(follower, target_mtx, link_data)

    def calculate_target_matrix(self, follower, target_nodes, link_data):
        """
        Calculate the target matrix to use for applying a linked position to the follower node.
        """
        return nodes.get_world_matrix(target_nodes[0])

    def set_follower_matrix_with_offset(self, follower, target_mtx, link_data):
        """
        Set the new world matrix of a follower node, incorporating
        the saved offsets from link_data if applicable.
        """
        offset_mtx = self.get_offset_matrix(link_data)
        new_mtx = offset_mtx * target_mtx
        nodes.set_world_matrix(follower, new_mtx)

    def get_target_node(self, link_data):
        """
        Return the first target node of the link.
        """
        target_nodes = self.get_target_nodes(link_data)
        if target_nodes:
            return target_nodes[0]

    def get_target_nodes(self, link_data):
        return link_data.get("targetNodes", [])


class DefaultLinkPositioner(LinkPositioner):
    """
    Default link positioner, updates the follower to match a single leaders position.
    """

    linkType = LinkType.DEFAULT

    def calculate_target_matrix(self, follower, target_nodes, link_data):
        """
        Calculate the target matrix to use for a linked node.
        """
        return nodes.get_world_matrix(target_nodes[0])


POSITIONER_CLASS_MAP[DefaultLinkPositioner.linkType] = DefaultLinkPositioner


class IKPoleLinkPositioner(LinkPositioner):
    """
    IK Pole positioner, updates the follower to be placed
    along the pole vector.
    """

    linkType = LinkType.IK_POLE

    def __init__(self):
        super().__init__()

        self.ikpoleDistance = None

    def create_link(self, follower, target_nodes):
        link_data = {
            "targetNodes": target_nodes,
        }

        if self.ikpoleDistance is not None:
            link_data["ikpoleDistance"] = self.ikpoleDistance

        self.set_link_meta_data(follower, link_data)

    def calculate_target_matrix(self, follower, target_nodes, link_data):
        leader = target_nodes[0]
        pole_vector, mid_point = joints.get_ik_pole_vector_and_mid_point_for_joint(leader)

        distance = link_data.get("ikpoleDistance")
        if not distance:
            # calculate distance based on followers current location
            mid_to_follower_vector = follower.getTranslation(space="world") - mid_point
            distance = pole_vector.dot(mid_to_follower_vector)

        new_translate = mid_point + pole_vector * distance
        target_mtx = pm.dt.TransformationMatrix(follower.wm.get())
        target_mtx.setTranslation(new_translate, space="world")
        return target_mtx


POSITIONER_CLASS_MAP[IKPoleLinkPositioner.linkType] = IKPoleLinkPositioner


class WeightedLinkPositioner(LinkPositioner):
    """
    Weighted positioner updates the follower to be placed at a
    weighted location between targets.
    """

    linkType = LinkType.WEIGHTED

    def __init__(self):
        super().__init__()
        # the weights to use when creating a new link
        self.weights = None

    def create_link(self, follower, target_nodes):
        if self.weights is None:
            self.weights = [1] * len(target_nodes)
        elif len(target_nodes) != len(self.weights):
            raise ValueError("weights must be the same length as targetNodes")

        link_data = {
            "targetNodes": target_nodes,
            "weights": self.weights,
        }

        if self.keepOffset:
            target_mtx = self.calculate_target_matrix(follower, target_nodes, link_data)
            offsets = self.calculate_offsets(follower, target_mtx)
            link_data.update(offsets)

        self.set_link_meta_data(follower, link_data)

    def recreate_link(self, node, link_data):
        self.weights = link_data.get("weights")
        self.create_link(node, self.get_target_nodes(link_data))

    def calculate_target_matrix(self, follower, target_nodes, link_data):
        mtxs = [n.wm.get() for n in target_nodes]
        weights = link_data.get("weights", [])
        total_weight = sum(weights)

        # pair and sort by weights, so the highest weight gets starting priority
        mtx_weights = list(zip(mtxs, weights))
        sorted(mtx_weights, key=operator.itemgetter(1), reverse=True)

        target_translate = pm.dt.TransformationMatrix(mtxs[0]).getTranslation(space="world")
        # blend to each following mtx using weights
        for mtx, weight in mtx_weights[1:]:
            alpha = weight / total_weight
            translate = pm.dt.TransformationMatrix(mtx).getTranslation(space="world")
            target_translate = math.lerp_vector(target_translate, translate, alpha)

        # currently only blending translate, the rest stays unmodified
        target_mtx = pm.dt.TransformationMatrix(follower.wm.get())
        target_mtx.setTranslation(target_translate, space="world")
        return target_mtx


POSITIONER_CLASS_MAP[WeightedLinkPositioner.linkType] = WeightedLinkPositioner
