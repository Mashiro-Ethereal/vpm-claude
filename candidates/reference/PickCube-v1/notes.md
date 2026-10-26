# Notes: PickCube-v1

## 1. Why the stages are split this way

One pick-and-place round without the release: reach → grasp → carry → settle. Boundaries sit where contact changes (the fingers close on the cube) and where goal relations are reached (the cube is at the goal; the arm is at rest). PickCube's success does not require letting go, so there is no release stage.

reach only brings the gripper to the cube's vicinity (`near`); lining up and closing are left to exploration during grasp.

Invariants and regress targets:

- grasp keeps `near(g, cube)` → reach: the gripper wanders off while trying to grasp.
- carry keeps `grasped(g, cube)` → reach: the cube slips out; the teacher walks forward again in the same step, to grasp if the gripper is still at the cube, else reach.
- settle keeps `at_goal(cube, goal)` → carry, the stage that established it: the cube drifts out of the goal while the arm slows down. If the cube was also dropped, carry's invariant sends the teacher to reach at the next step; there is one step of carry guidance for a cube that is no longer held.

Progress: reach has its own progress 1 − d/d0 with the fixed scale `progress.reach.d0`; grasp has a boolean guard and none; carry and settle use the default progress (at_goal with scale 0.3 m; arm_static with scale 1 rad/s).

Other ways: when the goal is low (its height is the cube's resting height plus U[0, 0.3]), pushing the cube to the goal without grasping can also succeed. The chain does not follow this.

## 2. Guards with more than one literal

None.

## 3. Predicates rewritten from evaluate()

| Literals | Key | How |
| --- | --- | --- |
| `grasped(g, cube)` | `is_grasped` | `w.grasping` is `agent.is_grasping` with its default arguments, the call evaluate() makes |
| `at_goal(cube, goal)` | `is_obj_placed` | 3-D distance between the goal's position and the cube's center ≤ goal_thresh = 0.025, the panda value |
| `arm_static(g)` | `is_robot_static` | max \|qvel\| over the arm joints ≤ 0.2; `arm_qvel` excludes the two finger joints, as Panda.is_static does |
| `arm_static(g)`, `at_goal(cube, goal)` | `success` | settle's guard plus its invariant |

Their thresholds are fixed and not in params; near's threshold is tunable.

## 4. Uncertainties

- `near.max_dist` = 0.02: near holds within about 5.5 cm of the cube's center (half diagonal 3.46 cm plus 2 cm).
- goal_thresh is the panda value; another robot would need another value.
- arm_static can flicker while the arm decelerates; at_goal can flicker at the 2.5 cm boundary, moving the teacher between carry and settle.
- grasped comes from contact forces and can flicker in the first steps of a grasp; each flicker during carry sends the teacher back to reach, and it walks forward again in the same step.
