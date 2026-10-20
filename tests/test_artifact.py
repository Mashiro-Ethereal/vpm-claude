from dataclasses import replace
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType
import unittest

from pydantic import ValidationError
import yaml

from tests import ROOT, TOY
from vpmkit.artifact.astcheck import check_candidate_ast
from vpmkit.artifact.loader import CandidateError, load_candidate
from vpmkit.artifact.schema import StageGraph, check_graph


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = load_candidate(TOY)

    def graph(self):
        return self.candidate.graph.model_copy(deep=True)

    def codes(self, graph, specs=None, progress=None):
        return {i.code for i in check_graph(
            graph, self.candidate.predicate_specs if specs is None else specs,
            self.candidate.progress_specs if progress is None else progress,
        )}

    def test_valid_graph(self):
        self.assertEqual(self.codes(self.graph()), set())

    def test_every_required_semantic_issue(self):
        cases = [
            (lambda g: g.stages[0].exit.append("near(g,)"), "literal_syntax"),
            (lambda g: g.stages[0].exit.append("missing(g)"), "unknown_predicate"),
            (lambda g: g.stages[0].exit.append("near(g)"), "object_arity"),
            (lambda g: g.stages[0].exit.append("near(g, absent)"), "undefined_object"),
            (lambda g: setattr(g.stages[2].invariants[0], "regress_to", "carry"), "regress_not_earlier"),
            (lambda g: setattr(g.stages[2].invariants[0], "regress_to", "absent"), "regress_not_earlier"),
            (lambda g: setattr(g.stages[1], "name", "reach"), "duplicate_stage"),
            (lambda g: setattr(g.stages[2].invariants[0], "event", "Move {absent}"), "event_placeholder"),
            (lambda g: setattr(g.stages[2].invariants[0], "event", "Move {block"), "event_placeholder"),
            (lambda g: setattr(g.params[0], "name", "near.missing"), "unknown_param"),
            (lambda g: setattr(g.params[1], "name", "progress.missing.span"), "unknown_param"),
            (lambda g: setattr(g.params[1], "name", "progress.carry.missing"), "unknown_param"),
            (lambda g: setattr(g.params[0], "default", 0.9), "default_out_of_range"),
            (lambda g: setattr(g.params[0], "range", (0.1, 0.1)), "invalid_range"),
            (lambda g: setattr(g.params[0], "range", (0.2, 0.1)), "invalid_range"),
            (lambda g: setattr(g.params[0], "name", "in_region.radius"), "official_tunable"),
        ]
        for change, code in cases:
            with self.subTest(code=code):
                graph = self.graph()
                change(graph)
                self.assertIn(code, self.codes(graph))
        specs = dict(self.candidate.predicate_specs)
        specs["grasped"] = replace(specs["grasped"], need_false=None)
        self.assertIn("missing_need_false", self.codes(self.graph(), specs))

    def test_all_issues_accumulate(self):
        graph = self.graph()
        graph.stages[0].exit += ["bad syntax", "unknown(no_object)", "near(g)"]
        graph.stages[2].invariants[0].event = "{missing}"
        graph.params[0].range = (0.8, 0.2)
        self.assertTrue({"literal_syntax", "unknown_predicate", "undefined_object", "object_arity",
                         "event_placeholder", "invalid_range", "default_out_of_range"} <= self.codes(graph))

    def test_extra_fields_and_structural_constraints(self):
        changes = [
            lambda d: d.update(unknown=True),
            lambda d: d["stages"][0].update(unknown=True),
            lambda d: d["objects"]["g"].update(unknown=True),
            lambda d: d["runtime"].update(debounce=0),
            lambda d: d["runtime"].update(debounce=1.5),
            lambda d: d.update(stages=[]),
            lambda d: d["stages"][0].update(exit=[]),
            lambda d: d["official"][0].update(literals=[]),
            lambda d: d["params"][0].update(range=[0]),
        ]
        for change in changes:
            data = self.candidate.graph.model_dump()
            change(data)
            with self.assertRaises(ValidationError):
                StageGraph.model_validate(data)


class TemporaryCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="candidate_")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        shutil.copytree(TOY, self.path, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))

    def write(self, name, text):
        (self.path / name).write_text(text)

    def ast_codes(self):
        return {issue.code for issue in check_candidate_ast(self.path)}


class ASTTests(TemporaryCandidateTests):
    def test_toy_passes(self):
        self.assertEqual(check_candidate_ast(self.path), [])

    def test_forbidden_imports_attributes_names_and_loop(self):
        original = (self.path / "predicates.py").read_text()
        snippets = [
            ("import os\n", "forbidden_import"),
            ("from pathlib import Path\n", "forbidden_import"),
            ("def helper(x): return x.item()\n", "forbidden_attribute"),
            ("def helper(x): return x.name\n", "forbidden_attribute"),
            ("def helper(x): return x._handle\n", "forbidden_attribute"),
            ("def helper(x): return x.official\n", "forbidden_attribute"),
            ("def helper(x): return getattr(x, 'pos')\n", "forbidden_name"),
            ("@predicate(desc='x', need_true='x')\ndef extra(w, x):\n    for i in [1]:\n        pass\n    return x.pos[:, 0]\n", "forbidden_loop"),
            ("@predicate(desc='x', need_true='x')\ndef extra(w, x):\n    while False:\n        pass\n    return x.pos[:, 0]\n", "forbidden_loop"),
        ]
        for snippet, code in snippets:
            with self.subTest(snippet=snippet):
                self.write("predicates.py", original + "\n" + snippet)
                self.assertIn(code, self.ast_codes())

    def test_undecorated_predicate_and_helpers(self):
        self.write("predicates.py", "def near(w, g, block): return g.pos[:, 0]\n")
        self.assertIn("missing_decorator", self.ast_codes())
        self.write("predicates.py", "def helper(w, g): return sum([x for x in [1, 2]])\n")
        self.assertEqual(self.ast_codes(), set())

    def test_progress_imports_signature_and_loops(self):
        self.write("progress.py", "from predicates import near\ndef progress_carry(w, o, *, span=-0.5):\n    return o.block.pos[:, 0]\n")
        self.assertEqual(self.ast_codes(), set())
        for code in ["def progress_carry(w, obj): return 0", "def progress_carry(w, o, p=1): return 0",
                     "def progress_carry(w, o, *, p): return 0", "def progress_carry(w, o, *, p=True): return 0"]:
            self.write("progress.py", code)
            self.assertIn("progress_signature", self.ast_codes())
        self.write("progress.py", "def progress_carry(w, o):\n    for x in [1]:\n        pass\n")
        self.assertIn("forbidden_loop", self.ast_codes())

    def test_bind_is_required_and_environment_access_allowed(self):
        self.write("bindings.py", "import numpy as np\ndef bind(env, api):\n    return api.actor(getattr(env, 'block'), [1, 1, 1])\n")
        self.assertEqual(self.ast_codes(), set())
        self.write("bindings.py", "import torch\n")
        self.assertIn("missing_bind", self.ast_codes())
        self.write("bindings.py", "def bind(environment): pass\n")
        self.assertIn("bind_signature", self.ast_codes())
        self.write("bindings.py", "def bind(env, api): return open('file')\n")
        self.assertIn("forbidden_name", self.ast_codes())

    def test_alias_decorator_comprehension_and_syntax_error(self):
        self.write("predicates.py", "from vpmkit.api import predicate as pred\n@pred(desc='x', need_true='x')\ndef near(w, g, block):\n    return sum([x for x in [1, 2]])\n")
        self.assertEqual(self.ast_codes(), set())
        self.write("predicates.py", "def bad(:")
        self.assertIn("python_syntax", self.ast_codes())


class LoaderTests(TemporaryCandidateTests):
    def test_progress_accepts_numeric_default_expressions(self):
        self.write("progress.py", "import math\ndef progress_carry(w, o, *, span=math.pi / 2):\n    return o.block.pos[:, 0] / span\n")
        candidate = load_candidate(self.path)
        self.assertAlmostEqual(candidate.progress_specs["carry"].params["span"], 1.5707963267948966)
        self.write("progress.py", "import math\ndef progress_carry(w, o, *, span=str(math.pi)):\n    return o.block.pos[:, 0]\n")
        with self.assertRaises(CandidateError) as ctx:
            load_candidate(self.path)
        self.assertIn("progress_signature", {i.code for i in ctx.exception.issues})

    def test_load_and_bind_is_not_executed(self):
        self.write("bindings.py", "def bind(env, api):\n    raise RuntimeError('M1 must not bind')\n")
        candidate = load_candidate(self.path)
        self.assertEqual(set(candidate.predicates), {"near", "gripper_open", "grasped", "in_region"})
        self.assertEqual(set(candidate.progress), {"carry"})
        self.assertEqual(candidate.display_names["region"], "target region")
        self.assertEqual(candidate.params["near.max_dist"], 0.1)
        self.assertEqual(candidate.dir, self.path)
        self.assertTrue(callable(candidate.bind))

    def test_optional_progress(self):
        (self.path / "progress.py").unlink()
        data = yaml.safe_load((self.path / "stage_graph.yaml").read_text())
        data["params"] = data["params"][:1]
        self.write("stage_graph.yaml", yaml.safe_dump(data))
        candidate = load_candidate(self.path)
        self.assertEqual(candidate.progress, {})
        self.assertEqual(candidate.progress_specs, {})

    def test_module_alias_and_path_restored_on_success_and_failure(self):
        sentinel = ModuleType("predicates")
        original = sys.modules.get("predicates")
        sys.modules["predicates"] = sentinel
        before_path = sys.path[:]
        before_candidates = {k for k in sys.modules if k.startswith("_vpm_candidate_")}
        try:
            first = load_candidate(self.path)
            second = load_candidate(self.path)
            self.assertNotEqual(first.predicates["near"].__module__, second.predicates["near"].__module__)
            self.assertIs(sys.modules["predicates"], sentinel)
            self.assertEqual(sys.path, before_path)
            self.write("progress.py", "from predicates import near\nraise RuntimeError('broken progress')\n")
            with self.assertRaises(CandidateError) as ctx:
                load_candidate(self.path)
            self.assertIn("import_error", {i.code for i in ctx.exception.issues})
            self.assertIs(sys.modules["predicates"], sentinel)
            self.assertEqual(sys.path, before_path)
            self.assertEqual({k for k in sys.modules if k.startswith("_vpm_candidate_")}, before_candidates)
        finally:
            if original is None:
                sys.modules.pop("predicates", None)
            else:
                sys.modules["predicates"] = original

    def test_params_copy_validation(self):
        candidate = load_candidate(self.path)
        changed = candidate.with_params({"near.max_dist": 0.2, "progress.carry.span": 0.8})
        self.assertEqual(candidate.params["near.max_dist"], 0.1)
        self.assertEqual(changed.params["near.max_dist"], 0.2)
        for overrides in [{"absent": 0.1}, {"near.max_dist": 1}, {"near.max_dist": float("nan")},
                          {"near.max_dist": float("inf")}, {"near.max_dist": True}]:
            with self.assertRaises(CandidateError):
                candidate.with_params(overrides)

    def test_reports_multiple_ast_issues(self):
        self.write("predicates.py", "import os\ndef near(w, g, block): return g.name\n")
        self.write("bindings.py", "pass\n")
        with self.assertRaises(CandidateError) as ctx:
            load_candidate(self.path)
        self.assertTrue({"forbidden_import", "missing_decorator", "forbidden_attribute", "missing_bind"}
                        <= {i.code for i in ctx.exception.issues})

    def test_schema_and_missing_file_errors(self):
        self.write("stage_graph.yaml", "task: x\nstages: []\nobjects: {}\nextra: true\n")
        (self.path / "bindings.py").unlink()
        with self.assertRaises(CandidateError) as ctx:
            load_candidate(self.path)
        self.assertTrue({"schema", "missing_file"} <= {i.code for i in ctx.exception.issues})

    def test_malformed_yaml_collections_are_candidate_errors(self):
        for field in ("stages", "official"):
            data = yaml.safe_load((TOY / "stage_graph.yaml").read_text())
            data[field] = 7
            self.write("stage_graph.yaml", yaml.safe_dump(data))
            with self.subTest(field=field), self.assertRaises(CandidateError) as ctx:
                load_candidate(self.path)
            self.assertIn("schema", {i.code for i in ctx.exception.issues})
