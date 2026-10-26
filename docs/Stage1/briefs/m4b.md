<task>
Implement milestone M4b of `vpmkit` in the git repository /home/zxh/projects_dir/vpm-claude (branch stage1-impl): the generation harness and the second layer (the review agent). The harness turns an input package into a candidate: it creates a run directory, starts the generating agent (Claude Code connected to DeepSeek) in it, runs the first layer and the review agent after each round, hands problems back for repair, and records everything. You do NOT call DeepSeek in this milestone: all tests use a scripted backend. The real trial run is done later by the orchestrator.

State: M1a-M4a are committed. Read first: docs/Stage1/00_technical_plan.md sections 2.1, 7 and 8 (in Chinese; they define the harness and both layers), vpmkit/validate/layer1.py and check_sh.py (first layer, check.sh), vpmkit/package/ (input packages; the PickCube-v1 package is in outputs/stage1/packages/PickCube-v1/), vpmkit/candidate/report.py, vpmkit/resources/review_prompt.md (the review agent's prompt template, written by the orchestrator).

Facts about the CLI (measured on 2026-10-21 with Claude Code 2.1.223; the wrapper is /home/zxh/.local/bin/claude-deepseek). Never read the wrapper script or its configuration file (it contains a key), never print environment variable values, never run the wrapper in this milestone (tests mock subprocess calls):
- Started from inside a Claude Code process, the CLI inherits CLAUDE* and ANTHROPIC* variables and fails with "Not logged in". The harness therefore builds the child environment itself.
- A working generation command line (argv items, in this order):
  [wrapper, "-p", prompt, "--output-format", "stream-json", "--verbose", "--max-turns", N, "--tools", "Read,Write,Edit,Glob,Grep,Bash", "--allowedTools", "Write(./**)", "Edit(./**)", "Bash(./check.sh)", "--disallowedTools", "WebFetch", "WebSearch", "Task", "--permission-mode", "dontAsk", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--settings", '{"autoMemoryEnabled": false}']
  A repair round resumes the session: [wrapper, "--resume", session_id, "-p", prompt, ...the same flags...]. Do not pass --model or --no-session-persistence. Never add a general Read, Glob or Grep permission (without one, reads are confined to the working directory).
- stdout is JSON lines. The first event {"type": "system", "subtype": "init", "session_id": ...}; the last event {"type": "result", "subtype": "success" | "error_max_turns" | ..., "is_error": bool, "terminal_reason": "completed" | "max_turns" | ..., "num_turns", "session_id", "usage": {...}, "permission_denials": [...], "result": <final text>, ...}. A run that reached --max-turns exits with code 1, is_error true and subtype "error_max_turns". Judge success by the exit code and is_error, never by subtype alone (an error can carry subtype "success").

Create:
1. configs/default.yaml: generation (max_turns, round_timeout_s), review (max_turns, timeout_s), max_rounds: 4, harness_retries: 2, k: 1, gpu, and paths (packages, runs, the wrapper). Use these placeholder values, which the orchestrator will set: generation max_turns 80 and round_timeout_s 2400; review max_turns 40 and timeout_s 900.
2. vpmkit/harness/env.py: `child_env(gpu) -> dict`: only HOME, PATH, LANG, LANGUAGE, LC_ALL, HTTP_PROXY, HTTPS_PROXY, NO_PROXY (those present in os.environ), plus CUDA_VISIBLE_DEVICES=str(gpu); nothing else. `env_names(env)`: the sorted names, for the records.
3. vpmkit/harness/rundir.py: `create_run(package_dir, runs_root, env_id, gpu) -> Run`: `<runs_root>/<env_id>/<run_id>/` (run_id = local time "%Y%m%d-%H%M%S", with a suffix if taken) with
   - workspace/: a copy of every file of the package, made read-only (files 0444, the package's subdirectories such as example/ 0555; workspace/ itself stays writable because the CLI may need it); an empty, writable candidate/; check.sh written by vpmkit.validate.check_sh.write_check_sh (executable, read-only); then `git init -q` in workspace/ (so that the agent's git context belongs to this run only);
   - records/: outside workspace/, written only by the harness.
4. vpmkit/harness/backends.py:
   - `ClaudeCodeBackend(wrapper, max_turns, timeout_s)`: `generate(workspace, prompt, session_id=None, record_dir) -> RoundResult` builds the argv above (with --resume when session_id is given), runs it with cwd=workspace, env=child_env(...), stdin=DEVNULL, stdout and stderr streamed to files in record_dir (generation.jsonl, generation.stderr.txt); on timeout it terminates the process (then kills it after a grace period). `review(workspace, prompt, record_dir) -> ReviewCall` runs a separate session: same output flags, its own max_turns and timeout, "--tools", "Read,Glob,Grep", "--disallowedTools", "Write", "Edit", "Bash", "WebFetch", "WebSearch", "Task", "--permission-mode", "dontAsk", the same MCP and settings flags, no --allowedTools, cwd=workspace.
   - Parsing the stream: session_id (from init or result), the result event, exit code, timed_out, num_turns, usage, permission_denials, the final text. Outcome of a generation round: "completed" (exit 0, not is_error), "max_turns" (subtype error_max_turns), "timeout" (killed by the round time limit) — all three end the round normally — or "error" (anything else: no result event, other non-zero exits or is_error), which is a harness failure.
   - `ScriptedBackend`: for tests. generate() replaces the contents of workspace/candidate with a given candidate directory for that round (or calls a given function), and returns a completed RoundResult with a fake session id; review() returns a given JSON text for that round, or raises/returns an error to simulate harness failures.
5. vpmkit/harness/review.py: `review_prompt(env_id, layer1_markdown, previous_items) -> str` from vpmkit/resources/review_prompt.md (plain replacement of {env_id}, {layer1_report} and {previous_review}; {previous_review} becomes "" in round 1, else a short paragraph "The previous review reported these errors:" followed by the previous round's error items as JSON). `parse_review(text) -> list[ReviewItem]`: accept the bare JSON array, or one wrapped in a ```json fence; each item needs category in a..j, severity, location, problem, fix (strings); severity is "error" or "reminder"; categories f-j are always reminders (an "error" there is corrected to "reminder" and noted in the item); categories a-e accept both, because the prompt asks the reviewer to downgrade a problem it is unsure about to a reminder; anything else raises ReviewParseError (a harness failure). `render_review(items) -> str`: Markdown for the generating agent: errors first, then reminders, each with category letter and name, location, problem, suggested fix.
6. vpmkit/harness/run.py: `run_generation(env_id, backend, config, run=None) -> Verdict`, the round loop of 00 section 8.4:
   - Round 1 prompt: exactly "Read TASK.md first."
   - Each round: generation (round 1 fresh; later rounds resume the session with the repair prompt) -> copy workspace/candidate to records/round_<k>/candidate/ -> first layer with vpmkit.validate.layer1.run_layer1(workspace/candidate, env_id), report saved as JSON and Markdown; it passed iff report.layer1_passed -> if it failed, the repair prompt carries the first-layer Markdown -> if it passed, the review (prompt and raw stream saved; parsed items saved as JSON) -> no errors: the run passes; otherwise the repair prompt carries the rendered review.
   - Repair prompt: "The checks after round <k> found problems in candidate/. Fix them, run ./check.sh until it passes, and end your turn with a short summary." followed by the report; for review problems add: "If you disagree with an error, do not change the candidate for it; give your reasons under the heading Responses to review at the end of candidate/notes.md."
   - At most max_rounds rounds (first generation plus 3 repairs); a run not passing after the last round fails.
   - Harness failures (generation outcome "error", review call failure, ReviewParseError): retry the same step up to harness_retries times (a generation retry resumes the session with the same prompt when a session id exists); if it still fails, stop and mark the run "harness_failure".
   - Records (records/): run.json (env_id, package_sha256 from the package manifest, config values, the child environment's variable NAMES only, the CLI version from `<wrapper> --version` run with the child environment, the session id, start and end time); per round: the prompt, the generation stream and stderr, outcome, num_turns, usage, permission denials, the candidate copy, both layers' reports; verdict.json: "passed" | "failed" | "harness_failure", the rounds used, per round the first-layer codes and the review error categories with counts, and per round the number of times the agent ran ./check.sh (count Bash tool uses of ./check.sh in the stream).
7. scripts/run_generation.py: `run_generation.py --env <env_id> [--gpu N] [--backend claude|scripted] [--config configs/default.yaml]`: builds the backend, runs K = config k runs one after another, prints each run directory and verdict. At startup it sets os.environ["CUDA_VISIBLE_DEVICES"] to the chosen card, so that the harness's own first-layer runs (run_layer1 inherits the caller's environment) use the same card as the agent's ./check.sh runs. It must behave the same whether started from a user's terminal or from inside another program (it builds the child environment itself), and puts the repository root on sys.path.
</task>

<tests>
Standard library unittest; mock subprocess for anything that would start the wrapper. Never start the real wrapper.
- Unit: child_env keeps only the allowed names, even when os.environ contains CLAUDE_CODE_ENTRYPOINT, ANTHROPIC_API_KEY and others (patch os.environ); argv for generation, resume and review equals the lists above; stream parsing on synthetic JSON lines (completed, error_max_turns with exit code 1, missing result event, is_error with subtype success); parse_review on a valid array, a fenced array, an item missing a field, non-JSON text, a severity mismatch; review_prompt fills all three placeholders; the round-1 prompt is exactly "Read TASK.md first."; in a created workspace the package files are read-only and candidate/ is writable, check.sh and a .git directory exist, and records/ lies outside workspace/.
- Integration (only with VPM_INTEGRATION=1; GPU 1; needs the PickCube-v1 package):
  - ScriptedBackend giving candidates/reference/PickCube-v1 in round 1 and a review of [] -> verdict passed in 1 round; all records present.
  - Round 1 a broken copy of the reference (fails the first layer), round 2 the reference -> passed in 2 rounds; the round-2 prompt contains the first-layer problem code.
  - Round 1 the reference with a review returning one category-a error, round 2 the reference with a review of [] -> passed in 2 rounds; the round-2 prompt contains the rendered error; the round-2 review prompt contains the previous error.
  - Every round fails the first layer -> failed after 4 rounds.
  - The review returns non-JSON 3 times -> harness_failure.
</tests>

<verification_loop>
Use GPU 1 only. Run from the repository root and make both fully green before finishing:
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
  cd /home/zxh/projects_dir/vpm-claude && ulimit -c 0 && VPM_INTEGRATION=1 TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES=1 /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/integration -t . -v
Also run once: scripts/run_generation.py --env PickCube-v1 --gpu 1 --backend scripted (with the reference candidate), and paste the run directory listing and verdict.json.
Afterwards `git status --short` must show only new or modified files under vpmkit/ (outside vpmkit/resources/), configs/, scripts/ and tests/.
</verification_loop>

<action_safety>
- This run has GPU access and no sandbox. Use CUDA_VISIBLE_DEVICES=1 for everything that touches the GPU; never use other cards.
- Never execute /home/zxh/.local/bin/claude-deepseek, never read it or any of its configuration files, never print environment variable values. Tests mock it.
- Use only /home/zxh/anaconda3/envs/vpm-mani/bin/python. Do not install packages, do not modify the conda environment, do not modify /home/zxh/projects_dir/ManiSkill. No network.
- Write only inside /home/zxh/projects_dir/vpm-claude. Do not modify vpmkit/resources/, docs/, VPM_idea.md, README.md, .gitignore.
- Prefix every command that creates a simulation environment with `ulimit -c 0` and set XDG_CACHE_HOME as above. Never create two GPU environments in one process.
- Do NOT run git add, git commit, git stash or any branch command in the repository (the `git init` inside a run's workspace/ under outputs/ is part of the harness). Leave the work uncommitted.
- Out of scope: the PBRS wrapper (M5); G1; tasks other than PickCube-v1.
- Code style: English identifiers, comments and docstrings; type hints; sparse, factual comments; no TODO, phase or milestone wording in code.
</action_safety>

<structured_output_contract>
End with a report in this shape:
1. What was built, per module in 1-3 lines, including every design choice this brief did not dictate.
2. Files created or modified.
3. Test results: the exact final lines of both unittest runs.
4. The scripted run: directory listing and verdict.json.
5. Deviations from this brief, and open questions.
</structured_output_contract>


<!-- Rework 1 (same Codex session) -->

<task>
Review of your M4b work found four things to change. Keep everything else as it is. This turn runs without GPU access: change the code and the unit tests only; the orchestrator re-runs the GPU integration tests afterwards.

1. vpmkit/harness/backends.py, ClaudeCodeBackend._call: the wrapper may start child processes, and terminating only the wrapper can leave an agent running that keeps writing to candidate/ while the harness already runs the first layer. Start the subprocess in its own session (`start_new_session=True`) and, on timeout, send SIGTERM to the whole process group (`os.killpg(process.pid, signal.SIGTERM)`), wait the grace period, then SIGKILL the group if it is still alive (ignore ProcessLookupError). After a normal exit, also make sure no member of the group survives: send SIGTERM to the group and ignore ProcessLookupError.

2. scripts/run_generation.py: the harness's own first-layer runs inherit its environment (run_layer1 starts the worker with the caller's environment). At startup, before importing vpmkit, set os.environ["XDG_CACHE_HOME"] = <repo>/outputs/cache, os.environ["MS_ASSET_DIR"] = <repo>/outputs/maniskill and os.environ["TMPDIR"] = <repo>/outputs/tmp (create the directories), as check.sh does, so that a run started from a plain terminal behaves like one started from anywhere else. The child environment of the agents is unaffected (child_env keeps only its allowlist).

3. vpmkit/harness/review.py, parse_review: the reviewer may wrap the array in a sentence despite the instructions. Accept, in this order: the bare JSON array; a ```json fenced block anywhere in the text; otherwise the substring from the first "[" to the last "]". Raise ReviewParseError only if none of these parses as a JSON array of valid items. Validation of the items is unchanged.

4. vpmkit/harness/run.py: when a round's first layer fails, keep the error items of the last review instead of resetting them, so that the next review prompt still lists the errors that notes.md may answer under Responses to review. The items are replaced only when a new review runs.

Add unit tests for each change: Popen receives start_new_session=True and the timeout path signals the process group (mock os.killpg); run_generation.py sets the three variables (mock run_generation and the backends as the existing CLI test does); parse_review accepts an array preceded and followed by prose and a fenced block inside prose, and still rejects text without a valid array; a scripted sequence review-with-error -> first-layer failure -> clean first layer shows the first review's errors in the third round's review prompt (mock run_layer1 so that no GPU is needed).
</task>

<verification_loop>
Run and make green (no GPU in this turn):
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
</verification_loop>

<action_safety>
Same rules as before: never execute or read /home/zxh/.local/bin/claude-deepseek or its configuration; no package installs, no network; write only inside the repository and only vpmkit/harness/, scripts/run_generation.py and tests/; do not run git add/commit/stash or branch commands.
</action_safety>

<structured_output_contract>
Report: (1) each change and the files touched, (2) the exact final lines of the unit test run, (3) anything you left open.
</structured_output_contract>


<!-- Rework 2 (same Codex session) -->

<task>
One more change in vpmkit/harness/backends.py: the run records must never hold anything that looks like a credential. The CLI's init event has a field `apiKeySource`; it names where a key comes from rather than holding one, but records follow the same rule as the 2026-10-21 probe, which redacted it.

After a Claude Code call has finished (normally or after the timeout), rewrite its saved stream file (generation.jsonl or review.jsonl) in place:
- In every JSON event, at any depth, replace the value of each key whose name matches the case-insensitive regular expression `api_?key|secret|authorization|password|credential|access_?token|auth_?token|bearer` with the string "[REDACTED]". Keep the key, all other fields and the line order. Token counts such as `input_tokens`, `output_tokens` and `cacheReadInputTokens` do not match this expression and must stay.
- A line that is not JSON is kept, unless it matches the same expression anywhere, in which case it becomes "[REDACTED: sensitive-pattern line]".
- Apply the same rule to the stderr file of the call (line by line).
- Then parse the rewritten stream as before.

Add unit tests: an init event with `apiKeySource` is redacted while `session_id`, `model` and `usage` token counts remain; a nested key such as `{"headers": {"Authorization": "x"}}` is redacted; a non-JSON line containing "Bearer" is replaced; parse_stream still returns the session id and the result.
</task>

<verification_loop>
Run and make green (no GPU in this turn):
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
</verification_loop>

<action_safety>
Same rules as before: never execute or read /home/zxh/.local/bin/claude-deepseek or its configuration; no package installs, no network; write only vpmkit/harness/ and tests/; do not run git add/commit/stash or branch commands.
</action_safety>

<structured_output_contract>
Report: (1) the change and the files touched, (2) the exact final lines of the unit test run, (3) anything you left open.
</structured_output_contract>
