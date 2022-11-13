import unittest

import pymel.core as pm

from pulse.core import load_actions
from pulse import util_nodes


class TestUtilNodes(unittest.TestCase):
    def setUp(self) -> None:
        load_actions()

    def test_createUtilityNode(self):
        node = util_nodes.create_utility_node("multiplyDivide")
        self.assertEqual(node.nodeType(), "multiplyDivide")

    def test_utilityOutputAttr(self):
        node = util_nodes.create_utility_node("multiplyDivide")
        output_attr = util_nodes.get_output_attr(node)
        self.assertEqual(output_attr.longName(), "output")
        output_attr = util_nodes.get_output_attr(node.input1X)
        self.assertEqual(output_attr.longName(), "outputX")
        output_attr = util_nodes.get_output_attr(node.input1Y)
        self.assertEqual(output_attr.longName(), "outputY")

        node = util_nodes.create_utility_node("condition")
        output_attr = util_nodes.get_output_attr(node.colorIfTrueR)
        self.assertEqual(output_attr.longName(), "outColorR")

    def test_plusMinusAverageOutputAttr(self):
        node = util_nodes.create_utility_node("plusMinusAverage")
        output_1d = util_nodes.get_plus_minus_average_output_attr(node)
        self.assertEqual(output_1d.longName(), "output1D")
        output_1d = util_nodes.get_output_attr(node)
        self.assertEqual(output_1d.longName(), "output1D")
        output_2d = util_nodes.get_plus_minus_average_output_attr(node.input2D)
        self.assertEqual(output_2d.longName(), "output2D")
        output_2d = util_nodes.get_output_attr(node.input2D)
        self.assertEqual(output_2d.longName(), "output2D")
        output_3dx = util_nodes.get_plus_minus_average_output_attr(node.input3D[0].input3Dx)
        self.assertEqual(output_3dx.longName(), "output3Dx")
        output_3dy = util_nodes.get_plus_minus_average_output_attr(node.input3D[0].input3Dy)
        self.assertEqual(output_3dy.longName(), "output3Dy")

    def test_attrDimensions(self):
        node = util_nodes.create_utility_node("multiplyDivide")
        largest = util_nodes.get_largest_dimension_attr([node.outputX, node.output])
        self.assertEqual(largest.longName(), "output")

    def test_inputConnections(self):
        node = util_nodes.create_utility_node("multiplyDivide")

        cons = util_nodes.get_input_connections(1, node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), "input1X")

        cons = util_nodes.get_input_connections([1, 2], node.input1)
        self.assertEqual(len(cons), 2)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), "input1X")
        self.assertEqual(cons[1][0], 2)
        self.assertEqual(cons[1][1].longName(), "input1Y")

        cons = util_nodes.get_input_connections([1, 2, 3], node.input1)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], [1, 2, 3])
        self.assertEqual(cons[0][1].longName(), "input1")

        node = util_nodes.create_utility_node("condition")
        cons = util_nodes.get_input_connections(1, node.colorIfTrueR)
        self.assertEqual(len(cons), 1)
        self.assertEqual(cons[0][0], 1)
        self.assertEqual(cons[0][1].longName(), "colorIfTrueR")

    def test_addSubtract(self):
        sum_attr = util_nodes.add(1, 2, 3, 4)
        self.assertIsInstance(sum_attr, pm.Attribute)
        self.assertEqual(sum_attr.get(), 10)

        sub_attr = util_nodes.subtract(8, 3)
        self.assertEqual(sub_attr.get(), 5)

    def test_multiplyDivide(self):
        mult_attr = util_nodes.multiply(3, 7)
        self.assertIsInstance(mult_attr, pm.Attribute)
        self.assertEqual(mult_attr.get(), 21)

        div_attr = util_nodes.divide(10, 2)
        self.assertEqual(div_attr.get(), 5)

    def test_conditions(self):
        equal_attr = util_nodes.equal(7, 7, 1, 0)
        self.assertEqual(equal_attr.longName(), "outColorR")
        self.assertEqual(equal_attr.get(), 1)
