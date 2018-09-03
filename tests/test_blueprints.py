
import unittest
import pymel.core as pm

import pulse
import pulse.controlshapes


class TestBlueprints(unittest.TestCase):

    def test_build(self):
        bp = pulse.Blueprint()
        bp.rigName = 'testRig'
        bp.initializeDefaultActions()

        mainStep = bp.getStepByPath('Main')

        ctlNode = pm.polyCube(n='my_ctl')[0]

        ctlStep = pulse.BuildStep(actionId='Pulse.AnimControl')
        ctlStep.actionProxy.setAttrValue('controlNode', ctlNode)
        mainStep.addChild(ctlStep)

        self.assertTrue(len(mainStep.children) == 1)

        builder = pulse.BlueprintBuilder(bp)
        builder.start()

        self.assertTrue(builder.isFinished)
        self.assertTrue(len(builder.errors) == 0)

        rig_node = pm.ls('testRig')
        self.assertTrue(len(rig_node) == 1)

        # make sure anim control action was run
        ctlNode = pm.ls('my_ctl')[0]
        self.assertTrue(ctlNode.tx.isKeyable())
        self.assertFalse(ctlNode.v.isKeyable())
        self.assertFalse(ctlNode.rp.isKeyable())
        ctlParentNode = ctlNode.getParent()
        self.assertEqual(ctlParentNode.nodeName(), 'my_ctl_offset')

        # check top-level transforms (4 cameras + 1 rig node)
        assemblies = pm.ls(assemblies=True)
        self.assertTrue(len(assemblies) == 5)

