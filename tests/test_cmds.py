
import unittest
import maya.cmds as cmds

import pulse
import pulse.views


class TestPulseCmds(unittest.TestCase):
    """
    Tests the pulse plugin cmds for working with a BlueprintUIModel.
    """

    def setUp(self):
        cmds.loadPlugin('pulse', quiet=True)

    def test_create_step(self):
        blueprintModel = pulse.views.BlueprintUIModel.getDefaultModel()
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
        self.assertTrue(stepB is not None)

        cmds.undo()
        stepA = bp.getStepByPath('StepA')
        stepB = bp.getStepByPath('StepB')
        self.assertTrue(stepB is not None)
        self.assertTrue(stepA.numChildren() == 0)

        cmds.pulseMoveStep('StepB', 'StepBY')
        stepB = bp.getStepByPath('StepBY')
        self.assertTrue(stepB is not None)

        cmds.undo()
        cmds.redo()
        stepB = bp.getStepByPath('StepBY')
        self.assertTrue(stepB is not None)
