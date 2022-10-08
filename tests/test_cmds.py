
import unittest
import maya.cmds as cmds

from pulse.ui.core import BlueprintUIModel


class TestPulseCmds(unittest.TestCase):
    """
    Tests the pulse plugin cmds for working with a BlueprintUIModel.
    """

    def setUp(self):
        cmds.loadPlugin('pulse', quiet=True)

    def test_create_step(self):
        blueprintModel = BlueprintUIModel.getDefaultModel()
        bp = blueprintModel.blueprint

        result = cmds.pulseCreateStep("", 0, "{'name':'StepA'}")
        self.assertEqual(result, ['StepA'])

        result = cmds.pulseCreateStep("", 0, "{'name':'StepB'}")
        self.assertEqual(result, ['StepB'])

        result = cmds.pulseCreateStep("", 0, "")
        self.assertEqual(result, ['New Step'])

        self.assertTrue(bp.rootStep.numChildren() == 3)
        cmds.undo()
        self.assertTrue(bp.rootStep.numChildren() == 2)

        cmds.pulseDeleteStep('StepA')
        self.assertTrue(bp.rootStep.numChildren() == 1)
        cmds.undo()
        self.assertTrue(bp.rootStep.numChildren() == 2)

        cmds.pulseMoveStep('StepB', 'StepA/StepBX')
        stepB = bp.getStepByPath('StepA/StepBX')
        self.assertIsNotNone(stepB)

        cmds.undo()
        stepA = bp.getStepByPath('StepA')
        stepB = bp.getStepByPath('StepB')
        self.assertIsNotNone(stepB)
        self.assertTrue(stepA.numChildren() == 0)

        cmds.pulseMoveStep('StepB', 'StepBY')
        stepB = bp.getStepByPath('StepBY')
        self.assertIsNotNone(stepB)

        cmds.undo()
        cmds.redo()
        stepB = bp.getStepByPath('StepBY')
        self.assertIsNotNone(stepB)

        cmds.pulseMoveStep('StepBY', 'StepA/StepBY')
        cmds.pulseRenameStep('StepA/StepBY', 'StepBZ')
        stepB = bp.getStepByPath('StepA/StepBZ')
        self.assertIsNotNone(stepB)
