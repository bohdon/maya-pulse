
import unittest
import pymel.core as pm

import pulse
import pulse.controlshapes

EXAMPLE_BLUEPRINT_A = """
version: 1.0.0
rigName: TestRig
steps:
  name: Root
  children:
  - name: Import References
    action:
      id: Pulse.ImportReferences
  - name: Build Core Hierarchy
    action:
      id: Pulse.BuildCoreHierarchy
      allNodes: true
  - name: Main
    children:
    - name: GroupA
      children:
      - name: GroupC
    - name: GroupB
  - name: Rename Scene
    action:
      id: Pulse.RenameScene
"""


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

    def test_build_steps(self):
        bp = pulse.Blueprint()

        stepA = pulse.BuildStep('StepFirst')
        stepB = pulse.BuildStep('StepB')
        stepC = pulse.BuildStep('StepC')
        stepX = pulse.BuildStep('StepX')
        stepY = pulse.BuildStep('StepY')
        stepZ = pulse.BuildStep('StepZ')

        self.assertEqual(stepA.getDisplayName(), 'StepFirst (0)')
        stepA.setName(None)
        self.assertEqual(stepA.name, 'New Step')
        stepA.setName('StepA')

        bp.rootStep.addChild(stepA)
        self.assertTrue(bp.rootStep.numChildren() == 1)
        self.assertEqual(stepA.parent, bp.rootStep)
        self.assertTrue(stepA.hasParent(bp.rootStep))

        bp.rootStep.addChild(stepA)
        self.assertTrue(bp.rootStep.numChildren() == 1)

        bp.rootStep.removeChild(stepA)
        self.assertTrue(bp.rootStep.numChildren() == 0)
        self.assertEqual(stepA.parent, None)

        bp.rootStep.insertChild(0, stepA)
        self.assertTrue(bp.rootStep.numChildren() == 1)
        self.assertEqual(stepA.parent, bp.rootStep)

        bp.rootStep.insertChild(0, stepB)
        self.assertTrue(bp.rootStep.numChildren() == 2)
        self.assertEqual(stepB.parent, bp.rootStep)

        bp.rootStep.insertChild(0, stepC)
        self.assertTrue(bp.rootStep.numChildren() == 3)
        self.assertEqual(stepC.parent, bp.rootStep)

        self.assertEqual(bp.rootStep.getChildAt(0), stepC)
        self.assertEqual(bp.rootStep.getChildAt(1), stepB)
        self.assertEqual(bp.rootStep.getChildAt(2), stepA)

        stepA.setName('StepC')
        self.assertEqual(stepA.name, 'StepC 1')

        stepC.addChild(stepX)
        stepY.setParent(stepX)
        stepY.addChild(stepZ)
        self.assertEqual(stepC.getFullPath(), 'StepC')
        self.assertEqual(stepX.getFullPath(), 'StepC/StepX')
        self.assertEqual(stepY.getFullPath(), 'StepC/StepX/StepY')
        self.assertEqual(stepZ.getFullPath(), 'StepC/StepX/StepY/StepZ')

        self.assertTrue(stepZ.hasParent(bp.rootStep))
        self.assertTrue(stepZ.hasParent(stepX))
        self.assertFalse(stepX.hasParent(stepY))

        stepY.setParent(stepB)
        self.assertEqual(stepZ.getFullPath(), 'StepB/StepY/StepZ')
        self.assertTrue(stepX.numChildren() == 0)

    def test_deserialize(self):
        bp = pulse.Blueprint()
        bp.loadFromYaml(EXAMPLE_BLUEPRINT_A)

        self.assertEqual(bp.rigName, 'TestRig')
        self.assertTrue(bp.rootStep.numChildren() == 4)

        stepA = bp.getStepByPath('Main/GroupA')
        stepC = bp.getStepByPath('Main/GroupA/GroupC')
        self.assertIsNotNone(stepC)
        self.assertEqual(stepC.parent, stepA)
        self.assertTrue(stepC.hasParent(bp.rootStep))
