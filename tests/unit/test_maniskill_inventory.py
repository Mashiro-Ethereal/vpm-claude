"""Inventory attribute discovery and formatting without simulation."""

import unittest

import numpy as np
import torch

from vpmkit.adapters.maniskill.inventory import _evaluate_attributes, _axes, _reading_type


class AttributeTask:
    num_envs = 2
    threshold = 0.025
    shared = torch.tensor([[1., 2.], [1., 2.]])
    varying = torch.tensor([[1., 2.], [3., 4.]])
    numeric_list = [1., 2., 3.]
    label = "skip"
    callback = staticmethod(lambda: None)

    def evaluate(self):
        def nested():
            return self.shared + self.varying
        return self.threshold, nested(), self.numeric_list, self.label, self.callback


class InheritedTask(AttributeTask):
    pass


class InventoryTest(unittest.TestCase):
    def test_inherited_evaluate_and_nested_reads(self) -> None:
        rows = dict((name, (value, same)) for name, value, same in _evaluate_attributes(InheritedTask()))
        self.assertEqual(rows, {"shared": ("[1, 2]", "yes"),
                                "varying": ("[1 … 3, 2 … 4]", "no"),
                                "threshold": ("0.025", "yes"),
                                "numeric_list": ("[1, 2, 3]", "yes")})

    def test_ranges_and_types(self) -> None:
        self.assertEqual(_axes(np.array([[-0.01, 0, 0.02001], [0.01, 0, 0.02002]])),
                         "x −0.010 … 0.010, y 0, z 0.020")
        self.assertEqual(_reading_type(torch.ones(8, dtype=torch.bool)), "bool [N]")
        self.assertEqual(_reading_type(torch.ones(8, 3)), "float [N, 3]")
        self.assertEqual(_reading_type(torch.ones(8, dtype=torch.int64)), "int [N]")
