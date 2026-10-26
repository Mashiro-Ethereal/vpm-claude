"""Errors at the boundary between candidates and the runtime."""


class CandidateError(Exception):
    """Base class for candidate execution errors."""


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
