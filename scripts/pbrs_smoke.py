#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
"""Check PBRS auto-reset and measure its cost in separate GPU 1 workers."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
PYTHON = "/home/zxh/anaconda3/envs/vpm-mani/bin/python"
sys.path.insert(0, str(ROOT))


def defaults() -> dict[str, float]:
    with (ROOT / "configs/default.yaml").open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)["pbrs"]


def run_worker(mode: str, gamma: float, r_bonus: float) -> dict[str, Any]:
    (ROOT / "outputs/tmp").mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "1",
                   "TMPDIR": str(ROOT / "outputs/tmp"),
                   "XDG_CACHE_HOME": str(ROOT / "outputs/cache"),
                   "MS_ASSET_DIR": str(ROOT / "outputs/maniskill"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        ["bash", "-c", 'ulimit -c 0; exec "$@"', "pbrs-worker", PYTHON,
         str(Path(__file__).resolve()), "--worker", mode,
         "--gamma", str(gamma), "--r-bonus", str(r_bonus)],
        cwd=ROOT, env=environment, text=True, capture_output=True, timeout=300)
    if result.returncode:
        raise RuntimeError(f"{mode} worker failed ({result.returncode}):\n{result.stdout}{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def smoke(gamma: float, r_bonus: float) -> dict[str, Any]:
    from unittest.mock import patch

    import torch
    from torch import Tensor
    from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv

    from vpmkit.adapters.maniskill import make_env
    from vpmkit.candidate import load_candidate
    from vpmkit.rewards import PBRSWrapper
    from vpmkit.world import Snapshot

    candidate = load_candidate(ROOT / "candidates/reference/PickCube-v1")
    wrapper = PBRSWrapper(make_env("PickCube-v1", 16), candidate, gamma, r_bonus)
    env = ManiSkillVectorEnv(wrapper, auto_reset=True, ignore_terminations=False)
    device = wrapper.device
    teacher_step = wrapper.teacher.step
    last_evaluation: dict[str, Tensor] = {}

    def record_step(snapshot: Snapshot, env_mask: Tensor | None = None) -> dict[str, Tensor]:
        out = teacher_step(snapshot, env_mask=env_mask)
        last_evaluation["phi"] = out["phi"].clone()
        last_evaluation["elapsed_steps"] = env.unwrapped.elapsed_steps.clone()
        last_evaluation["mask"] = (torch.ones(16, dtype=torch.bool, device=device)
                                   if env_mask is None else env_mask.clone())
        return out

    try:
        torch.manual_seed(0)
        with torch.no_grad(), patch.object(wrapper.teacher, "step", side_effect=record_step) as calls:
            env.reset(seed=0)
            assert torch.all(last_evaluation["elapsed_steps"] == 0)
            expected_prev = last_evaluation["phi"].clone()
            initial = expected_prev.double()
            discounted = torch.zeros(16, dtype=torch.float64, device=device)
            discount = torch.ones_like(discounted)
            resets = torch.zeros(16, dtype=torch.long, device=device)
            terminations = torch.zeros_like(resets)
            truncations = torch.zeros_like(resets)
            low = torch.as_tensor(env.action_space.low, device=device)
            high = torch.as_tensor(env.action_space.high, device=device)
            reset_batches = 0
            max_error = 0.0
            for _ in range(120):
                action = low + (high - low) * torch.rand(low.shape, device=device)
                _, reward, terminated, truncated, info = env.step(action)
                step_info = info.get("final_info", info)
                pbrs = step_info["pbrs"]
                assert reward.shape == (16,) and reward.dtype == torch.float32
                assert reward.device == wrapper.phi_prev.device
                assert torch.isfinite(reward).all()
                torch.testing.assert_close(pbrs["phi_prev"], expected_prev, rtol=0, atol=0)
                torch.testing.assert_close(pbrs["phi_used"], torch.where(terminated, 0.0, pbrs["phi"]),
                                           rtol=0, atol=0)
                shaping = gamma * pbrs["phi_used"] - pbrs["phi_prev"]
                torch.testing.assert_close(pbrs["shaping"], shaping, rtol=0, atol=0)
                torch.testing.assert_close(reward, shaping + step_info["success"] * r_bonus,
                                           rtol=0, atol=0)
                assert torch.all(pbrs["elapsed_steps"][truncated] == 50)
                discounted += discount * pbrs["shaping"].double()
                discount *= gamma
                endpoint = discount * pbrs["phi_used"].double() - initial
                error = (discounted - endpoint).abs().max().item()
                max_error = max(max_error, error)
                torch.testing.assert_close(discounted, endpoint, rtol=0, atol=1e-5)
                done = terminated | truncated
                expected_prev = pbrs["phi"].clone()
                if done.any():
                    reset_batches += 1
                    assert torch.equal(info["_final_info"], done)
                    assert torch.equal(last_evaluation["mask"], done)
                    assert torch.all(last_evaluation["elapsed_steps"][done] == 0)
                    assert torch.all(info["elapsed_steps"][done] == 0)
                    expected_prev[done] = last_evaluation["phi"][done]
                    torch.testing.assert_close(wrapper.phi_prev, expected_prev, rtol=0, atol=0)
                    initial[done] = expected_prev[done].double()
                    discounted[done] = 0
                    discount[done] = 1
                resets += done.long()
                terminations += terminated.long()
                truncations += truncated.long()
            assert torch.all(resets >= 2)
            assert truncations.sum() > 0
            assert calls.call_count == 121 + reset_batches
            return {"num_envs": 16, "steps": 120, "gamma": gamma, "r_bonus": r_bonus,
                    "episodes": resets.sum().item(), "terminated": terminations.sum().item(),
                    "truncated": truncations.sum().item(), "min_resets": resets.min().item(),
                    "max_resets": resets.max().item(), "max_telescope_error": max_error}
    finally:
        env.close()


def cost() -> dict[str, Any]:
    import torch

    from vpmkit.adapters.maniskill import ManiSkillAdapter, make_env
    from vpmkit.candidate import load_candidate
    from vpmkit.teacher import Teacher

    candidate = load_candidate(ROOT / "candidates/reference/PickCube-v1")
    warmup, measured = 10, 50
    env = make_env("PickCube-v1", 1024, max_episode_steps=warmup + measured)
    try:
        device = env.unwrapped.device
        adapter = ManiSkillAdapter(env, candidate.bind)
        teacher = Teacher(candidate, 1024, device)
        torch.manual_seed(0)
        with torch.no_grad():
            _, info = env.reset(seed=0)
            teacher.step(adapter.snapshot(info))
            low = torch.as_tensor(env.action_space.low, device=device)
            high = torch.as_tensor(env.action_space.high, device=device)
            env_seconds = teacher_seconds = 0.0
            for step in range(warmup + measured):
                action = low + (high - low) * torch.rand(low.shape, device=device)
                torch.cuda.synchronize(device)
                start = perf_counter()
                _, _, _, _, info = env.step(action)
                torch.cuda.synchronize(device)
                after_env = perf_counter()
                teacher.step(adapter.snapshot(info))
                torch.cuda.synchronize(device)
                after_teacher = perf_counter()
                if step >= warmup:
                    env_seconds += after_env - start
                    teacher_seconds += after_teacher - after_env
        return {"num_envs": 1024, "warmup": warmup, "steps": measured,
                "env_step_ms": env_seconds * 1000 / measured,
                "snapshot_teacher_ms": teacher_seconds * 1000 / measured}
    finally:
        env.close()


def main() -> int:
    config = defaults()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gamma", type=float, default=config["gamma"])
    parser.add_argument("--r-bonus", type=float, default=config["r_bonus"])
    parser.add_argument("--worker", choices=("smoke", "cost"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if os.environ.get("VPM_INTEGRATION") != "1":
        print("SKIP: set VPM_INTEGRATION=1 to run the GPU smoke and cost measurements.")
        return 0
    if args.worker:
        if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
            parser.error("workers require CUDA_VISIBLE_DEVICES=1")
        result = smoke(args.gamma, args.r_bonus) if args.worker == "smoke" else cost()
        print(json.dumps(result))
        return 0
    checked = run_worker("smoke", args.gamma, args.r_bonus)
    print(f"PBRS smoke: PASS (PickCube-v1, N=16, steps=120, "
          f"gamma={args.gamma:g}, r_bonus={args.r_bonus:g})", flush=True)
    print(f"Episodes: {checked['episodes']} (terminated={checked['terminated']}, "
          f"truncated={checked['truncated']}); resets/env={checked['min_resets']}..{checked['max_resets']}")
    print("Checks: float32 [16], finite rewards, reward identity, final elapsed_steps=50, reset Phi reuse")
    print(f"Max telescope error: {checked['max_telescope_error']:.3e} (tolerance 1e-5)", flush=True)
    measured = run_worker("cost", args.gamma, args.r_bonus)
    print(f"Cost: N={measured['num_envs']}, warm-up={measured['warmup']}, measured={measured['steps']} steps")
    print(f"  env.step: {measured['env_step_ms']:.3f} ms/step")
    print(f"  adapter.snapshot + teacher.step: {measured['snapshot_teacher_ms']:.3f} ms/step")
    return 0


if __name__ == "__main__":
    sys.exit(main())
