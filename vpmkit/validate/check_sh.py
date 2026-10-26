"""Render the workspace check command with absolute installation paths."""

from pathlib import Path
import shlex

from . import REPO_ROOT, VPM_PYTHON


def write_check_sh(workspace_dir: str | Path, env_id: str) -> Path:
    workspace = Path(workspace_dir).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    source = (REPO_ROOT / "vpmkit/resources/check.sh.template").read_text(encoding="utf-8")
    for name, value in {"REPO_ROOT": str(REPO_ROOT), "VPM_PYTHON": str(VPM_PYTHON),
                        "ENV_ID": env_id}.items():
        source = source.replace(f"@{name}@", shlex.quote(value))
    output = workspace / "check.sh"
    output.write_text(source, encoding="utf-8")
    output.chmod(0o755)
    return output
