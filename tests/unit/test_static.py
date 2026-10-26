"""Candidate static checks, diagnostic locations and checked loading."""

import ast
from contextlib import contextmanager
from pathlib import Path
import re
import shutil
import tempfile
from typing import Iterator
import unittest
from unittest.mock import patch

from vpmkit.candidate import Candidate, Problem, Report, check_static, load_candidate
from vpmkit.candidate.codes import CODES
from vpmkit.candidate.pyinfo import extract_bindings, extract_predicates, extract_progress
from vpmkit.errors import CandidateCheckError
from vpmkit.teacher import Teacher
from tests.fixtures.mutations import Edit, MUTATIONS, NEAR_PARAM, PROGRESS_PARAM
from .synth import EXAMPLE, snapshot


@contextmanager
def example_copy(*edits: Edit) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "candidate"
        shutil.copytree(EXAMPLE, path)
        for edit in edits:
            edit.apply(path)
        yield path


class StaticCheckTest(unittest.TestCase):
    def assert_passes(self, path: Path) -> Report:
        report = check_static(path)
        self.assertTrue(report.passed, report.to_markdown())
        self.assertEqual(report.problems, [])
        self.assertEqual(report.groups, {"parse": "passed", "schema": "passed", "ast": "passed", "run": "skipped"})
        return report

    def test_example_and_checked_loading(self) -> None:
        self.assert_passes(EXAMPLE)
        candidate = load_candidate(EXAMPLE)
        self.assertIsInstance(candidate, Candidate)
        self.assertEqual(set(candidate.predicates), {"near", "grasped", "on", "static"})
        teacher = Teacher(candidate, num_envs=2)
        result = teacher.step(snapshot(n=2))
        self.assertEqual(result["stage"].shape, (2,))
        self.assertEqual(result["margin"].shape, (2, 4))
        self.assertTrue(teacher.render(result, 0))

    def test_registry_and_mutation_coverage(self) -> None:
        source = (EXAMPLE.parents[1] / "candidate_api.md").read_text(encoding="utf-8")
        rows = re.findall(r"^\| `((?:parse|schema|ast|run)\.[^`]+)` \| (.*) \|$", source, re.M)
        self.assertEqual(CODES, {code: (code.split(".")[0], rule) for code, rule in rows})
        self.assertEqual(len(CODES), 34)
        self.assertEqual({mutation.code for mutation in MUTATIONS},
                         {code for code, (group, _) in CODES.items() if group != "run"})
        self.assertEqual(len({mutation.name for mutation in MUTATIONS}), len(MUTATIONS))

    def test_mutations(self) -> None:
        for mutation in MUTATIONS:
            with self.subTest(mutation=mutation.name), example_copy() as path:
                mutation.apply(path)
                report = check_static(path)
                self.assertFalse(report.passed, mutation.name)
                self.assertIn((mutation.code, mutation.location),
                              [(p.code, p.location) for p in report.problems], report.to_markdown())
                self.assertEqual({p.code for p in report.problems}, mutation.codes, report.to_markdown())
                failed = mutation.code.split(".")[0]
                groups = ["parse", "schema", "ast"]
                self.assertEqual(report.groups, {**{group: "passed" if i < groups.index(failed)
                                                     else "failed" if group == failed else "skipped"
                                                     for i, group in enumerate(groups)}, "run": "skipped"})

    def test_parse_collects_problems_and_gates(self) -> None:
        with example_copy(Edit("notes.md", None, None),
                          Edit("stage_graph.yaml", None, "task: [\n"),
                          Edit("predicates.py", None, "def bad(:\n"),
                          Edit("helpers/bad.py", None, "def also_bad(:\n")) as path:
            report = check_static(path)
        self.assertEqual(len(report.problems), 4)
        self.assertEqual({p.code for p in report.problems}, {"parse.missing_file", "parse.yaml", "parse.python"})
        self.assertEqual(report.groups, {"parse": "failed", "schema": "skipped", "ast": "skipped", "run": "skipped"})

    def test_format_collects_errors_and_suppresses_other_schema_rules(self) -> None:
        with example_copy(Edit("stage_graph.yaml", "", "surprise: 1\n"),
                          Edit("stage_graph.yaml", "{name: the red cube}", "{}"),
                          Edit("stage_graph.yaml", '"near(g, cube)"', '"invalid literal"')) as path:
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems}, {"schema.format"})
        self.assertEqual({p.location for p in report.problems},
                         {"stage_graph.yaml: surprise", "stage_graph.yaml: objects.cube.name"})
        self.assertEqual(report.groups["ast"], "skipped")

    def test_format_reports_empty_collections_alongside_other_errors(self) -> None:
        with example_copy(Edit("stage_graph.yaml", None, "objects: {}\nstages: []\nofficial: []\n")) as path:
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems}, {"schema.format"})
        self.assertEqual({p.location for p in report.problems},
                         {"stage_graph.yaml: task", "stage_graph.yaml: objects", "stage_graph.yaml: stages"})

    def test_schema_collects_independent_problems_and_gates_ast(self) -> None:
        with example_copy(Edit("stage_graph.yaml", NEAR_PARAM, ""),
                          Edit("predicates.py", "scale=0.3", "scale=0"),
                          Edit("bindings.py", '"pad": api.actor', '"extra": api.actor'),
                          Edit("helpers/unsafe.py", None, "import os\n")) as path:
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems},
                         {"schema.param_missing", "schema.template", "schema.binding_keys"})
        binding = next(p for p in report.problems if p.code == "schema.binding_keys")
        self.assertIn("missing keys: pad", binding.message)
        self.assertIn("extra keys: extra", binding.message)
        self.assertEqual(report.groups["ast"], "skipped")

    def test_ast_collects_every_violation(self) -> None:
        with example_copy(Edit("predicates.py", "import torch\n", "import torch\nimport os\n"),
                          Edit("progress.py", "return 1.0", "return o.cube.pos.cpu() + 1.0"),
                          Edit("helpers/unsafe.py", None, "open('data')\nvalue = obj.__class__\n")) as path:
            report = check_static(path)
        self.assertEqual([(p.code, p.location) for p in report.problems], [
            ("ast.unsafe", "helpers/unsafe.py:1"), ("ast.unsafe", "helpers/unsafe.py:2"),
            ("ast.import", "predicates.py:3"), ("ast.unsafe", "predicates.py:3"),
            ("ast.host_transfer", "progress.py:12"),
        ])

    def test_static_never_executes_candidate_code(self) -> None:
        with example_copy(Edit("predicates.py", "", '\nraise RuntimeError("must not execute")\n'),
                          Edit("bindings.py", "", '\nraise RuntimeError("must not execute")\n'),
                          Edit("progress.py", "", '\nraise RuntimeError("must not execute")\n')) as path:
            self.assert_passes(path)

    def test_checked_load_rejects_before_execution(self) -> None:
        with example_copy(Edit("notes.md", None, None),
                          Edit("predicates.py", "", '\nraise RuntimeError("must not execute")\n')) as path:
            with patch("vpmkit.candidate.load_candidate_unchecked") as loader:
                with self.assertRaises(CandidateCheckError) as raised:
                    load_candidate(path)
                loader.assert_not_called()
        self.assertFalse(raised.exception.report.passed)
        self.assertEqual(raised.exception.report.problems[0].code, "parse.missing_file")
        self.assertIn("Check report: FAILED", str(raised.exception))

    def test_optional_progress(self) -> None:
        with example_copy(Edit("progress.py", None, None),
                          Edit("stage_graph.yaml", PROGRESS_PARAM, "")) as path:
            self.assert_passes(path)

    def test_pycache_is_excluded_recursively(self) -> None:
        with example_copy(Edit("__pycache__/broken.py", None, "invalid syntax !"),
                          Edit("helpers/__pycache__/unsafe.py", None, "import os")) as path:
            self.assert_passes(path)

    def test_allowed_imports_and_restriction_scope(self) -> None:
        imports = ("\nimport torch.linalg as linalg, math\nfrom torch.nn import functional\n"
                   "from math import sqrt\nimport vpmkit.api as api\nfrom vpmkit.api import G\n")
        with example_copy(Edit("predicates.py", "", imports),
                          Edit("progress.py", "", imports + "value = object.name\n"),
                          Edit("bindings.py", "", "\nimport random\nvalues = [i for i in ()]\n"),
                          Edit("helpers/plain.py", None, "import random\nfor x in ():\n    x.cpu()\n")) as path:
            self.assert_passes(path)

    def test_each_forbidden_module_in_any_python_file(self) -> None:
        modules = ("os", "sys", "io", "pathlib", "shutil", "glob", "tempfile", "pickle", "shelve",
                   "subprocess", "multiprocessing", "threading", "socket", "urllib", "http", "requests",
                   "importlib", "ctypes", "builtins")
        for module in modules:
            with self.subTest(module=module), example_copy(
                    Edit("helpers/module.py", None, f"from {module}.submodule import value\n")) as path:
                report = check_static(path)
                self.assertEqual([(p.code, p.location) for p in report.problems], [("ast.unsafe", "helpers/module.py:1")])

    def test_import_boundaries(self) -> None:
        for source in ("import math.extra", "import vpmkit.api.extra", "import torchlike",
                       "from .torch import value", "import torch, random"):
            with self.subTest(source=source), example_copy(Edit("predicates.py", "", "\n" + source + "\n")) as path:
                report = check_static(path)
                self.assertEqual({p.code for p in report.problems}, {"ast.import"})

    def test_progress_loops_and_helpers_are_checked(self) -> None:
        with example_copy(Edit("progress.py", "", "\ndef helper():\n    return [x for x in ()]\n")) as path:
            report = check_static(path)
        self.assertEqual([(p.code, p.location) for p in report.problems], [("ast.loop", "progress.py:15")])

    def test_canonical_literal_sets_and_order(self) -> None:
        with example_copy(Edit("stage_graph.yaml", 'literal: "near(g, cube)"', 'literal: " near (g,cube) "'),
                          Edit("stage_graph.yaml", '["on(cube, pad)", "static(cube)", "not grasped(g, cube)"]',
                               '["static ( cube )", "not grasped(g,cube)", "on(cube,pad)", "static(cube)"]')) as path:
            self.assert_passes(path)

    def test_regress_matches_polarity(self) -> None:
        with example_copy(Edit("stage_graph.yaml", 'literal: "near(g, cube)"', 'literal: "not near(g, cube)"')) as path:
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems}, {"schema.regress_too_late"})

    def test_regress_can_target_the_establishing_stage(self) -> None:
        with example_copy(Edit("stage_graph.yaml", 'literal: "grasped(g, cube)", regress_to: reach',
                               'literal: "grasped(g, cube)", regress_to: grasp')) as path:
            self.assert_passes(path)

    def test_qualified_decorator_keyword_thresholds_and_negative_default(self) -> None:
        with example_copy(Edit("predicates.py", "from vpmkit.api import predicate, signed",
                               "from vpmkit.api import predicate, signed\nimport vpmkit.api as api"),
                          Edit("predicates.py", "@predicate(", "@api.predicate("),
                          Edit("predicates.py", "o, max_dist=0.02", "o, *, max_dist=-0.02"),
                          Edit("progress.py", "o, d0=0.3", "o, *, d0=0.3"),
                          Edit("stage_graph.yaml", "default: 0.02, range: [0.0, 0.05]",
                               "default: -0.02, range: [-0.05, 0.05]")) as path:
            self.assert_passes(path)

    def test_unused_predicate_metadata_optional_but_placeholders_checked(self) -> None:
        source = '\n@predicate(scale=1)\ndef unused(w, obj, threshold=1):\n    return threshold\n'
        with example_copy(Edit("predicates.py", "", source)) as path:
            self.assert_passes(path)
            Edit("predicates.py", "@predicate(scale=1)", '@predicate(scale=1, need_false="{unknown}")').apply(path)
            report = check_static(path)
        self.assertEqual([(p.code, p.location) for p in report.problems],
                         [("schema.template_placeholder", "predicates.py:73")])

    def test_unnegated_predicate_need_false_is_optional(self) -> None:
        with example_copy(Edit("predicates.py", '    need_false="{g} is too close to {o}; move {g} away from {o}.",\n', "")) as path:
            self.assert_passes(path)

    def test_official_only_predicate_is_used(self) -> None:
        source = '\n@predicate(desc="Flag", need_true="move {o}", scale=1)\ndef only_official(w, o, tol=1):\n    return tol\n'
        with example_copy(Edit("predicates.py", "", source),
                          Edit("stage_graph.yaml", "official:\n", 'official:\n  - {literals: ["only_official(cube)"], key: flag}\n')) as path:
            self.assert_passes(path)
            Edit("predicates.py", 'desc="Flag", need_true="move {o}", ', "").apply(path)
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems}, {"schema.template"})

    def test_predicate_used_only_by_invariant(self) -> None:
        with example_copy(Edit("stage_graph.yaml", 'exit: ["near(g, cube)"]', 'exit: ["grasped(g, cube)"]'),
                          Edit("stage_graph.yaml", NEAR_PARAM, "")) as path:
            report = check_static(path)
        self.assertEqual({p.code for p in report.problems}, {"schema.regress_too_late", "schema.param_missing"})

    def test_ast_metadata_extraction(self) -> None:
        predicates = extract_predicates(ast.parse((EXAMPLE / "predicates.py").read_text()))
        near = predicates[0]
        self.assertEqual((near.name, near.line, near.object_params), ("near", 21, ("g", "o")))
        self.assertEqual(near.thresholds, {"max_dist": 0.02})
        self.assertEqual(near.keywords["scale"], 0.3)
        self.assertIn("TCP", near.keywords["desc"])
        progress = extract_progress(ast.parse((EXAMPLE / "progress.py").read_text()))[0]
        self.assertEqual((progress.name, progress.defaults), ("progress_reach", {"d0": 0.3}))
        bind = extract_bindings(ast.parse((EXAMPLE / "bindings.py").read_text()))[0]
        self.assertEqual(bind.keys, ["g", "cube", "pad"])


class ReportTest(unittest.TestCase):
    def test_json_round_trip_and_markdown(self) -> None:
        report = Report("candidate", {"parse": "passed", "schema": "failed", "ast": "skipped", "run": "skipped"}, [
            Problem("schema.param_missing", "stage_graph.yaml: params", "Declare 'near.max_dist'."),
            Problem("schema.template", "predicates.py:12", "need_true must be a non-empty string literal."),
        ])
        self.assertEqual(Report.from_json(report.to_json()), report)
        markdown = report.to_markdown()
        self.assertEqual(markdown.splitlines()[0], "Check report: FAILED")
        for group, status in report.groups.items():
            self.assertIn(f"{group}: {status}", markdown)
        for i, problem in enumerate(report.problems, 1):
            self.assertIn(f"{i}. `{problem.code}` at {problem.location}: {problem.message}", markdown)
        report = check_static(EXAMPLE)
        self.assertEqual(Report.from_json(report.to_json()), report)
        self.assertEqual(report.to_markdown().splitlines()[0], "Check report: PASSED")

    def test_passed_requires_all_static_groups_and_no_failure(self) -> None:
        groups = {"parse": "passed", "schema": "passed", "ast": "passed", "run": "skipped"}
        self.assertTrue(Report("candidate", groups, []).passed)
        self.assertTrue(Report("candidate", {**groups, "run": "passed"}, []).passed)
        for group in groups:
            self.assertFalse(Report("candidate", {**groups, group: "failed"}, []).passed)
        for group in ("parse", "schema", "ast"):
            self.assertFalse(Report("candidate", {**groups, group: "skipped"}, []).passed)

    def test_unknown_codes_and_invalid_statuses_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown check code"):
            Problem("schema.made_up", "stage_graph.yaml", "invalid")
        with self.assertRaisesRegex(ValueError, "Report groups"):
            Report("candidate", {}, [])
        with self.assertRaisesRegex(ValueError, "Group status"):
            Report("candidate", {"parse": "pending", "schema": "skipped", "ast": "skipped", "run": "skipped"}, [])
