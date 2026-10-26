#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
# Adapted from ManiSkill examples/baselines/sac/sac.py (Apache-2.0).
"""Train state-based SAC with a Stage1 teacher, dense reward, or sparse reward."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from importlib.metadata import version
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
for name, folder in (("XDG_CACHE_HOME", "cache"), ("MS_ASSET_DIR", "maniskill"),
                     ("TMPDIR", "tmp")):
    directory = REPO_ROOT / "outputs" / folder
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[name] = str(directory)

import gymnasium as gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import yaml

from scripts.ppo_check import evaluate, log_evaluation
from vpmkit.candidate import load_candidate
from vpmkit.rewards import PBRSWrapper


def parse_args() -> argparse.Namespace:
    defaults = yaml.safe_load((REPO_ROOT / "configs/default.yaml").read_text())["pbrs"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", default="PickCube-v1")
    parser.add_argument("--reward", choices=("teacher", "dense", "sparse"), required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--total-timesteps", type=int, default=1_000_000)
    parser.add_argument("--num-envs", type=int, default=32)
    parser.add_argument("--control-mode", default="pd_ee_delta_pos")
    parser.add_argument("--buffer-size", type=int, default=500_000)
    parser.add_argument("--buffer-device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--gamma", type=float, default=0.8)
    parser.add_argument("--r-bonus", type=float, default=defaults["r_bonus"])
    parser.add_argument("--phi-unnormalized", action="store_true")
    parser.add_argument("--tau", type=float, default=0.01)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--learning-starts", type=int, default=4_000)
    parser.add_argument("--policy-lr", type=float, default=3e-4)
    parser.add_argument("--q-lr", type=float, default=3e-4)
    parser.add_argument("--policy-frequency", type=int, default=1)
    parser.add_argument("--target-network-frequency", type=int, default=1)
    parser.add_argument("--alpha", type=float, default=0.2)
    parser.add_argument("--autotune", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--torch-deterministic", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--training-freq", type=int, default=64)
    parser.add_argument("--utd", type=float, default=0.5)
    parser.add_argument("--bootstrap-at-done", choices=("truncated", "always", "never"), default="truncated")
    parser.add_argument("--log-freq", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--eval-seed", type=int)
    parser.add_argument("--eval-resets", type=int, default=8)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--track", action="store_true")
    parser.add_argument("--wandb-project", default="vpm-stage1")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-group")
    parser.add_argument("--wandb-mode", choices=("online", "offline", "disabled"), default="online")
    parser.add_argument("--run-name")
    args = parser.parse_args()
    if args.reward == "teacher" and args.candidate is None:
        parser.error("--candidate is required for --reward teacher")
    if min(args.num_envs, args.total_timesteps, args.training_freq, args.batch_size,
           args.policy_frequency, args.target_network_frequency, args.log_freq, args.eval_resets) < 1:
        parser.error("environment, step, batch, frequency, and evaluation counts must be positive")
    if args.training_freq % args.num_envs or args.buffer_size < args.num_envs:
        parser.error("training-freq must be divisible by num-envs; buffer-size must hold at least one batch of environments")
    args.steps_per_env = args.training_freq // args.num_envs
    args.grad_steps_per_iteration = int(args.training_freq * args.utd)
    if args.grad_steps_per_iteration < 1:
        parser.error("training-freq * utd must give at least one gradient update")
    if args.eval_seed is None:
        args.eval_seed = args.seed + 10_000
    if args.out is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        args.out = REPO_ROOT / "outputs/stage1/ppo_check" / f"{args.env_id}-{args.reward}-sac-seed{args.seed}-{stamp}"
    args.out = args.out.resolve()
    if args.candidate is not None:
        args.candidate = args.candidate.resolve()
    if args.run_name is None:
        args.run_name = args.out.name
    return args


def replay_transition(next_obs: torch.Tensor, terminated: torch.Tensor,
                      truncated: torch.Tensor, info: dict[str, Any],
                      bootstrap_at_done: str = "truncated") -> tuple[torch.Tensor, torch.Tensor]:
    """Store final observations for bootstrapped endings, never auto-reset observations."""
    done = terminated | truncated
    if bootstrap_at_done == "always":
        stop_bootstrap = torch.zeros_like(done)
    elif bootstrap_at_done == "never":
        stop_bootstrap = done
    else:
        stop_bootstrap = terminated
    real_next_obs = next_obs.clone()
    need_final_obs = done & ~stop_bootstrap
    if "final_observation" in info:
        real_next_obs[need_final_obs] = info["final_observation"][need_final_obs]
    return real_next_obs, stop_bootstrap


@dataclass
class ReplayBufferSample:
    obs: torch.Tensor
    next_obs: torch.Tensor
    actions: torch.Tensor
    rewards: torch.Tensor
    dones: torch.Tensor


class ReplayBuffer:
    def __init__(self, env: Any, num_envs: int, buffer_size: int,
                 storage_device: torch.device, sample_device: torch.device) -> None:
        self.pos = 0
        self.full = False
        self.num_envs = num_envs
        self.storage_device = storage_device
        self.sample_device = sample_device
        self.per_env_buffer_size = buffer_size // num_envs
        shape = (self.per_env_buffer_size, num_envs)
        self.obs = torch.zeros(shape + env.single_observation_space.shape, device=storage_device)
        self.next_obs = torch.zeros_like(self.obs)
        self.actions = torch.zeros(shape + env.single_action_space.shape, device=storage_device)
        self.rewards = torch.zeros(shape, device=storage_device)
        self.dones = torch.zeros(shape, device=storage_device)

    def add(self, obs: torch.Tensor, next_obs: torch.Tensor, actions: torch.Tensor,
            rewards: torch.Tensor, dones: torch.Tensor) -> None:
        self.obs[self.pos] = obs.to(self.storage_device)
        self.next_obs[self.pos] = next_obs.to(self.storage_device)
        self.actions[self.pos] = actions.to(self.storage_device)
        self.rewards[self.pos] = rewards.to(self.storage_device)
        self.dones[self.pos] = dones.to(self.storage_device)
        self.pos += 1
        if self.pos == self.per_env_buffer_size:
            self.full = True
            self.pos = 0

    def sample(self, batch_size: int) -> ReplayBufferSample:
        upper = self.per_env_buffer_size if self.full else self.pos
        batch_inds = torch.randint(0, upper, (batch_size,))
        env_inds = torch.randint(0, self.num_envs, (batch_size,))
        return ReplayBufferSample(
            obs=self.obs[batch_inds, env_inds].to(self.sample_device),
            next_obs=self.next_obs[batch_inds, env_inds].to(self.sample_device),
            actions=self.actions[batch_inds, env_inds].to(self.sample_device),
            rewards=self.rewards[batch_inds, env_inds].to(self.sample_device),
            dones=self.dones[batch_inds, env_inds].to(self.sample_device),
        )


class SoftQNetwork(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(np.array(env.single_observation_space.shape).prod() + np.prod(env.single_action_space.shape), 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
        )

    def forward(self, x, a):
        x = torch.cat([x, a], 1)
        return self.net(x)


LOG_STD_MAX = 2
LOG_STD_MIN = -5


class Actor(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(np.array(env.single_observation_space.shape).prod(), 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
        )
        self.fc_mean = nn.Linear(256, np.prod(env.single_action_space.shape))
        self.fc_logstd = nn.Linear(256, np.prod(env.single_action_space.shape))
        # action rescaling
        h, l = env.single_action_space.high, env.single_action_space.low
        self.register_buffer("action_scale", torch.tensor((h - l) / 2.0, dtype=torch.float32))
        self.register_buffer("action_bias", torch.tensor((h + l) / 2.0, dtype=torch.float32))

    def forward(self, x):
        x = self.backbone(x)
        mean = self.fc_mean(x)
        log_std = self.fc_logstd(x)
        log_std = torch.tanh(log_std)
        log_std = LOG_STD_MIN + 0.5 * (LOG_STD_MAX - LOG_STD_MIN) * (log_std + 1)  # From SpinUp / Denis Yarats

        return mean, log_std

    def get_eval_action(self, x):
        x = self.backbone(x)
        mean = self.fc_mean(x)
        action = torch.tanh(mean) * self.action_scale + self.action_bias
        return action

    def get_action(self, x, deterministic=False):
        if deterministic:
            return self.get_eval_action(x)
        mean, log_std = self(x)
        std = log_std.exp()
        normal = torch.distributions.Normal(mean, std)
        x_t = normal.rsample()  # for reparameterization trick (mean + std * N(0,1))
        y_t = torch.tanh(x_t)
        action = y_t * self.action_scale + self.action_bias
        log_prob = normal.log_prob(x_t)
        # Enforcing Action Bound
        log_prob -= torch.log(self.action_scale * (1 - y_t.pow(2)) + 1e-6)
        log_prob = log_prob.sum(1, keepdim=True)
        mean = torch.tanh(mean) * self.action_scale + self.action_bias
        return action, log_prob, mean


def evaluate_resets(actor: Actor, envs: Any, seed: int, max_episode_steps: int,
                    stage_names: list[str], num_resets: int = 8) -> dict[str, Any]:
    batches = [evaluate(actor, envs, seed + index, max_episode_steps, stage_names)
               for index in range(num_resets)]
    result = {"seed": seed, "seeds": list(range(seed, seed + num_resets)),
              "episodes": envs.num_envs * num_resets, "max_episode_steps": max_episode_steps}
    for key in ("success_once", "success_at_end", "length_mean"):
        result[key] = sum(batch[key] for batch in batches) / num_resets
    result["per_environment"] = [
        dict(row, reset_index=index, seed=seed + index)
        for index, batch in enumerate(batches) for row in batch["per_environment"]
    ]
    if stage_names:
        teacher = {}
        for key in ("first_success_stage_histogram", "unsuccessful_end_stage_histogram"):
            teacher[key] = {name: sum(batch["teacher"][key][name] for batch in batches)
                            for name in stage_names}
        counts = teacher["first_success_stage_histogram"]
        successes = sum(counts.values())
        teacher["first_success_last_stage_fraction"] = counts[stage_names[-1]] / successes if successes else None
        result["teacher"] = teacher
    return result


def train(args: argparse.Namespace, envs: Any, stage_names: list[str],
          wandb: Any) -> tuple[Actor, dict[str, Any], int]:
    device = envs.device
    actor = Actor(envs).to(device)
    qf1, qf2 = SoftQNetwork(envs).to(device), SoftQNetwork(envs).to(device)
    qf1_target, qf2_target = SoftQNetwork(envs).to(device), SoftQNetwork(envs).to(device)
    qf1_target.load_state_dict(qf1.state_dict())
    qf2_target.load_state_dict(qf2.state_dict())
    q_optimizer = optim.Adam(list(qf1.parameters()) + list(qf2.parameters()), lr=args.q_lr)
    actor_optimizer = optim.Adam(actor.parameters(), lr=args.policy_lr)
    log_alpha = None
    if args.autotune:
        target_entropy = -float(np.prod(envs.single_action_space.shape))
        log_alpha = torch.zeros(1, requires_grad=True, device=device)
        alpha = log_alpha.exp().item()
        a_optimizer = optim.Adam([log_alpha], lr=args.q_lr)
    else:
        alpha = args.alpha
    rb = ReplayBuffer(envs, args.num_envs, args.buffer_size, torch.device(args.buffer_device), device)
    global_step, global_update, last_log_step = 0, 0, 0
    learning_has_started = False
    episode_metrics = defaultdict(list)
    phi_sum, shaping_sum, reward_sum = (torch.zeros((), device=device) for _ in range(3))
    stage_counts = torch.zeros(len(stage_names), dtype=torch.long, device=device)
    stage_ones = torch.ones(args.num_envs, dtype=torch.long, device=device)
    losses = {}
    interval_rollout_time, interval_update_time = 0.0, 0.0
    total_rollout_time, total_update_time = 0.0, 0.0
    low = torch.as_tensor(envs.single_action_space.low, device=device)
    high = torch.as_tensor(envs.single_action_space.high, device=device)
    start_time = time.perf_counter()
    obs, _ = envs.reset(seed=args.seed)
    print(f"Training {args.total_timesteps} transitions; bootstrap_at_done={args.bootstrap_at_done}; "
          f"updates_per_iteration={args.grad_steps_per_iteration}", flush=True)
    while global_step < args.total_timesteps:
        rollout_start = time.perf_counter()
        for _ in range(args.steps_per_env):
            global_step += args.num_envs
            with torch.no_grad():
                if not learning_has_started:
                    actions = low + (high - low) * torch.rand(envs.action_space.shape, device=device)
                else:
                    actions, _, _ = actor.get_action(obs)
            next_obs, rewards, terminated, truncated, info = envs.step(actions)
            real_next_obs, stop_bootstrap = replay_transition(
                next_obs, terminated, truncated, info, args.bootstrap_at_done)
            rb.add(obs, real_next_obs, actions, rewards, stop_bootstrap)
            obs = next_obs
            reward_sum += rewards.sum()
            step_info = info.get("final_info", info)
            if stage_names:
                pbrs = step_info["pbrs"]
                phi_sum += pbrs["phi_teacher"].sum()
                shaping_sum += pbrs["shaping"].sum()
                stage_counts.scatter_add_(0, pbrs["stage"], stage_ones)
            if "final_info" in info:
                done_mask = info["_final_info"]
                episode = step_info["episode"]
                for key in ("success_once", "return", "episode_len"):
                    episode_metrics[key].append(episode[key][done_mask])
                episode_metrics["success_at_end"].append(step_info["success"][done_mask])
        rollout_time = time.perf_counter() - rollout_start
        interval_rollout_time += rollout_time
        total_rollout_time += rollout_time

        if global_step >= args.learning_starts:
            learning_has_started = True
            update_start = time.perf_counter()
            for _ in range(args.grad_steps_per_iteration):
                global_update += 1
                data = rb.sample(args.batch_size)
                with torch.no_grad():
                    next_actions, next_log_pi, _ = actor.get_action(data.next_obs)
                    next_q = torch.min(qf1_target(data.next_obs, next_actions),
                                       qf2_target(data.next_obs, next_actions)) - alpha * next_log_pi
                    target = data.rewards.flatten() + (1 - data.dones.flatten()) * args.gamma * next_q.view(-1)
                qf1_values = qf1(data.obs, data.actions).view(-1)
                qf2_values = qf2(data.obs, data.actions).view(-1)
                qf1_loss, qf2_loss = F.mse_loss(qf1_values, target), F.mse_loss(qf2_values, target)
                qf_loss = qf1_loss + qf2_loss
                q_optimizer.zero_grad()
                qf_loss.backward()
                q_optimizer.step()
                losses.update({"qf1_values": qf1_values.detach().mean(),
                               "qf2_values": qf2_values.detach().mean(),
                               "qf1_loss": qf1_loss.detach(), "qf2_loss": qf2_loss.detach(),
                               "qf_loss": qf_loss.detach() / 2})
                if global_update % args.policy_frequency == 0:
                    pi, log_pi, _ = actor.get_action(data.obs)
                    min_qf_pi = torch.min(qf1(data.obs, pi), qf2(data.obs, pi))
                    actor_loss = (alpha * log_pi - min_qf_pi).mean()
                    actor_optimizer.zero_grad()
                    actor_loss.backward()
                    actor_optimizer.step()
                    losses["actor_loss"] = actor_loss.detach()
                    if args.autotune:
                        with torch.no_grad():
                            _, log_pi, _ = actor.get_action(data.obs)
                        alpha_loss = (-log_alpha.exp() * (log_pi + target_entropy)).mean()
                        a_optimizer.zero_grad()
                        alpha_loss.backward()
                        a_optimizer.step()
                        alpha = log_alpha.exp().item()
                        losses["alpha_loss"] = alpha_loss.detach()
                if global_update % args.target_network_frequency == 0:
                    with torch.no_grad():
                        for network, target_network in ((qf1, qf1_target), (qf2, qf2_target)):
                            for param, target_param in zip(network.parameters(), target_network.parameters()):
                                target_param.copy_(args.tau * param + (1 - args.tau) * target_param)
            update_time = time.perf_counter() - update_start
            interval_update_time += update_time
            total_update_time += update_time

        if global_step // args.log_freq > last_log_step // args.log_freq or global_step >= args.total_timesteps:
            elapsed = time.perf_counter() - start_time
            transitions = global_step - last_log_step
            record = {
                "global_step": global_step, "global_update": global_update,
                "wall_time_s": elapsed, "SPS": int(global_step / elapsed),
                "rollout/reward_mean": reward_sum.item() / transitions,
                "train/episodes": sum(v.numel() for v in episode_metrics["return"]),
                "losses/alpha": alpha, "time/update_time": interval_update_time,
                "time/rollout_time": interval_rollout_time,
                "time/rollout_fps": transitions / interval_rollout_time,
                "time/total_update_time": total_update_time, "time/total_rollout_time": total_rollout_time,
            }
            record.update({f"losses/{key}": value.item() for key, value in losses.items()})
            for key, label in (("success_once", "success_once"), ("success_at_end", "success_at_end"),
                               ("return", "return_mean"), ("episode_len", "length_mean")):
                samples = episode_metrics[key]
                record[f"train/{label}"] = torch.cat(samples).float().mean().item() if samples else None
            if stage_names:
                record["teacher/phi_mean"] = phi_sum.item() / transitions
                record["teacher/shaping_mean"] = shaping_sum.item() / transitions
                for name, count in zip(stage_names, stage_counts.tolist()):
                    record[f"teacher/stage_frac/{name}"] = count / transitions
            with (args.out / "train.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, allow_nan=False) + "\n")
            if wandb is not None:
                wandb.log(record, step=global_step, commit=False)
            print(json.dumps(record, allow_nan=False), flush=True)
            last_log_step = global_step
            episode_metrics.clear()
            phi_sum.zero_()
            shaping_sum.zero_()
            reward_sum.zero_()
            stage_counts.zero_()
            interval_rollout_time, interval_update_time = 0.0, 0.0
    checkpoint = {"actor": actor.state_dict(), "qf1": qf1.state_dict(), "qf2": qf2.state_dict(),
                  "qf1_target": qf1_target.state_dict(), "qf2_target": qf2_target.state_dict(),
                  "alpha": alpha, "log_alpha": log_alpha.detach() if log_alpha is not None else None,
                  "global_step": global_step, "global_update": global_update}
    return actor, checkpoint, global_step


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidate = load_candidate(args.candidate) if args.reward == "teacher" else None
    stage_names = [stage.name for stage in candidate.graph.stages] if candidate is not None else []
    phi_scale = float(len(stage_names)) if args.phi_unnormalized and candidate is not None else 1.0
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    config.update(
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip(),
        maniskill_version=version("mani_skill"), phi_scale=phi_scale,
        eval_num_envs=args.num_envs, eval_episodes=args.eval_resets * args.num_envs,
        device="cuda", sim_backend="physx_cuda", obs_mode="state", render_mode=None,
        reward_mode="normalized_dense" if args.reward == "dense" else "sparse",
        ignore_terminations=False, auto_reset=True,
    )
    (args.out / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    wandb, envs = None, None
    completed = False
    try:
        if args.track:
            import wandb

            wandb.init(project=args.wandb_project, entity=args.wandb_entity, group=args.wandb_group,
                       name=args.run_name, mode=args.wandb_mode, dir=str(args.out), config=config)
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        torch.backends.cudnn.deterministic = args.torch_deterministic
        import mani_skill.envs
        from mani_skill.utils import gym_utils
        from mani_skill.utils.wrappers.flatten import FlattenActionSpaceWrapper
        from mani_skill.vector.wrappers.gymnasium import ManiSkillVectorEnv

        envs = gym.make(args.env_id, num_envs=args.num_envs, obs_mode="state",
                        control_mode=args.control_mode, sim_backend="physx_cuda", render_mode=None,
                        reward_mode=config["reward_mode"])
        if candidate is not None:
            envs = PBRSWrapper(envs, candidate, args.gamma, args.r_bonus, phi_scale=phi_scale)
        if isinstance(envs.action_space, gym.spaces.Dict):
            envs = FlattenActionSpaceWrapper(envs)
        envs = ManiSkillVectorEnv(envs, args.num_envs, ignore_terminations=False,
                                 record_metrics=True, auto_reset=True)
        assert isinstance(envs.single_action_space, gym.spaces.Box), "only continuous actions are supported"
        max_episode_steps = gym_utils.find_max_episode_steps_value(envs._env)
        actor, checkpoint, global_step = train(args, envs, stage_names, wandb)
        torch.save(checkpoint, args.out / "final_model.pt")
        result = evaluate_resets(actor, envs, args.eval_seed, max_episode_steps, stage_names, args.eval_resets)
        encoded = json.dumps(result, indent=2, allow_nan=False)
        (args.out / "eval.json").write_text(encoded + "\n", encoding="utf-8")
        print(encoded, flush=True)
        if wandb is not None:
            log_evaluation(wandb, result, global_step)
        completed = True
    finally:
        try:
            if envs is not None:
                envs.close()
        finally:
            if wandb is not None:
                wandb.finish(exit_code=0 if completed else 1)


if __name__ == "__main__":
    main()
