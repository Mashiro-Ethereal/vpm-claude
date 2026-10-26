"""Snapshot validation, tensor selection, persistence and candidate views."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import torch

from vpmkit.world import Snapshot, make_views
from .synth import snapshot


class WorldTest(unittest.TestCase):
    def assertSnapshotsEqual(self, a: Snapshot, b: Snapshot) -> None:
        self.assertEqual(a.to_dict().keys(), b.to_dict().keys())
        self.assertEqual(a.bodies.keys(), b.bodies.keys())
        self.assertEqual(a.grasping.keys(), b.grasping.keys())
        self.assertEqual(a.contact_force.keys(), b.contact_force.keys())
        self.assertEqual(a.official.keys(), b.official.keys())
        left, right = dict(a._tensor_items()), dict(b._tensor_items())
        self.assertEqual(left.keys(), right.keys())
        for name in left:
            torch.testing.assert_close(left[name], right[name])
        for key in a.bodies:
            self.assertEqual(a.bodies[key].kind, b.bodies[key].kind)

    def test_view_fields_share_storage(self) -> None:
        s = snapshot(3)
        s.bodies["cube"].attrs["slot_pose"] = torch.randn(3, 7)
        w, views, o = make_views(s)
        self.assertIs(o.cube, views["cube"])
        self.assertIs(o.cube.pose, s.bodies["cube"].pose)
        self.assertIs(o.cube.lin_vel, s.bodies["cube"].lin_vel)
        self.assertIs(o.cube.ang_vel, s.bodies["cube"].ang_vel)
        self.assertIs(o.cube.half_size, s.bodies["cube"].half_size)
        self.assertIs(o.cube.slot_pose, s.bodies["cube"].attrs["slot_pose"])
        self.assertIs(o.cube.pos._base, s.bodies["cube"].pose)
        self.assertIs(o.cube.quat._base, s.bodies["cube"].pose)
        self.assertEqual(o.cube.pos.shape, (3, 3))
        self.assertEqual(o.cube.quat.shape, (3, 4))
        for name in ("pose", "width", "max_width", "arm_qvel", "lin_vel", "ang_vel"):
            self.assertIs(getattr(o.g, name), getattr(s.bodies["g"], name))
        self.assertIs(w.table_z, s.table_z)
        self.assertEqual(w.batch_size, 3)
        self.assertEqual(w.device, torch.device("cpu"))

    def test_read_only_and_unknown_fields(self) -> None:
        w, views, objects = make_views(snapshot())
        for view in [w, objects, *views.values()]:
            with self.subTest(view=type(view).__name__):
                with self.assertRaisesRegex(AttributeError, "read-only"):
                    view.pose = torch.zeros(1, 7)
                with self.assertRaisesRegex(AttributeError, "read-only"):
                    del view.pose
                with self.assertRaises(AttributeError):
                    view.name
        with self.assertRaisesRegex(AttributeError, "available fields:.*pose"):
            objects.cube.unknown
        with self.assertRaisesRegex(AttributeError, "available fields:.*cube"):
            objects.unknown
        with self.assertRaises(AttributeError):
            w.cube

    def test_object_keys_with_leading_underscores(self) -> None:
        s = snapshot()
        s.bodies["_views"] = s.bodies["cube"]
        _, views, objects = make_views(s)
        self.assertIs(objects._views, views["_views"])

    def test_missing_and_present_optional_readings(self) -> None:
        s = snapshot(2)
        s.bodies["g"] = replace(s.bodies["g"], width=None, max_width=None, arm_qvel=None)
        _, _, o = make_views(s)
        for name in ("joint_pos", "joint_vel", "joint_limits"):
            with self.assertRaisesRegex(AttributeError, "no joint reading"):
                getattr(o.cube, name)
        for name in ("width", "max_width"):
            with self.assertRaisesRegex(AttributeError, "no finger reading"):
                getattr(o.g, name)
        with self.assertRaisesRegex(AttributeError, "no arm velocity reading"):
            o.g.arm_qvel
        s.bodies["cube"] = replace(s.bodies["cube"], joint_pos=torch.zeros(2),
                                   joint_vel=torch.ones(2), joint_limits=torch.zeros(2, 2))
        _, _, o = make_views(s)
        for name in ("joint_pos", "joint_vel", "joint_limits"):
            self.assertIs(getattr(o.cube, name), getattr(s.bodies["cube"], name))

    def test_pairs_and_official_isolation(self) -> None:
        s = snapshot(2, grasp=[True, False])
        w, _, o = make_views(s)
        self.assertIs(w.grasping(o.g, o.cube), s.grasping[("g", "cube")])
        self.assertIs(w.contact_force(o.pad, o.cube), s.contact_force[("cube", "pad")])
        self.assertIs(w.contact_force(o.cube, o.pad), s.contact_force[("cube", "pad")])
        with self.assertRaisesRegex(KeyError, "no grasp reading.*site cannot be grasped"):
            w.grasping(o.g, o.pad)
        with self.assertRaisesRegex(KeyError, "no contact force reading.*g, pad"):
            w.contact_force(o.g, o.pad)
        for name in ("official", "success", "_snapshot", "__dict__"):
            self.assertFalse(hasattr(w, name))
        for slot in w.__slots__:
            self.assertIsNot(getattr(w, slot), s)
            self.assertIsNot(getattr(w, slot), s.official)

    def test_body_validation(self) -> None:
        body = snapshot(2).bodies["cube"]
        cases = [(dict(kind="robot"), "kind"), (dict(pose=torch.zeros(2, 6)), "pose"),
                 (dict(lin_vel=torch.zeros(1, 3)), "lin_vel"),
                 (dict(ang_vel=torch.zeros(2, 4)), "ang_vel"), (dict(half_size=None), "half_size"),
                 (dict(width=torch.zeros(2)), "only allowed on a gripper"),
                 (dict(max_width=torch.zeros(2)), "only allowed on a gripper"),
                 (dict(arm_qvel=torch.zeros(2, 7)), "only allowed on a gripper"),
                 (dict(joint_limits=torch.zeros(2)), "joint_limits"),
                 (dict(joint_pos=torch.zeros(2, 1)), "joint_pos"),
                 (dict(attrs={"pose": torch.zeros(2)}), "clashes"),
                 (dict(attrs={"name": torch.zeros(2)}), "clashes"),
                 (dict(attrs={"reading": torch.zeros(3)}), "first dimension"),
                 (dict(attrs={"reading": 2}), "tensor"),
                 (dict(attrs=None), "dictionary"),
                 (dict(lin_vel=torch.zeros(2, 3, device="meta")), "device")]
        for kwargs, message in cases:
            with self.subTest(kwargs=kwargs.keys()), self.assertRaisesRegex(ValueError, message):
                replace(body, **kwargs)
        gripper = snapshot(2).bodies["g"]
        for kwargs, message in [(dict(half_size=torch.ones(2, 3)), "None"),
                                (dict(joint_vel=torch.zeros(2)), "actor or site"),
                                (dict(width=torch.zeros(2, 1)), "width"),
                                (dict(arm_qvel=torch.zeros(2)), "arm_qvel")]:
            with self.assertRaisesRegex(ValueError, message):
                replace(gripper, **kwargs)

    def test_snapshot_validation(self) -> None:
        s = snapshot(2)
        for kwargs, message in [
            (dict(table_z=torch.zeros(2, 1)), "table_z"),
            (dict(table_z=torch.zeros(3)), "expected shape"),
            (dict(official=None), "dictionary"),
            (dict(grasping={("g", "cube"): torch.zeros(2)}), "bool"),
            (dict(grasping={("g", "cube"): torch.zeros(2, 1, dtype=torch.bool)}), "shape"),
            (dict(contact_force={("g", "cube"): torch.zeros(3)}), "shape"),
            (dict(contact_force={"g,cube": torch.zeros(2)}), "pair of string"),
            (dict(official={"success": torch.zeros(1)}), "first dimension"),
            (dict(official={"success": True}), "tensors"),
            (dict(official={"success": torch.zeros(2, device="meta")}), "device"),
        ]:
            with self.subTest(kwargs=kwargs.keys()), self.assertRaisesRegex(ValueError, message):
                replace(s, **kwargs)

    def test_select_cat_and_to(self) -> None:
        s = snapshot(4, tcp=torch.arange(12).reshape(4, 3), grasp=[True, False, True, False])
        self.assertEqual(s.select(2).batch_size, 1)
        self.assertSnapshotsEqual(s.select(-1), s.select(3))
        self.assertSnapshotsEqual(s.select(slice(1, 3)), s.select(torch.tensor([1, 2])))
        self.assertSnapshotsEqual(s.select(torch.tensor([True, False, True, False])), s.select(torch.tensor([0, 2])))
        self.assertSnapshotsEqual(Snapshot.cat([s.select(0), s.select(slice(1, None))]), s)
        self.assertSnapshotsEqual(s.to("cpu"), s)
        with self.assertRaisesRegex(ValueError, "at least one"):
            Snapshot.cat([])
        other = snapshot(4)
        other.bodies["cube"].attrs["extra"] = torch.zeros(4)
        with self.assertRaisesRegex(ValueError, "identical keys"):
            Snapshot.cat([s, other])
        other = snapshot(4)
        other.bodies["g"].width = None
        with self.assertRaisesRegex(ValueError, "identical"):
            Snapshot.cat([s, other])
        with self.assertRaises(ValueError):
            s.select(torch.tensor([0.0]))
        with self.assertRaises(IndexError):
            s.select(4)

    def test_save_load_and_dict_format(self) -> None:
        s = snapshot(3)
        s.bodies["cube"].attrs["slot_pose"] = torch.randn(3, 7)
        data = s.to_dict()
        self.assertEqual(data["format"], "vpmkit.snapshot.v1")

        def allowed(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertIsInstance(key, str)
                    allowed(child)
            else:
                self.assertTrue(value is None or isinstance(value, (str, int, torch.Tensor)))

        allowed(data)
        self.assertSnapshotsEqual(s, Snapshot.from_dict(data))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "snapshot.pt"
            s.save(path)
            self.assertSnapshotsEqual(s, Snapshot.load(path, map_location="cpu"))
        with self.assertRaisesRegex(ValueError, "unknown snapshot format"):
            Snapshot.from_dict({**data, "format": "wrong"})
