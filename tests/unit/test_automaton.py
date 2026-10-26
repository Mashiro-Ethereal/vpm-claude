"""Direct truth-table tests of stage transition and debounce semantics."""

import unittest

import torch

from vpmkit.automaton import Automaton


class AutomatonTest(unittest.TestCase):
    def setUp(self) -> None:
        # Slots: near, grasped, at_goal, arm_static.
        self.pick = Automaton([[0], [1], [2], [3]], [(1, 0, 0), (2, 1, 0), (3, 2, 2)], 4)
        # Slots: near, grasped, on, not grasped, static.
        self.stack = Automaton([[0], [1], [2], [3, 4]], [(1, 0, 0), (2, 1, 0), (3, 2, 0)], 5)

    def test_pick_slip_near_and_far(self) -> None:
        truth = torch.tensor([[True, False, False, False], [False, False, False, False]])
        stages, counters = self.pick.step(torch.tensor([2, 2]), torch.zeros(2, 3, dtype=torch.long), truth)
        self.assertEqual(stages.tolist(), [1, 0])
        self.assertEqual(counters.tolist(), [[0, 0, 0], [0, 0, 0]])
        self.assertEqual((~truth[0, [1]]).tolist(), [True])
        self.assertEqual((~truth[1, [0]]).tolist(), [True])

    def test_all_guards_advance_to_last_and_stop(self) -> None:
        stage = torch.tensor([0, 1, 2, 3])
        counters = torch.zeros(4, 3, dtype=torch.long)
        truth = torch.ones(4, 4, dtype=torch.bool)
        result, counts = self.pick.step(stage, counters, truth)
        self.assertEqual(result.tolist(), [3, 3, 3, 3])
        self.assertTrue(torch.equal(stage, torch.tensor([0, 1, 2, 3])))
        self.assertTrue(torch.equal(counters, counts))
        self.assertTrue(self.pick.guard_holds(truth).all())

    def test_earliest_of_multiple_regress_targets(self) -> None:
        automaton = Automaton([[0], [1], [2], [3]], [(3, 4, 2), (3, 5, 0)], 6)
        stage, _ = automaton.step(torch.tensor([3]), torch.zeros(1, 2, dtype=torch.long),
                                  torch.zeros(1, 6, dtype=torch.bool))
        self.assertEqual(stage.tolist(), [0])

    def test_new_stage_invariants_start_next_step(self) -> None:
        automaton = Automaton([[0], [1]], [(1, 2, 0)], 3)
        truth = torch.tensor([[True, False, False]])
        stage, counters = automaton.step(torch.tensor([0]), torch.zeros(1, 1, dtype=torch.long), truth, 2)
        self.assertEqual(stage.tolist(), [1])
        self.assertEqual(counters.tolist(), [[0]])
        stage, counters = automaton.step(stage, counters, truth, 2)
        self.assertEqual(counters.tolist(), [[1]])
        stage, counters = automaton.step(stage, counters, truth, 2)
        self.assertEqual(stage.tolist(), [1])
        self.assertEqual(counters.tolist(), [[0]])

    def test_debounce_false_true_false_false(self) -> None:
        stage = torch.tensor([2])
        counters = torch.zeros(1, 3, dtype=torch.long)
        false = torch.tensor([[False, False, False, False]])
        true = torch.tensor([[False, True, False, False]])
        stage, counters = self.pick.step(stage, counters, false, 2)
        self.assertEqual(stage.tolist(), [2])
        self.assertEqual(counters.tolist(), [[0, 1, 0]])
        stage, counters = self.pick.step(stage, counters, true, 2)
        self.assertEqual(counters.tolist(), [[0, 0, 0]])
        stage, counters = self.pick.step(stage, counters, false, 2)
        self.assertEqual(stage.tolist(), [2])
        stage, counters = self.pick.step(stage, counters, false, 2)
        self.assertEqual(stage.tolist(), [0])
        self.assertEqual(counters.tolist(), [[0, 0, 0]])

    def test_counter_reset_on_advance_and_inactive_invariants(self) -> None:
        stage, counters = self.pick.step(torch.tensor([1]), torch.tensor([[0, 9, 8]]),
                                         torch.tensor([[False, True, False, False]]), 2)
        self.assertEqual(stage.tolist(), [2])
        self.assertEqual(counters.tolist(), [[0, 0, 0]])
        stage, counters = self.pick.step(stage, counters, torch.tensor([[False, False, False, False]]), 2)
        self.assertEqual(counters.tolist(), [[0, 1, 0]])

    def test_regress_then_walk_forward(self) -> None:
        truth = torch.tensor([[True, True, False, False, True],
                              [True, False, False, True, True],
                              [False, False, False, True, True]])
        stage, counters = self.stack.step(torch.tensor([3, 3, 3]), torch.zeros(3, 3, dtype=torch.long), truth)
        self.assertEqual(stage.tolist(), [2, 1, 0])
        self.assertTrue((counters == 0).all())

    def test_stack_release_guards(self) -> None:
        truth = torch.tensor([[True, True, True, False, True],
                              [True, False, True, True, False],
                              [True, False, True, True, True]])
        stage, _ = self.stack.step(torch.full((3,), 3), torch.zeros(3, 3, dtype=torch.long), truth)
        self.assertEqual(stage.tolist(), [3, 3, 3])
        self.assertEqual((~truth[:, [3, 4]]).tolist(), [[True, False], [False, True], [False, False]])
        self.assertEqual(self.stack.guard_holds(truth)[:, -1].tolist(), [False, False, True])

    def test_without_invariants_and_invalid_compiled_spec(self) -> None:
        automaton = Automaton([[0]], [], 1)
        stage, counters = automaton.step(torch.zeros(2, dtype=torch.long), torch.zeros(2, 0, dtype=torch.long),
                                         torch.ones(2, 1, dtype=torch.bool))
        self.assertEqual(stage.tolist(), [0, 0])
        self.assertEqual(counters.shape, (2, 0))
        for guards, invariants, size in [([], [], 1), ([[]], [], 1), ([[1]], [], 1), ([[0]], [(0, 0, 0)], 1)]:
            with self.assertRaises(ValueError):
                Automaton(guards, invariants, size)
        with self.assertRaises(ValueError):
            automaton.step(stage, counters, torch.ones(2, 1, dtype=torch.bool), 0)
