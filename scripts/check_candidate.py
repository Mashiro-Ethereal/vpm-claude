#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
"""Run the complete first layer for a candidate directory."""

import argparse
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("candidate_dir", type=Path)
    args = parser.parse_args()
    try:
        from vpmkit.validate.layer1 import run_layer1

        report = run_layer1(args.candidate_dir, args.env)
        print(report.to_markdown(), end="")
        if args.json is not None:
            args.json.write_text(report.to_json(), encoding="utf-8")
        return 0 if report.layer1_passed else 1
    except Exception as exc:
        print(f"check_candidate: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
