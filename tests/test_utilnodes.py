
import unittest
import pymel.core as pm

import pulse
from pulse import utilnodes


class TestUtilNodes(unittest.TestCase):

    def test_createUtilityNode(self):
        node = utilnodes.create_utility_node('multiplyDivide')
        self.assertEqual(node.nodeType(), 'multiplyDivide')

    def test_utilityOutputAttr(self):
        node = utilnodes.create_utility_node('multiplyDivide')
        outputAttr = utilnodes.get_output_attr(node)
        self.assertEqual(outputAttr.longName(), 'output')
        outputAttr = utilnodes.get_output_attr(node.input1X)
        self.assertEqual(outputAttr.longName(), 'outputX')
        outputAttr = utilnodes.get_output_attr(node.input1Y)
        self.assertEqual(outputAttr.longName(), 'outputY')

        node = utilnodes.create_utility_node('condition')
        outputAttr = utilnodes.get_output_attr(node.colorIfTrueR)
        self.assertEqual(outputAttr.longName(), 'outColorR')

    def test_plusMinusAverageOutputAttr(self):
        node = utilnodes.create_utility_node('plusMinusAverage')
        output1D = utilnodes.get_plus_minus_average_output_attr(node)
        self.assertEqual(output1D.longName(), 'output1D')
        output1D = utilnodes.get_output_attr(node)
        self.assertEqual(output1D.longName(), 'output1D')
        output2D = utilnodes.get_plus_minus_average_output_attr(node.input2D)
        self.assertEqual(output2D.longName(), 'output2D')
        output2D = utilnodes.get_output_attr(node.input2D)
        self.assertEqual(output2D.longName(), 'output2D')
        output3DX = utilnodes.get_plus_minus_average_output_attr(
            node.input3D[0].input3Dx)
        self.assertEqual(output3DX.longName(), 'output3Dx')
        output3Dy = utilnodes.get_plus_minus_average_output_attr(
            node.input3D[0].input3Dy)
        self.assertEqual(output3Dy.longName(), 'output3Dy')

    def test_attrDimensions(self):
        node = utilnodes.create_utility_node('multiplyDivide')
        largest = utilnodes.get_largest_dimension_attr(
            [node.outputX, node.output])
        self.assertEqual(largest.longName(), 'output')

    def test_inputConnections(self):
        node = utilnodes.create_utility_node('multiplyDivide')

        cons = utilnodes.get_input_connections(1, node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'input1X')

        cons = utilnodes.get_input_connections([1, 2], node.input1)
        self.assertEqual(len(cons), 2)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'input1X')
        self.assertEqual(cons[1][0], 2)
        self.assertEqual(cons[1][1].longName(), 'input1Y')

        cons = utilnodes.get_input_connections([1, 2, 3], node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], [1, 2, 3])
        self.assertEqual(cons[0][1].longName(), 'input1')

        node = utilnodes.create_utility_node('condition')
        cons = utilnodes.get_input_connections(1, node.colorIfTrueR)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'colorIfTrueR')

    def test_addSubtract(self):
        sumAttr = utilnodes.add(1, 2, 3, 4)
        self.assertIsInstance(sumAttr, pm.Attribute)
        self.assertEqual(sumAttr.get(), 10)

        subAttr = utilnodes.subtract(8, 3)
        self.assertEqual(subAttr.get(), 5)

    def test_multiplyDivide(self):
        multAttr = utilnodes.multiply(3, 7)
        self.assertIsInstance(multAttr, pm.Attribute)
        self.assertEqual(multAttr.get(), 21)

        divAttr = utilnodes.divide(10, 2)
        self.assertEqual(divAttr.get(), 5)

    def test_conditions(self):
        equalAttr = utilnodes.equal(7, 7, 1, 0)
        self.assertEqual(equalAttr.longName(), 'outColorR')
        self.assertEqual(equalAttr.get(), 1)
