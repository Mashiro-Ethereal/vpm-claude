import unittest

import torch

from tests import world
from vpmkit.world import ObjView, WorldState, WorldView


class WorldTests(unittest.TestCase):
    def test_cat_index_and_to(self):
        a, b = world(2, block_x=[1., 2.], held=[True, False]), world(block_x=3., held=True)
        combined = WorldState.cat([a, b])
        combined.validate()
        self.assertEqual(combined.N, 3)
        for index in [torch.tensor([2, 0]), torch.tensor([True, False, True])]:
            selected = combined.index(index)
            selected.validate()
            torch.testing.assert_close(selected.objects["block"].pos, combined.objects["block"].pos[index])
            torch.testing.assert_close(selected.grasping["g", "block"], combined.grasping["g", "block"][index])
            torch.testing.assert_close(selected.official["success"], combined.official["success"][index])
            self.assertEqual(selected.N, 2)
        copied = combined.to("cpu")
        copied.validate()
        self.assertIsNot(copied, combined)
        self.assertEqual(copied.meta, combined.meta)

    def test_views_expose_only_supported_public_members(self):
        ws = world()
        w, g, block = WorldView(ws), ObjView(ws.objects["g"], "g"), ObjView(ws.objects["block"], "block")
        self.assertEqual(w.N, 1)
        self.assertEqual(g.kind, "gripper")
        self.assertEqual(g.arm_qvel.shape, (1, 7))
        self.assertEqual(g.width.shape, (1,))
        torch.testing.assert_close(w.contact_force(g, block), w.contact_force(block, g))
        torch.testing.assert_close(w.bool_margin(w.grasping(g, block)), torch.tensor([-1.]))
        for name in ["objects", "official", "meta"]:
            self.assertFalse(hasattr(w, name))
        for name in ["name", "width", "arm_qvel"]:
            self.assertFalse(hasattr(block, name))
        with self.assertRaisesRegex(KeyError, "missing"):
            block.attr("missing")
        with self.assertRaises(AttributeError):
            block.pos = torch.zeros(1, 3)

    def test_validation_shapes_dtypes_and_gripper_attrs(self):
        cases = [
            (lambda w: setattr(w.objects["block"], "pos", torch.zeros(1, 2)), "block.pos"),
            (lambda w: setattr(w.objects["block"], "quat", torch.ones(1, 4, dtype=torch.long)), "floating"),
            (lambda w: w.grasping.update({("g", "block"): torch.ones(1)}), "dtype"),
            (lambda w: w.objects["g"].attrs.pop("width"), "width"),
            (lambda w: w.objects["g"].attrs.update(arm_qvel=torch.zeros(1)), "arm_qvel"),
            (lambda w: w.official.update(success=torch.zeros(2)), "leading dimension"),
            (lambda w: w.contacts.update({("block", "g"): torch.ones(1)}), "both orders"),
        ]
        for change, expected in cases:
            with self.subTest(expected=expected):
                ws = world()
                change(ws)
                with self.assertRaisesRegex(ValueError, expected):
                    ws.validate()

    def test_cat_mismatches_and_bad_indices(self):
        with self.assertRaises(ValueError):
            WorldState.cat([])
        ws = world()
        other = world()
        other.official = {}
        with self.assertRaisesRegex(ValueError, "official keys"):
            WorldState.cat([ws, other])
        other = world()
        other.objects["block"].attrs["color"] = torch.ones(1, 3)
        with self.assertRaisesRegex(ValueError, "attrs"):
            WorldState.cat([ws, other])
        for idx in [torch.tensor([0.]), torch.tensor([[0]]), torch.tensor([True, False])]:
            with self.assertRaises(ValueError):
                ws.index(idx)
