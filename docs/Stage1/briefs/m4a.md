<task>
Implement milestone M4a of `vpmkit` in the git repository /home/zxh/projects_dir/vpm-claude (branch stage1-impl): the input-package builder. Build only the PickCube-v1 package now, but write the builder for any ManiSkill task; the reward-removal logic is tested on all 16 task source files listed below.

State: M1a, M1b, M2 and M3 are committed. Read first: vpmkit/resources/ (candidate_api.md, TASK_template.md, example/), vpmkit/adapters/maniskill/ (inventory.py, helpers_table.py, env.py), docs/Stage1/00_technical_plan.md sections 6.1 and 6.2 (in Chinese; they define the package).

An input package is everything the generating agent sees, one folder per task:
```text
<out_root>/<env_id>/
  TASK.md             rendered from vpmkit/resources/TASK_template.md
  env_source.py       the task class's source file with the two reward functions removed
  helpers.py          the helpers that evaluate() calls, from the helper table
  scene_inventory.md  generated from the running environment
  candidate_api.md    copied from vpmkit/resources/
  example/            copied from vpmkit/resources/example/
  manifest.json       provenance, ManiSkill version, hashes
```

Create:
1. vpmkit/package/__init__.py.
2. vpmkit/package/strip.py: `strip_reward_functions(source: str) -> StripResult(text, removed)`. Parse with ast; for every function definition named `compute_dense_reward` or `compute_normalized_dense_reward` (methods of any class in the file), remove the lines from its first decorator (or its `def` line) through its end_lineno. Keep every other line byte for byte, including comments, blank lines and line endings; do not regenerate code. `removed` lists (name, first line, last line) in the original numbering. Then search the remaining text for the lowercase substring "reward" (case-sensitive, so `SUPPORTED_REWARD_MODES` does not count); if present, raise `ResidualRewardError` whose message lists each offending line number and line, for a human to look at.
3. vpmkit/package/helpers.py: `render_helpers_py(env_id) -> str` in the format of vpmkit/resources/example/helpers.py (a header comment, then per helper a separator line, the call as written in evaluate(), where the helper is defined, how a candidate uses it, and either "Source not included." or the source code), using `TASK_HELPERS[env_id]` and the entries of vpmkit/adapters/maniskill/helpers_table.py. The header is the example's first line only ("# Helpers that evaluate() in env_source.py calls, and how a candidate uses each."); drop the sentences about the example. A task without entries gets the header and the line "# evaluate() calls no helper outside the task class."
4. vpmkit/package/build.py: `build_package(env_id, out_root="outputs/stage1/packages", overwrite=False) -> Path`.
   - Task facts without creating an environment: the class `REGISTERED_ENVS[env_id].cls` (from mani_skill.utils.registration, after `import mani_skill.envs`); its source file (inspect.getsourcefile); max_episode_steps from the registration; the docstring via inspect.getdoc(cls); the default robot uid from the signature default of `robot_uids` in the class's `__init__`.
   - env_source.py: `strip_reward_functions(source).text`, nothing added (no header).
   - scene_inventory.md: `scene_inventory(env_id)` run in a subprocess with the vpm-mani Python (it creates a GPU environment), inheriting CUDA_VISIBLE_DEVICES, with core dumps disabled.
   - helpers.py: render_helpers_py(env_id).
   - TASK.md: TASK_template.md with exactly these placeholders replaced by plain string replacement (not str.format: the template contains other braces): {env_id}, {class_name}, {robot_uid}, {max_episode_steps}, {docstring}. Raise if any of these five placeholders remains.
   - candidate_api.md: copied unchanged. Refuse to build (raise) if it contains the text "<!-- Planned interface" (a reminder that must be removed before any package is built).
   - example/: copy exactly these files from vpmkit/resources/example/: env_source.py, helpers.py, scene_inventory.md, candidate/stage_graph.yaml, candidate/bindings.py, candidate/predicates.py, candidate/progress.py, candidate/notes.md (never __pycache__ or other files).
   - manifest.json: env_id; ManiSkill version; the source file path relative to the mani_skill package; for every other file of the package its relative path, sha256 and source (where it came from); and `package_sha256` = sha256 over the sorted lines "<relative path>\0<sha256>\n" of those files. No timestamps or other run-dependent values, so that two builds of one task give identical files and the same package_sha256.
   - Build into a temporary sibling directory and move it into place at the end. If `<out_root>/<env_id>` exists and overwrite is False, raise.
5. scripts/build_packages.py: `build_packages.py --env <env_id> [--out <dir>] [--overwrite]`: builds one package, prints its path and package_sha256; it puts the repository root on sys.path itself.
</task>

<facts>
The 16 tasks and the expected result of strip_reward_functions on their source files (ManiSkill 3.0.1, checked on 2026-10-26): PickCube-v1 216 -> 186 lines; LiftPegUpright-v1 144 -> 111; StackCube-v1 186 -> 145; PegInsertionSide-v1 360 -> 300; StackPyramid-v1 196 -> 196 (no reward function); PullCubeTool-v1, TurnFaucet-v1 and PushT-v1 raise ResidualRewardError (PullCubeTool's evaluate() returns a "reward" field; TurnFaucet has a commented-out dense reward at the end of the class; PushT's evaluate() helper has a local variable named reward); PushCube-v1, PullCube-v1, RollBall-v1, PlaceSphere-v1, PickSingleYCB-v1, PokeCube-v1, PlugCharger-v1 and AssemblingKits-v1 pass.
</facts>

<tests>
- Unit (CPU; reading sources only, no environment): the 16 source files give the facts above; for the passing files, the stripped text equals the original with exactly the removed line ranges deleted; render_helpers_py("PickCube-v1") contains both entries in order, with the call texts, the source of Panda.is_static, and the example's separator format; TASK.md rendering (with the scene inventory mocked) leaves none of the five placeholders; the "<!-- Planned interface" refusal works (patch the path of candidate_api.md to a temporary copy that contains it).
- Integration (only with VPM_INTEGRATION=1; GPU): build_package("PickCube-v1") twice into two temporary out_roots gives identical files and the same package_sha256; the package has exactly the 7 entries above and the 8 example files; env_source.py has 186 lines and no "reward"; scene_inventory.md contains `self.goal_thresh` with 0.025; TASK.md names PickCube-v1, PickCubeEnv, panda and 50 steps.
- Then build the real package once with scripts/build_packages.py --env PickCube-v1 into outputs/stage1/packages/ and paste its path and package_sha256 in the report.
</tests>

<verification_loop>
Use GPU 1 only. Run from the repository root and make both fully green before finishing:
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
  cd /home/zxh/projects_dir/vpm-claude && ulimit -c 0 && VPM_INTEGRATION=1 TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES=1 /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/integration -t . -v
Afterwards `git status --short` must show only new or modified files under vpmkit/ (outside vpmkit/resources/), scripts/ and tests/. outputs/ is git-ignored.
</verification_loop>

<action_safety>
- This run has GPU access and no sandbox. Use CUDA_VISIBLE_DEVICES=1 for everything that touches the GPU; never use other cards.
- Use only /home/zxh/anaconda3/envs/vpm-mani/bin/python. Do not install packages, do not modify the conda environment, do not modify /home/zxh/projects_dir/ManiSkill. No network, no downloads.
- Write only inside /home/zxh/projects_dir/vpm-claude. Do not modify vpmkit/resources/, docs/, VPM_idea.md, README.md, .gitignore.
- Prefix every command that creates a simulation environment with `ulimit -c 0` and set XDG_CACHE_HOME as above. Never create two GPU environments in one process.
- Do NOT run git add, git commit, git stash or any branch command. Leave the work uncommitted.
- Out of scope: packages for the other 15 tasks; deciding what to do with the three blocked tasks; the harness and the review agent (M4b).
- Code style: English identifiers, comments and docstrings; type hints; sparse, factual comments; no TODO, phase or milestone wording in code.
</action_safety>

<structured_output_contract>
End with a report in this shape:
1. What was built, per module in 1-3 lines, including every design choice this brief did not dictate.
2. Files created or modified.
3. Test results: the exact final lines of both unittest runs; the table of the 16 strip results (lines before and after, or the residual lines for the blocked ones).
4. The path and package_sha256 of the PickCube-v1 package, and its TASK.md and helpers.py pasted in full.
5. Deviations from this brief, and open questions.
</structured_output_contract>
