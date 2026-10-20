"""Batched torch geometry; quaternions use (w, x, y, z)."""

import torch


def quat_normalize(q):
    return q / torch.linalg.vector_norm(q, dim=-1, keepdim=True)


def quat_mul(q1, q2):
    a, b, c, d = q1.unbind(-1)
    e, f, g, h = q2.unbind(-1)
    return torch.stack((a*e-b*f-c*g-d*h, a*f+b*e+c*h-d*g,
                        a*g-b*h+c*e+d*f, a*h+b*g-c*f+d*e), dim=-1)


def quat_conj(q):
    return torch.cat((q[..., :1], -q[..., 1:]), dim=-1)


def quat_to_matrix(q):
    """Rotation matrix for a nonzero quaternion, including nonunit inputs."""
    r, i, j, k = q.unbind(-1)
    two_s = 2.0 / (q * q).sum(-1)
    return torch.stack((
        1-two_s*(j*j+k*k), two_s*(i*j-k*r), two_s*(i*k+j*r),
        two_s*(i*j+k*r), 1-two_s*(i*i+k*k), two_s*(j*k-i*r),
        two_s*(i*k-j*r), two_s*(j*k+i*r), 1-two_s*(i*i+j*j),
    ), dim=-1).reshape(q.shape[:-1] + (3, 3))


def quat_apply(q, v):
    return torch.matmul(quat_to_matrix(q), v.unsqueeze(-1)).squeeze(-1)


def _angle_from_tan(axis, other_axis, data, horizontal, tait_bryan):
    # PyTorch3D's matrix_to_euler_angles helper, preserving its axis conventions.
    i1, i2 = {"X": (2, 1), "Y": (0, 2), "Z": (1, 0)}[axis]
    if horizontal:
        i2, i1 = i1, i2
    even = (axis + other_axis) in ["XY", "YZ", "ZX"]
    if horizontal == even:
        return torch.atan2(data[..., i1], data[..., i2])
    if tait_bryan:
        return torch.atan2(-data[..., i2], data[..., i1])
    return torch.atan2(data[..., i2], -data[..., i1])


def quat_to_euler_xyz(q):
    """PyTorch3D matrix_to_euler_angles(quaternion_to_matrix(q), 'XYZ')."""
    matrix = quat_to_matrix(q)
    central_angle = torch.asin(matrix[..., 0, 2])
    return torch.stack((
        _angle_from_tan("X", "Y", matrix[..., 2], False, True),
        central_angle,
        _angle_from_tan("Z", "Y", matrix[..., 0, :], True, True),
    ), dim=-1)


def pose_mul(p1, q1, p2, q2):
    return p1 + quat_apply(q1, p2), quat_mul(q1, q2)


def pose_inv(p, q):
    qi = quat_conj(quat_normalize(q))
    return -quat_apply(qi, p), qi


def to_local(frame_p, frame_q, points):
    """Transform [N,3] or [N,...,3] world points into frame coordinates."""
    while frame_p.ndim < points.ndim:
        frame_p = frame_p.unsqueeze(-2)
        frame_q = frame_q.unsqueeze(-2)
    return quat_apply(quat_conj(frame_q), points - frame_p)


def from_local(frame_p, frame_q, points):
    """Transform [N,3] or [N,...,3] frame points into world coordinates."""
    while frame_p.ndim < points.ndim:
        frame_p = frame_p.unsqueeze(-2)
        frame_q = frame_q.unsqueeze(-2)
    return frame_p + quat_apply(frame_q, points)


def body_axis(q, i):
    return quat_to_matrix(q)[..., :, i]


def angle_between(u, v):
    un = torch.nn.functional.normalize(u, dim=-1)
    vn = torch.nn.functional.normalize(v, dim=-1)
    return torch.acos((un * vn).sum(-1).clamp(-1.0, 1.0))


def dist(a_pos, b_pos):
    return torch.linalg.vector_norm(a_pos - b_pos, dim=-1)


def xy_dist(a_pos, b_pos):
    return dist(a_pos[..., :2], b_pos[..., :2])


def obb_corners(pos, quat, half_size):
    signs = half_size.new_tensor([
        [-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
        [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1],
    ])
    return from_local(pos, quat, half_size.unsqueeze(-2) * signs)


def obb_min_z(pos, quat, half_size):
    return obb_corners(pos, quat, half_size)[..., 2].amin(-1)


def obb_max_z(pos, quat, half_size):
    return obb_corners(pos, quat, half_size)[..., 2].amax(-1)
