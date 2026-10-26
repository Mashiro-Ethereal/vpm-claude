"""Broadcasting torch geometry with ManiSkill's wxyz conventions."""

import torch
from torch import Tensor


def _conj(q: Tensor) -> Tensor:
    return q * q.new_tensor([1, -1, -1, -1])


def _mul(a: Tensor, b: Tensor) -> Tensor:
    aw, ax, ay, az = a.unbind(-1)
    bw, bx, by, bz = b.unbind(-1)
    return torch.stack((aw*bw - ax*bx - ay*by - az*bz,
                        aw*bx + ax*bw + ay*bz - az*by,
                        aw*by - ax*bz + ay*bw + az*bx,
                        aw*bz + ax*by - ay*bx + az*bw), -1)


def quat_to_matrix(q: Tensor) -> Tensor:
    """Convert [..., 4] quaternions to [..., 3, 3] rotation matrices."""
    r, i, j, k = q.unbind(-1)
    s = 2.0 / (q * q).sum(-1)
    values = torch.stack((1 - s*(j*j + k*k), s*(i*j - k*r), s*(i*k + j*r),
                          s*(i*j + k*r), 1 - s*(i*i + k*k), s*(j*k - i*r),
                          s*(i*k - j*r), s*(j*k + i*r), 1 - s*(i*i + j*j)), -1)
    return values.reshape(q.shape[:-1] + (3, 3))


def quat_apply(q: Tensor, v: Tensor) -> Tensor:
    """Rotate vectors using q * (0, v) * conjugate(q)."""
    pure = torch.cat((v.new_zeros(v.shape[:-1] + (1,)), v), -1)
    return _mul(_mul(q, pure), _conj(q))[..., 1:]


def quat_to_euler_xyz(q: Tensor) -> Tensor:
    """Return XYZ Euler angles with ManiSkill's asin clamp."""
    m = quat_to_matrix(q)
    return torch.stack((torch.atan2(-m[..., 1, 2], m[..., 2, 2]),
                        torch.asin(m[..., 0, 2].clamp(-1 + 1e-8, 1 - 1e-8)),
                        torch.atan2(-m[..., 0, 1], m[..., 0, 0])), -1)


def axis(q: Tensor, i: int) -> Tensor:
    """Return column i of the rotated frame."""
    return quat_to_matrix(q)[..., :, i]


def angle_between(u: Tensor, v: Tensor) -> Tensor:
    """Return the unsigned angle; a zero vector gives zero."""
    u, v = torch.broadcast_tensors(u, v)
    return torch.atan2(torch.linalg.vector_norm(torch.linalg.cross(u, v), dim=-1),
                       (u * v).sum(-1))


def pose_inv(p: Tensor) -> Tensor:
    """Invert a pose without standardizing its quaternion."""
    q = _conj(p[..., 3:])
    return torch.cat((quat_apply(q, -p[..., :3]), q), -1)


def pose_mul(a: Tensor, b: Tensor) -> Tensor:
    """Compose poses, standardizing the product quaternion's sign."""
    q = _mul(a[..., 3:], b[..., 3:])
    q = torch.where(q[..., :1] < 0, -q, q)
    return torch.cat((a[..., :3] + quat_apply(a[..., 3:], b[..., :3]), q), -1)


def to_local(pose: Tensor, x: Tensor) -> Tensor:
    return quat_apply(_conj(pose[..., 3:]), x - pose[..., :3])


def to_world(pose: Tensor, x: Tensor) -> Tensor:
    return pose[..., :3] + quat_apply(pose[..., 3:], x)


def box_corners(pose: Tensor, half_size: Tensor) -> Tensor:
    """Return eight corners in lexicographic (-1, 1) sign order."""
    signs = half_size.new_tensor([[-1, -1, -1], [-1, -1, 1], [-1, 1, -1], [-1, 1, 1],
                                  [1, -1, -1], [1, -1, 1], [1, 1, -1], [1, 1, 1]])
    return to_world(pose.unsqueeze(-2), half_size.unsqueeze(-2) * signs)


def box_bottom_z(pose: Tensor, half_size: Tensor) -> Tensor:
    return box_corners(pose, half_size)[..., 2].amin(-1)


def box_top_z(pose: Tensor, half_size: Tensor) -> Tensor:
    return box_corners(pose, half_size)[..., 2].amax(-1)
