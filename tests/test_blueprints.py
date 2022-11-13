import unittest
import pymel.core as pm

from pulse.blueprints import Blueprint, BlueprintSettings, BlueprintBuilder
import pulse.loader
import pulse.build_items
import pulse.control_shapes
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
    def setUp(self) -> None:
        pulse.loader.load_actions()

    def tearDown(self):
        pm.delete(pulse.rigs.get_all_rigs())

    def test_build(self):
        bp = Blueprint()
        bp.set_setting(BlueprintSettings.RIG_NAME, "test")
        bp.add_default_actions()

        main_step = bp.get_step_by_path("Main")

        ctl_node = pm.polyCube(n="my_ctl")[0]

        ctl_step = pulse.build_items.BuildStep(action_id="Pulse.AnimControl")
        ctl_step.action_proxy.get_attr("controlNode").set_value(ctl_node)
        main_step.add_child(ctl_step)

        self.assertTrue(len(main_step.children) == 1)

        builder = BlueprintBuilder(bp)
        builder.start()

        self.assertTrue(builder.is_finished)
        self.assertTrue(len(builder.errors) == 0)

        rig_node = pm.ls("test_rig")
        self.assertTrue(len(rig_node) == 1)

        # make sure anim control action was run
        ctl_node = pm.ls("my_ctl")[0]
        self.assertTrue(ctl_node.tx.isKeyable())
        self.assertFalse(ctl_node.v.isKeyable())
        self.assertFalse(ctl_node.rp.isKeyable())

        # check top-level transforms (4 cameras + 1 rig node)
        assemblies = pm.ls(assemblies=True)
        self.assertTrue(len(assemblies) == 5)

    def test_build_steps(self):
        bp = Blueprint()

        step_a = pulse.build_items.BuildStep("StepFirst")
        step_b = pulse.build_items.BuildStep("StepB")
        step_c = pulse.build_items.BuildStep("StepC")
        step_x = pulse.build_items.BuildStep("StepX")
        step_y = pulse.build_items.BuildStep("StepY")
        step_z = pulse.build_items.BuildStep("StepZ")

        self.assertEqual(step_a.get_display_name(), "StepFirst (0)")
        step_a.set_name(None)
        self.assertEqual(step_a.name, "New Step")
        step_a.set_name("StepA")

        bp.rootStep.add_child(step_a)
        self.assertTrue(bp.rootStep.num_children() == 1)
        self.assertEqual(step_a.parent, bp.rootStep)
        self.assertTrue(step_a.has_parent(bp.rootStep))

        bp.rootStep.add_child(step_a)
        self.assertTrue(bp.rootStep.num_children() == 1)

        bp.rootStep.remove_child(step_a)
        self.assertTrue(bp.rootStep.num_children() == 0)
        self.assertEqual(step_a.parent, None)

        bp.rootStep.insert_child(0, step_a)
        self.assertTrue(bp.rootStep.num_children() == 1)
        self.assertEqual(step_a.parent, bp.rootStep)

        bp.rootStep.insert_child(0, step_b)
        self.assertTrue(bp.rootStep.num_children() == 2)
        self.assertEqual(step_b.parent, bp.rootStep)

        bp.rootStep.insert_child(0, step_c)
        self.assertTrue(bp.rootStep.num_children() == 3)
        self.assertEqual(step_c.parent, bp.rootStep)

        self.assertEqual(bp.rootStep.get_child_at(0), step_c)
        self.assertEqual(bp.rootStep.get_child_at(1), step_b)
        self.assertEqual(bp.rootStep.get_child_at(2), step_a)

        step_a.set_name("StepC")
        self.assertEqual(step_a.name, "StepC 1")

        step_c.add_child(step_x)
        step_y.set_parent(step_x)
        step_y.add_child(step_z)
        self.assertEqual(step_c.get_full_path(), "StepC")
        self.assertEqual(step_x.get_full_path(), "StepC/StepX")
        self.assertEqual(step_y.get_full_path(), "StepC/StepX/StepY")
        self.assertEqual(step_z.get_full_path(), "StepC/StepX/StepY/StepZ")

        self.assertTrue(step_z.has_parent(bp.rootStep))
        self.assertTrue(step_z.has_parent(step_x))
        self.assertFalse(step_x.has_parent(step_y))

        step_y.set_parent(step_b)
        self.assertEqual(step_z.get_full_path(), "StepB/StepY/StepZ")
        self.assertTrue(step_x.num_children() == 0)

    def test_deserialize(self):
        bp = Blueprint()
        bp.load_from_yaml(EXAMPLE_BLUEPRINT_A)

        self.assertEqual(bp.get_setting(BlueprintSettings.RIG_NAME), "TestRig")
        self.assertTrue(bp.rootStep.num_children() == 4)

        step_a = bp.get_step_by_path("Main/GroupA")
        step_c = bp.get_step_by_path("Main/GroupA/GroupC")
        self.assertIsNotNone(step_c)
        self.assertEqual(step_c.parent, step_a)
        self.assertTrue(step_c.has_parent(bp.rootStep))
