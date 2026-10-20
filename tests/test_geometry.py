import math
import unittest

import torch

from vpmkit import geometry as G


def axis_quat(axis, angle):
    q = torch.zeros(1, 4, dtype=torch.float64)
    q[:, 0] = math.cos(angle / 2)
    q[:, axis + 1] = math.sin(angle / 2)
    return q


class GeometryTests(unittest.TestCase):
    def test_quaternion_apply_matrix_and_roundtrip(self):
        torch.manual_seed(7)
        q = G.quat_normalize(torch.randn(5, 4, dtype=torch.float64))
        v = torch.randn(5, 3, dtype=torch.float64)
        rotated = G.quat_apply(q, v)
        torch.testing.assert_close(rotated, (G.quat_to_matrix(q) @ v[..., None]).squeeze(-1))
        torch.testing.assert_close(G.quat_apply(G.quat_conj(q), rotated), v)
        identity = torch.tensor([1., 0., 0., 0.], dtype=torch.float64).expand(5, 4)
        torch.testing.assert_close(G.quat_mul(q, G.quat_conj(q)), identity)
        torch.testing.assert_close(G.quat_to_matrix(q * 3), G.quat_to_matrix(q))

    def test_euler_xyz_known_and_composed_rotations(self):
        for axis in range(3):
            q = axis_quat(axis, 0.6)
            expected = torch.zeros(1, 3, dtype=torch.float64)
            expected[:, axis] = 0.6
            torch.testing.assert_close(G.quat_to_euler_xyz(q), expected)
        # XYZ means Rx @ Ry @ Rz, rather than the common roll/pitch/yaw order.
        q = G.quat_mul(G.quat_mul(axis_quat(0, 0.3), axis_quat(1, -0.5)), axis_quat(2, 0.7))
        torch.testing.assert_close(G.quat_to_euler_xyz(q), torch.tensor([[0.3, -0.5, 0.7]], dtype=torch.float64))
        torch.testing.assert_close(G.quat_to_euler_xyz(-q * 4), G.quat_to_euler_xyz(q))

    def test_pose_and_point_roundtrips(self):
        p = torch.tensor([[1., 2., 3.]], dtype=torch.float64)
        q = axis_quat(2, 0.7)
        pi, qi = G.pose_inv(p, q)
        zero, identity = G.pose_mul(p, q, pi, qi)
        torch.testing.assert_close(zero, torch.zeros_like(p))
        torch.testing.assert_close(identity, torch.tensor([[1., 0., 0., 0.]], dtype=torch.float64))
        points = torch.tensor([[[3., 4., 5.], [7., 8., 9.]]], dtype=torch.float64)
        torch.testing.assert_close(G.from_local(p, q, G.to_local(p, q, points)), points)
        torch.testing.assert_close(G.from_local(p, q, G.to_local(p, q, points[:, 0])), points[:, 0])

    def test_rotated_box_extents(self):
        p = torch.tensor([[0., 0., 5.]], dtype=torch.float64)
        q = axis_quat(1, math.pi / 4)
        half = torch.tensor([[1., 2., 3.]], dtype=torch.float64)
        self.assertEqual(G.obb_corners(p, q, half).shape, (1, 8, 3))
        extent = 4 / math.sqrt(2)
        torch.testing.assert_close(G.obb_min_z(p, q, half), torch.tensor([5-extent], dtype=torch.float64))
        torch.testing.assert_close(G.obb_max_z(p, q, half), torch.tensor([5+extent], dtype=torch.float64))

    def test_axes_distances_and_gradient(self):
        q = axis_quat(2, math.pi / 2)
        torch.testing.assert_close(G.body_axis(q, 0), torch.tensor([[0., 1., 0.]], dtype=torch.float64))
        a, b = torch.tensor([[3., 4., 12.]]), torch.zeros(1, 3)
        torch.testing.assert_close(G.dist(a, b), torch.tensor([13.]))
        torch.testing.assert_close(G.xy_dist(a, b), torch.tensor([5.]))
        torch.testing.assert_close(G.angle_between(torch.tensor([[1., 0., 0.]]), torch.tensor([[0., 1., 0.]])), torch.tensor([math.pi / 2]))
        q.requires_grad_()
        G.quat_apply(q, torch.ones(1, 3, dtype=torch.float64)).sum().backward()
        self.assertTrue(torch.isfinite(q.grad).all())
