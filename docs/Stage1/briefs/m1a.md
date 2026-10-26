<task>
Implement milestone M1a of the Python package `vpmkit` in the git repository /home/zxh/projects_dir/vpm-claude (branch stage1-impl): the CPU-testable runtime of a "process teacher". No simulator is used in this milestone. The repository currently contains no code: `vpmkit/` holds only `vpmkit/resources/` (specification files you must read but not modify).

Read first (they are the specification):
- vpmkit/resources/candidate_api.md: the technical spec of a "candidate" (authoritative for field names, function signatures and runtime semantics). Sections 3-8 are what this milestone implements. Section 9 lists static checks with error codes; those belong to the NEXT milestone (M1b). Do not implement them now.
- vpmkit/resources/example/candidate/: a complete legal candidate for a fictional pick-and-place task (stage_graph.yaml, predicates.py, progress.py, bindings.py, notes.md). Your runtime must load it and run it on synthetic snapshots.
- docs/Stage1/00_technical_plan.md sections 3-4 (in Chinese) restate the same semantics. If anything in this brief seems to conflict with candidate_api.md, follow this brief and report the conflict.

Summary of the model: a candidate is a linear chain of stages 0..K-1. Each stage has a guard (`exit`: a conjunction of literals) and optional invariants (a literal plus a regress target, which is an earlier stage). A literal is a predicate instance `p(a, b)` or its negation `not p(a, b)`. Predicates are Python functions decorated with `@predicate`; they take a world view `w`, object views, and numeric thresholds, and return a signed margin tensor of shape [N] (>= 0 means the condition holds). Optional progress functions `progress_<stage>(w, o, **params)` give in-stage progress. The teacher keeps an integer stage per parallel environment and at every step outputs stage, stage_progress, phi, pred, margin and guidance. N is the batch: parallel environments online, or frames of a saved trajectory offline. Everything is batched torch on one device.

Create these modules (and only these, plus tests):

1. vpmkit/__init__.py: lightweight (no heavy imports).

2. vpmkit/api.py: the only vpmkit module candidates import. `__all__ = ["predicate", "signed", "G"]`. `G` is the geometry module (or a namespace exposing its 12 functions), used as `G.quat_to_euler_xyz(q)`.

3. vpmkit/geometry.py: the 12 functions of candidate_api.md section 4.4. Batched over leading dimensions with broadcasting, torch only, any device, no Python loops over the batch, no .item(). Quaternions are (w, x, y, z); a pose is [..., 7] = position (3) + quaternion (4). Match ManiSkill 3.0.1 exactly (read-only source: /home/zxh/projects_dir/ManiSkill/mani_skill/utils/geometry/rotation_conversions.py and /home/zxh/projects_dir/ManiSkill/mani_skill/utils/structs/pose.py):
   - quat_to_matrix(q): the formula of ManiSkill `quaternion_to_matrix` (it scales by 2/|q|^2).
   - quat_apply(q, v): as ManiSkill `quaternion_apply` (q * (0, v) * conj(q)).
   - quat_to_euler_xyz(q): identical to `matrix_to_euler_angles(quaternion_to_matrix(q), "XYZ")`, including its clamp of the asin argument to [-1+1e-8, 1-1e-8]. For "XYZ" this is (atan2(-m12, m22), asin(clamp(m02)), atan2(-m01, m00)) with m = quat_to_matrix(q).
   - axis(q, i): column i (0 = x, 1 = y, 2 = z) of quat_to_matrix(q).
   - angle_between(u, v): atan2(|u x v|, u . v), in [0, pi].
   - pose_inv(p): as `Pose.inv()`: q' = (w, -x, -y, -z) (no renormalization, no sign standardization), p' = quat_apply(q', -p).
   - pose_mul(a, b): as `Pose.__mul__`: q = a.q * b.q standardized to a nonnegative real part (ManiSkill `quaternion_multiply`), p = a.p + quat_apply(a.q, b.p).
   - to_local(pose, x) = quat_apply(conj(q), x - p); to_world(pose, x) = p + quat_apply(q, x).
   - box_corners(pose, half_size) -> [..., 8, 3]: corner j uses the signs of itertools.product((-1, 1), repeat=3)[j] on (x, y, z) in the box frame, mapped with to_world.
   - box_bottom_z(pose, half_size), box_top_z(pose, half_size): min / max z over box_corners.

4. vpmkit/world.py: tensor snapshot and read-only views.
   ```python
   @dataclass
   class BodyState:
       kind: str                      # "gripper" | "actor" | "site"
       pose: Tensor                   # [N, 7]
       lin_vel: Tensor                # [N, 3] (zeros for a site)
       ang_vel: Tensor                # [N, 3] (zeros for a site)
       half_size: Tensor | None       # [N, 3]; required for actor and site, None for the gripper
       attrs: dict[str, Tensor]       # task-specific readings, each [N, ...]
       width: Tensor | None = None        # gripper with fingers: [N]
       max_width: Tensor | None = None    # gripper with fingers: [N]
       arm_qvel: Tensor | None = None     # gripper: [N, J]
       joint_pos: Tensor | None = None    # object bound to an articulation joint: [N]
       joint_vel: Tensor | None = None    # [N]
       joint_limits: Tensor | None = None # [N, 2]

   @dataclass
   class Snapshot:
       bodies: dict[str, BodyState]                  # by object key
       table_z: Tensor                               # [N]
       grasping: dict[tuple[str, str], Tensor]       # (gripper key, object key) -> [N] bool
       contact_force: dict[tuple[str, str], Tensor]  # (key a, key b) -> [N]; looked up symmetrically
       official: dict[str, Tensor]                   # evaluate() fields; never visible to predicates
   ```
   - `__post_init__` validates: one batch size N (first dimension) and one device for every tensor; the shapes above; grasping values are bool; gripper-only fields appear only on a gripper and joint fields only on actor/site; attr names do not clash with view field names. Violations raise ValueError with a precise message.
   - Methods: `batch_size`, `device`, `to(device)`, `select(index)` (int -> a snapshot with N = 1; slice; LongTensor of indices; bool mask), classmethod `cat(snapshots)` (concatenate along the batch; identical structure required), `to_dict()` / classmethod `from_dict(d)` (only str keys, tensors, str/int/None values; pair keys encoded as strings), `save(path)` / classmethod `load(path, map_location=None)` using torch.save and torch.load(weights_only=True), with a format tag "vpmkit.snapshot.v1".
   - Views. All are read-only (setting an attribute raises AttributeError), have no `.name`, and offer no way to look up other objects by key. They return the snapshot tensors themselves (no copies; `pos` and `quat` are slices of `pose`). Each view keeps its object key in a private attribute so that World can find pair readings.
     - ObjectView (actor or site): `pos` [N, 3], `quat` [N, 4], `pose` [N, 7], `lin_vel`, `ang_vel`, `half_size`, every attr by name (`o.slot_pose`), and `joint_pos` / `joint_vel` / `joint_limits` only when present (otherwise AttributeError saying the object has no joint reading).
     - GripperView: `pos`, `quat`, `pose` (the TCP), `lin_vel`, `ang_vel`, `width`, `max_width`, `arm_qvel`, attrs. If width/max_width are None (a pushing stick), accessing them raises AttributeError with a clear message.
     - An unknown attribute raises AttributeError that names the available fields.
     - World (the `w` argument): `table_z` [N], `batch_size` (int), `device`, `grasping(g, o)` -> [N] bool, `contact_force(a, b)` -> [N] (look up (a, b), then (b, a)). A missing reading raises KeyError with a clear message (e.g. "no grasp reading for (g, pad): a site cannot be grasped"). World must not hold a reference to `official` (build it from the other parts of the snapshot).
     - Objects: the `o` argument of progress functions; `o.<key>` returns that object's view; nothing else is public.
     - `make_views(snapshot) -> (World, dict[str, view], Objects)`.

5. vpmkit/predicate.py
   - `predicate(*, desc: str, need_true: str, need_false: str | None = None, scale: float)`: decorator returning a `Predicate` callable that wraps the function (functools.update_wrapper) and carries `meta: PredicateMeta(name, desc, need_true, need_false, scale, object_params: tuple[str, ...], thresholds: dict[str, float])`.
   - Validate at decoration time, raising TypeError with a clear message: the first parameter is named `w`; then at least one object parameter (positional-or-keyword, no default); then thresholds (parameters with defaults, positional-or-keyword or keyword-only) whose defaults are int or float (not bool); no *args or **kwargs; no keyword-only parameter without a default; scale is a positive int or float (not bool); desc and need_true are non-empty strings.
   - Active thresholds: a contextvars-based context manager `active_thresholds(mapping)` whose keys are "<predicate>.<threshold>" (e.g. "near.max_dist"). When a Predicate is called, each threshold not passed explicitly takes the value from the active mapping if its key is there, otherwise its signature default. Explicit arguments always win. Outside any context, defaults apply. A nested context replaces the outer one. This is how a predicate called directly from a progress function or another predicate uses the current (default or tuned) threshold, and it lets several Teachers with different parameters share one loaded candidate.
   - `signed(flag)` -> float32 tensor: +1.0 where flag is true, -1.0 elsewhere, same device; accepts bool or numeric tensors.

6. vpmkit/literal.py
   - `Literal(predicate: str, args: tuple[str, ...], negated: bool)`, a frozen dataclass; property `instance` = (predicate, args); `instance_text` = "p(a, b)"; `__str__` = canonical "p(a, b)" or "not p(a, b)" (", " separator).
   - `parse_literal(text) -> Literal`. Grammar: optional `not` followed by whitespace; an identifier `[A-Za-z_][A-Za-z0-9_]*`; "("; one or more identifiers separated by commas; ")". Arbitrary whitespace around tokens is allowed. Nothing else: no "not not", no "or"/"and", no numbers, no empty argument list, no trailing comma. Errors raise `LiteralSyntaxError(ValueError)` quoting the text.

7. vpmkit/automaton.py: a pure, batched update of the linear chain. It holds no mutable per-environment state (the Teacher does).
   - Construction from a compiled, index-based spec: K stages; L literal slots (the distinct literals used by guards and invariants); for each stage, its guard literal slots (non-empty); for each invariant, (owner stage, literal slot, regress target < owner). Precompute index and mask tensors on the device.
   - `step(stage [N] long, counters [N, I] long, lit_true [N, L] bool, debounce m >= 1) -> (new_stage, new_counters)`, implementing exactly:
     1. For each invariant of the current stage: counter += 1 if its literal is false, else counter = 0. Counters of invariants that do not belong to the current stage are 0.
     2. An invariant is violated when its counter >= m. If any is violated, stage := the smallest regress target among the violated invariants.
     3. Advance: while stage < K-1 and the guard of `stage` holds (all its literals true), stage += 1. One step can pass several stages, also right after a regress. The last stage never advances (there is no "done" node).
     4. If a regress happened, or the final stage differs from the stage at the start of the step, all counters of that environment are reset to 0.
     Consequences that must hold (test them): the invariants of a stage entered during a step are first checked at the next step; with m = 1 a single false step regresses.
   - `guard_holds(lit_true) -> [N, K] bool`.
   - No per-environment Python loops; a Python loop over the K stages is fine.

8. vpmkit/candidate/schema.py: pydantic v2 models of stage_graph.yaml (candidate_api.md section 3), all with extra="forbid":
   - `StageGraph(task: str, objects: dict[str, ObjectDecl], stages: list[Stage], official: list[Official], params: list[Param] = [])`; `ObjectDecl(name: str)`; `Stage(name: str, exit: list[str], invariants: list[Invariant] = [])`; `Invariant(literal: str, regress_to: str)`; `Official(literals: list[str], key: str)`; `Param(name: str, default: float, range: tuple[float, float])`.
   - Object keys and stage names are lowercase identifiers `[a-z_][a-z0-9_]*`; stage names are unique; param names are unique. Nothing more: references, arity, params vs. signatures and the other rules of candidate_api.md section 9.2 are M1b.
   - Helpers: classmethod `from_yaml(path)`, `stage_index(name)`, `param_defaults() -> dict[str, float]`.

9. vpmkit/candidate/modules.py and vpmkit/candidate/__init__.py
   - `Candidate` dataclass: `path`, `graph: StageGraph`, `predicates: dict[str, Predicate]` (keyed by meta.name), `progress: dict[str, Callable]` (keyed by stage name, from the functions named `progress_<stage>` defined in progress.py itself), `bind: Callable | None` (the `bind` function of bindings.py, if the file exists).
   - `load_candidate_unchecked(path) -> Candidate`: parse stage_graph.yaml with the schema; import predicates.py, progress.py (optional) and bindings.py (optional) as submodules of a fresh, uniquely named package whose `__path__` is the candidate directory, so that `from .predicates import tcp_dist` in progress.py works. Every call creates a new namespace: two loads of one directory are independent, and two different candidates loaded in one process do not collide. Importing must not write into the candidate directory (no __pycache__: set sys.dont_write_bytecode while importing, then restore it). No static checks here (they are M1b).

10. vpmkit/errors.py
   - `CandidateError(Exception)`: base class.
   - `CandidateRuntimeError(CandidateError)`: an exception raised inside candidate code. Attributes `function` (e.g. "near", "progress_reach") and `target` (e.g. "near(g, cube)" or a stage name); the original exception is chained (`raise ... from exc`).
   - `CandidateOutputError(CandidateError)`: a candidate function returned a bad value. Same attributes; the message states expected vs. got (type, dtype, shape, device).
   Later milestones map these to the run-check codes `run.error` and `run.output`.

11. vpmkit/teacher.py: `Teacher(candidate, num_envs=1, device="cpu", params=None)`
   - Columns: the P distinct predicate instances used in stage_graph.yaml, in order of first appearance when scanning the stages in order (for each stage its exit literals, then its invariant literals), then the official entries. `teacher.instances` is the list of instance texts ("near(g, cube)"). `p` and `not p` share a column. Also expose `stage_names` and `num_stages` (K).
   - Parameters: effective values are the graph's param defaults overridden by `params` (used by Bayesian optimization). Override names must be declared in graph.params or be "runtime.debounce"; values must be numbers inside the declared range; otherwise ValueError. "runtime.debounce" (m) defaults to 1 and must be an integer >= 1. Threshold params "<pred>.<thr>" form the active-threshold mapping (predicate.active_thresholds) during every candidate call. Progress params "progress.<stage>.<param>" are passed as keyword arguments to progress_<stage>.
   - Construction validates what the runtime relies on and raises ValueError with a clear message otherwise: literals parse; predicates exist; arity matches; objects are declared; regress targets are earlier stages; progress functions name existing stages; a negated guard literal's predicate has need_false. Keep this minimal: full static checking is M1b.
   - `compute_margins(snapshot) -> [N, P] float32`: calls each instance once, inside the active-threshold context, with the World view and the views of its argument objects. Each raw return must be a floating torch tensor of shape (N,) on the snapshot's device, else CandidateOutputError naming the function and instance. An exception inside candidate code becomes CandidateRuntimeError. After each candidate call, detect in-place modification of snapshot tensors by comparing `tensor._version` of every snapshot tensor before and after the call (views share the counter with their base) and raise CandidateRuntimeError naming the function; if `_version` cannot be read (inference-mode tensors), skip the check for that tensor.
   - `compute_progress(snapshot, margins) -> [N, K]`: the raw (unclipped) progress of EVERY stage. For a stage with progress_<stage>: call it as (w, objects, **its params), with the same output validation, error wrapping and mutation detection. Otherwise the default progress: the mean over the stage's guard literals of (1 if the literal holds, else clamp(1 + lit_margin / scale, 0, 1)), where lit_margin is the margin for `p` and -margin for `not p`, and scale is the predicate's meta.scale.
   - Truth: `p` holds iff margin >= 0 (exactly 0 holds); `not p` holds iff `p` does not; the margin of `not p` is -margin(p).
   - State: `stage` [N] long (starts at 0) and invariant counters [N, I] long, on `device`. Read-only property `stage`.
   - `reset(env_idx=None, stage=None)`: env_idx None means all, else a LongTensor or a sequence of indices; stage None means 0, else an int or a tensor with one value per selected environment (0 <= stage < K, else ValueError). Resets the counters of those environments to 0.
   - `step(snapshot) -> dict` with exactly these keys:
     - "stage" [N] long: after the automaton update;
     - "stage_progress" [N] float32: p_k, the progress of the resulting stage clipped to [0, 1]; if the resulting stage is the last stage and all its guard literals hold, p_k = 1 whatever its progress function returns;
     - "phi" [N] float32: (k + p_k) / K;
     - "pred" [N, P] bool and "margin" [N, P] float32;
     - "guidance" [N, P] bool: True at the column of each literal of the resulting stage's guard that does not hold.
     Order inside a step: margins once -> literal truth -> automaton update (invariants and guards use this step's values) -> progress, phi and guidance of the resulting stage. Requires snapshot.batch_size == num_envs and the snapshot on the Teacher's device (normalize devices so "cuda" and "cuda:<current>" compare equal), else ValueError.
   - `evaluate_offline(snapshots, initial_stage=0) -> dict` with the same keys and leading [T, N] shapes. Concatenate the T snapshots (each with the same N) along the batch, compute all margins and all stages' progress with one call each, reshape to [T, N, ...], then run the automaton over T with counters starting at 0 and the stage starting at initial_stage (int or [N] long). The result must equal stepping a fresh Teacher (same params) reset to initial_stage. It does not touch the Teacher's online state.
   - `render(output, i) -> list[str]`: delegates to render.py for environment i of a step-shaped output (for offline output the caller slices a time index first).
   - Torch operations on [N] tensors on the device only: no per-environment loops and no .item()/.cpu()/.tolist() in the per-step path.

12. vpmkit/render.py: for environment i, k = output["stage"][i]; for each literal of stage k's guard, in guard order, whose column is True in output["guidance"][i]: use need_false if the literal is negated, else need_true; replace each `{param}` placeholder (param = an object parameter name of the predicate) with the display name (graph.objects[key].name) of the object the literal passes for that parameter; uppercase the first character only (do not lowercase the rest). An unknown placeholder or a missing need_false raises ValueError. Examples with the example candidate: `near(g, cube)` needing to hold gives "The gripper is far from the red cube; move the gripper to the red cube."; `not grasped(g, cube)` not holding gives "The red cube is still held; release the red cube."
</task>

<tests>
Use the standard library unittest only (pytest is not installed). Put the tests in tests/unit/ with tests/__init__.py and tests/unit/__init__.py. Build snapshots with helpers in tests/unit/synth.py (for example, a builder of the example task's snapshot from TCP position, cube pose, pad pose, grasp flag and velocities, for N environments). Everything runs on CPU. Temporary candidate directories go under tempfile (TMPDIR is set to a directory inside the repo by the test command below).

Required coverage:
A. Geometry: every function against ManiSkill's own functions on >= 1000 random unit quaternions/poses, including XYZ Euler angles with pitch near +-pi/2, atol 1e-5 in float32: quat_to_matrix vs rotation_conversions.quaternion_to_matrix; quat_apply vs quaternion_apply; quat_to_euler_xyz vs matrix_to_euler_angles(quaternion_to_matrix(q), "XYZ"); pose_inv and pose_mul vs mani_skill Pose (Pose.create_from_pq, .inv(), *, .raw_pose). Import order matters: `import mani_skill.envs` must run before `from mani_skill.utils.geometry import rotation_conversions` and `from mani_skill.utils.structs.pose import Pose`, otherwise a circular-import error occurs. If mani_skill cannot be imported in your sandbox, those tests skip with a reason; in all cases also test hand-computed cases: 90-degree rotations about each axis, compositions, pose_mul(pose_inv(p), p) = identity, corners/bottom/top of a box rotated 45 degrees about z and about x, angle_between for parallel, antiparallel, orthogonal and zero vectors, to_local/to_world round trip.
B. Literal parsing: valid forms with unusual whitespace; invalid forms ("not not p(a)", "p()", "p(a,)", "p(a b)", "p(a) and q(b)", "near(g, 0.1)", "", "not(p(a))", "p(a) or q(a)").
C. Predicate decorator: metadata (object params, thresholds and defaults); each decoration-time error; active thresholds (default outside a context, active value inside, explicit argument wins, nested contexts); signed.
D. World and views: fields and shapes; read-only; no `.name`; missing joint fields raise AttributeError; grasping and contact lookups, including symmetric contact and a missing pair; World cannot reach `official`; snapshot validation errors; select and cat; save/load round trip.
E. Automaton rules, driving lit_true directly, with these chains:
   PickCube: reach [near(g, cube)]; grasp [grasped(g, cube)] inv near(g, cube) -> reach; carry [at_goal(cube, goal)] inv grasped(g, cube) -> reach; settle [arm_static(g)] inv at_goal(cube, goal) -> carry.
   StackCube: reach [near(g, red)]; grasp [grasped(g, red)] inv near(g, red) -> reach; carry [on(red, green)] inv grasped(g, red) -> reach; release [not grasped(g, red), static(red)] inv on(red, green) -> reach.
   - PickCube, the cube slips during carry (grasped false): gripper still near -> ends in grasp with guidance on grasped; gripper far -> ends in reach with guidance on near.
   - several stages passed in one step (all guards true right after reset -> stops at the last stage, never beyond);
   - several invariants violated at once -> the earliest regress target (a small chain with two invariants on one stage);
   - the invariants of a stage entered in this step are not checked in this step;
   - m = 2: one false step does not regress, two consecutive false steps do; a true step in between resets the count; counters reset when the stage changes;
   - reset by env_idx affects only those environments; starting from a saved stage (reset(stage=...)) checks that stage's invariants at the next step;
   - StackCube release: cube held -> guidance on "not grasped(g, red)"; released but moving -> guidance on static; both hold -> empty guidance; red knocked off green -> regress to reach and walk forward in the same step to the stage the state allows.
F. Teacher on the example candidate (vpmkit/resources/example/candidate, loaded with load_candidate_unchecked) and synthetic snapshots:
   - teacher.instances == ["near(g, cube)", "grasped(g, cube)", "on(cube, pad)", "static(cube)"];
   - grasp: the TCP leaves the cube's vicinity (near false) -> back to reach, render gives ["The gripper is far from the red cube; move the gripper to the red cube."]; still near and not grasped -> stays in grasp with ["The red cube is not held; grasp the red cube with the gripper."];
   - carry: the cube slips (grasp flag false) with the TCP near -> grasp; with the TCP far -> reach;
   - release: cube still held and at rest on the pad -> ["The red cube is still held; release the red cube."];
   - last stage with all guard literals holding (and the invariant holding) -> guidance empty, stage_progress 1, phi 1.0 (K = 4);
   - a temporary candidate written by the test whose last stage has its own progress function returning 0.3 -> stage_progress 1 when the last guard holds, 0.3 otherwise;
   - negation truth and margin; margin exactly 0 counts as holding; default progress of carry and release equals a hand computation; boolean predicate margins are +-1;
   - parameter override: with near.max_dist = 0.0, near(g, cube) fails for a TCP 0.04 m above the center of a cube of half size 0.02 that holds with the default 0.02; a progress function of a temporary candidate that calls near without thresholds sees the overridden value; an unknown name and an out-of-range value raise ValueError; runtime.debounce = 2 is honored;
   - batching: N = 6 environments in different stages give the same outputs, over a multi-step sequence, as 6 Teachers with N = 1 fed snapshot.select(i);
   - offline: evaluate_offline over a T = 12 sequence equals stepping, from stage 0 and from a nonzero initial_stage, and again after a save/load round trip of the snapshots;
   - every predicate and progress function of the example, on random synthetic snapshots (N = 64), returns a float tensor of shape [N], all finite;
   - error wrapping: a temporary candidate whose predicate raises -> CandidateRuntimeError with function and target set; one returning shape [N, 1] or a bool tensor -> CandidateOutputError; one that modifies `o.pos` in place -> CandidateRuntimeError.
G. Candidate loading: the example loads; `from .predicates import ...` works; two loads give independent modules; no __pycache__ appears in the candidate directory.
</tests>

<verification_loop>
Run from the repository root and make it fully green before finishing:
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
Also run: /home/zxh/anaconda3/envs/vpm-mani/bin/python -m compileall -q vpmkit tests (then delete the __pycache__ directories it creates under vpmkit/resources/, if any).
Afterwards `git status --short` must show only new files under vpmkit/ (outside vpmkit/resources/) and under tests/. outputs/ is git-ignored.
</verification_loop>

<action_safety>
- Use only the Python of the conda environment vpm-mani: /home/zxh/anaconda3/envs/vpm-mani/bin/python (Python 3.10, torch 2.12, pydantic 2.13, PyYAML 6). Do not install packages, do not modify the conda environment, do not modify anything under /home/zxh/projects_dir/ManiSkill (read its source only). No network.
- Write only inside /home/zxh/projects_dir/vpm-claude. Do not modify vpmkit/resources/ (candidate_api.md and the example are the specification), docs/, VPM_idea.md, README.md or .gitignore.
- CPU only: do not create any simulation environment. Import mani_skill only in the geometry comparison tests.
- Do NOT run git add, git commit, git stash or any branch command. Leave all work uncommitted in the working tree.
- Out of scope (later milestones): the static checks and error codes of candidate_api.md section 9, AST restrictions and reports (M1b); the ManiSkill adapter and the binding API api.gripper/actor/site (M2).
- Code style: English identifiers, comments and docstrings; type hints; sparse, factual comments; no TODO, phase or milestone wording in code.
</action_safety>

<structured_output_contract>
End with a report in this shape:
1. What was built, per module in 1-3 lines, including every design choice this brief did not dictate.
2. Files created.
3. Test results: the exact final lines of the unittest run (count, OK/FAILED, skipped tests with reasons).
4. Deviations from this brief or from candidate_api.md, and open questions.
</structured_output_contract>
