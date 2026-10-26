"""Claude Code subprocess calls and deterministic scripted calls."""

from collections.abc import Callable, Iterable, Sequence
from contextlib import suppress
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from typing import Any, Literal, Protocol

from .env import child_env


SENSITIVE_PATTERN = re.compile(
    r"api_?key|secret|authorization|password|credential|access_?token|auth_?token|bearer",
    re.IGNORECASE,
)


def _redact_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SENSITIVE_PATTERN.search(key) else _redact_fields(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_fields(item) for item in value]
    return value


def _redact_file(path: Path) -> None:
    with path.open("r+", encoding="utf-8") as stream:
        lines = stream.readlines()
        stream.seek(0)
        for line in lines:
            ending = "\n" if line.endswith("\n") else ""
            try:
                event = json.loads(line)
            except ValueError:
                if SENSITIVE_PATTERN.search(line):
                    line = "[REDACTED: sensitive-pattern line]" + ending
            else:
                line = json.dumps(_redact_fields(event), ensure_ascii=False) + ending
            stream.write(line)
        stream.truncate()


@dataclass
class RoundResult:
    outcome: Literal["completed", "max_turns", "timeout", "error"]
    session_id: str | None = None
    result_event: dict[str, Any] | None = None
    exit_code: int | None = None
    timed_out: bool = False
    num_turns: int | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    permission_denials: list[Any] = field(default_factory=list)
    final_text: str = ""
    check_sh_calls: int = 0
    error: str | None = None


@dataclass
class ReviewCall(RoundResult):
    @property
    def succeeded(self) -> bool:
        return self.outcome == "completed"


class Backend(Protocol):
    gpu: int | str

    def version(self) -> str | None: ...

    def generate(self, workspace: Path, prompt: str, session_id: str | None = None,
                 *, record_dir: Path) -> RoundResult: ...

    def review(self, workspace: Path, prompt: str, *, record_dir: Path) -> ReviewCall: ...


def parse_stream(lines: Iterable[str], exit_code: int | None, timed_out: bool = False) -> RoundResult:
    session_id = None
    result = None
    check_calls = 0
    seen_tools = set()
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            session_id = event.get("session_id", session_id)
        if event.get("type") == "result":
            result = event
            session_id = event.get("session_id", session_id)
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if (isinstance(block, dict) and block.get("type") == "tool_use"
                        and block.get("name") == "Bash"
                        and block.get("input", {}).get("command", "").strip() == "./check.sh"):
                    tool_id = block.get("id")
                    if tool_id is None or tool_id not in seen_tools:
                        check_calls += 1
                        seen_tools.add(tool_id)
    if timed_out:
        outcome = "timeout"
    elif result is not None and exit_code == 0 and result.get("is_error") is False:
        outcome = "completed"
    elif result is not None and result.get("subtype") == "error_max_turns":
        outcome = "max_turns"
    else:
        outcome = "error"
    data = result or {}
    return RoundResult(outcome=outcome, session_id=session_id, result_event=result,
                       exit_code=exit_code, timed_out=timed_out, num_turns=data.get("num_turns"),
                       usage=data.get("usage", {}), permission_denials=data.get("permission_denials", []),
                       final_text=data.get("result", ""), check_sh_calls=check_calls)


class ClaudeCodeBackend:
    def __init__(self, wrapper: str | Path, max_turns: int, timeout_s: float, *,
                 gpu: int | str = 1, review_max_turns: int = 40,
                 review_timeout_s: float = 900) -> None:
        self.wrapper = str(wrapper)
        self.max_turns = max_turns
        self.timeout_s = timeout_s
        self.gpu = gpu
        self.review_max_turns = review_max_turns
        self.review_timeout_s = review_timeout_s

    def version(self) -> str:
        result = subprocess.run([self.wrapper, "--version"], env=child_env(self.gpu),
                                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                timeout=30, check=True)
        return result.stdout.strip()

    def _argv(self, prompt: str, session_id: str | None, review: bool) -> list[str]:
        command = [self.wrapper]
        if session_id is not None:
            command.extend(["--resume", session_id])
        command.extend(["-p", prompt, "--output-format", "stream-json", "--verbose",
                        "--max-turns", str(self.review_max_turns if review else self.max_turns)])
        if review:
            command.extend(["--tools", "Read,Glob,Grep", "--disallowedTools", "Write", "Edit",
                            "Bash", "WebFetch", "WebSearch", "Task"])
        else:
            command.extend(["--tools", "Read,Write,Edit,Glob,Grep,Bash", "--allowedTools",
                            "Write(./**)", "Edit(./**)", "Bash(./check.sh)",
                            "--disallowedTools", "WebFetch", "WebSearch", "Task"])
        command.extend(["--permission-mode", "dontAsk", "--strict-mcp-config", "--mcp-config",
                        '{"mcpServers":{}}', "--settings", '{"autoMemoryEnabled": false}'])
        return command

    def _call(self, workspace: Path, prompt: str, session_id: str | None,
              record_dir: Path, review: bool) -> RoundResult:
        record_dir.mkdir(parents=True, exist_ok=True)
        name = "review" if review else "generation"
        stream_path = record_dir / f"{name}.jsonl"
        stderr_path = record_dir / f"{name}.stderr.txt"
        timed_out = False
        with stream_path.open("w", encoding="utf-8") as stdout, \
                stderr_path.open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(self._argv(prompt, session_id, review), cwd=workspace,
                                       env=child_env(self.gpu), stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            try:
                process.wait(timeout=self.review_timeout_s if review else self.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                deadline = time.monotonic() + 5
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, 0)
                    time.sleep(max(0, deadline - time.monotonic()))
                    os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            else:
                with suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
        _redact_file(stream_path)
        _redact_file(stderr_path)
        with stream_path.open(encoding="utf-8") as stream:
            return parse_stream(stream, process.returncode, timed_out)

    def generate(self, workspace: Path, prompt: str, session_id: str | None = None,
                 *, record_dir: Path) -> RoundResult:
        return self._call(workspace, prompt, session_id, record_dir, review=False)

    def review(self, workspace: Path, prompt: str, *, record_dir: Path) -> ReviewCall:
        return ReviewCall(**asdict(self._call(workspace, prompt, None, record_dir, review=True)))


CandidateScript = str | Path | Callable[[Path], RoundResult | None] | RoundResult | Exception


class ScriptedBackend:
    """Consume one candidate or review script per call, including retry attempts."""

    def __init__(self, candidates: Sequence[CandidateScript],
                 reviews: Sequence[str | ReviewCall | Exception] = ("[]",)) -> None:
        self.gpu: int | str = 1
        self._candidates = iter(candidates)
        self._reviews = iter(reviews)

    def version(self) -> None:
        return None

    @staticmethod
    def _record(record_dir: Path, name: str, result: RoundResult) -> None:
        record_dir.mkdir(parents=True, exist_ok=True)
        event = result.result_event or {
            "type": "result", "subtype": "success" if result.outcome == "completed" else "error",
            "is_error": result.outcome != "completed", "session_id": result.session_id,
            "terminal_reason": result.outcome, "num_turns": result.num_turns,
            "usage": result.usage, "permission_denials": result.permission_denials,
            "result": result.final_text,
        }
        result.result_event = event
        events = [{"type": "system", "subtype": "init", "session_id": result.session_id}, event]
        (record_dir / f"{name}.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        (record_dir / f"{name}.stderr.txt").write_text(result.error or "", encoding="utf-8")

    def generate(self, workspace: Path, prompt: str, session_id: str | None = None,
                 *, record_dir: Path) -> RoundResult:
        script = next(self._candidates)
        if isinstance(script, Exception):
            raise script
        candidate = workspace / "candidate"
        if isinstance(script, RoundResult):
            result = script
        else:
            shutil.rmtree(candidate)
            if callable(script):
                candidate.mkdir()
                result = script(candidate)
            else:
                shutil.copytree(script, candidate)
                result = None
        if result is None:
            result = RoundResult("completed", session_id=session_id or f"scripted-{workspace.parent.name}",
                                 exit_code=0, num_turns=1)
        self._record(record_dir, "generation", result)
        return result

    def review(self, workspace: Path, prompt: str, *, record_dir: Path) -> ReviewCall:
        script = next(self._reviews)
        if isinstance(script, Exception):
            raise script
        result = (script if isinstance(script, ReviewCall) else
                  ReviewCall("completed", session_id="scripted-review", exit_code=0,
                             num_turns=1, final_text=script))
        self._record(record_dir, "review", result)
        return result
