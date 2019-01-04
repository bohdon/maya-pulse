
import unittest
import pymel.core as pm

import pulse
import pulse.views


class TestPulseCmds(unittest.TestCase):
    """
    Tests the pulse plugin cmds for editing a Blueprint instance.
    """

    def setUp(self):
        pm.loadPlugin('pulse', quiet=True)

    def test_create_step(self):
        blueprintModel = pulse.views.BlueprintUIModel.getDefaultModel()
        bp = blueprintModel.blueprint

        result = pm.pulseCreateStep("", 0, "{'name':'StepA'}")
        self.assertEqual(result, ['StepA'])

        result = pm.pulseCreateStep("", 0, "{'name':'StepB'}")
        self.assertEqual(result, ['StepB'])

        result = pm.pulseCreateStep("", 0, "{'name':'StepC'}")
        self.assertEqual(result, ['StepC'])

        self.assertTrue(bp.rootStep.numChildren() == 3)
        pm.undo()
        self.assertTrue(bp.rootStep.numChildren() == 2)

        pm.pulseDeleteStep('StepA')
        self.assertTrue(bp.rootStep.numChildren() == 1)
        pm.undo()
        self.assertTrue(bp.rootStep.numChildren() == 2)

        pm.pulseMoveStep('StepB', 'StepA/StepBX')
        stepB = bp.getStepByPath('StepA/StepBX')
        self.assertTrue(stepB is not None)

        pm.undo()
        stepA = bp.getStepByPath('StepA')
        stepB = bp.getStepByPath('StepB')
        self.assertTrue(stepB is not None)
        self.assertTrue(stepA.numChildren() == 0)

        pm.pulseMoveStep('StepB', 'StepBY')
        stepB = bp.getStepByPath('StepBY')
        self.assertTrue(stepB is not None)

        pm.undo()
        pm.redo()
        stepB = bp.getStepByPath('StepBY')
        self.assertTrue(stepB is not None)
