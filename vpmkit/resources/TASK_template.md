# Task: write a process teacher for {env_id}

You will write a *candidate*: a process teacher for the ManiSkill task `{env_id}`. A process teacher follows an episode step by step. It splits the task into a linear chain of stages, states what must hold to leave each stage (its guard) and what must stay true during it (its invariants), and from these gives a progress signal and short guidance in English. It reads the simulator's privileged state. It never decides whether the task has succeeded: the environment does.

The candidate will be used as a shaped reward and as step-by-step guidance for reinforcement learning, and its parameters will be tuned later. It must agree with the task's own success check, be computable in every state, and follow the format in `candidate_api.md`.

## Files in this directory

| File | Content |
| --- | --- |
| `TASK.md` | this file |
| `candidate_api.md` | the technical specification of a candidate: files, world view, runtime semantics, and the checks. Read it first, completely |
| `example/` | a complete candidate for a fictional pick-and-place task, `PlaceCubeOnPad-v1`, with that task's environment source, helpers and scene inventory. Its layout mirrors this directory. Follow its style |
| `env_source.py` | the source file of the task class of `{env_id}`, with the two reward functions removed |
| `helpers.py` | the helpers that `evaluate()` calls outside the task class, and how a candidate uses each |
| `scene_inventory.md` | objects, sizes and initial poses read from the running environment, the keys that `evaluate()` returns, and the actual values of the attributes that `evaluate()` reads |
| `candidate/` | empty: write your candidate here |
| `check.sh` | runs the checks on `candidate/` |

## The task

- Environment `{env_id}`: task class `{class_name}` in `env_source.py`, robot `{robot_uid}`, at most {max_episode_steps} steps per episode.
- Success is `evaluate()["success"]`.
- The task's docstring:

```text
{docstring}
```

## What to produce

In `candidate/`: `stage_graph.yaml`, `bindings.py`, `predicates.py`, `notes.md`, and `progress.py` if a stage needs its own progress function (candidate_api.md section 2). Write whatever predicates you need.

## How to work

1. Read `candidate_api.md`, then every file in `example/`, then `env_source.py`, `helpers.py` and `scene_inventory.md`.
2. Design the chain following the design rules below, then write the files.
3. Run `./check.sh`. It takes no arguments and is the only command you can run. It checks `./candidate` with exactly the checks of candidate_api.md section 9, including binding your candidate to the real environment on the GPU and running it in about 744 states, which takes 10 to 20 seconds. Fix every problem it reports and run it again.
4. When `./check.sh` passes and `notes.md` is complete, end your turn with a short summary.

No one will answer questions during the work: make each decision yourself, following the design rules, and record what you are unsure about under **Uncertainties** in `notes.md`.

What happens next: the same checks run once more, and then a review agent reads this directory and your candidate. It reports as errors: an `official` declaration that does not match `evaluate()` term by term (thresholds, 3-D or horizontal distance, reference points, frames, absolute values, missing conjuncts), or a last stage whose conditions are not exactly success; a predicate whose description does not match its code; a chain that cannot reach success; a regress target outside the round that established the broken condition; a guard that blocks a normal way of doing the task. It also gives reminders about granularity, templates, progress, thresholds and alternative ways. The problems come back to you in this session for fixing, for at most 3 repair rounds. If you disagree with an error from the review, do not change the candidate for it; give your reasons under the heading **Responses to review** at the end of `notes.md` (candidate_api.md section 10).

## Design rules

These rules need judgment. The rules a program can check are in candidate_api.md and are enforced by `./check.sh`.

The teacher keeps its current stage as context, so each stage answers only two questions: what must hold to move on (the guard), and what, if it breaks, sends the teacher back (the invariants). Whether a condition holds in other stages does not matter. For example, when three cubes are stacked into a pyramid, `grasped(g, a)` becomes false as planned once cube a has been placed, but the stages that move cube c look only at their own guards and invariants. The only link between stages is going back, so going back is kept local too (rule 3).

1. **Stages.** Put stage boundaries where contact changes (grasping, releasing) and where a goal relation is reached (arriving, aligning, placing on). Grasping and releasing each get their own stage. The example follows reach → grasp → carry → release. If the task can be done in several ways, write the chain for the most natural one and list the others in `notes.md`.
2. **Guards.** A guard contains only conditions that must hold at the end of its stage and are needed to complete the task: usually one literal. Use several literals only when they must hold at the same time, and say why in `notes.md`. Do not build a composite predicate just to fit a guard into one literal. Prefer literals that describe a state (`near`: the gripper is close to the cube) to literals that describe a momentary action (`gripper_open`).
3. **Invariants and going back.** An invariant is a condition that must hold throughout its stage and that, once broken, must be repaired by going back. Conditions that come one after another go into adjacent stages, and an invariant keeps the earlier one: in the example, grasp keeps `near(g, cube)`, so the teacher returns to reach when the gripper wanders away while trying to grasp. Choose the regress target within the round of subgoals that established the condition (the start of that round, or the stage that established it), never in an earlier round. For example, in the pyramid task: if cube c drops, go back to reaching or grasping c; if placing c knocks cube a out of place (noticed only if the stages of c declare an invariant such as `next_to(a, b)`), that condition was established in the round of a, so go back to reaching a. Whether to declare such invariants is your judgment.
4. **The last stage.** Its guard literals together with its invariant literals are exactly the environment's success condition, declared in `official` under `success`.
5. **Predicates.**
   - One definition and one threshold per predicate, shared by all its instances. Put differences between objects into the definition: measure to an object's surface or grasp point, or scale with its half size. A different tolerance is a different condition, so give it another name.
   - Give each predicate one sentence that states the physical condition it tests, and make it match the code.
   - Write both templates, `need_true` and `need_false`, for every predicate. Each states the condition that does not hold, then its natural remedy, and names objects by their display names, with articles.
   - To use one of the task's own checks in `evaluate()`, rewrite its formula as a predicate over its object parameters, copy its thresholds exactly, and declare the correspondence in `official`. Copy the arguments of helper calls too: `is_static(lin_thresh=1e-2, ang_thresh=0.5)` is not the default `is_static()`. Never read the fields that `evaluate()` returns. When an official check does not mean what a stage needs, write your own predicate and declare nothing.
6. **Progress.** A stage whose guard is about a distance or an angle may get its own progress function; a stage whose guard is boolean gets none. Normalize with fixed scale parameters declared in `params` with a default and a range.

## Limits

- Work only in this directory. Write only inside `candidate/`; do not change the other files.
- The only command you can run is `./check.sh`.
