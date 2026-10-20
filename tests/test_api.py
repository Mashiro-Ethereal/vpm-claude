import unittest

import torch

from vpmkit.api import predicate, bool_margin, _progress_spec


class APITests(unittest.TestCase):
    def test_signature_metadata_and_identity(self):
        def close(w, a, b, *, distance=1, tolerance=0.2):
            return a.pos[:, 0]
        wrapped = predicate(desc="close", need_true="Move {a} to {b}.", scale=0.5)(close)
        self.assertIs(wrapped, close)
        spec = wrapped.__vpm_predicate__
        self.assertEqual(spec.name, "close")
        self.assertEqual(spec.obj_params, ("a", "b"))
        self.assertEqual(spec.thresholds, {"distance": 1.0, "tolerance": 0.2})

    def test_invalid_predicate_signatures(self):
        sources = ["def f(): pass", "def f(world, a): pass", "def f(w=None): pass",
                   "def f(w, a=None): pass", "def f(w, *args): pass",
                   "def f(w, **kwargs): pass", "def f(w, *, p): pass",
                   "def f(w, *, p=True): pass", "def f(w, *, p='x'): pass",
                   "def f(*, w): pass"]
        for source in sources:
            with self.subTest(source=source):
                ns = {}
                exec(source, ns)
                with self.assertRaises(ValueError):
                    predicate(desc="x", need_true="x")(ns["f"])

    def test_scale_and_finite_defaults(self):
        for scale in [0, -1, float("nan"), float("inf")]:
            with self.assertRaises(ValueError):
                predicate(desc="x", need_true="x", scale=scale)
        def f(w, *, p=float("inf")):
            pass
        with self.assertRaises(ValueError):
            predicate(desc="x", need_true="x")(f)

    def test_progress_signature(self):
        def f(w, o, *, speed=2):
            pass
        self.assertEqual(_progress_spec(f, "carry").params, {"speed": 2.0})
        for fn in [lambda w, objects: None, lambda w, o, p=1: None, lambda w, o, **kw: None]:
            with self.assertRaises(ValueError):
                _progress_spec(fn, "carry")

    def test_bool_margin(self):
        result = bool_margin(torch.tensor([True, False]))
        torch.testing.assert_close(result, torch.tensor([1., -1.]))
        self.assertEqual(result.dtype, torch.float32)
        with self.assertRaises(TypeError):
            bool_margin(torch.ones(2))
