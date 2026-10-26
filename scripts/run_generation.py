#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
"""Generate and validate candidates using Claude Code or the PickCube reference."""

import argparse
import os
from pathlib import Path
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True)
    parser.add_argument("--gpu", type=int)
    parser.add_argument("--backend", choices=("claude", "scripted"), default="claude")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / "configs/default.yaml")
    args = parser.parse_args()
    try:
        for name, folder in (("XDG_CACHE_HOME", "cache"), ("MS_ASSET_DIR", "maniskill"),
                             ("TMPDIR", "tmp")):
            directory = REPO_ROOT / "outputs" / folder
            directory.mkdir(parents=True, exist_ok=True)
            os.environ[name] = str(directory)
        config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
        if args.gpu is not None:
            config["gpu"] = args.gpu
        os.environ["CUDA_VISIBLE_DEVICES"] = str(config["gpu"])
        if config["k"] < 1:
            raise ValueError("k must be positive")
        from vpmkit.harness.backends import ClaudeCodeBackend, ScriptedBackend
        from vpmkit.harness.run import run_generation

        statuses = []
        for _ in range(config["k"]):
            if args.backend == "scripted":
                if args.env != "PickCube-v1":
                    raise ValueError("The scripted CLI uses the PickCube-v1 reference candidate")
                backend = ScriptedBackend([REPO_ROOT / "candidates/reference/PickCube-v1"])
            else:
                backend = ClaudeCodeBackend(
                    config["paths"]["wrapper"], config["generation"]["max_turns"],
                    config["generation"]["round_timeout_s"], gpu=config["gpu"],
                    review_max_turns=config["review"]["max_turns"],
                    review_timeout_s=config["review"]["timeout_s"])
            verdict = run_generation(args.env, backend, config)
            print(f"{verdict.run_dir}: {verdict.status} ({verdict.rounds_used} rounds)", flush=True)
            statuses.append(verdict.status)
        return 0 if "passed" in statuses else (2 if "harness_failure" in statuses else 1)
    except Exception as exc:
        print(f"run_generation: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
