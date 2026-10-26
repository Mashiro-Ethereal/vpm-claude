"""Pure batched updates of a linear stage chain."""

from typing import Sequence

import torch
from torch import Tensor


class Automaton:
    """Compile guards as literal-slot lists and invariants as (owner, slot, target)."""

    def __init__(self, guards: Sequence[Sequence[int]],
                 invariants: Sequence[tuple[int, int, int]], num_literals: int,
                 device: str | torch.device = "cpu") -> None:
        if not guards or any(not guard for guard in guards):
            raise ValueError("the chain must contain stages with non-empty guards")
        self.num_stages = len(guards)
        self.num_invariants = len(invariants)
        if any(not 0 <= slot < num_literals for guard in guards for slot in guard):
            raise ValueError("guard literal slot out of range")
        if any(not (0 <= target < owner < self.num_stages and 0 <= slot < num_literals)
               for owner, slot, target in invariants):
            raise ValueError("invariants require valid literal slots and targets earlier than their owner")
        width = max(map(len, guards))
        self._guard_slots = torch.tensor([list(g) + [0] * (width - len(g)) for g in guards],
                                         dtype=torch.long, device=device)
        self._guard_mask = torch.tensor([[True] * len(g) + [False] * (width - len(g)) for g in guards],
                                        dtype=torch.bool, device=device)
        self._owners = torch.tensor([x[0] for x in invariants], dtype=torch.long, device=device)
        self._slots = torch.tensor([x[1] for x in invariants], dtype=torch.long, device=device)
        self._targets = torch.tensor([x[2] for x in invariants], dtype=torch.long, device=device)

    def guard_holds(self, lit_true: Tensor) -> Tensor:
        return (lit_true[:, self._guard_slots] | ~self._guard_mask).all(-1)

    def step(self, stage: Tensor, counters: Tensor, lit_true: Tensor,
             debounce: int = 1) -> tuple[Tensor, Tensor]:
        if isinstance(debounce, bool) or not isinstance(debounce, int) or debounce < 1:
            raise ValueError("debounce must be an integer >= 1")
        active_false = (stage[:, None] == self._owners) & ~lit_true[:, self._slots]
        new_counters = torch.where(active_false, counters + 1, 0)
        if self.num_invariants:
            target = torch.where(new_counters >= debounce, self._targets, self.num_stages).amin(-1)
            regressed = target < self.num_stages
            new_stage = torch.where(regressed, target, stage)
        else:
            regressed = torch.zeros_like(stage, dtype=torch.bool)
            new_stage = stage.clone()
        guards = self.guard_holds(lit_true)
        for k in range(self.num_stages - 1):
            new_stage = new_stage + ((new_stage == k) & guards[:, k]).long()
        reset = regressed | (new_stage != stage)
        new_counters = torch.where(reset[:, None], 0, new_counters)
        return new_stage, new_counters
