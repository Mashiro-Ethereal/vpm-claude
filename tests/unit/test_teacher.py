"""End-to-end teacher behavior on synthetic CPU snapshots."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from vpmkit.candidate import load_candidate_unchecked
from vpmkit.errors import CandidateOutputError, CandidateRuntimeError
from vpmkit.predicate import active_thresholds
from vpmkit.teacher import Teacher
from vpmkit.world import Snapshot, make_views
from .synth import DEFAULT_PREDICATES, EXAMPLE, candidate, graph, snapshot, trajectory


class TeacherTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.example = load_candidate_unchecked(EXAMPLE)

    def assertOutputEqual(self, actual: dict, expected: dict) -> None:
        self.assertEqual(set(actual), {"stage", "stage_progress", "phi", "pred", "margin", "guidance"})
        self.assertEqual(actual.keys(), expected.keys())
        for key in actual:
            with self.subTest(output=key):
                torch.testing.assert_close(actual[key], expected[key], atol=1e-6, rtol=0)

    def test_columns_shapes_and_types(self) -> None:
        teacher = Teacher(self.example, 6)
        self.assertEqual(teacher.instances, ["near(g, cube)", "grasped(g, cube)", "on(cube, pad)", "static(cube)"])
        self.assertEqual(teacher.stage_names, ["reach", "grasp", "carry", "release"])
        self.assertEqual(teacher.num_stages, 4)
        output = teacher.step(snapshot(6))
        for key in ("stage", "stage_progress", "phi"):
            self.assertEqual(output[key].shape, (6,))
        for key in ("margin", "pred", "guidance"):
            self.assertEqual(output[key].shape, (6, 4))
        self.assertEqual(output["stage"].dtype, torch.long)
        for key in ("stage_progress", "phi", "margin"):
            self.assertEqual(output[key].dtype, torch.float32)
        for key in ("pred", "guidance"):
            self.assertEqual(output[key].dtype, torch.bool)
        with self.assertRaises(AttributeError):
            teacher.stage = torch.tensor([1])

    def test_grasp_near_invariant_and_render(self) -> None:
        teacher = Teacher(self.example)
        teacher.reset(stage=1)
        output = teacher.step(snapshot(tcp=(0.3, 0, 0.02)))
        self.assertEqual(output["stage"].tolist(), [0])
        self.assertEqual(teacher.render(output, 0), ["The gripper is far from the red cube; move the gripper to the red cube."])
        teacher.reset(stage=1)
        output = teacher.step(snapshot())
        self.assertEqual(output["stage"].tolist(), [1])
        self.assertEqual(teacher.render(output, 0), ["The red cube is not held; grasp the red cube with the gripper."])

    def test_carry_slips_near_and_far(self) -> None:
        teacher = Teacher(self.example, 2)
        teacher.reset(stage=2)
        output = teacher.step(snapshot(2, tcp=[[0, 0, 0.06], [0.3, 0, 0.02]]))
        self.assertEqual(output["stage"].tolist(), [1, 0])
        self.assertEqual(output["guidance"].tolist(), [[False, True, False, False], [True, False, False, False]])

    def test_release_guidance_and_completion(self) -> None:
        teacher = Teacher(self.example, 3)
        teacher.reset(stage=3)
        s = snapshot(3, cube=(0.2, 0, 0.03), grasp=[True, False, False],
                     lin_vel=[[0, 0, 0], [0.02, 0, 0], [0, 0, 0]])
        output = teacher.step(s)
        self.assertEqual(output["stage"].tolist(), [3, 3, 3])
        self.assertEqual(teacher.render(output, 0), ["The red cube is still held; release the red cube."])
        self.assertEqual(teacher.render(output, 1), ["The red cube is still moving; hold still until the red cube comes to rest."])
        self.assertEqual(teacher.render(output, 2), [])
        self.assertEqual(output["guidance"].tolist(), [[False, True, False, False], [False, False, False, True], [False] * 4])
        self.assertEqual(float(output["stage_progress"][2]), 1)
        self.assertEqual(float(output["phi"][2]), 1)
        # Both failed literals preserve guard order in text.
        s.grasping[("g", "cube")][1] = True
        messages = teacher.render(teacher.step(s), 1)
        self.assertEqual(messages, ["The red cube is still held; release the red cube.",
                                    "The red cube is still moving; hold still until the red cube comes to rest."])

    def test_release_knocked_off_and_forward_walk(self) -> None:
        teacher = Teacher(self.example, 3)
        teacher.reset(stage=3)
        output = teacher.step(snapshot(3, tcp=[[0, 0, 0.06], [0, 0, 0.06], [0.4, 0, 0.06]],
                                       grasp=[True, False, False]))
        self.assertEqual(output["stage"].tolist(), [2, 1, 0])
        self.assertEqual(output["guidance"].tolist(), [[False, False, True, False],
                                                       [False, True, False, False], [True, False, False, False]])

    def test_all_guards_walk_to_last(self) -> None:
        teacher = Teacher(self.example)
        output = teacher.step(snapshot(tcp=(0.2, 0, 0.07), cube=(0.2, 0, 0.03), grasp=True))
        self.assertEqual(output["stage"].tolist(), [3])
        self.assertEqual(teacher.render(output, 0), ["The red cube is still held; release the red cube."])

    def test_last_stage_progress_override(self) -> None:
        progress = "def progress_only(w, o):\n    return w.table_z + 0.3\n"
        with candidate(progress=progress) as c:
            teacher = Teacher(c, 2)
            s = snapshot(2, cube=[[1, 0, 0], [-1, 0, 0]])
            raw = teacher.compute_progress(s, teacher.compute_margins(s))
            torch.testing.assert_close(raw, torch.full((2, 1), 0.3))
            output = teacher.step(s)
            torch.testing.assert_close(output["stage_progress"], torch.tensor([1., 0.3]))
            self.assertEqual(output["guidance"].tolist(), [[False], [True]])

    def test_raw_progress_is_unclipped_and_step_clips(self) -> None:
        progress = "def progress_only(w, o):\n    return o.g.pos[:, 0]\n"
        with candidate(progress=progress) as c:
            teacher = Teacher(c, 2)
            s = snapshot(2, cube=(-1, 0, 0), tcp=[[-2, 0, 0], [3, 0, 0]])
            torch.testing.assert_close(teacher.compute_progress(s, teacher.compute_margins(s)), torch.tensor([[-2.], [3.]]))
            torch.testing.assert_close(teacher.step(s)["stage_progress"], torch.tensor([0., 1.]))

    def test_negation_zero_boundary_and_signed_margins(self) -> None:
        data = graph(stages=[{"name": "only", "exit": ["not p(cube)"]}])
        with candidate(data=data) as c:
            teacher = Teacher(c, 3)
            margins = teacher.compute_margins(snapshot(3, cube=[[-0.2, 0, 0], [0, 0, 0], [0.2, 0, 0]]))
            torch.testing.assert_close(margins[:, 0], torch.tensor([-0.2, 0, 0.2]))
            output = teacher.step(snapshot(3, cube=[[-0.2, 0, 0], [0, 0, 0], [0.2, 0, 0]]))
            self.assertEqual(output["pred"].tolist(), [[False], [True], [True]])
            self.assertEqual(output["guidance"].tolist(), [[False], [True], [True]])
            torch.testing.assert_close(output["stage_progress"], torch.tensor([1., 1., 0.8]))
        teacher = Teacher(self.example, 2)
        margins = teacher.compute_margins(snapshot(2, grasp=[False, True]))
        torch.testing.assert_close(margins[:, 1], torch.tensor([-1., 1.]))

    def test_default_progress_hand_computation(self) -> None:
        teacher = Teacher(self.example, 2)
        s = snapshot(2, grasp=[True, False], lin_vel=[[0, 0, 0], [0.015, 0, 0]])
        progress = teacher.compute_progress(s, teacher.compute_margins(s))
        # on: min(0.06 - 0.02 - 0.2, 0.005 - abs(0.02 - 0.005 - 0.02 - 0.005)) = -0.16.
        torch.testing.assert_close(progress[:, 2], torch.full((2,), 1 - 0.16 / 0.2))
        # Release: held and static -> (0 + 1)/2; free and speed 1.5x limit -> (1 + 0.5)/2.
        torch.testing.assert_close(progress[:, 3], torch.tensor([0.5, 0.75]))

    def test_threshold_overrides_shared_candidate_and_progress(self) -> None:
        s = snapshot(tcp=(0, 0, 0.06), cube=(0, 0, 0.02))
        default = Teacher(self.example)
        tuned = Teacher(self.example, params={"near.max_dist": 0.0, "progress.reach.d0": 0.1})
        self.assertTrue(default.step(s)["pred"][0, 0])
        self.assertFalse(tuned.step(s)["pred"][0, 0])
        self.assertTrue(default.step(s)["pred"][0, 0])
        self.assertAlmostEqual(float(tuned.compute_progress(s, tuned.compute_margins(s))[0, 0]), 0.6, places=5)
        source = (EXAMPLE / "predicates.py").read_text()
        data = graph(stages=[{"name": "reach", "exit": ["near(g, cube)"]}],
                     params=[{"name": "near.max_dist", "default": 0.02, "range": [0, 0.05]}])
        progress = "from .predicates import near\ndef progress_reach(w, o):\n    return near(w, o.g, o.cube)\n"
        with candidate(data=data, predicates=source, progress=progress) as c:
            teacher = Teacher(c, params={"near.max_dist": 0.0})
            margin = teacher.compute_margins(s)
            torch.testing.assert_close(teacher.compute_progress(s, margin), margin)
            with active_thresholds({"near.max_dist": 9}):
                torch.testing.assert_close(teacher.compute_margins(s), margin)

    def test_parameter_errors_and_runtime_debounce(self) -> None:
        for params in ({"unknown": 1}, {"near.max_dist": -0.01}, {"near.max_dist": 0.06},
                       {"near.max_dist": True}, {"near.max_dist": "x"}, {"near.max_dist": float("nan")},
                       {"runtime.debounce": 0}, {"runtime.debounce": 1.5}, {"runtime.debounce": True},
                       {"runtime.debounce": float("inf")}, {"runtime.debounce": float("nan")}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                Teacher(self.example, params=params)
        teacher = Teacher(self.example, params={"runtime.debounce": 2})
        teacher.reset(stage=2)
        slip = snapshot(tcp=(0.3, 0, 0.02))
        self.assertEqual(teacher.step(slip)["stage"].tolist(), [2])
        self.assertEqual(teacher.step(slip)["stage"].tolist(), [0])

    def test_reset_selected_environments_and_saved_stage(self) -> None:
        teacher = Teacher(self.example, 3, params={"runtime.debounce": 2})
        teacher.reset(stage=2)
        slip = snapshot(3, tcp=(0.3, 0, 0.02))
        teacher.step(slip)
        teacher.reset(env_idx=[0], stage=2)
        self.assertEqual(teacher._counters.tolist(), [[0, 0, 0], [0, 1, 0], [0, 1, 0]])
        self.assertEqual(teacher.step(slip)["stage"].tolist(), [2, 0, 0])
        teacher.reset(env_idx=torch.tensor([0, 2]), stage=torch.tensor([1, 3]))
        self.assertEqual(teacher.stage.tolist(), [1, 0, 3])
        teacher.reset()
        self.assertEqual(teacher.stage.tolist(), [0, 0, 0])
        teacher.reset(env_idx=[])
        teacher = Teacher(self.example)
        teacher.reset(stage=2)
        self.assertEqual(teacher.step(snapshot())["stage"].tolist(), [1])
        for kwargs in ({"stage": -1}, {"stage": 4}, {"stage": torch.tensor([1., 2.])},
                       {"env_idx": [1]}, {"env_idx": [True]}, {"env_idx": [-1]},
                       {"stage": torch.tensor([0, 1])}):
            with self.assertRaises(ValueError):
                teacher.reset(**kwargs)

    def test_batched_matches_six_individual_teachers(self) -> None:
        params = {"runtime.debounce": 2, "near.max_dist": 0.01}
        batched = Teacher(self.example, 6, params=params)
        singles = [Teacher(self.example, params=params) for _ in range(6)]
        starts = torch.tensor([0, 1, 2, 3, 0, 2])
        batched.reset(stage=starts)
        for i, teacher in enumerate(singles):
            teacher.reset(stage=int(starts[i]))
        for s in trajectory():
            actual = batched.step(s)
            outputs = [teacher.step(s.select(i)) for i, teacher in enumerate(singles)]
            self.assertOutputEqual(actual, {key: torch.cat([out[key] for out in outputs]) for key in actual})

    def test_offline_matches_online_and_saved_snapshots(self) -> None:
        snapshots = trajectory()
        params = {"runtime.debounce": 2, "near.max_dist": 0.01}
        teacher = Teacher(self.example, 6, params=params)
        teacher.reset(stage=2)
        teacher.step(snapshot(6))
        saved_stage, saved_counters = teacher.stage.clone(), teacher._counters.clone()
        with tempfile.TemporaryDirectory() as folder:
            restored = []
            for t, s in enumerate(snapshots):
                path = Path(folder) / f"{t}.pt"
                s.save(path)
                restored.append(Snapshot.load(path))
            for initial in (0, 2, torch.tensor([0, 1, 2, 3, 2, 1])):
                online = Teacher(self.example, 6, params=params)
                online.reset(stage=initial)
                sequence = [online.step(s) for s in snapshots]
                expected = {key: torch.stack([out[key] for out in sequence]) for key in sequence[0]}
                self.assertOutputEqual(teacher.evaluate_offline(snapshots, initial), expected)
                self.assertOutputEqual(teacher.evaluate_offline(restored, initial), expected)
        torch.testing.assert_close(teacher.stage, saved_stage)
        torch.testing.assert_close(teacher._counters, saved_counters)

    def test_offline_evaluates_each_function_once_on_all_frames(self) -> None:
        teacher = Teacher(self.example)
        with patch.object(teacher, "_call", wraps=teacher._call) as calls:
            result = teacher.evaluate_offline(trajectory())
        self.assertEqual(result["stage"].shape, (12, 6))
        self.assertEqual(calls.call_count, 5)
        self.assertEqual([call.args[0].batch_size for call in calls.call_args_list], [72] * 5)
        with patch.object(teacher, "_call", wraps=teacher._call) as calls:
            teacher.step(snapshot())
        self.assertEqual(calls.call_count, 5)

    def test_example_functions_random_snapshots(self) -> None:
        generator = torch.Generator().manual_seed(12)
        n = 64
        q = torch.randn(n, 4, generator=generator)
        q /= q.norm(dim=-1, keepdim=True)
        s = snapshot(n, tcp=torch.randn(n, 3, generator=generator), cube=torch.randn(n, 3, generator=generator),
                     pad=torch.randn(n, 3, generator=generator), grasp=torch.rand(n, generator=generator) > 0.5,
                     lin_vel=torch.randn(n, 3, generator=generator), ang_vel=torch.randn(n, 3, generator=generator), cube_quat=q)
        teacher = Teacher(self.example, n)
        margins = teacher.compute_margins(s)
        progress = teacher.compute_progress(s, margins)
        self.assertEqual(margins.shape, (64, 4))
        self.assertEqual(progress.shape, (64, 4))
        self.assertTrue(torch.isfinite(margins).all())
        self.assertTrue(torch.isfinite(progress).all())
        w, _, o = make_views(s)
        values = [self.example.predicates["near"](w, o.g, o.cube),
                  self.example.predicates["grasped"](w, o.g, o.cube),
                  self.example.predicates["on"](w, o.cube, o.pad),
                  self.example.predicates["static"](w, o.cube), self.example.progress["reach"](w, o)]
        for value in values:
            self.assertTrue(value.is_floating_point())
            self.assertEqual(value.shape, (64,))
            self.assertTrue(torch.isfinite(value).all())

    def test_snapshot_requirements(self) -> None:
        teacher = Teacher(self.example, 2)
        with self.assertRaisesRegex(ValueError, "batch_size"):
            teacher.step(snapshot())
        with self.assertRaisesRegex(ValueError, "device"):
            teacher.step(snapshot(2).to("meta"))
        with self.assertRaisesRegex(ValueError, "at least one"):
            teacher.evaluate_offline([])
        with self.assertRaisesRegex(ValueError, "same batch_size"):
            teacher.evaluate_offline([snapshot(), snapshot(2)])

    def test_output_stage_is_stable_after_reset(self) -> None:
        teacher = Teacher(self.example)
        output = teacher.step(snapshot())
        teacher.reset()
        self.assertEqual(output["stage"].tolist(), [1])


class CandidateExecutionTest(unittest.TestCase):
    def test_predicate_exception_is_chained(self) -> None:
        source = DEFAULT_PREDICATES.replace("return o.pos[:, 0]", "raise RuntimeError('candidate failed')")
        with candidate(predicates=source) as c:
            with self.assertRaises(CandidateRuntimeError) as raised:
                Teacher(c).step(snapshot())
        self.assertEqual(raised.exception.function, "p")
        self.assertEqual(raised.exception.target, "p(cube)")
        self.assertIsInstance(raised.exception.__cause__, RuntimeError)
        self.assertIn("candidate failed", str(raised.exception))

    def test_predicate_bad_outputs(self) -> None:
        for expression in ("o.pos[:, :1]", "o.pos[:, 0] > 0", "o.pos[:, 0].long()", "0.5",
                           "torch.zeros(w.batch_size, device='meta')"):
            with self.subTest(expression=expression):
                source = DEFAULT_PREDICATES.replace("o.pos[:, 0]", expression)
                with candidate(predicates=source) as c, self.assertRaises(CandidateOutputError) as raised:
                    Teacher(c).step(snapshot())
                self.assertEqual(raised.exception.function, "p")
                self.assertEqual(raised.exception.target, "p(cube)")
                self.assertIn("expected floating Tensor", str(raised.exception))
                self.assertIn("got", str(raised.exception))
        source = DEFAULT_PREDICATES.replace("o.pos[:, 0]", "o.pos[:, 0].double()")
        with candidate(predicates=source) as c:
            self.assertEqual(Teacher(c).step(snapshot())["margin"].dtype, torch.float32)

    def test_predicate_mutation_detected_through_slice(self) -> None:
        source = DEFAULT_PREDICATES.replace("return o.pos[:, 0]", "o.pos.add_(1)\n    return o.pos[:, 0]")
        with candidate(predicates=source) as c, self.assertRaises(CandidateRuntimeError) as raised:
            Teacher(c).step(snapshot())
        self.assertEqual(raised.exception.function, "p")
        self.assertEqual(raised.exception.target, "p(cube)")
        self.assertIn("modified snapshot tensor bodies.cube.pose", str(raised.exception))
        self.assertIsNotNone(raised.exception.__cause__)

    def test_progress_errors_and_mutations(self) -> None:
        for body, error in [("raise ValueError('bad progress')", CandidateRuntimeError),
                            ("return o.cube.pos", CandidateOutputError),
                            ("return o.cube.pos[:, 0] > 0", CandidateOutputError),
                            ("w.table_z.add_(1)\n    return w.table_z", CandidateRuntimeError),
                            ("o.cube.pos.add_(1)\n    return w.table_z", CandidateRuntimeError)]:
            progress = "def progress_only(w, o):\n    " + body + "\n"
            with self.subTest(body=body), candidate(progress=progress) as c:
                with self.assertRaises(error) as raised:
                    Teacher(c).step(snapshot())
                self.assertEqual(raised.exception.function, "progress_only")
                self.assertEqual(raised.exception.target, "only")

    def test_all_stages_progress_evaluated(self) -> None:
        data = graph(stages=[{"name": "first", "exit": ["p(cube)"]}, {"name": "last", "exit": ["p(cube)"]}])
        with candidate(data=data, progress="def progress_last(w, o):\n    raise ValueError('last called')") as c:
            with self.assertRaisesRegex(CandidateRuntimeError, "last called"):
                Teacher(c).step(snapshot(cube=(-1, 0, 0)))

    def test_inference_tensors_without_version_are_supported(self) -> None:
        with torch.inference_mode():
            s = snapshot()
        with candidate() as c:
            self.assertEqual(Teacher(c).step(s)["stage"].tolist(), [0])

    def test_render_preserves_case_and_rejects_unknown_placeholders(self) -> None:
        source = DEFAULT_PREDICATES.replace('need_true="move {o}."', 'need_true="move {o} to TCP."')
        with candidate(predicates=source) as c:
            teacher = Teacher(c)
            output = teacher.step(snapshot(cube=(-1, 0, 0)))
            self.assertEqual(teacher.render(output, 0), ["Move the red cube to TCP."])
            c.predicates["p"].meta = replace(c.predicates["p"].meta, need_true="move {unknown}.")
            with self.assertRaisesRegex(ValueError, "unknown placeholder"):
                teacher.render(output, 0)
        data = graph(stages=[{"name": "only", "exit": ["not p(cube)"]}])
        with candidate(data=data) as c:
            teacher = Teacher(c)
            output = teacher.step(snapshot())
            c.predicates["p"].meta = replace(c.predicates["p"].meta, need_false=None)
            with self.assertRaisesRegex(ValueError, "missing need_false"):
                teacher.render(output, 0)
