# Notes: PlaceCubeOnPad-v1

## 1. Why the stages are split this way

The task is one pick-and-place round: reach → grasp → carry → release. Stage boundaries sit where contact changes (the fingers close on the cube; they let go) and where the goal relation is reached (the cube rests on the pad). Grasping and releasing each get their own stage.

reach only brings the gripper to the cube's vicinity (`near`); lining up with the cube and closing on it are left to exploration during grasp.

Invariants and regress targets:
- grasp keeps `near(g, cube)`. If the gripper wanders out of the cube's vicinity while trying to grasp, the teacher goes back to reach: the guidance asks to move to the cube again, Φ drops, and reach's progress leads the gripper back.
- carry keeps `grasped(g, cube)`. If the cube slips out, the teacher goes back to reach and walks forward again in the same step: it stops at grasp if the gripper is still at the cube, and at reach if it is not.
- release keeps `on(cube, pad)`. If the cube leaves the pad (lifted again before letting go, or knocked off afterwards), the teacher goes back to reach, the start of the round, and walks forward to the stage the state calls for: carry if the cube is still held, grasp or reach if not. Going back only to carry would give one step of "put the red cube on the target pad" for a cube that is no longer held.

Progress: reach has its own progress, 1 − d/d0 on the distance from the TCP to the cube's center, with a fixed scale d0 declared as `progress.reach.d0` so that the approach shaping can be tuned. grasp has a boolean guard and no progress. carry and release use the default progress of their guard literals.

Other ways to do the task: letting go above the pad so that the cube drops onto it also succeeds. The chain does not follow this: when the cube leaves the gripper during carry, the teacher goes back to grasp or reach. Pushing the cube onto the pad would need it lifted over the pad's 1 cm edge, so the chain does not consider it.

## 2. Guards with more than one literal

release: `not grasped(g, cube)` and `static(cube)`. evaluate() requires both at the same time, and neither implies the other: a held cube can be still, and a released cube can still be rocking or sliding. A separate settle stage for `static(cube)` would add a boundary that is neither a contact change nor a goal relation.

## 3. Predicates rewritten from evaluate()

| Literals | Key | How |
| --- | --- | --- |
| `grasped(g, cube)` | `is_cube_grasped` | `w.grasping` is `agent.is_grasping` with its default arguments, the call evaluate() makes |
| `on(cube, pad)` | `is_cube_on_pad` | the same two tests: the horizontal distance between the centers is at most the pad's x half size minus the cube's x half size; the vertical gap between the cube's bottom and the pad's top is within 0.005 m. The half sizes are bound from `cube_half_size` and `pad_half_size`, the attributes evaluate() reads |
| `static(cube)` | `is_cube_static` | `Actor.is_static` with the arguments evaluate() passes: `lin_thresh=1e-2`, `ang_thresh=0.5` (the default `ang_thresh` is 0.1) |
| `on(cube, pad)`, `static(cube)`, `not grasped(g, cube)` | `success` | release's guard plus its invariant |

The thresholds of these predicates are copied from evaluate() and fixed, so they are not in params. `near` has no official counterpart; its threshold `near.max_dist` is tunable.

## 4. Uncertainties

- `near.max_dist` = 0.02: near holds within 5.5 cm of the cube's center (its half diagonal, 3.5 cm, plus 2 cm). grasp therefore begins with the gripper near the cube but not yet around it, and lining up and closing get no shaping. If grasping learns slowly, tuning can lower `max_dist`; at 0, near holds only inside the cube's bounding sphere.
- At the edge of the vicinity, `near` can change from one step to the next, moving the teacher between reach and grasp. Each change moves Φ only a little, between about 0.20 and 0.25.
- `on` measures the horizontal room with the x half sizes only, as evaluate() does. Because the pad is square and never rotated, this equals the y version.
- `static` returns the smaller slack of the two speed limits, as a fraction of the limit. With scale 1, its share of release's default progress rises from 0 at twice the limits to 1 at the limits.
- `grasped` comes from contact forces and can flicker during the first steps of a grasp. Each flicker during carry sends the teacher back to reach; it walks forward to grasp in the same step and returns to carry once the grasp holds again.
