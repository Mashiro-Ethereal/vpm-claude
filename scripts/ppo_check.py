#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
# Adapted from ManiSkill examples/baselines/ppo/ppo.py (Apache-2.0).
"""Train state-based PPO with a Stage1 teacher, dense reward, or sparse reward."""

import argparse
from collections import defaultdict
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
import torch.optim as optim
from torch.distributions.normal import Normal
import yaml

from vpmkit.candidate import load_candidate
from vpmkit.ppo_bootstrap import final_bootstrap_mask
from vpmkit.rewards import PBRSWrapper


def parse_args() -> argparse.Namespace:
    defaults = yaml.safe_load((REPO_ROOT / "configs/default.yaml").read_text())["pbrs"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", default="PickCube-v1")
    parser.add_argument("--reward", choices=("teacher", "dense", "sparse"), required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--total-timesteps", type=int, default=5_000_000)
    parser.add_argument("--num-envs", type=int, default=1024)
    parser.add_argument("--num-steps", type=int, default=50)
    parser.add_argument("--update-epochs", type=int, default=8)
    parser.add_argument("--num-minibatches", type=int, default=32)
    parser.add_argument("--gamma", type=float, default=defaults["gamma"])
    parser.add_argument("--r-bonus", type=float, default=defaults["r_bonus"])
    parser.add_argument("--phi-unnormalized", action="store_true")
    parser.add_argument("--gae-lambda", type=float, default=0.9)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--clip-coef", type=float, default=0.2)
    parser.add_argument("--ent-coef", type=float, default=0.0)
    parser.add_argument("--vf-coef", type=float, default=0.5)
    parser.add_argument("--max-grad-norm", type=float, default=0.5)
    parser.add_argument("--target-kl", type=float, default=0.1)
    parser.add_argument("--reward-scale", type=float, default=1.0)
    for name, default in (("torch-deterministic", True), ("anneal-lr", False),
                          ("norm-adv", True), ("clip-vloss", False),
                          ("finite-horizon-gae", False), ("bootstrap-terminations", False)):
        parser.add_argument(f"--{name}", action=argparse.BooleanOptionalAction, default=default)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--eval-episodes-envs", type=int, default=256,
                        help="Requested evaluation count; this check reports all training environments.")
    parser.add_argument("--track", action="store_true")
    parser.add_argument("--wandb-project", default="vpm-stage1")
    parser.add_argument("--wandb-entity")
    parser.add_argument("--wandb-group")
    parser.add_argument("--wandb-mode", choices=("online", "offline", "disabled"), default="online")
    parser.add_argument("--run-name")
    args = parser.parse_args()
    if args.reward == "teacher" and args.candidate is None:
        parser.error("--candidate is required for --reward teacher")
    if min(args.num_envs, args.num_steps, args.num_minibatches, args.update_epochs) < 1:
        parser.error("environment, rollout, minibatch, and epoch counts must be positive")
    args.batch_size = args.num_envs * args.num_steps
    args.minibatch_size = args.batch_size // args.num_minibatches
    args.num_iterations = args.total_timesteps // args.batch_size
    if args.num_iterations < 1 or args.minibatch_size < 2:
        parser.error("need at least one full rollout and at least two samples per minibatch")
    if args.out is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        args.out = REPO_ROOT / "outputs/stage1/ppo_check" / f"{args.env_id}-{args.reward}-seed{args.seed}-{stamp}"
    args.out = args.out.resolve()
    if args.candidate is not None:
        args.candidate = args.candidate.resolve()
    if args.run_name is None:
        args.run_name = args.out.name
    return args


def layer_init(layer, std=np.sqrt(2), bias_const=0.0):
    torch.nn.init.orthogonal_(layer.weight, std)
    torch.nn.init.constant_(layer.bias, bias_const)
    return layer


class Agent(nn.Module):
    def __init__(self, envs):
        super().__init__()
        self.critic = nn.Sequential(
            layer_init(nn.Linear(np.array(envs.single_observation_space.shape).prod(), 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, 1)),
        )
        self.actor_mean = nn.Sequential(
            layer_init(nn.Linear(np.array(envs.single_observation_space.shape).prod(), 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, 256)),
            nn.Tanh(),
            layer_init(nn.Linear(256, np.prod(envs.single_action_space.shape)), std=0.01*np.sqrt(2)),
        )
        self.actor_logstd = nn.Parameter(torch.ones(1, np.prod(envs.single_action_space.shape)) * -0.5)

    def get_value(self, x):
        return self.critic(x)
    def get_action(self, x, deterministic=False):
        action_mean = self.actor_mean(x)
        if deterministic:
            return action_mean
        action_logstd = self.actor_logstd.expand_as(action_mean)
        action_std = torch.exp(action_logstd)
        probs = Normal(action_mean, action_std)
        return probs.sample()
    def get_action_and_value(self, x, action=None):
        action_mean = self.actor_mean(x)
        action_logstd = self.actor_logstd.expand_as(action_mean)
        action_std = torch.exp(action_logstd)
        probs = Normal(action_mean, action_std)
        if action is None:
            action = probs.sample()
        return action, probs.log_prob(action).sum(1), probs.entropy().sum(1), self.critic(x)


@torch.no_grad()
def evaluate(agent: Agent, envs: Any, seed: int, max_episode_steps: int,
             stage_names: list[str]) -> dict[str, Any]:
    """Measure only the first episode of each environment after a seeded reset."""
    agent.eval()
    obs, _ = envs.reset(seed=seed)
    count, device = envs.num_envs, envs.device
    active = torch.ones(count, dtype=torch.bool, device=device)
    success_once = torch.zeros_like(active)
    success_at_end = torch.zeros_like(active)
    lengths = torch.zeros(count, dtype=torch.long, device=device)
    first_success_step = torch.full_like(lengths, -1)
    first_success_stage = torch.full_like(lengths, -1)
    end_stage = torch.full_like(lengths, -1)
    low = torch.as_tensor(envs.single_action_space.low, device=device)
    high = torch.as_tensor(envs.single_action_space.high, device=device)
    for _ in range(max_episode_steps):
        action = agent.get_action(obs, deterministic=True).clamp(low, high)
        obs, _, terminated, truncated, info = envs.step(action)
        # final_info contains the entire pre-reset batch, including unfinished environments.
        step_info = info.get("final_info", info)
        success = step_info["success"].bool()
        lengths += active.long()
        first_success = active & success & ~success_once
        first_success_step[first_success] = lengths[first_success]
        success_once |= active & success
        ended = active & (terminated | truncated)
        success_at_end[ended] = success[ended]
        if stage_names:
            stage = step_info["pbrs"]["stage"]
            first_success_stage[first_success] = stage[first_success]
            end_stage[ended] = stage[ended]
        active &= ~ended
    if active.any():
        raise RuntimeError("Evaluation ended before every environment completed its first episode")

    result = {
        "seed": seed, "episodes": count, "max_episode_steps": max_episode_steps,
        "success_once": success_once.float().mean().item(),
        "success_at_end": success_at_end.float().mean().item(),
        "length_mean": lengths.float().mean().item(),
    }
    if stage_names:
        success_counts = torch.bincount(first_success_stage[success_once], minlength=len(stage_names)).tolist()
        failure_counts = torch.bincount(end_stage[~success_once], minlength=len(stage_names)).tolist()
        successes = sum(success_counts)
        result["teacher"] = {
            "first_success_stage_histogram": dict(zip(stage_names, success_counts)),
            "first_success_last_stage_fraction": success_counts[-1] / successes if successes else None,
            "unsuccessful_end_stage_histogram": dict(zip(stage_names, failure_counts)),
        }
    per_environment = []
    rows = zip(success_once.tolist(), success_at_end.tolist(), lengths.tolist(),
               first_success_step.tolist(), first_success_stage.tolist(), end_stage.tolist())
    for index, (once, at_end, length, first_step, first_stage, last_stage) in enumerate(rows):
        row = {"env_index": index, "success_once": once, "success_at_end": at_end,
               "length": length, "first_success_step": first_step if once else None}
        if stage_names:
            row["first_success_stage"] = stage_names[first_stage] if once else None
            row["end_stage"] = stage_names[last_stage]
        per_environment.append(row)
    result["per_environment"] = per_environment
    return result


def train(args: argparse.Namespace, envs: Any, stage_names: list[str],
          wandb: Any) -> tuple[Agent, int]:
    device = envs.device
    agent = Agent(envs).to(device)
    optimizer = optim.Adam(agent.parameters(), lr=args.learning_rate, eps=1e-5)
    obs = torch.zeros((args.num_steps, args.num_envs) + envs.single_observation_space.shape, device=device)
    actions = torch.zeros((args.num_steps, args.num_envs) + envs.single_action_space.shape, device=device)
    logprobs = torch.zeros((args.num_steps, args.num_envs), device=device)
    rewards = torch.zeros_like(logprobs)
    dones = torch.zeros_like(logprobs)
    values = torch.zeros_like(logprobs)
    global_step = 0
    start_time = time.perf_counter()
    next_obs, _ = envs.reset(seed=args.seed)
    next_done = torch.zeros(args.num_envs, device=device)
    low = torch.as_tensor(envs.single_action_space.low, device=device)
    high = torch.as_tensor(envs.single_action_space.high, device=device)
    stage_ones = torch.ones(args.num_envs, dtype=torch.long, device=device)
    print(f"Training {args.num_iterations} iterations / {args.num_iterations * args.batch_size} transitions; "
          f"bootstrap_terminations={args.bootstrap_terminations}", flush=True)

    for iteration in range(1, args.num_iterations + 1):
        final_values = torch.zeros_like(values)
        episode_metrics = defaultdict(list)
        phi_sum = torch.zeros((), device=device)
        shaping_sum = torch.zeros((), device=device)
        stage_counts = torch.zeros(len(stage_names), dtype=torch.long, device=device)
        agent.eval()
        if args.anneal_lr:
            frac = 1.0 - (iteration - 1.0) / args.num_iterations
            optimizer.param_groups[0]["lr"] = frac * args.learning_rate

        rollout_time = time.perf_counter()
        for step in range(args.num_steps):
            global_step += args.num_envs
            obs[step] = next_obs
            dones[step] = next_done
            with torch.no_grad():
                action, logprob, _, value = agent.get_action_and_value(next_obs)
                values[step] = value.flatten()
            actions[step] = action
            logprobs[step] = logprob
            next_obs, reward, terminations, truncations, infos = envs.step(action.detach().clamp(low, high))
            next_done = torch.logical_or(terminations, truncations).to(torch.float32)
            rewards[step] = reward.view(-1) * args.reward_scale
            step_info = infos.get("final_info", infos)
            if stage_names:
                pbrs = step_info["pbrs"]
                phi_sum += pbrs["phi_teacher"].sum()
                shaping_sum += pbrs["shaping"].sum()
                stage_counts.scatter_add_(0, pbrs["stage"], stage_ones)
            if "final_info" in infos:
                done_mask = infos["_final_info"]
                episode = step_info["episode"]
                for key in ("success_once", "return", "episode_len"):
                    episode_metrics[key].append(episode[key][done_mask])
                at_end = episode.get("success_at_end", step_info.get("success"))
                if at_end is not None:
                    episode_metrics["success_at_end"].append(at_end[done_mask])
                bootstrap_mask = final_bootstrap_mask(
                    done_mask, terminations, truncations, args.bootstrap_terminations)
                with torch.no_grad():
                    final_values[step, bootstrap_mask] = agent.get_value(
                        infos["final_observation"][bootstrap_mask]).view(-1)
        rollout_time = time.perf_counter() - rollout_time

        with torch.no_grad():
            next_value = agent.get_value(next_obs).reshape(1, -1)
            advantages = torch.zeros_like(rewards).to(device)
            lastgaelam = 0
            for t in reversed(range(args.num_steps)):
                if t == args.num_steps - 1:
                    next_not_done = 1.0 - next_done
                    nextvalues = next_value
                else:
                    next_not_done = 1.0 - dones[t + 1]
                    nextvalues = values[t + 1]
                real_next_values = next_not_done * nextvalues + final_values[t]
                if args.finite_horizon_gae:
                    if t == args.num_steps - 1:
                        lam_coef_sum = 0.
                        reward_term_sum = 0.
                        value_term_sum = 0.
                    lam_coef_sum = lam_coef_sum * next_not_done
                    reward_term_sum = reward_term_sum * next_not_done
                    value_term_sum = value_term_sum * next_not_done

                    lam_coef_sum = 1 + args.gae_lambda * lam_coef_sum
                    reward_term_sum = args.gae_lambda * args.gamma * reward_term_sum + lam_coef_sum * rewards[t]
                    value_term_sum = args.gae_lambda * args.gamma * value_term_sum + args.gamma * real_next_values

                    advantages[t] = (reward_term_sum + value_term_sum) / lam_coef_sum - values[t]
                else:
                    delta = rewards[t] + args.gamma * real_next_values - values[t]
                    advantages[t] = lastgaelam = delta + args.gamma * args.gae_lambda * next_not_done * lastgaelam
            returns = advantages + values

        b_obs = obs.reshape((-1,) + envs.single_observation_space.shape)
        b_logprobs = logprobs.reshape(-1)
        b_actions = actions.reshape((-1,) + envs.single_action_space.shape)
        b_advantages = advantages.reshape(-1)
        b_returns = returns.reshape(-1)
        b_values = values.reshape(-1)

        agent.train()
        b_inds = np.arange(args.batch_size)
        clipfracs = []
        update_time = time.perf_counter()
        for epoch in range(args.update_epochs):
            np.random.shuffle(b_inds)
            for start in range(0, args.batch_size, args.minibatch_size):
                end = start + args.minibatch_size
                mb_inds = b_inds[start:end]

                _, newlogprob, entropy, newvalue = agent.get_action_and_value(b_obs[mb_inds], b_actions[mb_inds])
                logratio = newlogprob - b_logprobs[mb_inds]
                ratio = logratio.exp()

                with torch.no_grad():
                    old_approx_kl = (-logratio).mean()
                    approx_kl = ((ratio - 1) - logratio).mean()
                    clipfracs += [((ratio - 1.0).abs() > args.clip_coef).float().mean().item()]

                if args.target_kl is not None and approx_kl > args.target_kl:
                    break

                mb_advantages = b_advantages[mb_inds]
                if args.norm_adv:
                    mb_advantages = (mb_advantages - mb_advantages.mean()) / (mb_advantages.std() + 1e-8)

                pg_loss1 = -mb_advantages * ratio
                pg_loss2 = -mb_advantages * torch.clamp(ratio, 1 - args.clip_coef, 1 + args.clip_coef)
                pg_loss = torch.max(pg_loss1, pg_loss2).mean()

                newvalue = newvalue.view(-1)
                if args.clip_vloss:
                    v_loss_unclipped = (newvalue - b_returns[mb_inds]) ** 2
                    v_clipped = b_values[mb_inds] + torch.clamp(
                        newvalue - b_values[mb_inds],
                        -args.clip_coef,
                        args.clip_coef,
                    )
                    v_loss_clipped = (v_clipped - b_returns[mb_inds]) ** 2
                    v_loss_max = torch.max(v_loss_unclipped, v_loss_clipped)
                    v_loss = 0.5 * v_loss_max.mean()
                else:
                    v_loss = 0.5 * ((newvalue - b_returns[mb_inds]) ** 2).mean()

                entropy_loss = entropy.mean()
                loss = pg_loss - args.ent_coef * entropy_loss + v_loss * args.vf_coef

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(agent.parameters(), args.max_grad_norm)
                optimizer.step()

            if args.target_kl is not None and approx_kl > args.target_kl:
                break

        update_time = time.perf_counter() - update_time
        y_pred, y_true = b_values.cpu().numpy(), b_returns.cpu().numpy()
        var_y = np.var(y_true)
        explained_var = None if var_y == 0 else float(1 - np.var(y_true - y_pred) / var_y)
        elapsed = time.perf_counter() - start_time
        record = {
            "global_step": global_step, "iteration": iteration, "wall_time_s": elapsed,
            "SPS": int(global_step / elapsed), "rollout/reward_mean": rewards.mean().item(),
            "train/episodes": sum(v.numel() for v in episode_metrics["return"]),
            "charts/learning_rate": optimizer.param_groups[0]["lr"],
            "losses/value_loss": v_loss.item(), "losses/policy_loss": pg_loss.item(),
            "losses/entropy": entropy_loss.item(), "losses/old_approx_kl": old_approx_kl.item(),
            "losses/approx_kl": approx_kl.item(), "losses/clipfrac": float(np.mean(clipfracs)),
            "losses/explained_variance": explained_var,
            "time/update_time": update_time, "time/rollout_time": rollout_time,
            "time/rollout_fps": args.batch_size / rollout_time,
        }
        for key, label in (("success_once", "success_once"), ("success_at_end", "success_at_end"),
                           ("return", "return_mean"), ("episode_len", "length_mean")):
            samples = episode_metrics[key]
            record[f"train/{label}"] = torch.cat(samples).float().mean().item() if samples else None
        if stage_names:
            record["teacher/phi_mean"] = phi_sum.item() / args.batch_size
            record["teacher/shaping_mean"] = shaping_sum.item() / args.batch_size
            for name, count in zip(stage_names, stage_counts.tolist()):
                record[f"teacher/stage_frac/{name}"] = count / args.batch_size
        with (args.out / "train.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        if wandb is not None:
            wandb.log(record, step=global_step, commit=False)
        success = record["train/success_once"]
        success_text = "n/a" if success is None else f"{success:.3f}"
        print(f"iter={iteration} step={global_step} wall={elapsed:.1f}s SPS={record['SPS']} "
              f"reward={record['rollout/reward_mean']:.4f} episodes={record['train/episodes']} "
              f"success={success_text}", flush=True)
    return agent, global_step


def log_evaluation(wandb: Any, result: dict[str, Any], global_step: int) -> None:
    metrics = {}

    def flatten(prefix: str, values: dict[str, Any]) -> None:
        for key, value in values.items():
            if isinstance(value, dict):
                flatten(f"{prefix}/{key}", value)
            elif key != "per_environment":
                metrics[f"{prefix}/{key}"] = value

    flatten("eval", result)
    rows = result["per_environment"]
    columns = list(rows[0])
    metrics["eval/per_environment"] = wandb.Table(
        columns=columns, data=[[row[key] for key in columns] for row in rows])
    wandb.log(metrics, step=global_step)


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidate = load_candidate(args.candidate) if args.reward == "teacher" else None
    stage_names = [stage.name for stage in candidate.graph.stages] if candidate is not None else []
    phi_scale = float(len(stage_names)) if args.phi_unnormalized and candidate is not None else 1.0
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()}
    config.update(
        git_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip(),
        maniskill_version=version("mani_skill"), eval_seed=args.seed + 10_000,
        eval_num_envs=args.num_envs, device="cuda", control_mode="pd_joint_delta_pos",
        sim_backend="physx_cuda", obs_mode="state", render_mode=None,
        reward_mode="normalized_dense" if args.reward == "dense" else "sparse",
        ignore_terminations=False, auto_reset=True, phi_scale=phi_scale,
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
                        control_mode="pd_joint_delta_pos", sim_backend="physx_cuda", render_mode=None,
                        reward_mode=config["reward_mode"])
        if candidate is not None:
            envs = PBRSWrapper(envs, candidate, args.gamma, args.r_bonus, phi_scale=phi_scale)
        if isinstance(envs.action_space, gym.spaces.Dict):
            envs = FlattenActionSpaceWrapper(envs)
        envs = ManiSkillVectorEnv(envs, args.num_envs, ignore_terminations=False,
                                 record_metrics=True, auto_reset=True)
        assert isinstance(envs.single_action_space, gym.spaces.Box), "only continuous actions are supported"
        max_episode_steps = gym_utils.find_max_episode_steps_value(envs._env)
        agent, global_step = train(args, envs, stage_names, wandb)
        torch.save(agent.state_dict(), args.out / "final_model.pt")
        result = evaluate(agent, envs, config["eval_seed"], max_episode_steps, stage_names)
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
