import unittest

import pymel.core as pm

from pulse.core import Blueprint, BlueprintBuilder, BlueprintSettings
from pulse.core import BuildStep
from pulse.core import load_actions, get_all_rigs

EXAMPLE_BLUEPRINT_A = """
version: 1
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
    def setUp(self) -> None:
        load_actions()

    def tearDown(self):
        pm.delete(get_all_rigs())

    def test_build(self):
        # initialize default actions and set rig name
        blueprint = Blueprint()
        blueprint.reset_to_default()
        blueprint.set_setting(BlueprintSettings.RIG_NAME, "test")

        self.assertGreater(blueprint.root_step.num_children(), 0)

        # disable 'Rename Scene' step since we will not be saving any scenes
        rename_step = blueprint.root_step.get_child_by_name("Rename Scene")
        rename_step.is_disabled = True

        # add anim control build step
        ctl_node = pm.polyCube(name="my_ctl")[0]
        ctl_step = BuildStep(action_id="Pulse.AnimControl")
        ctl_step.action_proxy.get_attr("useAllControls").set_value(False)
        ctl_step.action_proxy.get_attr("controlNodes").set_value([ctl_node])

        main_step = blueprint.get_step_by_path("/Main")
        main_step.add_child(ctl_step)

        self.assertEqual(main_step.num_children(), 1)

        builder = BlueprintBuilder(blueprint)
        builder.start()

        self.assertTrue(builder.is_finished)
        self.assertFalse(builder.has_errors())

        rig_node = pm.ls("test_rig")
        self.assertEqual(len(rig_node), 1)

        # make sure anim control action was run
        ctl_node = pm.ls("my_ctl")[0]
        self.assertTrue(ctl_node.tx.isKeyable())
        self.assertFalse(ctl_node.v.isKeyable())
        self.assertFalse(ctl_node.rp.isKeyable())

        # check top-level transforms (4 cameras + 1 rig node)
        assemblies = pm.ls(assemblies=True)
        self.assertEqual(len(assemblies), 5)

    def test_build_steps(self):
        bp = Blueprint()

        step_a = BuildStep("StepFirst")
        step_b = BuildStep("StepB")
        step_c = BuildStep("StepC")
        step_x = BuildStep("StepX")
        step_y = BuildStep("StepY")
        step_z = BuildStep("StepZ")

        bp.root_step.add_child(step_a)
        self.assertTrue(bp.root_step.num_children() == 1)
        self.assertEqual(step_a.parent, bp.root_step)
        self.assertTrue(step_a.has_parent(bp.root_step))

        self.assertEqual(step_a.get_display_name(), "StepFirst (0)")
        step_a.set_name(None)
        self.assertEqual(step_a.name, "New Step")
        self.assertEqual(step_a.get_display_name(), "New Step (0)")
        step_a.set_name("StepA")

        bp.root_step.add_child(step_a)
        self.assertTrue(bp.root_step.num_children() == 1)

        bp.root_step.remove_child(step_a)
        self.assertTrue(bp.root_step.num_children() == 0)
        self.assertEqual(step_a.parent, None)

        bp.root_step.insert_child(0, step_a)
        self.assertTrue(bp.root_step.num_children() == 1)
        self.assertEqual(step_a.parent, bp.root_step)

        bp.root_step.insert_child(0, step_b)
        self.assertTrue(bp.root_step.num_children() == 2)
        self.assertEqual(step_b.parent, bp.root_step)

        bp.root_step.insert_child(0, step_c)
        self.assertTrue(bp.root_step.num_children() == 3)
        self.assertEqual(step_c.parent, bp.root_step)

        self.assertEqual(bp.root_step.get_child_at(0), step_c)
        self.assertEqual(bp.root_step.get_child_at(1), step_b)
        self.assertEqual(bp.root_step.get_child_at(2), step_a)

        step_a.set_name("StepC")
        self.assertEqual(step_a.name, "StepC 1")

        step_c.add_child(step_x)
        step_y.set_parent(step_x)
        step_y.add_child(step_z)
        self.assertEqual(step_c.get_full_path(), "/StepC")
        self.assertEqual(step_x.get_full_path(), "/StepC/StepX")
        self.assertEqual(step_y.get_full_path(), "/StepC/StepX/StepY")
        self.assertEqual(step_z.get_full_path(), "/StepC/StepX/StepY/StepZ")

        self.assertTrue(step_z.has_parent(bp.root_step))
        self.assertTrue(step_z.has_parent(step_x))
        self.assertFalse(step_x.has_parent(step_y))

        step_y.set_parent(step_b)
        self.assertEqual(step_z.get_full_path(), "/StepB/StepY/StepZ")
        self.assertTrue(step_x.num_children() == 0)

    def test_deserialize(self):
        bp = Blueprint()
        bp.deserialize_yaml(EXAMPLE_BLUEPRINT_A)

        self.assertEqual(bp.get_setting(BlueprintSettings.RIG_NAME), "TestRig")
        self.assertEqual(bp.root_step.num_children(), 4)

        step_a = bp.get_step_by_path("/Main/GroupA")
        step_c = bp.get_step_by_path("/Main/GroupA/GroupC")
        self.assertIsNotNone(step_c)
        self.assertEqual(step_c.parent, step_a)
        self.assertTrue(step_c.has_parent(bp.root_step))
