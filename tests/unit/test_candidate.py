"""Schema boundaries and isolated candidate imports."""

import sys
import unittest

from pydantic import ValidationError

from vpmkit.candidate import StageGraph, load_candidate_unchecked
from vpmkit.candidate.schema import Invariant, ObjectDecl, Official, Param, Stage
from vpmkit.teacher import Teacher
from .synth import DEFAULT_PREDICATES, EXAMPLE, candidate_dir, graph


class CandidateTest(unittest.TestCase):
    def test_example_load_and_relative_imports(self) -> None:
        c = load_candidate_unchecked(EXAMPLE)
        self.assertEqual(set(c.predicates), {"near", "grasped", "on", "static"})
        self.assertEqual(set(c.progress), {"reach"})
        self.assertTrue(callable(c.bind))
        helper = c.progress["reach"].__globals__["tcp_dist"]
        self.assertIs(helper, c.predicates["near"].__wrapped__.__globals__["tcp_dist"])
        self.assertEqual(c.graph.stage_index("release"), 3)
        self.assertEqual(c.graph.param_defaults(), {"near.max_dist": 0.02, "progress.reach.d0": 0.3})
        self.assertFalse((EXAMPLE / "__pycache__").exists())

    def test_independent_loads_and_no_bytecode(self) -> None:
        progress = "from .predicates import p\ndef progress_only(w, o):\n    return p(w, o.cube)\n"
        old = sys.dont_write_bytecode
        with candidate_dir(progress=progress) as path, candidate_dir() as other:
            a = load_candidate_unchecked(path)
            b = load_candidate_unchecked(path)
            c = load_candidate_unchecked(other)
            self.assertIsNot(a.predicates["p"], b.predicates["p"])
            self.assertEqual(len({x.predicates["p"].__module__ for x in (a, b, c)}), 3)
            a.predicates["p"].__wrapped__.__globals__["load_marker"] = 1
            self.assertNotIn("load_marker", b.predicates["p"].__wrapped__.__globals__)
            self.assertIs(a.progress["only"].__globals__["p"], a.predicates["p"])
            self.assertFalse(list(path.rglob("__pycache__")))
            self.assertIsNone(c.bind)
            self.assertEqual(c.progress, {})
        self.assertEqual(sys.dont_write_bytecode, old)

    def test_only_progress_functions_defined_in_progress_module(self) -> None:
        source = DEFAULT_PREDICATES + "\ndef progress_external(w, o):\n    return p(w, o.cube)\n"
        progress = "from .predicates import progress_external\ndef progress_only(w, o):\n    return progress_external(w, o)\n"
        with candidate_dir(predicates=source, progress=progress) as path:
            self.assertEqual(set(load_candidate_unchecked(path).progress), {"only"})

    def test_bytecode_flag_restored_after_failure(self) -> None:
        old = sys.dont_write_bytecode
        with candidate_dir(predicates="raise RuntimeError('bad import')") as path:
            with self.assertRaisesRegex(RuntimeError, "bad import"):
                load_candidate_unchecked(path)
            self.assertEqual(sys.dont_write_bytecode, old)
            self.assertFalse(list(path.rglob("__pycache__")))

    def test_schema_extra_fields_and_names(self) -> None:
        for cls, data in [(ObjectDecl, {"name": "cube"}), (Invariant, {"literal": "p(cube)", "regress_to": "a"}),
                          (Official, {"literals": ["p(cube)"], "key": "success"}),
                          (Param, {"name": "p.t", "default": 1, "range": [0, 2]}),
                          (Stage, {"name": "a", "exit": ["p(cube)"]}), (StageGraph, graph())]:
            with self.subTest(model=cls.__name__), self.assertRaises(ValidationError):
                cls.model_validate({**data, "unknown": 1})
        for name in ("Upper", "two words", "1first", "has-dash"):
            data = graph()
            data["objects"][name] = {"name": "object"}
            with self.assertRaises(ValidationError):
                StageGraph.model_validate(data)
            with self.assertRaises(ValidationError):
                Stage(name=name, exit=["p(cube)"])
        data = graph()
        data["stages"] *= 2
        with self.assertRaisesRegex(ValidationError, "stage names must be unique"):
            StageGraph.model_validate(data)
        data = graph(params=[{"name": "p.t", "default": 1, "range": [0, 2]}] * 2)
        with self.assertRaisesRegex(ValidationError, "param names must be unique"):
            StageGraph.model_validate(data)

    def test_schema_does_not_perform_reference_checks(self) -> None:
        data = graph(stages=[{"name": "only", "exit": [], "invariants": [
            {"literal": "not valid text", "regress_to": "unknown"}]}],
            params=[{"name": "unmatched", "default": 5, "range": [2, 1]}])
        parsed = StageGraph.model_validate(data)
        self.assertEqual(parsed.params[0].default, 5)
        with self.assertRaisesRegex(ValueError, "unknown stage"):
            parsed.stage_index("missing")

    def test_teacher_minimum_construction_checks(self) -> None:
        cases = [("not not p(cube)", "Invalid literal"), ("missing(cube)", "unknown predicate"),
                 ("p(g, cube)", "expected 1 objects"), ("p(missing)", "undeclared object")]
        for literal, message in cases:
            with candidate_dir(data=graph(stages=[{"name": "only", "exit": [literal]}])) as path:
                with self.assertRaisesRegex(ValueError, message):
                    Teacher(load_candidate_unchecked(path))
        for stages in ([], [{"name": "only", "exit": []}],
                       [{"name": "only", "exit": ["p(cube)"],
                         "invariants": [{"literal": "p(cube)", "regress_to": "only"}]}]):
            with candidate_dir(data=graph(stages=stages)) as path, self.assertRaises(ValueError):
                Teacher(load_candidate_unchecked(path))
        with candidate_dir(progress="def progress_missing(w, o): return w.table_z") as path:
            with self.assertRaisesRegex(ValueError, "unknown stage"):
                Teacher(load_candidate_unchecked(path))
        source = DEFAULT_PREDICATES.replace('need_false="release {o}.", ', "")
        with candidate_dir(data=graph(stages=[{"name": "only", "exit": ["not p(cube)"]}]), predicates=source) as path:
            with self.assertRaisesRegex(ValueError, "need_false"):
                Teacher(load_candidate_unchecked(path))

    def test_first_appearance_including_official_only_instance(self) -> None:
        data = graph(stages=[{"name": "a", "exit": ["p(cube)"]},
                            {"name": "b", "exit": ["not p(cube)"],
                             "invariants": [{"literal": "p(pad)", "regress_to": "a"}]}])
        data["official"] = [{"key": "reading", "literals": ["p(g)", "p(pad)"]}]
        with candidate_dir(data=data) as path:
            teacher = Teacher(load_candidate_unchecked(path))
            self.assertEqual(teacher.instances, ["p(cube)", "p(pad)", "p(g)"])
