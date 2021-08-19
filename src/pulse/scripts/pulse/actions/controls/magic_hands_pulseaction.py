import pulse.nodes
import pulse.utilnodes
from pulse.core.buildItems import BuildAction, BuildActionError


class MagicHandsAction(BuildAction):
    _offsetName = '{0}_magic'

    def validate(self):
        if not self.ctl1 and not self.ctl2 and not self.ctl3 and not self.ctl4:
            raise BuildActionError("No controls were given")

    def run(self):
        fingerCtls = [self.ctl2, self.ctl3, self.ctl4]
        fingerCtls = [c for c in fingerCtls if c]

        # TODO(bsayre): reuse these attributes across multiple fingers
        # convert finger position from 0..1, to 1..-1
        splayFactor = (self.fingerPosition - 0.5) * 2.0
        # get a zeroed scaleY attr for driving splay
        syZeroed = pulse.utilnodes.add(self.control.sy, -1)

        if self.ctl1:
            # {metacarpal}.rz = (sy - 1) * splayFactor * splayScale * 0.5
            metacarpalRz = pulse.utilnodes.multiply(
                syZeroed, splayFactor * self.splayScale * 0.5)

            # create and connect offset
            offset1 = pulse.nodes.createOffsetTransform(
                self.ctl1, name=self._offsetName)
            metacarpalRz >> offset1.rz

        # TODO(bsayre): Expose scalar for rotation-splay?
        splayAttr = pulse.utilnodes.multiply(
            self.control.rx, splayFactor * -1.0)

        # {finger.ry} = ry + (rx * splayFactor)
        fingersRy = pulse.utilnodes.add(
            self.control.ry, splayAttr)
        # for first joint of a finger, add rotate offset driven by translate
        # {finger}.ry = tz * metaRotateScale
        tzScaled = pulse.utilnodes.multiply(
            self.control.tz, self.metaRotateScale)
        baseFingersRy = pulse.utilnodes.add(
            fingersRy, tzScaled)
        # {finger.rz} = (sy - 1) * splayFactor * splayScale
        fingersRz = pulse.utilnodes.multiply(
            syZeroed, splayFactor * self.splayScale)

        for i, ctl in enumerate(fingerCtls):
            offset = pulse.nodes.createOffsetTransform(
                ctl, name=self._offsetName)
            if i == 0:
                # create and connect offsets
                baseFingersRy >> offset.ry
            else:
                fingersRy >> offset.ry
            fingersRz >> offset.rz
