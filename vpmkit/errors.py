"""Errors at the boundary between candidates and the runtime."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .candidate.report import Report


class CandidateError(Exception):
    """Base class for candidate validation and execution errors."""


class CandidateCheckError(CandidateError):
    def __init__(self, report: "Report") -> None:
        self.report = report
        super().__init__(report.to_markdown())


class CandidateRuntimeError(CandidateError):
    def __init__(self, function: str, target: str, message: str) -> None:
        self.function = function
        self.target = target
        super().__init__(f"{function} for {target}: {message}")


class CandidateOutputError(CandidateError):
    def __init__(self, function: str, target: str, message: str) -> None:
        self.function = function
        self.target = target
        super().__init__(f"{function} for {target}: {message}")
