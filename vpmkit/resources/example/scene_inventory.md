# Scene inventory: PlaceCubeOnPad-v1

Fictional example: the values follow `env_source.py`. In a real input package this file is generated from the running environment.

- ManiSkill 3.0.1; robot `panda`. The table top is at z = 0 (`w.table_z`).
- Initial states sampled: 3 seeds × 8 parallel environments = 24.
- Units: m, rad. World frame with z up; quaternions (w, x, y, z).

## Objects

| Attribute | Actor name | Kind | Half size (m) | Initial position (m), min … max | Initial orientation (XYZ Euler, rad), min … max |
| --- | --- | --- | --- | --- | --- |
| `env.cube` | `cube` | dynamic | [0.02, 0.02, 0.02] in all environments | x −0.118 … −0.043, y −0.097 … 0.095, z 0.020 | x 0, y 0, z −3.09 … 3.12 |
| `env.pad` | `pad` | kinematic | [0.05, 0.05, 0.005] in all environments | x 0.042 … 0.117, y −0.096 … 0.098, z 0.005 | x 0, y 0, z 0 |

Kinds: dynamic (moved by physics), kinematic (moved only by the task code), visual only (no collision).

## Robot

| Part | Value |
| --- | --- |
| Gripper | Panda two-finger gripper. TCP: link `panda_hand_tcp`, between the fingertips. Full opening 0.08 m |
| Arm | 7 joints, plus 2 finger joints |

## evaluate() keys

| Key | Type |
| --- | --- |
| `is_cube_grasped` | bool [N] |
| `is_cube_on_pad` | bool [N] |
| `is_cube_static` | bool [N] |
| `success` | bool [N] |

## Attribute values read by evaluate()

| Attribute | Value | Same in all environments |
| --- | --- | --- |
| `self.cube_half_size` | [0.02, 0.02, 0.02] | yes |
| `self.pad_half_size` | [0.05, 0.05, 0.005] | yes |
