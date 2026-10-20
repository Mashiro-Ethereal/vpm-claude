from dataclasses import fields, replace
import unittest
from unittest.mock import patch

import torch

from tests import TOY, world
from vpmkit.artifact.loader import load_candidate
from vpmkit.runtime.teacher import Teacher, TeacherError, TeacherOutput
from vpmkit.world import WorldState


class TeacherTests(unittest.TestCase):
    def setUp(self):
        self.candidate = load_candidate(TOY)

    def test_instances_margins_phi_and_default_progress(self):
        teacher = Teacher(self.candidate, 2)
        self.assertEqual(teacher.instance_keys, ("gripper_open(g)", "near(g, block)",
                                                "grasped(g, block)", "in_region(block, region)"))
        out = teacher.step(world(2, block_x=[0.2, 0.05]))
        self.assertEqual(out.stage.tolist(), [0, 1])
        torch.testing.assert_close(out.stage_progress, torch.tensor([0.75, 0.]))
        torch.testing.assert_close(out.phi, torch.tensor([0.1875, 0.25]))
        torch.testing.assert_close(out.margin[:, 2], torch.tensor([-1., -1.]))
        self.assertEqual(out.margin.dtype, torch.float32)
        self.assertEqual(out.value.dtype, torch.bool)
        self.assertEqual(out.need_true.tolist(), [[False, True, False, False], [False, False, True, False]])
        self.assertFalse(out.need_false.any())
        self.assertEqual(teacher.render_guidance(out, 0), ["Move gripper near block."])
        self.assertEqual(teacher.render_guidance(out, 1), ["Grasp block with gripper."])

    def test_custom_progress_raw_clamping_and_params(self):
        teacher = Teacher(self.candidate, 2)
        teacher.reset(stage=2)
        out = teacher.step(world(2, block_x=[0.2, 0.75], held=True))
        self.assertEqual(out.stage.tolist(), [2, 2])
        torch.testing.assert_close(out.progress_raw[:, 2], torch.tensor([-0.5, 0.6]))
        torch.testing.assert_close(out.stage_progress, torch.tensor([0., 0.6]))
        torch.testing.assert_close(out.phi, torch.tensor([0.5, 0.65]))
        changed = Teacher(self.candidate.with_params({"progress.carry.span": 1.0}), 1)
        changed.reset(stage=2)
        out = changed.step(world(block_x=0.75, held=True))
        torch.testing.assert_close(out.stage_progress, torch.tensor([0.8]))
        saturated = replace(self.candidate, progress={
            "carry": lambda w, o, **kw: torch.full((w.N,), 2.0, device=w.device),
        })
        teacher = Teacher(saturated, 1)
        teacher.reset(stage=2)
        out = teacher.step(world(held=True))
        self.assertEqual(out.stage.tolist(), [2])
        torch.testing.assert_close(out.progress_raw[:, 2], torch.tensor([2.]))
        torch.testing.assert_close(out.stage_progress, torch.tensor([1.]))

    def test_guidance_in_literal_order_and_negative_literal(self):
        teacher = Teacher(self.candidate, 1)
        teacher.reset(stage=3)
        out = teacher.step(world(block_x=0.2, held=True))
        self.assertEqual(out.need_true.tolist(), [[False, False, False, True]])
        self.assertEqual(out.need_false.tolist(), [[False, False, True, False]])
        self.assertEqual(teacher.render_guidance(out, 0), ["Move block into target region.", "Release block from gripper."])
        out = teacher.step(world(block_x=1., held=True))
        torch.testing.assert_close(out.stage_progress, torch.tensor([0.5]))
        torch.testing.assert_close(out.phi, torch.tensor([0.875]))
        out = teacher.step(world(block_x=1., held=False))
        self.assertTrue(out.done.all())
        self.assertEqual(out.stage.tolist(), [4])
        torch.testing.assert_close(out.stage_progress, torch.tensor([0.]))
        torch.testing.assert_close(out.phi, torch.tensor([1.]))
        self.assertFalse(out.need_true.any())
        self.assertFalse(out.need_false.any())
        self.assertEqual(teacher.render_guidance(out, 0), [])

    def test_carry_and_done_regression_events(self):
        teacher = Teacher(self.candidate, 1)
        teacher.reset(stage=2)
        self.assertFalse(teacher.step(world()).regressed.any())
        out = teacher.step(world())
        self.assertEqual(out.stage.tolist(), [1])
        self.assertTrue(out.regressed.all())
        self.assertEqual(teacher.render_event(out.event[0]), "Regrasp block with gripper.")
        teacher.reset(stage=3)
        teacher.step(world(block_x=1., held=False))
        self.assertEqual(teacher.step(world(block_x=1., held=True)).stage.tolist(), [4])
        out = teacher.step(world(block_x=1., held=True))
        self.assertEqual(out.stage.tolist(), [3])
        self.assertEqual(teacher.render_event(out.event[0]), "Release block from gripper.")
        teacher.reset(stage=4)
        teacher.step(world(block_x=0., held=True))
        out = teacher.step(world(block_x=0., held=True))
        self.assertEqual(teacher.render_event(out.event[0]), "Move block into target region.")
        self.assertEqual(teacher.render_event(-1), "")

    def test_done_also_keeps_last_stage_invariants(self):
        graph = self.candidate.graph.model_copy(deep=True)
        graph.stages[-1].invariants = [graph.stages[2].invariants[0].model_copy(deep=True)]
        teacher = Teacher(replace(self.candidate, graph=graph), 1)
        teacher.reset(stage=4)
        teacher.step(world(block_x=0., held=False))
        out = teacher.step(world(block_x=0., held=False))
        self.assertEqual(out.stage.tolist(), [1])
        self.assertEqual(teacher.render_event(out.event[0]), "Regrasp block with gripper.")

    def test_with_params_changes_threshold_effect(self):
        original = Teacher(self.candidate, 1)
        changed = Teacher(self.candidate.with_params({"near.max_dist": 0.3}), 1)
        self.assertEqual(original.step(world()).stage.tolist(), [0])
        self.assertEqual(changed.step(world()).stage.tolist(), [1])

    def test_reset_mask_and_output_snapshot(self):
        teacher = Teacher(self.candidate, 2)
        teacher.reset(stage=2)
        out = teacher.step(world(2))
        self.assertEqual(teacher.counters[:, 0].tolist(), [1, 1])
        teacher.reset(torch.tensor([True, False]), stage=1)
        self.assertEqual(teacher.stage.tolist(), [1, 2])
        self.assertEqual(teacher.counters[:, 0].tolist(), [0, 1])
        self.assertEqual(out.stage.tolist(), [2, 2])
        teacher.reset()
        self.assertEqual(teacher.stage.tolist(), [0, 0])
        self.assertFalse(teacher.counters.any())
        with self.assertRaises(ValueError):
            teacher.reset(stage=5)

    def test_sequence_matches_frame_steps_for_all_output_fields(self):
        frames = [world(block_x=0.2), world(block_x=0.05), world(block_x=0.2, held=True),
                  world(block_x=0.4), world(block_x=0.5, held=True), world(block_x=0.6),
                  world(block_x=0.6), world(block_x=1., held=True), world(block_x=1.),
                  world(block_x=0.2), world(block_x=0.2), world(block_x=1.)]
        ws = WorldState.cat(frames)
        sequential, batched = Teacher(self.candidate, 1), Teacher(self.candidate, 3)
        sequential.reset()
        expected = [sequential.step(frame) for frame in frames]
        batched.reset(stage=2)
        with patch.object(batched, "evaluate", wraps=batched.evaluate) as evaluate:
            actual = batched.run_sequence(ws)
        self.assertEqual(evaluate.call_count, 1)
        self.assertEqual(batched.stage.tolist(), [2, 2, 2])
        for field in fields(TeacherOutput):
            with self.subTest(field=field.name):
                torch.testing.assert_close(getattr(actual, field.name),
                                           torch.cat([getattr(out, field.name) for out in expected]), rtol=0, atol=0)

    def test_sequence_initial_stage_and_empty_frames(self):
        teacher = Teacher(self.candidate, 1)
        ws = WorldState.cat([world(), world()])
        out = teacher.run_sequence(ws, initial_stage=2)
        self.assertEqual(out.stage.tolist(), [2, 1])
        empty = ws.index(torch.empty(0, dtype=torch.long))
        out = teacher.run_sequence(empty)
        self.assertEqual(out.stage.shape, (0,))
        self.assertEqual(out.progress_raw.shape, (0, 4))

    def test_invalid_predicate_results_name_instance(self):
        for result in [torch.tensor([float("nan")]), torch.tensor([float("inf")]),
                       torch.zeros(1, 1), torch.tensor(1.0), True]:
            predicates = dict(self.candidate.predicates)
            predicates["near"] = lambda *args, _result=result, **kwargs: _result
            teacher = Teacher(replace(self.candidate, predicates=predicates), 1)
            with self.subTest(result=result), self.assertRaisesRegex(TeacherError, r"near\(g, block\)"):
                teacher.step(world())

    def test_invalid_custom_progress_and_batch_size(self):
        candidate = replace(self.candidate, progress={"carry": lambda w, o, **kw: torch.tensor([float("nan")])})
        teacher = Teacher(candidate, 1)
        with self.assertRaisesRegex(TeacherError, "progress_carry"):
            teacher.step(world())
        with self.assertRaisesRegex(TeacherError, "N=1"):
            teacher.step(world(2))

    def test_zero_margin_is_true_and_evaluate_is_stateless(self):
        teacher = Teacher(self.candidate, 1)
        margin, value = teacher.evaluate(world(block_x=0.1, width=0.04))
        self.assertEqual(margin[0, :2].tolist(), [0., 0.])
        self.assertEqual(value[0, :2].tolist(), [True, True])
        self.assertEqual(teacher.stage.tolist(), [0])

    def test_official_only_instances_are_evaluated_after_invariants(self):
        graph = self.candidate.graph.model_copy(deep=True)
        graph.official[0].literals.append("gripper_open(g)")
        graph.stages[0].exit = ["near(g, block)"]
        graph.stages[2].invariants[0].literal = "near(block, region)"
        teacher = Teacher(replace(self.candidate, graph=graph), 1)
        self.assertEqual(teacher.instance_keys, ("near(g, block)", "grasped(g, block)",
                                                "in_region(block, region)", "near(block, region)", "gripper_open(g)"))
