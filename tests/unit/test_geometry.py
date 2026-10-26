"""Geometry checks against analytic results and ManiSkill source functions."""

import itertools
import math
import unittest

import torch

from vpmkit import geometry as G


def rotation(axis: int, angle: float) -> torch.Tensor:
    q = torch.zeros(4)
    q[0] = math.cos(angle / 2)
    q[axis + 1] = math.sin(angle / 2)
    return q


class GeometryTest(unittest.TestCase):
    def assertClose(self, actual: torch.Tensor, expected: torch.Tensor) -> None:
        torch.testing.assert_close(actual, expected, atol=1e-5, rtol=0)

    def test_quarter_turns(self) -> None:
        matrices = torch.tensor([[[1, 0, 0], [0, 0, -1], [0, 1, 0]],
                                 [[0, 0, 1], [0, 1, 0], [-1, 0, 0]],
                                 [[0, -1, 0], [1, 0, 0], [0, 0, 1]]], dtype=torch.float32)
        for i in range(3):
            q = rotation(i, math.pi / 2)
            self.assertClose(G.quat_to_matrix(q), matrices[i])
            self.assertClose(G.quat_apply(q, torch.eye(3)), matrices[i].T)
            for j in range(3):
                self.assertClose(G.axis(q, j), matrices[i, :, j])
        self.assertClose(G.quat_to_euler_xyz(rotation(0, math.pi / 2)), torch.tensor([math.pi / 2, 0, 0]))
        self.assertClose(G.quat_to_euler_xyz(rotation(2, math.pi / 2)), torch.tensor([0, 0, math.pi / 2]))
        self.assertAlmostEqual(float(G.quat_to_euler_xyz(rotation(1, math.pi / 2))[1]), math.pi / 2, places=5)

    def test_composition_inverse_and_round_trip(self) -> None:
        p = torch.cat((torch.tensor([1., 2., 3.]), rotation(2, math.pi / 2)))
        b = torch.tensor([1., 0., 0., 1., 0., 0., 0.])
        self.assertClose(G.pose_mul(p, b), torch.cat((torch.tensor([1., 3., 3.]), p[3:])))
        self.assertClose(G.pose_mul(G.pose_inv(p), p), torch.tensor([0., 0., 0., 1., 0., 0., 0.]))
        x = torch.tensor([[1., 3., 4.], [-3., 2., 1.]])
        self.assertClose(G.to_local(p, G.to_world(p, x)), x)
        self.assertClose(G.to_world(p, torch.tensor([1., 0., 0.])), torch.tensor([1., 3., 3.]))
        negative = p.clone()
        negative[3:] *= -1
        self.assertLess(float(G.pose_inv(negative)[3]), 0)
        self.assertGreater(float(G.pose_mul(negative, b)[3]), 0)

    def test_nonunit_quaternions(self) -> None:
        q = rotation(2, math.pi / 2)
        v = torch.tensor([1., 2., 3.])
        self.assertClose(G.quat_to_matrix(3 * q), G.quat_to_matrix(q))
        self.assertClose(G.quat_apply(3 * q, v), 9 * G.quat_apply(q, v))

    def test_boxes_rotated_z_and_x(self) -> None:
        half = torch.tensor([1., 2., 3.])
        signs = torch.tensor(list(itertools.product((-1, 1), repeat=3)))
        local = signs * half
        c = math.sqrt(0.5)
        for axis in (2, 0):
            p = torch.cat((torch.tensor([1., 2., 5.]), rotation(axis, math.pi / 4)))
            expected = local.clone()
            if axis == 2:
                expected[:, 0] = c * (local[:, 0] - local[:, 1])
                expected[:, 1] = c * (local[:, 0] + local[:, 1])
                extent = 3
            else:
                expected[:, 1] = c * (local[:, 1] - local[:, 2])
                expected[:, 2] = c * (local[:, 1] + local[:, 2])
                extent = 5 * c
            expected += torch.tensor([1., 2., 5.])
            self.assertClose(G.box_corners(p, half), expected)
            self.assertClose(G.box_bottom_z(p, half), torch.tensor(5 - extent, dtype=torch.float32))
            self.assertClose(G.box_top_z(p, half), torch.tensor(5 + extent, dtype=torch.float32))

    def test_angles_and_broadcasting(self) -> None:
        u = torch.tensor([1., 0., 0.])
        v = torch.tensor([[2., 0., 0.], [-2., 0., 0.], [0., 1., 0.], [0., 0., 0.]])
        self.assertClose(G.angle_between(u, v), torch.tensor([0., math.pi, math.pi / 2, 0.]))
        q = torch.stack([rotation(0, 0.1), rotation(1, 0.2)])[:, None, :]
        points = torch.randn(1, 5, 3)
        p = torch.cat((torch.zeros(2, 1, 3), q), -1)
        self.assertEqual(G.quat_apply(q, points).shape, (2, 5, 3))
        self.assertClose(G.to_local(p, G.to_world(p, points)), points.expand(2, 5, 3))
        self.assertEqual(G.box_corners(p, torch.ones(1, 5, 3)).shape, (2, 5, 8, 3))
        self.assertEqual(G.pose_mul(p, p.transpose(0, 1)).shape, (2, 2, 7))


class ManiSkillGeometryTest(unittest.TestCase):
    assertClose = GeometryTest.assertClose

    @classmethod
    def setUpClass(cls) -> None:
        try:
            import mani_skill.envs
            from mani_skill.utils.geometry import rotation_conversions
            from mani_skill.utils.structs.pose import Pose
        except Exception as exc:
            raise unittest.SkipTest(f"ManiSkill cannot be imported: {type(exc).__name__}: {exc}") from exc
        cls.rc = rotation_conversions
        cls.Pose = Pose

    def test_all_functions_against_maniskill(self) -> None:
        generator = torch.Generator().manual_seed(193)
        q = torch.randn(1200, 4, generator=generator)
        q /= q.norm(dim=-1, keepdim=True)
        r = torch.randn(1200, 4, generator=generator)
        r /= r.norm(dim=-1, keepdim=True)
        xyz = torch.randn(1200, 3, generator=generator)
        v = torch.randn(1200, 3, generator=generator)
        a = self.Pose.create_from_pq(xyz, q)
        b = self.Pose.create_from_pq(v, r)
        matrix = self.rc.quaternion_to_matrix(q)
        self.assertClose(G.quat_to_matrix(q), matrix)
        self.assertClose(G.quat_apply(q, v), self.rc.quaternion_apply(q, v))
        self.assertClose(G.quat_to_euler_xyz(q), self.rc.matrix_to_euler_angles(matrix, "XYZ"))
        self.assertClose(G.pose_inv(a.raw_pose), a.inv().raw_pose)
        self.assertClose(G.pose_mul(a.raw_pose, b.raw_pose), (a * b).raw_pose)
        for i in range(3):
            self.assertClose(G.axis(q, i), matrix[..., :, i])
        world = xyz + self.rc.quaternion_apply(q, v)
        local = self.rc.quaternion_apply(self.rc.quaternion_invert(q), v - xyz)
        self.assertClose(G.to_world(a.raw_pose, v), world)
        self.assertClose(G.to_local(a.raw_pose, v), local)
        angle = torch.atan2(torch.linalg.cross(xyz, v).norm(dim=-1), (xyz * v).sum(-1))
        self.assertClose(G.angle_between(xyz, v), angle)
        half = torch.rand(1200, 3, generator=generator)
        corners = half[:, None] * torch.tensor(list(itertools.product((-1, 1), repeat=3)))
        expected = xyz[:, None] + self.rc.quaternion_apply(q[:, None], corners)
        self.assertClose(G.box_corners(a.raw_pose, half), expected)
        self.assertClose(G.box_bottom_z(a.raw_pose, half), expected[..., 2].amin(-1))
        self.assertClose(G.box_top_z(a.raw_pose, half), expected[..., 2].amax(-1))

    def test_euler_near_gimbal_lock(self) -> None:
        angles = torch.zeros(1200, 3)
        angles[:, 0] = torch.linspace(-2.8, 2.8, 1200)
        angles[:, 1] = torch.cat((torch.linspace(math.pi / 2 - 1e-3, math.pi / 2 + 1e-3, 600),
                                  torch.linspace(-math.pi / 2 - 1e-3, -math.pi / 2 + 1e-3, 600)))
        angles[:, 2] = torch.linspace(2.7, -2.7, 1200)
        q = self.rc.matrix_to_quaternion(self.rc.euler_angles_to_matrix(angles, "XYZ"))
        expected = self.rc.matrix_to_euler_angles(self.rc.quaternion_to_matrix(q), "XYZ")
        self.assertClose(G.quat_to_euler_xyz(q), expected)
