import unittest
import maya.cmds as cmds

from pulse.core import load_actions
from pulse.ui.core import BlueprintUIModel


class TestPulseCmds(unittest.TestCase):
    """
    Tests the pulse plugin cmds for working with a BlueprintUIModel.
    """

    def setUp(self):
        cmds.loadPlugin("pulse", quiet=True)
        self.blueprint_model = BlueprintUIModel.get()
        self.blueprint_model.new_file(use_default_actions=False)

    def test_create_step(self):
        bp = self.blueprint_model.blueprint

        result = cmds.pulseCreateStep("", 0, "{'name':'StepA'}")
        self.assertEqual(result, ["/StepA"])

        result = cmds.pulseCreateStep("", 0, "{'name':'StepB'}")
        self.assertEqual(result, ["/StepB"])

        result = cmds.pulseCreateStep("", 0, "")
        self.assertEqual(result, ["/New Step"])

        self.assertTrue(bp.root_step.num_children() == 3)
        cmds.undo()
        self.assertTrue(bp.root_step.num_children() == 2)

        cmds.pulseDeleteStep("StepA")
        self.assertTrue(bp.root_step.num_children() == 1)
        cmds.undo()
        self.assertTrue(bp.root_step.num_children() == 2)

        cmds.pulseMoveStep("StepB", "StepA/StepBX")
        step_b = bp.get_step_by_path("/StepA/StepBX")
        self.assertIsNotNone(step_b)

        cmds.undo()
        step_a = bp.get_step_by_path("/StepA")
        step_b = bp.get_step_by_path("/StepB")
        self.assertIsNotNone(step_b)
        self.assertTrue(step_a.num_children() == 0)

        cmds.pulseMoveStep("StepB", "StepBY")
        step_b = bp.get_step_by_path("/StepBY")
        self.assertIsNotNone(step_b)

        cmds.undo()
        cmds.redo()
        step_b = bp.get_step_by_path("StepBY")
        self.assertIsNotNone(step_b)

        cmds.pulseMoveStep("/StepBY", "/StepA/StepBY")
        cmds.pulseRenameStep("/StepA/StepBY", "StepBZ")
        step_b = bp.get_step_by_path("/StepA/StepBZ")
        self.assertIsNotNone(step_b)
