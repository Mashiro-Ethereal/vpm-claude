<task>
Implement milestone M1b of the Python package `vpmkit` in the git repository /home/zxh/projects_dir/vpm-claude (branch stage1-impl): the static checks of a candidate directory, i.e. the first three of the four check groups that `./check.sh` runs (parse, schema, code restrictions), with a report. No simulator is used. The fourth group (run checks on the GPU) is a later milestone; only reserve its place in the report.

State of the repository: milestone M1a is committed. It provides the runtime: vpmkit/literal.py (`parse_literal`, `Literal`, `LiteralSyntaxError`), vpmkit/predicate.py (`@predicate`, `PredicateMeta`), vpmkit/candidate/schema.py (pydantic `StageGraph` model), vpmkit/candidate/__init__.py (`Candidate`, `load_candidate_unchecked`), vpmkit/teacher.py, and tests in tests/unit/. Read those modules first and reuse them; change them only where this brief requires and say so in the report.

Specification (read first):
- vpmkit/resources/candidate_api.md, especially section 9 (the checks and their error codes; this milestone implements 9.1, 9.2 and 9.3), and sections 3, 5, 6, 7, 10 that the rules refer to.
- vpmkit/resources/example/candidate/: a complete legal candidate. It must pass every static check with no problem reported.

Key principle: the static checks never import or execute candidate code. They read stage_graph.yaml with PyYAML and the .py files with the `ast` module only. (Candidate code is executed only after the code restrictions have passed, in the later run group.) Everything a rule needs about predicates, progress functions and `bind` is extracted from the AST.
</task>

<design>
Create:
- vpmkit/candidate/codes.py: the registry of all 34 codes of candidate_api.md section 9 (parse 3, schema 21, ast 5, run 5): code -> (group, one-line rule text copied from section 9). Single source of truth; every problem uses a code from it.
- vpmkit/candidate/report.py: `Problem(code, location, message)`; `Report(candidate: str, groups: dict[str, str], problems: list[Problem])` with groups "parse", "schema", "ast", "run", each "passed" | "failed" | "skipped"; `passed` property (True iff no group failed and none of parse/schema/ast is skipped); `to_json()` / `from_json()`; `to_markdown()`: a short summary an LLM agent can act on: a title line "Check report: PASSED" or "Check report: FAILED", the status of each group, then a numbered list of problems as "`code` at location: message". Locations are "stage_graph.yaml: stages[2].invariants[0].regress_to" (YAML path, zero-based indices, as in candidate_api.md section 9) or "predicates.py:23" (file and line).
- vpmkit/candidate/pyinfo.py: static extraction from the AST: decorated predicates (name, line, object params, thresholds with numeric-literal defaults, decorator keywords desc/need_true/need_false/scale when given as literals), progress functions (module-level `progress_<stage>`, their params and defaults), the `bind` function and its returned dict-literal keys.
- vpmkit/candidate/static.py: `check_static(path) -> Report`. Groups run in order parse -> schema -> ast; a group runs only if the previous one passed, otherwise it and the later ones are "skipped". Within a group, report every problem found (do not stop at the first). The run group is always "skipped" here.
- `load_candidate(path) -> Candidate` in vpmkit/candidate/__init__.py: runs check_static; if it did not pass, raise `CandidateCheckError(report)` (new exception in vpmkit/errors.py, carrying the report); otherwise return load_candidate_unchecked(path).
</design>

<rules>
Definitions: a literal "used in the file" appears in any `exit`, `invariants` or `official` entry of stage_graph.yaml. A predicate is "used" if a used literal names it. A predicate is "official" if it appears in any `official` entry. Literals compare by canonical text (`str(parse_literal(text))`), so `not p(a, b)` and `p(a, b)` differ and whitespace does not matter.

Group parse:
- parse.missing_file: stage_graph.yaml, bindings.py, predicates.py, notes.md exist in the candidate directory (progress.py is optional). One problem per missing file.
- parse.yaml: stage_graph.yaml is valid YAML (report the line and column from the YAML error).
- parse.python: every .py file in the candidate directory (recursively, excluding __pycache__) parses with ast.parse (report file:line).

Group schema. If schema.format reports anything, the remaining schema rules are not evaluated (the structure is unreliable); otherwise evaluate all of them:
- schema.format: the YAML has the structure of candidate_api.md section 3: validate with the M1a pydantic model and convert each pydantic error to one problem (location = YAML path from the error's loc; message = the pydantic message, made readable). Also: the top level is a mapping; `objects` and `stages` are non-empty. Keep `exit: []` valid for the model so that schema.empty_guard reports it.
- schema.literal_syntax: every literal string parses with parse_literal.
- schema.unknown_predicate: every literal names a function decorated with `@predicate(...)` in predicates.py (decorator written as `@predicate(...)` or `@<anything>.predicate(...)`).
- schema.arity: one argument per object parameter of the predicate.
- schema.unknown_object: every literal argument is a key of `objects`.
- schema.binding_keys: bindings.py defines a module-level `def bind(env, api)` whose last statement is `return {...}`, a dict literal whose keys are string constants, without duplicates, exactly equal to the keys of `objects`. Report missing and extra keys.
- schema.predicate_signature: every `@predicate` function (used or not) is defined at module level, once; follows section 5.1: first parameter `w`; then at least one object parameter, positional-or-keyword, without default; then thresholds, each with a numeric literal default (int or float constant, optionally with a unary minus; not bool, not a name or expression), positional-or-keyword or keyword-only; no positional-only parameters, no *args, no **kwargs, no keyword-only parameter without default.
- schema.progress_signature: every module-level function in progress.py whose name starts with `progress_` follows section 6.1: parameters (w, o, then parameters with numeric literal defaults); no *args/**kwargs; and `progress_<stage>` names an existing stage.
- schema.empty_guard: every stage has at least one exit literal.
- schema.regress_target: every regress_to names a stage that exists and comes before the invariant's own stage (so stage 0 can have no invariants).
- schema.guard_contradiction: no exit contains both `p` and `not p` of the same instance.
- schema.invariant_conflict: no invariant `p` while the same stage's exit has `not p`, and no invariant `not p` while the exit has `p`.
- schema.regress_too_late: an invariant of stage s with literal L and target t is valid only if L (same canonical text) appears in the exit of some stage u with t <= u <= s-1.
- schema.success: `official` has an entry with key `success`, and the set of its literals equals the set of the last stage's exit literals plus its invariant literals.
- schema.official_format: every `official` entry has at least one literal; no key appears in two entries. (Whether a key is really returned by evaluate() is the run group's rule run.official_key, not checked here.)
- schema.official_threshold: no `params` name starts with "<p>." for an official predicate p.
- schema.param_unknown: every `params` name is either "<p>.<t>" where p is a used predicate and t one of its thresholds, or "progress.<stage>.<q>" where progress_<stage> exists and has parameter q. (A name that is reported under schema.official_threshold is not reported again here.) "runtime.debounce" is unknown: it is not part of a candidate.
- schema.param_missing: every threshold of every used non-official predicate, and every parameter of every progress function, is declared in `params`.
- schema.param_value: every range has low < high; low <= default <= high; and the default equals the default in the function signature (exact float equality).
- schema.template: every used predicate's decorator gives desc and need_true as non-empty string literals and scale as a positive numeric literal, and need_false as a non-empty string literal if the predicate is negated in any used literal; the decorator has no other keywords.
- schema.template_placeholder: in need_true and need_false of every predicate, every brace belongs to a placeholder `{<object parameter name>}` of that predicate: no other names, no format specs or conversions, no positional `{}`, no stray or doubled braces.

Group ast (code restrictions):
- ast.import: predicates.py may only use `import torch`, `import torch.<sub> [as x]`, `from torch[.<sub>] import ...`, `import math`, `from math import ...`, `from vpmkit.api import ...`, `import vpmkit.api [as x]`. progress.py may use the same plus `from .predicates import ...`. Imports anywhere in the file count (also inside functions).
- ast.host_transfer: predicates.py and progress.py contain no call of a method named item, tolist, numpy or cpu.
- ast.loop: predicates.py and progress.py contain no for, async for, while, list/set/dict comprehension or generator expression.
- ast.name_access: predicates.py reads no attribute named `name`.
- ast.unsafe: in every .py file: no Name `open`, `exec`, `eval`, `compile` or `__import__`; no import (import or from-import, at any depth) of a module whose top-level package is one of os, sys, io, pathlib, shutil, glob, tempfile, pickle, shelve, subprocess, multiprocessing, threading, socket, urllib, http, requests, importlib, ctypes, builtins; no identifier (Name, Attribute, import alias, function/class/argument/keyword name) that starts and ends with a double underscore.
Report each violation with file:line.
</rules>

<tests>
Standard library unittest only. Put tests in tests/unit/ (the M1a tests must keep passing).
- The example candidate passes: report.passed, no problems, groups parse/schema/ast "passed", run "skipped". load_candidate on it returns a working Candidate.
- Fixtures: create tests/fixtures/mutations.py holding a table of mutations of the example candidate: for each code of groups parse, schema and ast (29 codes), at least one mutation (a list of edits: file, exact old text, new text; or a file deletion/addition) that produces that code. Tests copy the example candidate into a temporary directory, apply a mutation, run check_static and assert that the expected code is reported with the expected location (YAML path or file:line), and that the report did not pass. Use several mutations where a rule has several branches (e.g. schema.param_value: low >= high, default outside range, default differing from the signature; schema.binding_keys: missing key, extra key, not a dict literal; ast.unsafe: open, import os, a dunder attribute). Keep each mutation minimal so that it triggers only its own rule where possible, and assert the full set of codes in those cases.
- Group gating: a parse error leaves schema/ast "skipped"; a schema error leaves ast "skipped"; a schema.format error suppresses the other schema rules.
- Report: JSON round trip; Markdown contains the title line, the group statuses and every problem's code and location.
- No candidate code is executed by check_static: a mutation that puts `raise RuntimeError` at module level of predicates.py (still syntactically valid) yields no exception from check_static.
</tests>

<verification_loop>
Run from the repository root and make it fully green before finishing:
  cd /home/zxh/projects_dir/vpm-claude && mkdir -p outputs/tmp && ulimit -c 0 && TMPDIR=/home/zxh/projects_dir/vpm-claude/outputs/tmp XDG_CACHE_HOME=/home/zxh/projects_dir/vpm-claude/outputs/cache MS_ASSET_DIR=/home/zxh/projects_dir/vpm-claude/outputs/maniskill CUDA_VISIBLE_DEVICES="" /home/zxh/anaconda3/envs/vpm-mani/bin/python -m unittest discover -s tests/unit -t . -v
Afterwards `git status --short` must show only new or modified files under vpmkit/ (outside vpmkit/resources/) and tests/.
</verification_loop>

<action_safety>
- Use only /home/zxh/anaconda3/envs/vpm-mani/bin/python. Do not install packages or modify the conda environment; do not modify /home/zxh/projects_dir/ManiSkill. No network.
- Write only inside /home/zxh/projects_dir/vpm-claude. Do not modify vpmkit/resources/, docs/, VPM_idea.md, README.md, .gitignore.
- CPU only; no simulation environment.
- Do NOT run git add, git commit, git stash or any branch command. Leave the work uncommitted.
- Out of scope: the run group (binding to ManiSkill, run.* codes beyond listing them in codes.py), check.sh and scripts (later milestones).
- Code style: English identifiers, comments and docstrings; type hints; sparse, factual comments; no TODO, phase or milestone wording in code.
</action_safety>

<structured_output_contract>
End with a report in this shape:
1. What was built, per module in 1-3 lines, including every design choice this brief did not dictate.
2. Files created or modified (and why for each modified M1a file).
3. Test results: the exact final lines of the unittest run.
4. A table: code -> fixture mutation name(s) that cover it.
5. Deviations from this brief or from candidate_api.md, and open questions.
</structured_output_contract>
