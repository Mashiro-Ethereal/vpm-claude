"""Subprocess contracts, stream outcomes and isolated child environments."""

import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from vpmkit.harness.backends import ClaudeCodeBackend, parse_stream
from vpmkit.harness.env import child_env, env_names


WRAPPER = "/home/zxh/.local/bin/claude-deepseek"
ENDING = ["--permission-mode", "dontAsk", "--strict-mcp-config", "--mcp-config",
          '{"mcpServers":{}}', "--settings", '{"autoMemoryEnabled": false}']
GENERATION_FLAGS = ["--output-format", "stream-json", "--verbose", "--max-turns", "80",
                    "--tools", "Read,Write,Edit,Glob,Grep,Bash", "--allowedTools",
                    "Write(./**)", "Edit(./**)", "Bash(./check.sh)", "--disallowedTools",
                    "WebFetch", "WebSearch", "Task"] + ENDING
REVIEW_FLAGS = ["--output-format", "stream-json", "--verbose", "--max-turns", "40",
                "--tools", "Read,Glob,Grep", "--disallowedTools", "Write", "Edit", "Bash",
                "WebFetch", "WebSearch", "Task"] + ENDING


def stream_text(**changes) -> str:
    result = {"type": "result", "subtype": "success", "is_error": False,
              "terminal_reason": "completed", "num_turns": 3, "session_id": "session-one",
              "usage": {"input_tokens": 20, "output_tokens": 10},
              "permission_denials": [{"tool_name": "Bash"}], "result": "Summary"}
    result.update(changes)
    return json.dumps({"type": "system", "subtype": "init", "session_id": "session-one"}) + "\n" + json.dumps(result) + "\n"


class ChildEnvTest(unittest.TestCase):
    def test_allowlist_only_and_names_sorted(self) -> None:
        allowed = {name: "test-value" for name in (
            "HOME", "PATH", "LANG", "LANGUAGE", "LC_ALL", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")}
        inherited = {**allowed, "CLAUDE_CODE_ENTRYPOINT": "test-entrypoint",
                     "ANTHROPIC_API_KEY": "test-key", "CUDA_VISIBLE_DEVICES": "parent-card",
                     "XDG_CACHE_HOME": "test-cache", "http_proxy": "test-proxy", "OTHER": "test-other"}
        with patch.dict(os.environ, inherited, clear=True):
            environment = child_env(1)
        self.assertEqual(environment, {**allowed, "CUDA_VISIBLE_DEVICES": "1"})
        self.assertEqual(env_names(environment), sorted(environment))
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(child_env("1"), {"CUDA_VISIBLE_DEVICES": "1"})


class StreamTest(unittest.TestCase):
    def test_result_fields_and_session_from_result(self) -> None:
        result = parse_stream(stream_text().splitlines(), 0)
        self.assertEqual(result.outcome, "completed")
        self.assertEqual(result.session_id, "session-one")
        self.assertEqual(result.num_turns, 3)
        self.assertEqual(result.usage, {"input_tokens": 20, "output_tokens": 10})
        self.assertEqual(result.permission_denials, [{"tool_name": "Bash"}])
        self.assertEqual(result.final_text, "Summary")
        self.assertEqual(result.result_event["terminal_reason"], "completed")
        only_result = stream_text(session_id="result-session").splitlines()[1:]
        self.assertEqual(parse_stream(only_result, 0).session_id, "result-session")

    def test_normal_round_ends_and_harness_failures(self) -> None:
        cases = [
            (stream_text(), 0, False, "completed"),
            (stream_text(subtype="error_max_turns", is_error=True, terminal_reason="max_turns"), 1, False, "max_turns"),
            (stream_text(is_error=True), 0, False, "error"),
            (stream_text(), 1, False, "error"),
            (stream_text(subtype="error_api", is_error=True), 1, False, "error"),
            (stream_text().splitlines()[0], 0, False, "error"),
            (stream_text().splitlines()[0] + '\n{"type":', -15, True, "timeout"),
            ("", 1, False, "error"),
        ]
        for source, exit_code, timed_out, outcome in cases:
            with self.subTest(outcome=outcome, exit_code=exit_code):
                result = parse_stream(source.splitlines(), exit_code, timed_out)
                self.assertEqual(result.outcome, outcome)
                self.assertEqual(result.exit_code, exit_code)
                self.assertEqual(result.timed_out, timed_out)
                if source:
                    self.assertEqual(result.session_id, "session-one")

    def test_count_check_tool_uses_once_per_tool_id(self) -> None:
        def tool(identifier: str, command: str) -> dict:
            return {"type": "tool_use", "id": identifier, "name": "Bash", "input": {"command": command}}

        blocks = [tool("one", "./check.sh"), tool("two", " ./check.sh\n"),
                  tool("three", "./check.sh extra"), tool("four", "echo ./check.sh")]
        event = {"type": "assistant", "message": {"content": blocks}}
        source = [json.dumps(event), json.dumps(event), stream_text().splitlines()[-1]]
        self.assertEqual(parse_stream(source, 0).check_sh_calls, 2)


class ClaudeBackendTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.backend = ClaudeCodeBackend(WRAPPER, 80, 2400, gpu=1,
                                         review_max_turns=40, review_timeout_s=900)
        killpg = patch("vpmkit.harness.backends.os.killpg")
        self.killpg = killpg.start()
        self.addCleanup(killpg.stop)

    def test_exact_argv_stream_files_and_subprocess_options(self) -> None:
        for mode, session_id in (("generation", None), ("generation", "resume-this"), ("review", None)):
            with self.subTest(mode=mode, session=session_id):
                self.killpg.reset_mock()
                process = Mock(returncode=0)

                def spawn(command: list[str], **kwargs) -> Mock:
                    kwargs["stdout"].write(stream_text(result="[]"))
                    kwargs["stderr"].write("diagnostic\n")
                    return process

                records = self.root / (mode + str(session_id))
                with patch("vpmkit.harness.backends.subprocess.Popen", side_effect=spawn) as popen:
                    if mode == "review":
                        result = self.backend.review(self.root, "prompt text", record_dir=records)
                    else:
                        result = self.backend.generate(self.root, "prompt text", session_id, record_dir=records)
                prefix = [WRAPPER] + (["--resume", session_id] if session_id else []) + ["-p", "prompt text"]
                self.assertEqual(popen.call_args.args[0], prefix + (REVIEW_FLAGS if mode == "review" else GENERATION_FLAGS))
                options = popen.call_args.kwargs
                self.assertEqual(options["cwd"], self.root)
                self.assertEqual(options["env"], child_env(1))
                self.assertEqual(options["stdin"], subprocess.DEVNULL)
                self.assertTrue(options["start_new_session"])
                self.assertNotIn("shell", options)
                process.wait.assert_called_once_with(timeout=900 if mode == "review" else 2400)
                self.killpg.assert_called_once_with(process.pid, signal.SIGTERM)
                self.assertEqual((records / f"{mode}.jsonl").read_text(), stream_text(result="[]"))
                self.assertEqual((records / f"{mode}.stderr.txt").read_text(), "diagnostic\n")
                self.assertEqual(result.outcome, "completed")

    def test_saved_output_redaction_preserves_events_and_parsed_result(self) -> None:
        usage = {"input_tokens": 20, "output_tokens": 10, "cacheReadInputTokens": 5}
        sensitive_keys = ("apiKeySource", "API_KEY", "clientSecret", "Authorization", "PASSWORD",
                          "credentials", "accessToken", "ACCESS_TOKEN", "authToken", "AUTH_TOKEN", "Bearer")
        init = {"type": "system", "subtype": "init", "session_id": "session-one", "model": "test-model",
                "usage": usage, **dict.fromkeys(sensitive_keys, "fixture-value"),
                "details": [{"headers": {"Authorization": "x", "Accept": "application/json"},
                             "nested": [{"password": "x", "visible": True}]}]}
        final = json.loads(stream_text(usage=usage).splitlines()[-1])
        final["headers"] = {"Authorization": "x"}
        output = (json.dumps(init) + "\nplain diagnostic\nBearer fixture-value\n"
                  + json.dumps(final) + "\n")
        stderr = ('{"headers": {"Authorization": "x"}, "usage": {"input_tokens": 20}}\n'
                  'plain stderr diagnostic\nBearer fixture-value')
        expected_init = {**init, **dict.fromkeys(sensitive_keys, "[REDACTED]"),
                         "details": [{"headers": {"Authorization": "[REDACTED]", "Accept": "application/json"},
                                      "nested": [{"password": "[REDACTED]", "visible": True}]}]}
        expected_final = {**final, "headers": {"Authorization": "[REDACTED]"}}
        for mode in ("generation", "review"):
            for timed_out in (False, True):
                with self.subTest(mode=mode, timed_out=timed_out):
                    process = Mock(pid=12345, returncode=-15 if timed_out else 0)
                    if timed_out:
                        process.wait.side_effect = [subprocess.TimeoutExpired("mock-wrapper", 1), -15, -15]

                    def spawn(command: list[str], **kwargs) -> Mock:
                        kwargs["stdout"].write(output)
                        kwargs["stderr"].write(stderr)
                        return process

                    records = self.root / f"{mode}-{timed_out}"
                    with patch("vpmkit.harness.backends.subprocess.Popen", side_effect=spawn), \
                            patch("vpmkit.harness.backends.time.sleep"):
                        if mode == "review":
                            result = self.backend.review(self.root, "prompt", record_dir=records)
                        else:
                            result = self.backend.generate(self.root, "prompt", record_dir=records)
                    saved = (records / f"{mode}.jsonl").read_text().splitlines()
                    self.assertEqual(len(saved), 4)
                    self.assertEqual(json.loads(saved[0]), expected_init)
                    self.assertEqual(saved[1:3], ["plain diagnostic", "[REDACTED: sensitive-pattern line]"])
                    self.assertEqual(json.loads(saved[3]), expected_final)
                    saved_stderr = (records / f"{mode}.stderr.txt").read_text().splitlines()
                    self.assertEqual(len(saved_stderr), 3)
                    self.assertEqual(json.loads(saved_stderr[0]), {
                        "headers": {"Authorization": "[REDACTED]"}, "usage": {"input_tokens": 20}})
                    self.assertEqual(saved_stderr[1:], ["plain stderr diagnostic", "[REDACTED: sensitive-pattern line]"])
                    self.assertEqual(result.outcome, "timeout" if timed_out else "completed")
                    self.assertEqual(result.session_id, "session-one")
                    self.assertEqual(result.final_text, "Summary")
                    self.assertEqual(result.usage, usage)
                    self.assertEqual(result.result_event, expected_final)

    def test_timeout_kills_surviving_group_even_if_wrapper_exits_first(self) -> None:
        for wrapper_exits in (False, True):
            self.killpg.reset_mock()
            process = Mock(pid=12345, returncode=-15 if wrapper_exits else -9)
            timeout = subprocess.TimeoutExpired("mock-wrapper", 1)
            process.wait.side_effect = [timeout, -15, -15] if wrapper_exits else [timeout, timeout, -9]
            with patch("vpmkit.harness.backends.subprocess.Popen", return_value=process), \
                    patch("vpmkit.harness.backends.time.monotonic", side_effect=[100, 101 if wrapper_exits else 105]), \
                    patch("vpmkit.harness.backends.time.sleep") as sleep:
                result = self.backend.generate(self.root, "prompt", record_dir=self.root / str(wrapper_exits))
            self.assertEqual(result.outcome, "timeout")
            self.assertTrue(result.timed_out)
            self.assertEqual(self.killpg.call_args_list,
                             [call(process.pid, signal.SIGTERM), call(process.pid, 0),
                              call(process.pid, signal.SIGKILL)])
            sleep.assert_called_once_with(4 if wrapper_exits else 0)
            process.terminate.assert_not_called()
            process.kill.assert_not_called()
            self.assertEqual(process.wait.call_args_list[1].kwargs, {"timeout": 5})
            self.assertEqual(process.wait.call_args_list[-1], call())

    def test_timeout_ignores_process_group_disappearance(self) -> None:
        for signals in ([ProcessLookupError(), ProcessLookupError()],
                        [None, ProcessLookupError()], [None, None, ProcessLookupError()]):
            self.killpg.reset_mock()
            self.killpg.side_effect = signals
            process = Mock(pid=12345, returncode=-15)
            process.wait.side_effect = [subprocess.TimeoutExpired("mock-wrapper", 1), -15, -15]
            with patch("vpmkit.harness.backends.subprocess.Popen", return_value=process), \
                    patch("vpmkit.harness.backends.time.monotonic", return_value=100), \
                    patch("vpmkit.harness.backends.time.sleep") as sleep:
                result = self.backend.generate(self.root, "prompt", record_dir=self.root)
            self.assertEqual(result.outcome, "timeout")
            self.assertEqual(self.killpg.call_count, len(signals))
            self.assertEqual(sleep.call_count, int(len(signals) == 3))

    def test_normal_exit_ignores_absent_process_group(self) -> None:
        self.killpg.side_effect = ProcessLookupError

        def spawn(command: list[str], **kwargs) -> Mock:
            kwargs["stdout"].write(stream_text())
            return Mock(pid=12345, returncode=0)

        with patch("vpmkit.harness.backends.subprocess.Popen", side_effect=spawn):
            result = self.backend.generate(self.root, "prompt", record_dir=self.root)
        self.assertEqual(result.outcome, "completed")
        self.killpg.assert_called_once_with(12345, signal.SIGTERM)

    def test_review_turn_limit_is_call_failure_and_uses_own_limits(self) -> None:
        self.backend.review_max_turns = 7
        self.backend.review_timeout_s = 12

        def spawn(command: list[str], **kwargs) -> Mock:
            self.assertEqual(command[command.index("--max-turns") + 1], "7")
            kwargs["stdout"].write(stream_text(subtype="error_max_turns", is_error=True))
            return Mock(returncode=1)

        with patch("vpmkit.harness.backends.subprocess.Popen", side_effect=spawn):
            result = self.backend.review(self.root, "prompt", record_dir=self.root)
        self.assertFalse(result.succeeded)

    def test_version_uses_child_environment_without_agent_invocation(self) -> None:
        with patch("vpmkit.harness.backends.subprocess.run", return_value=
                   subprocess.CompletedProcess([], 0, "2.1.test\n", "")) as run:
            self.assertEqual(self.backend.version(), "2.1.test")
        self.assertEqual(run.call_args.args[0], [WRAPPER, "--version"])
        self.assertEqual(run.call_args.kwargs["env"], child_env(1))
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
