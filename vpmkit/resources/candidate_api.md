# Candidate API (ManiSkill)

This is the technical specification of a candidate: the files you write, the interfaces they use, how the runtime executes them, and the rules `./check.sh` enforces. TASK.md says what to build and gives the design rules that need judgment. `example/` holds a complete candidate for a fictional pick-and-place task; its layout mirrors your workspace (`env_source.py`, `helpers.py`, `scene_inventory.md`, and `candidate/`).

## 1. What a candidate is

A candidate is a process teacher for one task. It reads the simulator's privileged state and at every step reports:

- the current stage k and the progress within it, p_k in [0, 1];
- the potential Φ = (k + p_k) / K, where K is the number of stages;
- the truth value and margin of every predicate instance it uses;
- guidance: the literals of the current stage's guard that do not hold yet.

It consists of a linear chain of stages (`stage_graph.yaml`), the predicates the chain uses (`predicates.py`), optional per-stage progress functions (`progress.py`), and the bindings that tie its objects to the environment (`bindings.py`). The teacher never decides whether the task is done: success is the environment's `evaluate()["success"]`.

## 2. Files

Write everything in `candidate/`.

| File | Content | Required |
| --- | --- | --- |
| `stage_graph.yaml` | task sentence, objects with display names, the stage chain, official correspondences, tunable parameters | yes |
| `bindings.py` | `bind(env, api)`: which actor each object is, its size, task-specific readings. The only file that touches the environment | yes |
| `predicates.py` | measurement functions and predicates | yes |
| `progress.py` | progress functions for some stages | no |
| `notes.md` | design notes (Section 10) | yes |

## 3. stage_graph.yaml

```yaml
task: <one sentence>
objects:
  <key>: {name: <display name, with its article>}
stages:
  - name: <stage name>
    exit: [<literal>, ...]                        # the guard; at least one literal
    invariants:                                   # optional
      - {literal: <literal>, regress_to: <an earlier stage>}
official:
  - {literals: [<literal>, ...], key: <a key returned by evaluate()>}
params:
  - {name: <parameter name>, default: <number>, range: [<low>, <high>]}
```

- `task`: one sentence describing the task.
- `objects`: the keys are the names used in literals and in `bindings.py` (lowercase identifiers, e.g. `g`, `cube`). `name` is the display name used in guidance, with its article: `the red cube`.
- `stages`: the chain, in order. Names are unique lowercase identifiers. `exit` is the guard: when all its literals hold, the teacher moves to the next stage. Each invariant is one literal and a regress target: when the literal fails, the teacher goes back to that earlier stage. Stage 0 has no invariants.
- `official`: each entry states that the conjunction of `literals` equals the boolean that `evaluate()` returns under `key` (Section 3.3).
- `params`: the search space for the inner parameter optimization (Section 3.4).

Unknown keys are errors. Quote every literal: in a flow list such as `[near(g, cube)]` an unquoted literal is split at the comma.

### 3.1 Literals

A literal is a predicate instance `p(a, b)` or its negation `not p(a, b)`. `p` is a predicate defined in `predicates.py`; `a, b` are object keys, one for each object parameter of `p`, in order. `near(g, cube)` binds the predicate's parameters `(g, o)` to the objects `g` and `cube`.

- Guards, invariants and official correspondences contain only literals: no `or`, no negation of a group, no numeric comparison in YAML. Every condition is a named predicate. If you need an "or", put it inside one predicate (an official angle test that takes the absolute value is an "or" of two directions).
- `not p` holds exactly when `p` does not. Its margin is −margin(p). When margin(p) is exactly 0, `p` holds and `not p` does not.
- When a guard literal `not p` does not hold, its guidance is rendered with p's `need_false` template.

From `example/`:

```yaml
  - name: release
    exit: ["not grasped(g, cube)", "static(cube)"]
    invariants:
      - {literal: "on(cube, pad)", regress_to: reach}
```

```python
@predicate(
    desc="The gripper g holds o: both fingers press on o (the adapter's grasp reading).",
    need_true="{o} is not held; grasp {o} with {g}.",
    need_false="{o} is still held; release {o}.",   # used for "not grasped(g, cube)"
    scale=1.0,
)
def grasped(w, g, o):
    return signed(w.grasping(g, o))  # +1 held, -1 not held
```

While the cube is still held in `release`, the guidance is "The red cube is still held; release the red cube."

### 3.2 The last stage and success

There is no "done" node. The last stage's guard is used only for that stage's guidance and progress. The last stage's guard literals together with its invariant literals must be exactly the environment's success condition, and you declare this in `official` under the key `success`. Then, whenever the teacher is in the last stage and the task has succeeded, the guidance is empty and the progress is 1, in agreement with `success`.

### 3.3 Official correspondences

- Each entry: `literals` (one or more) and `key` (a key returned by `evaluate()`, as listed in `scene_inventory.md`). A key appears in at most one entry. The entry with key `success` is required (Section 3.2).
- A predicate that appears in any entry is an official predicate: you rewrote it from `evaluate()`. Its thresholds are copied from the official values and are fixed, so they never appear in `params`.
- Declare an entry only when the literals compute exactly what `evaluate()` computes for that key. A review agent compares the predicate code with the `evaluate()` source term by term: thresholds, horizontal or 3-D distance, reference points, frames, absolute values, missing conjuncts.

### 3.4 Parameters

- Names: `<predicate>.<threshold>` for a predicate threshold, such as `near.max_dist`; `progress.<stage>.<parameter>` for a progress parameter, such as `progress.reach.d0`.
- A threshold belongs to the predicate, not to an instance: one value is shared by all instances of that predicate.
- Each entry gives a default and a range `[low, high]` with low < high and low ≤ default ≤ high. The default must equal the default in the function signature.
- Declare every threshold of every non-official predicate the file uses, and every parameter of every progress function. Never declare thresholds of official predicates.
- The runtime's debounce setting `runtime.debounce` (m in Section 8.2) defaults to 1. It is not part of a candidate; leave it out.

## 4. World view

Predicates and progress functions read state only through the world view `w` and the object views passed to them. The views are read-only wrappers around a tensor snapshot that the adapter takes at every step, so the same code runs on live environments and on saved states.

Conventions:
- meters, radians, seconds; world frame with z up; the table top is at `w.table_z` (0 in ManiSkill);
- quaternions are `(w, x, y, z)`, as in ManiSkill; a pose is `[N, 7]`: position (3) followed by quaternion (4);
- every value is a torch tensor whose first dimension is the batch N: the parallel environments during training, or the frames of a saved trajectory when it is recomputed; all tensors are on the simulation device.

### 4.1 Object view

For an object bound with `api.actor` or `api.site` (Section 7):

| Field | Shape | Meaning |
| --- | --- | --- |
| `pos` | [N, 3] | origin of the object's frame (the center, for boxes, spheres and cylinders built by ManiSkill) |
| `quat` | [N, 4] | orientation |
| `pose` | [N, 7] | `pos` and `quat` together |
| `lin_vel` | [N, 3] | linear velocity in the world frame (m/s); zero for a site |
| `ang_vel` | [N, 3] | angular velocity in the world frame (rad/s); zero for a site |
| `half_size` | [N, 3] | half extents of the object's box along its own axes |
| `<attribute>` | as bound | a task-specific reading attached in `bindings.py` |

An object bound to an articulation joint (added to the adapter when a task needs it) also has `joint_pos` [N], `joint_vel` [N] and `joint_limits` [N, 2].

### 4.2 Gripper view

For the object bound with `api.gripper()`:

| Field | Shape | Meaning |
| --- | --- | --- |
| `pos`, `quat`, `pose` | [N, 3], [N, 4], [N, 7] | the TCP, the point between the fingertips |
| `lin_vel`, `ang_vel` | [N, 3] | TCP velocity |
| `width` | [N] | distance between the fingers (m) |
| `max_width` | [N] | the width when fully open (0.08 for Panda) |
| `arm_qvel` | [N, J] | arm joint velocities without the fingers (J = 7 for Panda) |

A robot without fingers (a pushing stick) has no `width`, no `max_width`, and no grasp reading.

### 4.3 World view `w`

| Member | Shape | Meaning |
| --- | --- | --- |
| `w.table_z` | [N] | height of the table top |
| `w.grasping(g, o)` | [N] bool | whether gripper g grasps actor o: ManiSkill's `agent.is_grasping(obj)` with its default arguments (both fingers press on o with at least 0.5 N, within 85° of the closing direction) |
| `w.contact_force(a, b)` | [N] | magnitude of the contact force between actors a and b (N); for the gripper, the sum over its two fingers |
| `w.batch_size` | int | N |
| `w.device` | | the simulation device |

The world view does not expose the fields returned by `evaluate()`, and it cannot look objects up by name: an object reaches a predicate only as an argument.

### 4.4 Geometry tools

`from vpmkit.api import G`. All functions are batched and broadcast over leading dimensions.

| Function | Result |
| --- | --- |
| `G.quat_to_matrix(q)` | rotation matrices [..., 3, 3] |
| `G.quat_apply(q, v)` | vectors v rotated by q, [..., 3] |
| `G.quat_to_euler_xyz(q)` | XYZ Euler angles [..., 3], identical to ManiSkill's `matrix_to_euler_angles(quaternion_to_matrix(q), "XYZ")` |
| `G.axis(q, i)` | the i-th axis (0 = x, 1 = y, 2 = z) of the rotated frame, in world coordinates, [..., 3] |
| `G.angle_between(u, v)` | angle between vectors, in [0, π], [...] |
| `G.pose_inv(p)` | the inverse pose, like ManiSkill's `Pose.inv()` |
| `G.pose_mul(a, b)` | the composed pose a·b, like ManiSkill's `a * b` |
| `G.to_local(pose, x)` | world points x expressed in the frame `pose`, [..., 3] |
| `G.to_world(pose, x)` | points x given in the frame `pose`, in world coordinates, [..., 3] |
| `G.box_corners(pose, half_size)` | the 8 corners of the oriented box, [..., 8, 3] |
| `G.box_bottom_z(pose, half_size)`, `G.box_top_z(pose, half_size)` | lowest and highest z of the oriented box, [...] |

## 5. predicates.py

```python
import torch

from vpmkit.api import predicate, signed


def tcp_dist(w, g, o):
    """Distance (m) from the TCP of g to the center of o."""
    return torch.linalg.norm(g.pos - o.pos, dim=-1)


@predicate(
    desc=(
        "The TCP of g is within max_dist of the bounding sphere of o: its distance "
        "to the center of o is at most o's half diagonal plus max_dist."
    ),
    need_true="{g} is far from {o}; move {g} to {o}.",
    need_false="{g} is too close to {o}; move {g} away from {o}.",
    scale=0.3,
)
def near(w, g, o, max_dist=0.02):
    radius = torch.linalg.norm(o.half_size, dim=-1)  # half diagonal of the box of o
    return radius + max_dist - tcp_dist(w, g, o)  # meters
```

`near` measures from the TCP (the point between the fingertips) to the object's center, and lets its reach grow with the object's size, so `max_dist` is a tolerance that does not depend on the object.

A predicate is a function decorated with `@predicate`. Other functions in the file are measurement functions: plain helpers that compute a quantity and may be shared by predicates and progress functions.

### 5.1 Signature

`f(w, <object parameters>, <thresholds>) -> margin [N]`

- The first parameter is `w`.
- Object parameters follow, positional and without defaults. A literal supplies one object per object parameter.
- Thresholds follow, each with a numeric literal default (`0.01`, `-0.015`, `1e-2`). Each threshold is declared in `params` as `<predicate>.<threshold>` unless the predicate is official.
- No `*args` or `**kwargs`.

### 5.2 Margin

- A float tensor [N]: ≥ 0 means the condition holds, and the magnitude says how far the state is from the threshold. State the unit in a comment next to `return`.
- A predicate that is itself a conjunction returns the minimum of its parts' margins, expressed in one unit. It holds exactly when every part holds.
- A boolean reading returns `signed(flag)`: +1 where the flag is true, −1 elsewhere.
- The margin depends only on the current state: no smoothing, no hysteresis, nothing remembered between calls.

### 5.3 Decorator fields

| Field | Required | Content |
| --- | --- | --- |
| `desc` | yes | one sentence: the physical condition the predicate tests. It must match the code |
| `need_true` | yes | guidance for a guard literal `p` that does not hold: the state that does not hold, then its natural remedy |
| `need_false` | if the predicate is ever negated | the same for a guard literal `not p` (TASK.md asks for it on every predicate) |
| `scale` | yes | a positive margin size used by the default progress (Section 6.2): the shortfall at which a failing literal counts 0. Use 1.0 for boolean readings |

Templates: placeholders are the predicate's object parameter names in braces, such as `{g}` and `{o}`; no other placeholders are allowed. When guidance is rendered, each placeholder becomes the display name of the object in that literal, and the first letter is capitalized: `near(g, cube)` gives "The gripper is far from the red cube; move the gripper to the red cube."

### 5.4 Rules

1. **Objects only through parameters.** Do not mention this task's objects inside a predicate, and do not put numbers that describe an object into a predicate (a hole's position, a slot's width). Attach such readings to the object in `bindings.py` and read them from the parameter. Then the predicate also runs on another task's state, with that task's objects.
2. **Current state only.** Read state only through `w` and the object views. Poses and velocities count as current state. Do not record values such as the distance at stage entry.
3. **One definition and one threshold per predicate**, shared by all instances. Put differences between objects into the definition: measure to the object's surface or grasp point, or scale with its half size. A different tolerance means a different condition, so give it a different name (`near(g, cube)` and `at_goal(cube, goal)`).
4. **Official fields are never read.** Generic readings such as `w.grasping` are used directly. To use a task-specific official check, rewrite its formula from `evaluate()` as a predicate over its object parameters, copy its thresholds, and declare it in `official`. When an official check does not mean what you need, write your own predicate and declare nothing. `success` is never a predicate.
5. **Batched tensors only:** torch operations on [N] tensors on the simulation device. No loops, no `.item()`, `.tolist()`, `.numpy()` or `.cpu()`.
6. Every predicate is evaluated in every state, whatever the current stage, so it must not assume that some earlier stage has been passed.

### 5.5 Calling predicates and measurement functions

Predicates and progress functions may call measurement functions. A predicate called directly returns its margin; any threshold you do not pass takes its current value (the default, or the value set by parameter tuning). Do not build composite predicates just to fit a guard into one literal (TASK.md).

## 6. progress.py

### 6.1 Progress functions

```python
from .predicates import tcp_dist


def progress_reach(w, o, d0=0.3):
    # 1 at the cube's center, 0 at d0 or farther; d0 is a fixed scale declared in params.
    return 1.0 - tcp_dist(w, o.g, o.cube) / d0
```

- The name is `progress_<stage>` for an existing stage. Other functions in the file are helpers.
- The signature is `(w, o, <parameters>) -> [N]`. `o` holds this task's objects by key (`o.g`, `o.cube`). Each parameter has a numeric literal default and is declared in `params` as `progress.<stage>.<parameter>`.
- Progress does not take part in cross-task merging, so it may name this task's objects, and it may call this task's predicates and measurement functions (`from .predicates import ...`).
- Progress depends only on the current state and the current stage. Normalize with fixed scale parameters, never with a value recorded when the stage began.
- The runtime clips the result to [0, 1].
- Every stage's progress function is evaluated at every step, whatever the current stage, so it must work in any state.

### 6.2 Default progress

A stage without a progress function gets the default: the mean, over its guard literals, of 1 for a literal that holds and clip(1 + margin / scale, 0, 1) for one that does not, where scale is the predicate's `scale`. The default progress and the guidance point at the same conditions.

- A stage whose guard is a single boolean literal (`grasped`) has default progress 0 until the literal holds, and then the stage advances at once. Write no progress for it.
- When all of the last stage's guard literals hold, its progress is 1, whatever its progress function returns.

## 7. bindings.py

<!-- Planned interface (2026-10-21): check against the M2 adapter, then delete this comment before any input package is built. -->

```python
def bind(env, api):
    return {
        "g": api.gripper(),
        "cube": api.actor(env.cube, half_size=env.cube_half_size),
        "pad": api.actor(env.pad, half_size=env.pad_half_size),
    }
```

- `env` is the unwrapped environment: an instance of the task class in `env_source.py`. `scene_inventory.md` lists its actors and the attribute values that `evaluate()` reads.
- `bind` ends with `return {...}`: a dict literal whose keys are exactly the keys of `objects`.
- `api.gripper(**attrs)` binds the robot's gripper (Section 4.2).
- `api.actor(actor, half_size, **attrs)` binds an actor of the environment. `half_size` is a number, a length-3 sequence or tensor, an [N, 3] tensor (when sizes differ between parallel environments), or a function of `env` that returns one of these.
- `api.site(pose, half_size=0.0, **attrs)` binds a frame that is not an actor, such as a target point computed by the task. `pose` is a function of `env` that returns an [N, 7] tensor or a ManiSkill `Pose`. A site has zero velocity and cannot be grasped.
- `attrs` attach task-specific readings: `name=value`, where value is a tensor (broadcast to [N, ...]) or a function of `env` that the adapter calls at every step. Names must not clash with the view fields. Predicates read them as `o.<name>`.

Attaching readings, for a hypothetical box with a slot:

```python
        "box": api.actor(
            env.box,
            half_size=env.box_half_sizes,                   # [N, 3]: differs between environments
            slot_pose=lambda env: env.slot_pose.raw_pose,   # re-read every step
            slot_width=env.slot_widths,                     # [N]
        ),
```

`bindings.py` is the only candidate file that touches the environment. It may import what it needs, subject to the safety rules in Section 9.

## 8. How the teacher runs

### 8.1 Stage variable

Each parallel environment has an integer `stage`, from 0 to K − 1, kept by the teacher; it is not part of the simulator state. At every episode start the stage of that environment is reset to 0. A run resumed from a saved state also restores the saved stage. The stage is the teacher's only memory: Φ depends on history only through k.

### 8.2 One step

1. Evaluate every predicate instance in the file once. Guards, invariants, guidance and outputs all use these values.
2. Check the current stage's invariants. If one fails, go back to its `regress_to` stage; if several fail, go back to the earliest of their targets. (An invariant must fail for m consecutive steps, where m = `runtime.debounce` = 1, so one step is enough.)
3. Advance while the current stage's guard holds: move to the next stage and check its guard, so one step can pass several stages. This also happens right after going back.
4. Compute the progress p_k, the potential Φ and the guidance of the resulting stage.

Invariants of a stage entered during this step are checked from the next step on.

Example (from `example/`): in `carry` the cube slips out of the gripper. The invariant `grasped(g, cube)` fails, so the stage goes back to `reach` and advances again in the same step. If the TCP is still at the cube, `near(g, cube)` holds and the stage stops at `grasp`: "The red cube is not held; grasp the red cube with the gripper." If the gripper is far, it stops at `reach`: "The gripper is far from the red cube; move the gripper to the red cube." Both are right. In the same way, `grasp` keeps `near(g, cube)` as an invariant: if the gripper wanders out of the cube's vicinity before it has grasped the cube, the stage goes back to `reach`. A regress target need not be exact: the guards walk the stage forward to the right place, as long as the target lies in the round that established the broken condition (TASK.md).

### 8.3 Success and episode end

The teacher does not read `success`. ManiSkill ends an episode when `evaluate()["success"]` becomes true. In runs that continue past success (evaluation, recordings), the last stage's conditions are exactly the success condition (Section 3.2), so once the teacher is in the last stage the guidance is empty and the progress is 1.

### 8.4 Outputs at every step

| Field | Shape | Meaning |
| --- | --- | --- |
| `stage` | [N] int | the current stage k |
| `stage_progress` | [N] | p_k in [0, 1] |
| `phi` | [N] | (k + p_k) / K |
| `pred` | [N, P] bool | truth value of each predicate instance used in the file |
| `margin` | [N, P] | margin of each instance |
| `guidance` | [N, P] bool | instances whose literal in the current stage's guard does not hold |

P counts distinct instances: `grasped(g, cube)` and `not grasped(g, cube)` share one column. Text is rendered only on request: the guard's failing literals, in guard order, each with its `need_true` or `need_false` template.

## 9. Checks run by ./check.sh

`./check.sh` checks `./candidate` and runs four groups of checks in order. A group runs only if the previous one passed. Every problem is reported with a code from the table below, a location (file and line, or a path in the YAML such as `stages[2].invariants[0].regress_to`) and a message. These are the same checks that decide whether the candidate passes the first layer.

### 9.1 Parse

| Code | Rule |
| --- | --- |
| `parse.missing_file` | `stage_graph.yaml`, `bindings.py`, `predicates.py` and `notes.md` exist |
| `parse.yaml` | `stage_graph.yaml` is valid YAML |
| `parse.python` | every `.py` file parses |

### 9.2 Schema and references

| Code | Rule |
| --- | --- |
| `schema.format` | the YAML has the structure of Section 3: required fields present, types right, no unknown keys, names unique |
| `schema.literal_syntax` | every literal is `p(a, ...)` or `not p(a, ...)` |
| `schema.unknown_predicate` | every literal names a `@predicate` function in `predicates.py` |
| `schema.arity` | every literal has one object per object parameter of its predicate |
| `schema.unknown_object` | every literal argument is a key of `objects` |
| `schema.binding_keys` | `bind` returns a dict literal whose keys are exactly the keys of `objects` |
| `schema.predicate_signature` | predicates follow Section 5.1 |
| `schema.progress_signature` | progress functions follow Section 6.1, and each names an existing stage |
| `schema.empty_guard` | every stage has at least one guard literal |
| `schema.regress_target` | every `regress_to` names a stage before the current one |
| `schema.guard_contradiction` | no guard contains both `p` and `not p`; such a stage could never be left |
| `schema.invariant_conflict` | no invariant contradicts its own stage's guard: invariant `p` with `not p` in the guard, or the reverse |
| `schema.regress_too_late` | an invariant's literal appears in the guard of some stage from its regress target up to the stage before its own. Otherwise, after going back, the guards walk straight back to the current stage and the invariant has no effect |
| `schema.success` | `official` has an entry with key `success`, and its literals are exactly the last stage's guard literals plus its invariant literals |
| `schema.official_format` | every `official` entry has at least one literal, and no key appears twice |
| `schema.official_threshold` | no threshold of an official predicate appears in `params` |
| `schema.param_unknown` | every `params` name is a threshold of a predicate the file uses, or a parameter of a progress function |
| `schema.param_missing` | every threshold of a non-official predicate the file uses, and every progress parameter, is declared in `params` |
| `schema.param_value` | every range has low < high, the default lies in the range, and it equals the signature default |
| `schema.template` | every predicate the file uses has `desc`, `need_true` and `scale`, and `need_false` if it is negated anywhere |
| `schema.template_placeholder` | templates use only `{<object parameter>}` placeholders |

### 9.3 Code restrictions

| Code | Rule |
| --- | --- |
| `ast.import` | `predicates.py` imports only `torch` (and its submodules), `math` and `vpmkit.api`; `progress.py` may also import from `.predicates` |
| `ast.host_transfer` | `predicates.py` and `progress.py` call none of `.item()`, `.tolist()`, `.numpy()`, `.cpu()` |
| `ast.loop` | `predicates.py` and `progress.py` contain no `for`, `while` or comprehension |
| `ast.name_access` | `predicates.py` reads no `.name` attribute |
| `ast.unsafe` | no `.py` file reads or writes files, starts processes or opens network connections: no `open`, `exec`, `eval`, `compile` or `__import__`; no import of `os`, `sys`, `io`, `pathlib`, `shutil`, `glob`, `tempfile`, `pickle`, `shelve`, `subprocess`, `multiprocessing`, `threading`, `socket`, `urllib`, `http`, `requests`, `importlib`, `ctypes` or `builtins`; no name or attribute that starts and ends with a double underscore |

### 9.4 Run check

The candidate is bound to the real environment on the GPU with 8 parallel environments; with each of 3 seeds the environment is reset and 30 random actions are taken (about 744 states). At every state the teacher computes every predicate instance, every stage's progress and the stage update.

| Code | Rule |
| --- | --- |
| `run.bind` | `bind` runs, and every binding reads without error |
| `run.official_key` | every `official` key is returned by `evaluate()` |
| `run.error` | no predicate, measurement function, progress function or stage update raises |
| `run.output` | predicates and progress functions return float tensors of shape [N] on the simulation device |
| `run.nonfinite` | no NaN or Inf |

The run check does not judge meaning. Because every stage's progress and every predicate are computed in every state, code errors in stages that random actions never reach are still found.

## 10. notes.md

Use these four headings:

1. **Why the stages are split this way.** Also list other ways to do the task that the chain does not follow.
2. **Guards with more than one literal**, and why their literals must hold at the same time.
3. **Predicates rewritten from `evaluate()`**, and the key each one corresponds to.
4. **Uncertainties.**

If you disagree with an error reported by the review, do not change the candidate for it; add a final section, **Responses to review**, that gives your reasons. The next review reads them and may withdraw the error.
