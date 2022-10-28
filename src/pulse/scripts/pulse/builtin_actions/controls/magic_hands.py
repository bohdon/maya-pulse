from pulse import nodes
from pulse import util_nodes
from pulse.build_items import BuildAction, BuildActionError
from pulse.build_items import BuildActionAttributeType as AttrType


class MagicHandsAction(BuildAction):
    """
    Controls all fingers of a hand using individual rotate axes for quick posing.
    """

    id = 'Pulse.MagicHands'
    display_name = 'Magic Hands'
    color = (.85, .65, .4)
    category = 'Controls'

    attr_definitions = [
        dict(name='control', type=AttrType.NODE, description='The magic hands control'),
        dict(name='fingerPosition', type=AttrType.FLOAT, value=0,
             description='Position of the finger along the hand, 0..1, 0 = pointer, 1 = pinky'),
        dict(name='metaRotateScale', type=AttrType.FLOAT, value=-10, min=-1000, max=1000,
             description='Scale applied to translate values to create metacarpal rotate values'),
        dict(name='splayScale', type=AttrType.FLOAT, value=15, min=-1000, max=1000,
             description='Scale applied to scale values to create finger splay rotate values'),
        dict(name='ctl1', type=AttrType.NODE, optional=True, description='The metacarpal ctl of the finger'),
        dict(name='ctl2', type=AttrType.NODE, optional=True, description='The proximal ctl of the finger'),
        dict(name='ctl3', type=AttrType.NODE, optional=True, description='The middle ctl of the finger'),
        dict(name='ctl4', type=AttrType.NODE, optional=True, description='The distal ctl of the finger'),
    ]

    _offsetName = '{0}_magic'

    def validate(self):
        if not self.ctl1 and not self.ctl2 and not self.ctl3 and not self.ctl4:
            raise BuildActionError("No controls were given")

    def run(self):
        finger_ctls = [self.ctl2, self.ctl3, self.ctl4]
        finger_ctls = [c for c in finger_ctls if c]

        # TODO(bsayre): reuse these attributes across multiple fingers
        # convert finger position from 0..1, to 1..-1
        splay_factor = (self.fingerPosition - 0.5) * 2.0
        # get a zeroed scaleY attr for driving splay
        sy_zeroed = util_nodes.add(self.control.sy, -1)

        if self.ctl1:
            # {metacarpal}.rz = (sy - 1) * splayFactor * splayScale * 0.5
            metacarpal_rz = util_nodes.multiply(sy_zeroed, splay_factor * self.splayScale * 0.5)

            # create and connect offset
            offset1 = nodes.create_offset_transform(self.ctl1, name=self._offsetName)
            metacarpal_rz >> offset1.rz

        # TODO(bsayre): Expose scalar for rotation-splay?
        splay_attr = util_nodes.multiply(self.control.rx, splay_factor * -1.0)

        # {finger.ry} = ry + (rx * splayFactor)
        fingers_ry = util_nodes.add(self.control.ry, splay_attr)
        # for first joint of a finger, add rotate offset driven by translate
        # {finger}.ry = tz * metaRotateScale
        tz_scaled = util_nodes.multiply(self.control.tz, self.metaRotateScale)
        base_fingers_ry = util_nodes.add(fingers_ry, tz_scaled)
        # {finger.rz} = (sy - 1) * splayFactor * splayScale
        fingers_rz = util_nodes.multiply(sy_zeroed, splay_factor * self.splayScale)

        for i, ctl in enumerate(finger_ctls):
            offset = nodes.create_offset_transform(ctl, name=self._offsetName)
            if i == 0:
                # create and connect offsets
                base_fingers_ry >> offset.ry
            else:
                fingers_ry >> offset.ry
            fingers_rz >> offset.rz
