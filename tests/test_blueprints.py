import unittest
import pymel.core as pm

from pulse.blueprints import Blueprint, BlueprintSettings, BlueprintBuilder
import pulse.buildItems
import pulse.controlshapes
import pulse.rigs

EXAMPLE_BLUEPRINT_A = """
version: 1.0.0
settings:
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

    def tearDown(self):
        pm.delete(pulse.rigs.getAllRigs())

    def test_build(self):
        bp = Blueprint()
        bp.set_setting(BlueprintSettings.RIG_NAME, 'testRig')
        bp.add_default_actions()

        mainStep = bp.get_step_by_path('Main')

        ctlNode = pm.polyCube(n='my_ctl')[0]

        ctlStep = pulse.buildItems.BuildStep(action_id='Pulse.AnimControl')
        ctlStep.action_proxy.get_attr('controlNode').set_value(ctlNode)
        mainStep.add_child(ctlStep)

        self.assertTrue(len(mainStep.children) == 1)

        builder = BlueprintBuilder(bp)
        builder.start()

        self.assertTrue(builder.is_finished)
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
        bp = Blueprint()

        stepA = pulse.buildItems.BuildStep('StepFirst')
        stepB = pulse.buildItems.BuildStep('StepB')
        stepC = pulse.buildItems.BuildStep('StepC')
        stepX = pulse.buildItems.BuildStep('StepX')
        stepY = pulse.buildItems.BuildStep('StepY')
        stepZ = pulse.buildItems.BuildStep('StepZ')

        self.assertEqual(stepA.get_display_name(), 'StepFirst (0)')
        stepA.set_name(None)
        self.assertEqual(stepA.name, 'New Step')
        stepA.set_name('StepA')

        bp.rootStep.add_child(stepA)
        self.assertTrue(bp.rootStep.num_children() == 1)
        self.assertEqual(stepA.parent, bp.rootStep)
        self.assertTrue(stepA.has_parent(bp.rootStep))

        bp.rootStep.add_child(stepA)
        self.assertTrue(bp.rootStep.num_children() == 1)

        bp.rootStep.remove_child(stepA)
        self.assertTrue(bp.rootStep.num_children() == 0)
        self.assertEqual(stepA.parent, None)

        bp.rootStep.insert_child(0, stepA)
        self.assertTrue(bp.rootStep.num_children() == 1)
        self.assertEqual(stepA.parent, bp.rootStep)

        bp.rootStep.insert_child(0, stepB)
        self.assertTrue(bp.rootStep.num_children() == 2)
        self.assertEqual(stepB.parent, bp.rootStep)

        bp.rootStep.insert_child(0, stepC)
        self.assertTrue(bp.rootStep.num_children() == 3)
        self.assertEqual(stepC.parent, bp.rootStep)

        self.assertEqual(bp.rootStep.get_child_at(0), stepC)
        self.assertEqual(bp.rootStep.get_child_at(1), stepB)
        self.assertEqual(bp.rootStep.get_child_at(2), stepA)

        stepA.set_name('StepC')
        self.assertEqual(stepA.name, 'StepC 1')

        stepC.add_child(stepX)
        stepY.set_parent(stepX)
        stepY.add_child(stepZ)
        self.assertEqual(stepC.get_full_path(), 'StepC')
        self.assertEqual(stepX.get_full_path(), 'StepC/StepX')
        self.assertEqual(stepY.get_full_path(), 'StepC/StepX/StepY')
        self.assertEqual(stepZ.get_full_path(), 'StepC/StepX/StepY/StepZ')

        self.assertTrue(stepZ.has_parent(bp.rootStep))
        self.assertTrue(stepZ.has_parent(stepX))
        self.assertFalse(stepX.has_parent(stepY))

        stepY.set_parent(stepB)
        self.assertEqual(stepZ.get_full_path(), 'StepB/StepY/StepZ')
        self.assertTrue(stepX.num_children() == 0)

    def test_deserialize(self):
        bp = Blueprint()
        bp.load_from_yaml(EXAMPLE_BLUEPRINT_A)

        self.assertEqual(bp.get_setting(BlueprintSettings.RIG_NAME), 'TestRig')
        self.assertTrue(bp.rootStep.num_children() == 4)

        stepA = bp.get_step_by_path('Main/GroupA')
        stepC = bp.get_step_by_path('Main/GroupA/GroupC')
        self.assertIsNotNone(stepC)
        self.assertEqual(stepC.parent, stepA)
        self.assertTrue(stepC.has_parent(bp.rootStep))
