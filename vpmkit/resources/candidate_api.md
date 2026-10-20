# Candidate API

A candidate describes a linear task process using object handles, tensor
predicates, and stage exit conditions. Each batch row is one environment or one
trajectory frame. Compute each row independently so that batched evaluation and
frame-by-frame evaluation agree. Use meters, world z up, table top z = 0, and
quaternions in `(w, x, y, z)` order. Keep tensors on `w.device`.

## Directory layout

```text
candidate/
  stage_graph.yaml
  bindings.py
  predicates.py
  progress.py       # optional; omitted stages use default progress
  notes.md          # optional author notes; ignored by the loader
```

## Stage graph

```yaml
task: Move a block to the region and release it
objects:
  g: {name: gripper}
  block: {name: block}
  region: {name: target region}
stages:
  - name: reach
    exit: ["gripper_open(g)", "near(g, block)"]
  - name: grasp
    exit: ["grasped(g, block)"]
  - name: carry
    exit: ["in_region(block, region)"]
    invariants:
      - literal: grasped(g, block)
        regress_to: grasp
        event: "Regrasp {block} with {g}."
  - name: release
    exit: ["in_region(block, region)", "not grasped(g, block)"]
official:
  - literals: ["in_region(block, region)", "not grasped(g, block)"]
    key: success
params:
  - {name: near.max_dist, default: 0.1, range: [0.02, 0.3]}
  - {name: progress.carry.span, default: 0.5, range: [0.1, 1.0]}
runtime: {debounce: 2}
```

`task`, `objects`, and `stages` are required. `objects` maps handles to display
names. Stage names must be unique; there must be at least one stage and each
`exit` must contain at least one literal. An exit is the conjunction of its
literals. `invariants`, `official`, and `params` default to empty lists.
`runtime.debounce` defaults to 2 and must be an integer at least 1. Unknown YAML
fields are rejected at every level.

An invariant has `literal`, `regress_to`, and `event`. Its target must name an
earlier stage. Event placeholders are object **handles** such as `{block}` and
are filled with display names.

Literals have the forms `near(g, block)`, `not near(g, block)`, or
`¬near(g, block)`. Whitespace is allowed around tokens; `not` needs following
whitespace. Predicates and handles are identifiers matching
`[A-Za-z_][A-Za-z0-9_]*`. Zero-object predicates use `ready()`.

Each `official` entry states that its literals' conjunction must equal the
environment judgment named by `key`, frame by frame. Every threshold of a
predicate used in an official entry stays fixed: none may appear in `params`.

Parameter names are `<predicate>.<threshold>` or `progress.<stage>.<param>`.
They must refer to an existing numeric keyword. Ranges have two finite bounds
with `lo < hi`; defaults and overrides must lie inside the inclusive range.
Duplicate parameter declarations are rejected. Declared YAML defaults override
Python defaults when Teacher calls a function. Calls made directly inside
candidate code follow normal Python argument rules. Undeclared keywords retain
their Python defaults.

## Predicates and margins

```python
from vpmkit.api import G, predicate, bool_margin

@predicate(
    desc="Gripper is near an object",
    need_true="Move {hand} near {obj}.",
    need_false="Move {hand} away from {obj}.",
    scale=0.2,
)
def near(w, hand, obj, *, max_dist=0.1):
    return max_dist - G.dist(hand.pos, obj.pos)
```

The first argument is required and named `w`. Following positional arguments
are required object parameters. All remaining arguments must be keyword-only
thresholds with finite `int` or `float` defaults (not booleans). Variadic
arguments and positional defaults are rejected when the decorator runs.

Return a tensor of shape `[N]`: preferably float32 margins, or boolean truth
values. The runtime converts numeric margins to float32 and boolean tensors to
`+1.0` for true and `-1.0` for false. A predicate holds exactly when its margin
is **greater than or equal to zero**. Negation reverses that truth value; a
negative literal is false at zero margin. Scalars, incorrect shapes, results on
another device, complex values, and NaN/Inf are rejected with the instance name.

`desc` describes the predicate. `need_true` describes how to make it hold;
`need_false` describes how to make it false and is required if any literal is
negated. These templates use **function object parameter names**, such as
`{hand}` and `{obj}` above, mapped to the bound objects' display names.
`scale` is a finite positive margin distance used by default progress (default
1.0); it does not alter predicate truth.

The decorator returns the original function and attaches `__vpm_predicate__`,
a `PredicateSpec` with `name`, `desc`, `need_true`, `need_false`, `scale`,
`obj_params`, and `thresholds`. Other undecorated helper functions are allowed.

## World and object views

`w` is a `WorldView` with this public interface:

| Member | Result |
| --- | --- |
| `w.N` | Batch size |
| `w.device` | Torch device |
| `w.grasping(g, obj)` | Boolean tensor `[N]` for a bound gripper/object pair |
| `w.contact_force(a, b)` | Contact force norm `[N]`, independent of pair order |
| `w.bool_margin(b)` | Boolean tensor converted to float32 `+1/-1` |

The free function `bool_margin(b)` has the same behavior. Pair queries use the
provided `ObjView` arguments; absent pairs raise `KeyError`.

An `ObjView` exposes read-only properties `pos [N,3]`, `quat [N,4]`,
`linvel [N,3]`, `angvel [N,3]`, `half_size [N,3]`, and string `kind` (one of
`actor`, `site`, `gripper`, `table`). `obj.attr(key)` returns a bound tensor with
leading dimension N and raises a descriptive `KeyError` if absent. Grippers
also expose `width [N]` and `arm_qvel [N,D]` properties. Treat all returned tensors
as read-only. Access objects through predicate arguments or the progress object
namespace; the world view supplies only the members listed above.

`vpmkit.api` re-exports `ObjView`, `WorldView`, `ObjSpec`, `BindingAPI`,
`PredicateSpec`, and `ProgressSpec` for annotations and introspection.

## Geometry

Import helpers through `from vpmkit.api import G` or `vpmkit.geometry`. They use
torch, preserve device and floating dtype, and are differentiable where natural.
Quaternions must be nonzero. Rotation functions accept nonunit quaternions;
`quat_mul` returns the Hamilton product without normalizing it.

| Helper | Operation |
| --- | --- |
| `quat_normalize(q)` | Unit quaternion |
| `quat_mul(q1, q2)` | Hamilton product, composition of rotations |
| `quat_conj(q)` | Quaternion conjugate |
| `quat_apply(q, v)` | Rotate vectors |
| `quat_to_matrix(q)` | Rotation matrix `[...,3,3]` |
| `quat_to_euler_xyz(q)` | XYZ angles in radians, using PyTorch3D's `matrix_to_euler_angles(quaternion_to_matrix(q), "XYZ")` convention |
| `pose_mul(p1, q1, p2, q2)` | Composed `(position, quaternion)` |
| `pose_inv(p, q)` | Inverse `(position, quaternion)` |
| `to_local(frame_p, frame_q, points)` | World points expressed in a frame |
| `from_local(frame_p, frame_q, points)` | Frame points expressed in world coordinates |
| `body_axis(q, i)` | Rotation matrix column i, for i = 0, 1, 2 |
| `angle_between(u, v)` | Angle in radians between nonzero vectors |
| `dist(a_pos, b_pos)` | Euclidean distance |
| `xy_dist(a_pos, b_pos)` | Distance in the xy plane |
| `obb_corners(pos, quat, half_size)` | Oriented-box corners `[N,8,3]` |
| `obb_min_z(pos, quat, half_size)` | Lowest corner height `[N]` |
| `obb_max_z(pos, quat, half_size)` | Highest corner height `[N]` |

Vector and quaternion operations support ordinary torch batch broadcasting.
`to_local` and `from_local` additionally accept `[N,...,3]` point collections
with `[N,3]` frame positions and `[N,4]` frame quaternions.

## Optional custom progress

```python
from predicates import in_region

def progress_carry(w, o, *, span=0.5):
    return 1.0 + in_region(w, o.block, o.region) / span
```

Each custom progress function is top-level, named `progress_<stage name>`, and
has signature `(w, o, *, <numeric defaults>)`. `o` exposes the bound `ObjView`s
as attributes by handle, such as `o.block`. Return a finite tensor `[N]`. The
runtime retains raw progress for every stage and clamps progress to `[0,1]`
when computing potential. Progress has no effect on stage transitions.
`ProgressSpec` records the stage `name` and numeric default `params`.

For a stage without custom progress, each exit literal contributes 1 if true;
otherwise it contributes `clamp(1 + s / scale, 0, 1)`. Here `s` is the predicate
margin for a positive literal and its negative for a negative literal. The
stage's default progress is the mean of these contributions.

## Bindings

```python
from vpmkit.api import BindingAPI

def bind(env, api: BindingAPI):
    return {
        "g": api.gripper(),
        "block": api.actor(env.block, half_size=[0.02, 0.02, 0.02]),
        "region": api.site(lambda: env.region_pose),
    }
```

Return a mapping from graph handles to `ObjSpec` objects. `BindingAPI` is a
protocol supplied by a simulator adapter:

| Method | Meaning |
| --- | --- |
| `gripper()` | Robot gripper specification |
| `actor(actor, half_size, attrs=None)` | Actor specification |
| `site(source, attrs=None)` | Site specification |
| `table()` | Table specification |

`ObjSpec` contains `kind`, opaque `source`, `half_size`, and `attrs`.
`half_size` may be a tensor, float, sequence, zero-argument callable, or `None`.
`attrs` maps keys to tensors or zero-argument callables returning tensors.
The adapter interprets sources and materializes batched object states.

## Runtime behavior

Stage indices are `0..K-1`; index K means done. On each step, the runtime checks
only invariants owned by the current stage. Each consecutive violating frame
increments its counter; a true or inactive invariant resets its counter.
After `debounce` consecutive violations, the earliest target stage wins. Ties
choose the lowest global invariant id. Regression clears that row's counters
and prevents advancement on the same step.

Otherwise, every satisfied stage exit advances immediately, potentially across
several stages in one step. Stage changes clear counters. Invariants of a newly
entered stage are first checked on the next step.

The done state retains every final-stage exit literal as an invariant targeting
the final stage, plus every final-stage invariant with its original target and
event. Breaking these conditions can leave done after debounce. Exit-derived
events use the literal's rendered guidance. Invariant ids follow stage/invariant
order, followed by final-stage exits and copied final-stage invariants.

`Teacher.step` returns stage, current clamped `stage_progress`, all-stage
`progress_raw [N,K]`, margins and truth `[N,I]`, guidance masks `[N,I]`, event ids,
regression flags, and done flags. Predicate instances are indexed by first
appearance across all exits, then invariants, then official declarations.
Potential is `(stage + stage_progress) / K`; done has potential 1 and current
progress 0. Guidance requests false positive exit literals to become true and
true negative exit literals to become false, in exit order. Done has no guidance.
An event id of -1 denotes no event and renders as an empty string.

`Teacher.reset` resets all rows or a boolean mask, to stage 0 or a supplied stage,
and clears their counters. `evaluate` is stateless. `run_sequence` accepts one
trajectory stacked as N = T frames, evaluates predicates in one batch, and replays
the automaton in temporal order starting at `initial_stage` (default 0). It
returns T rows and leaves live teacher state unchanged. `Candidate.with_params`
returns a copy with checked parameter overrides; the original values remain
unchanged.

## Static rules

In `predicates.py` and `progress.py`, allowed imports are `torch` (including
submodules), `math`, `vpmkit.api`, and `vpmkit.geometry`. Progress may also import
the sibling module `predicates`. Imports are absolute. Every top-level function
used as a predicate must have `@predicate`; undecorated helpers are allowed.
Predicate and progress bodies cannot contain `for` or `while` statements;
comprehensions are allowed.

Forbidden names are `eval`, `exec`, `compile`, `open`, `__import__`, `globals`,
`locals`, `getattr`, `setattr`, `delattr`, and `vars`. In predicates and progress,
these attribute names are also forbidden: `item`, `tolist`, `numpy`, `cpu`,
`name`, `_name`, `_handle`, `official`, `env`, `unwrapped`, `scene`, and `agent`.

`bindings.py` must define top-level `bind(env, api)`. Its allowed imports are
`torch`, `math`, `numpy` (including torch/numpy submodules), `vpmkit.api`,
`vpmkit.geometry`, and `vpmkit.world`. The same forbidden names apply except
`getattr` is allowed. Bindings may access the environment and use loops.

## Limitations

M1 loads the binding function but does not call it or provide a simulator adapter.
It records official declarations and evaluates their predicate instances;
comparison against environment judgments belongs to downstream validation.
The AST rules enforce the candidate API contract and are not a security sandbox.
