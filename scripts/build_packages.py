#!/home/zxh/anaconda3/envs/vpm-mani/bin/python
"""Build an input package for one ManiSkill task."""

import argparse
import json
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", required=True)
    parser.add_argument("--out", type=Path, default=Path("outputs/stage1/packages"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        from vpmkit.package.build import build_package

        package = build_package(args.env, args.out, args.overwrite)
        manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
        print(package)
        print("package_sha256: " + manifest["package_sha256"])
        return 0
    except Exception as exc:
        print(f"build_packages: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
