
import unittest
import pymel.core as pm

import pulse
from pulse import util_nodes


class TestUtilNodes(unittest.TestCase):

    def test_createUtilityNode(self):
        node = util_nodes.create_utility_node('multiplyDivide')
        self.assertEqual(node.nodeType(), 'multiplyDivide')

    def test_utilityOutputAttr(self):
        node = util_nodes.create_utility_node('multiplyDivide')
        outputAttr = util_nodes.get_output_attr(node)
        self.assertEqual(outputAttr.longName(), 'output')
        outputAttr = util_nodes.get_output_attr(node.input1X)
        self.assertEqual(outputAttr.longName(), 'outputX')
        outputAttr = util_nodes.get_output_attr(node.input1Y)
        self.assertEqual(outputAttr.longName(), 'outputY')

        node = util_nodes.create_utility_node('condition')
        outputAttr = util_nodes.get_output_attr(node.colorIfTrueR)
        self.assertEqual(outputAttr.longName(), 'outColorR')

    def test_plusMinusAverageOutputAttr(self):
        node = util_nodes.create_utility_node('plusMinusAverage')
        output1D = util_nodes.get_plus_minus_average_output_attr(node)
        self.assertEqual(output1D.longName(), 'output1D')
        output1D = util_nodes.get_output_attr(node)
        self.assertEqual(output1D.longName(), 'output1D')
        output2D = util_nodes.get_plus_minus_average_output_attr(node.input2D)
        self.assertEqual(output2D.longName(), 'output2D')
        output2D = util_nodes.get_output_attr(node.input2D)
        self.assertEqual(output2D.longName(), 'output2D')
        output3DX = util_nodes.get_plus_minus_average_output_attr(
            node.input3D[0].input3Dx)
        self.assertEqual(output3DX.longName(), 'output3Dx')
        output3Dy = util_nodes.get_plus_minus_average_output_attr(
            node.input3D[0].input3Dy)
        self.assertEqual(output3Dy.longName(), 'output3Dy')

    def test_attrDimensions(self):
        node = util_nodes.create_utility_node('multiplyDivide')
        largest = util_nodes.get_largest_dimension_attr(
            [node.outputX, node.output])
        self.assertEqual(largest.longName(), 'output')

    def test_inputConnections(self):
        node = util_nodes.create_utility_node('multiplyDivide')

        cons = util_nodes.get_input_connections(1, node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'input1X')

        cons = util_nodes.get_input_connections([1, 2], node.input1)
        self.assertEqual(len(cons), 2)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'input1X')
        self.assertEqual(cons[1][0], 2)
        self.assertEqual(cons[1][1].longName(), 'input1Y')

        cons = util_nodes.get_input_connections([1, 2, 3], node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], [1, 2, 3])
        self.assertEqual(cons[0][1].longName(), 'input1')

        node = util_nodes.create_utility_node('condition')
        cons = util_nodes.get_input_connections(1, node.colorIfTrueR)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), 'colorIfTrueR')

    def test_addSubtract(self):
        sumAttr = util_nodes.add(1, 2, 3, 4)
        self.assertIsInstance(sumAttr, pm.Attribute)
        self.assertEqual(sumAttr.get(), 10)

        subAttr = util_nodes.subtract(8, 3)
        self.assertEqual(subAttr.get(), 5)

    def test_multiplyDivide(self):
        multAttr = util_nodes.multiply(3, 7)
        self.assertIsInstance(multAttr, pm.Attribute)
        self.assertEqual(multAttr.get(), 21)

        divAttr = util_nodes.divide(10, 2)
        self.assertEqual(divAttr.get(), 5)

    def test_conditions(self):
        equalAttr = util_nodes.equal(7, 7, 1, 0)
        self.assertEqual(equalAttr.longName(), 'outColorR')
        self.assertEqual(equalAttr.get(), 1)
