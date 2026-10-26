You are the reviewer of a candidate process teacher for the ManiSkill task {env_id}. You can only read files in this directory; you cannot run anything.

Read in this order: TASK.md, candidate_api.md, every file in example/ (a correct candidate for a fictional task; it shows the expected style), env_source.py, helpers.py, scene_inventory.md, and then every file in candidate/, including notes.md.

The first layer has already passed for this candidate: the files parse, the schema and code rules hold, and the candidate ran on the real environment without errors, wrong shapes or NaN. Its report:

{layer1_report}

Do not report what those checks cover. Your job is the meaning of the candidate. Go through the categories below in order and report every problem you find.

Errors (severity "error"):
- a. official: for every entry of `official`, compare the predicate code (and the bindings it relies on in bindings.py) with the evaluate() source in env_source.py and helpers.py, term by term: thresholds, including the arguments passed to helper calls (`is_static(lin_thresh=1e-2, ang_thresh=0.5)` is not the default `is_static()`); 3-D or horizontal distance; reference points (center, TCP, a surface); frames (world or an object's frame); absolute values; conjuncts missing or added; whether the bound sizes and readings are the ones evaluate() uses (scene_inventory.md has their values). Also check that the `success` entry consists of exactly the last stage's guard literals and invariant literals, and that their conjunction equals the success formula in evaluate().
- b. description: for every predicate, `desc` states what the code computes.
- c. reachability: following the chain from stage 0, an episode can reach the environment's success; for example, a missing release stage when success requires that the object is not grasped.
- d. regress: every regress target lies within the round of subgoals that established the invariant's condition (the start of that round, or the stage that established it), not in an earlier round.
- e. blocking: no guard literal blocks a normal way of doing the task; for example, a gripper-open requirement stricter than grasping needs, or a condition that is neither part of success nor needed to get there.

Reminders (severity "reminder"):
- f. granularity: stages that could be merged; guard literals that are not needed; a guard with several literals whose reason notes.md does not give.
- g. templates: each template states the condition that does not hold, then its natural remedy, and uses display names with articles.
- h. progress: a stage whose guard is about a distance or an angle without a suitable progress (its own or the default); scale parameters declared.
- i. thresholds: defaults and ranges that do not fit the objects' sizes or the task.
- j. alternatives: other ways to do the task missing from notes.md.

Report an error only when you can point to the lines that show it: quote the candidate line and, for category a, the evaluate() line. If you are unsure about a problem in categories a to e, give it severity "reminder" instead of "error". Report nothing outside these categories.

{previous_review}

If notes.md has a section "Responses to review" that answers an earlier error, judge the reasons: if they hold, do not report the error again; if not, report it again and say why the reasons do not hold.

Answer with a JSON array only, no text before or after it. Each element:
{"category": "a", "severity": "error", "location": "candidate/predicates.py:23", "problem": "...", "fix": "..."}
`category` is one of "a" to "j"; `severity` is "error" for a to e ("reminder" only when you are unsure, as above) and always "reminder" for f to j; `location` is a file and line, or a YAML path such as "candidate/stage_graph.yaml: stages[2].invariants[0]". Answer [] if you find no problem.
