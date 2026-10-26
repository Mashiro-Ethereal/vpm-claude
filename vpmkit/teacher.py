"""Stateful process teachers and batched offline trajectory evaluation."""

from numbers import Real
from typing import Callable, Mapping, Sequence

import torch
from torch import Tensor

from .automaton import Automaton
from .candidate import Candidate
from .errors import CandidateOutputError, CandidateRuntimeError
from .literal import Literal, parse_literal
from .predicate import active_thresholds
from .world import Objects, Snapshot, World, make_views


class Teacher:
    def __init__(self, candidate: Candidate, num_envs: int = 1,
                 device: str | torch.device = "cpu", params: Mapping[str, float] | None = None) -> None:
        if isinstance(num_envs, bool) or not isinstance(num_envs, int) or num_envs < 1:
            raise ValueError("num_envs must be a positive integer")
        self.candidate = candidate
        graph = candidate.graph
        self.stage_names = [s.name for s in graph.stages]
        self.num_stages = len(self.stage_names)
        if not self.num_stages:
            raise ValueError("a teacher requires at least one stage")
        self.num_envs = num_envs
        self._stage = torch.zeros(num_envs, dtype=torch.long, device=device)
        self.device = self._stage.device
        self.params = graph.param_defaults()
        declarations = {param.name: param for param in graph.params}
        for name, value in (params or {}).items():
            if name != "runtime.debounce" and name not in declarations:
                raise ValueError(f"unknown parameter {name!r}")
            if isinstance(value, bool) or not isinstance(value, Real):
                raise ValueError(f"parameter {name!r} must be a number, not bool")
            if name != "runtime.debounce":
                low, high = declarations[name].range
                if not low <= value <= high:
                    raise ValueError(f"parameter {name!r} must be in [{low}, {high}], got {value}")
            self.params[name] = value
        debounce = self.params.get("runtime.debounce", 1)
        if (isinstance(debounce, bool) or not isinstance(debounce, Real)
                or not debounce >= 1 or debounce == float("inf") or int(debounce) != debounce):
            raise ValueError("runtime.debounce must be an integer >= 1")
        self.debounce = int(debounce)
        self._thresholds = {name: value for name, value in self.params.items()
                            if not name.startswith(("progress.", "runtime."))}
        self._progress_params = {
            stage: {name[len(f"progress.{stage}."):]: value for name, value in self.params.items()
                    if name.startswith(f"progress.{stage}.")}
            for stage in self.stage_names
        }
        for stage in candidate.progress:
            if stage not in self.stage_names:
                raise ValueError(f"progress function names unknown stage {stage!r}")

        self._instances: list[Literal] = []
        self._instance_columns: dict[tuple[str, tuple[str, ...]], int] = {}
        self._literals: list[Literal] = []
        literal_slots: dict[Literal, int] = {}

        def compile_literal(text: str) -> int:
            literal = parse_literal(text)
            if literal.predicate not in candidate.predicates:
                raise ValueError(f"{literal}: unknown predicate {literal.predicate!r}")
            meta = candidate.predicates[literal.predicate].meta
            if len(literal.args) != len(meta.object_params):
                raise ValueError(f"{literal}: expected {len(meta.object_params)} objects, got {len(literal.args)}")
            for key in literal.args:
                if key not in graph.objects:
                    raise ValueError(f"{literal}: undeclared object {key!r}")
            if literal.instance not in self._instance_columns:
                self._instance_columns[literal.instance] = len(self._instances)
                self._instances.append(literal)
            if literal not in literal_slots:
                literal_slots[literal] = len(self._literals)
                self._literals.append(literal)
            return literal_slots[literal]

        guards = []
        invariants = []
        self._guards: list[list[Literal]] = []
        for owner, stage in enumerate(graph.stages):
            if not stage.exit:
                raise ValueError(f"stage {stage.name!r} requires a non-empty guard")
            slots = [compile_literal(text) for text in stage.exit]
            guard = [self._literals[slot] for slot in slots]
            for literal in guard:
                if literal.negated and not candidate.predicates[literal.predicate].meta.need_false:
                    raise ValueError(f"{literal}: negated guard requires need_false")
            guards.append(slots)
            self._guards.append(guard)
            for invariant in stage.invariants:
                slot = compile_literal(invariant.literal)
                target = graph.stage_index(invariant.regress_to)
                if target >= owner:
                    raise ValueError(f"stage {stage.name!r}: regress target {invariant.regress_to!r} must be earlier")
                invariants.append((owner, slot, target))
        for official in graph.official:
            for text in official.literals:
                compile_literal(text)
        self.instances = [literal.instance_text for literal in self._instances]
        self._literal_columns = torch.tensor([self._instance_columns[lit.instance] for lit in self._literals],
                                              dtype=torch.long, device=self.device)
        self._negated = torch.tensor([lit.negated for lit in self._literals],
                                     dtype=torch.bool, device=self.device)
        self._scales = torch.tensor([candidate.predicates[lit.predicate].meta.scale for lit in self._literals],
                                    dtype=torch.float32, device=self.device)
        self._guard_slots = [torch.tensor(slots, dtype=torch.long, device=self.device) for slots in guards]
        self._positive_guards = torch.zeros((self.num_stages, len(self.instances)), dtype=torch.bool, device=self.device)
        self._negative_guards = torch.zeros_like(self._positive_guards)
        for k, guard in enumerate(self._guards):
            for literal in guard:
                mask = self._negative_guards if literal.negated else self._positive_guards
                mask[k, self._instance_columns[literal.instance]] = True
        self._automaton = Automaton(guards, invariants, len(self._literals), self.device)
        self._counters = torch.zeros((num_envs, len(invariants)), dtype=torch.long, device=self.device)

    @property
    def stage(self) -> Tensor:
        return self._stage

    def _check_snapshot(self, snapshot: Snapshot, check_batch: bool = False) -> None:
        if snapshot.device != self.device:
            raise ValueError(f"snapshot device must be {self.device}, got {snapshot.device}")
        if check_batch and snapshot.batch_size != self.num_envs:
            raise ValueError(f"snapshot batch_size must be {self.num_envs}, got {snapshot.batch_size}")

    def _call(self, snapshot: Snapshot, function: Callable, target: str,
              *args, **kwargs) -> Tensor:
        versions = []
        for name, tensor in snapshot._tensor_items():
            try:
                versions.append((name, tensor, tensor._version))
            except RuntimeError:
                pass  # Inference tensors have no version counter.
        function_name = function.__name__
        try:
            with active_thresholds(self._thresholds):
                result = function(*args, **kwargs)
        except Exception as exc:
            raise CandidateRuntimeError(function_name, target, str(exc)) from exc
        for name, tensor, version in versions:
            if tensor._version != version:
                exc = RuntimeError(f"modified snapshot tensor {name} in place")
                raise CandidateRuntimeError(function_name, target, str(exc)) from exc
        if (not isinstance(result, Tensor) or not result.is_floating_point()
                or result.shape != (snapshot.batch_size,) or result.device != snapshot.device):
            got = type(result).__name__
            if isinstance(result, Tensor):
                got += f" dtype={result.dtype}, shape={tuple(result.shape)}, device={result.device}"
            expected = f"floating Tensor with shape ({snapshot.batch_size},) on {snapshot.device}"
            raise CandidateOutputError(function_name, target, f"expected {expected}; got {got}")
        return result.to(torch.float32)

    def compute_margins(self, snapshot: Snapshot) -> Tensor:
        self._check_snapshot(snapshot)
        world, views, _ = make_views(snapshot)
        values = [self._call(snapshot, self.candidate.predicates[lit.predicate], lit.instance_text,
                             world, *(views[key] for key in lit.args)) for lit in self._instances]
        return torch.stack(values, dim=-1)

    def _literal_truth(self, margins: Tensor) -> Tensor:
        return (margins[:, self._literal_columns] >= 0) ^ self._negated

    def _progress_scores(self, margins: Tensor) -> Tensor:
        lit_true = self._literal_truth(margins)
        lit_margin = margins[:, self._literal_columns] * torch.where(self._negated, -1, 1)
        return torch.where(lit_true, 1.0, (1 + lit_margin / self._scales).clamp(0, 1))

    def _stage_progress(self, snapshot: Snapshot, k: int, scores: Tensor,
                        world: World, objects: Objects) -> Tensor:
        stage = self.stage_names[k]
        if stage in self.candidate.progress:
            return self._call(snapshot, self.candidate.progress[stage], stage,
                              world, objects, **self._progress_params[stage])
        return scores[:, self._guard_slots[k]].mean(-1)

    def compute_progress(self, snapshot: Snapshot, margins: Tensor) -> Tensor:
        self._check_snapshot(snapshot)
        world, _, objects = make_views(snapshot)
        scores = self._progress_scores(margins)
        progress = [self._stage_progress(snapshot, k, scores, world, objects)
                    for k in range(self.num_stages)]
        return torch.stack(progress, dim=-1)

    def _stage_values(self, stage: int | Tensor | None, count: int) -> Tensor:
        if stage is None:
            stage = 0
        if isinstance(stage, int) and not isinstance(stage, bool):
            if not 0 <= stage < self.num_stages:
                raise ValueError(f"stage must be in [0, {self.num_stages})")
            values = torch.full((count,), stage, dtype=torch.long, device=self.device)
        elif isinstance(stage, Tensor) and stage.dtype == torch.long and stage.shape == (count,):
            values = stage.to(self.device)
        else:
            raise ValueError(f"stage must be an int or a LongTensor with shape ({count},)")
        if torch.any((values < 0) | (values >= self.num_stages)):
            raise ValueError(f"stage must be in [0, {self.num_stages})")
        return values

    def reset(self, env_idx: Tensor | Sequence[int] | None = None,
              stage: int | Tensor | None = None) -> None:
        if env_idx is None:
            indices = torch.arange(self.num_envs, device=self.device)
        else:
            indices = torch.as_tensor(env_idx, device=self.device)
            if indices.numel() == 0 and not isinstance(env_idx, Tensor):
                indices = indices.long()
            if indices.ndim != 1 or indices.dtype != torch.long:
                raise ValueError("env_idx must be a 1-D LongTensor or sequence of integer indices")
            if torch.any((indices < 0) | (indices >= self.num_envs)):
                raise ValueError("env_idx contains an out-of-range environment index")
        self._stage[indices] = self._stage_values(stage, indices.shape[0])
        self._counters[indices] = 0

    def _output(self, stage: Tensor, margins: Tensor, lit_true: Tensor,
                progress: Tensor) -> dict[str, Tensor]:
        stage_progress = progress.gather(1, stage[:, None]).squeeze(1).clamp(0, 1)
        complete = (stage == self.num_stages - 1) & self._automaton.guard_holds(lit_true)[:, -1]
        stage_progress = torch.where(complete, 1.0, stage_progress)
        pred = margins >= 0
        guidance = ((self._positive_guards[stage] & ~pred)
                    | (self._negative_guards[stage] & pred))
        return {"stage": stage.clone(), "stage_progress": stage_progress,
                "phi": (stage + stage_progress) / self.num_stages,
                "pred": pred, "margin": margins, "guidance": guidance}

    def step(self, snapshot: Snapshot) -> dict[str, Tensor]:
        self._check_snapshot(snapshot, check_batch=True)
        margins = self.compute_margins(snapshot)
        lit_true = self._literal_truth(margins)
        self._stage, self._counters = self._automaton.step(self._stage, self._counters, lit_true, self.debounce)
        progress = self.compute_progress(snapshot, margins)
        return self._output(self._stage, margins, lit_true, progress)

    def evaluate_offline(self, snapshots: Sequence[Snapshot],
                         initial_stage: int | Tensor = 0) -> dict[str, Tensor]:
        if not snapshots:
            raise ValueError("evaluate_offline requires at least one snapshot")
        n = snapshots[0].batch_size
        for snapshot in snapshots:
            self._check_snapshot(snapshot)
            if snapshot.batch_size != n:
                raise ValueError("offline snapshots must have the same batch_size")
        combined = Snapshot.cat(snapshots)
        margins = self.compute_margins(combined)
        progress = self.compute_progress(combined, margins).reshape(len(snapshots), n, self.num_stages)
        lit_true = self._literal_truth(margins).reshape(len(snapshots), n, -1)
        margins = margins.reshape(len(snapshots), n, -1)
        stage = self._stage_values(initial_stage, n)
        counters = torch.zeros((n, self._automaton.num_invariants), dtype=torch.long, device=self.device)
        outputs = []
        for t in range(len(snapshots)):
            stage, counters = self._automaton.step(stage, counters, lit_true[t], self.debounce)
            outputs.append(self._output(stage, margins[t], lit_true[t], progress[t]))
        return {key: torch.stack([output[key] for output in outputs]) for key in outputs[0]}

    def render(self, output: dict[str, Tensor], i: int) -> list[str]:
        from .render import render

        return render(self, output, i)
