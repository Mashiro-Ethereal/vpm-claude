"""Literal grammar and predicate call contracts."""

import inspect
import unittest

import torch

from vpmkit.api import G, predicate, signed
from vpmkit.literal import Literal, LiteralSyntaxError, parse_literal
from vpmkit.predicate import Predicate, active_thresholds


class LiteralTest(unittest.TestCase):
    def test_valid_and_canonical(self) -> None:
        for text in ("near(g,cube)", " \tnear ( g ,\n cube ) ", "near(g, cube)"):
            with self.subTest(text=text):
                literal = parse_literal(text)
                self.assertEqual(literal, Literal("near", ("g", "cube"), False))
                self.assertEqual(literal.instance, ("near", ("g", "cube")))
                self.assertEqual(literal.instance_text, "near(g, cube)")
                self.assertEqual(str(literal), "near(g, cube)")
        self.assertEqual(str(parse_literal(" \nnot\t p_1 ( A_2 ) ")), "not p_1(A_2)")
        self.assertEqual(str(parse_literal("notable(_a)")), "notable(_a)")
        with self.assertRaises(AttributeError):
            literal.negated = True

    def test_invalid(self) -> None:
        for text in ("not not p(a)", "p()", "p(a,)", "p(a b)", "p(a) and q(b)",
                     "near(g, 0.1)", "", "not(p(a))", "p(a) or q(a)", "p(a.b)",
                     "p(a)[0]", "p(a);", "1p(a)", "p('a')"):
            with self.subTest(text=text), self.assertRaises(LiteralSyntaxError) as raised:
                parse_literal(text)
            self.assertIn(repr(text), str(raised.exception))


class PredicateTest(unittest.TestCase):
    def test_metadata_and_wrapper(self) -> None:
        def near(w, g, o, max_dist=0.02, *, factor=2):
            """A test measurement."""
            return max_dist * factor

        wrapped = predicate(desc="Nearby.", need_true="move {g} to {o}.", scale=0.3)(near)
        self.assertIsInstance(wrapped, Predicate)
        self.assertIs(wrapped.__wrapped__, near)
        self.assertEqual(wrapped.__doc__, near.__doc__)
        self.assertEqual(inspect.signature(wrapped), inspect.signature(near))
        self.assertEqual(wrapped.meta.name, "near")
        self.assertEqual(wrapped.meta.desc, "Nearby.")
        self.assertEqual(wrapped.meta.need_true, "move {g} to {o}.")
        self.assertIsNone(wrapped.meta.need_false)
        self.assertEqual(wrapped.meta.scale, 0.3)
        self.assertEqual(wrapped.meta.object_params, ("g", "o"))
        self.assertEqual(wrapped.meta.thresholds, {"max_dist": 0.02, "factor": 2})

    def test_signature_errors(self) -> None:
        sources = ["def f(): pass", "def f(world, o): pass", "def f(w): pass",
                   "def f(w, o=1): pass", "def f(w, *objects): pass",
                   "def f(w, o, **kwargs): pass", "def f(w, o, *args): pass",
                   "def f(w, *, o): pass", "def f(w, o, *, threshold): pass",
                   "def f(w, o, t=True): pass", "def f(w, o, t=None): pass",
                   "def f(w, o, t='0.1'): pass", "def f(w, o, /): pass",
                   "def f(w=0): pass"]
        for source in sources:
            namespace = {}
            exec(source, namespace)
            with self.subTest(source=source), self.assertRaisesRegex(TypeError, ".+"):
                predicate(desc="x", need_true="x", scale=1)(namespace["f"])

    def test_metadata_errors(self) -> None:
        for field, values in {"desc": ("", " ", None, 3), "need_true": ("", " ", None, 3),
                              "scale": (0, -1, True, "1", None, float("nan"))}.items():
            for value in values:
                kwargs = {"desc": "x", "need_true": "x", "scale": 1, field: value}
                with self.subTest(field=field, value=value), self.assertRaisesRegex(TypeError, field):
                    predicate(**kwargs)

    def test_active_thresholds_and_explicit_arguments(self) -> None:
        @predicate(desc="near", need_true="near", scale=1)
        def near(w, o, distance=0.02, *, factor=2):
            return distance * factor

        self.assertEqual(near(None, None), 0.04)
        with active_thresholds({"near.distance": 0.1, "near.factor": 3}):
            self.assertAlmostEqual(near(None, None), 0.3)
            self.assertAlmostEqual(near(None, None, 0.2), 0.6)
            self.assertAlmostEqual(near(None, None, distance=0.2, factor=4), 0.8)
            with active_thresholds({"near.factor": 5}):
                self.assertEqual(near(None, None), 0.1)
            self.assertAlmostEqual(near(None, None), 0.3)
        self.assertEqual(near(None, None), 0.04)
        with self.assertRaises(RuntimeError):
            with active_thresholds({"near.distance": 9}):
                raise RuntimeError("restore context")
        self.assertEqual(near(None, None), 0.04)

    def test_direct_calls_from_another_predicate(self) -> None:
        @predicate(desc="inner", need_true="inner", scale=1)
        def inner(w, o, t=1):
            return t

        @predicate(desc="outer", need_true="outer", scale=1)
        def outer(w, o):
            return inner(w, o)

        with active_thresholds({"inner.t": 3}):
            self.assertEqual(outer(None, None), 3)

    def test_world_parameter_can_be_positional_only(self) -> None:
        @predicate(desc="reading", need_true="reading", scale=1)
        def reading(w, /, o, t=2):
            return t

        with active_thresholds({"reading.t": 3}):
            self.assertEqual(reading(None, None), 3)

    def test_signed_and_api_exports(self) -> None:
        for value in (torch.tensor([False, True]), torch.tensor([0, -3]), torch.tensor([0., 0.2])):
            result = signed(value)
            torch.testing.assert_close(result, torch.tensor([-1., 1.]))
            self.assertEqual(result.dtype, torch.float32)
            self.assertEqual(result.device, value.device)
        import vpmkit.api
        self.assertEqual(vpmkit.api.__all__, ["predicate", "signed", "G"])
        self.assertTrue(callable(G.quat_apply))
