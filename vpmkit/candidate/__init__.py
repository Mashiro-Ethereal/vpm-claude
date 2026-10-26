"""Candidate schema, static checks and loading."""

from pathlib import Path

from ..errors import CandidateCheckError
from .modules import Candidate, load_candidate_unchecked
from .report import Problem, Report
from .schema import StageGraph
from .static import check_static

__all__ = ["Candidate", "StageGraph", "Problem", "Report", "check_static",
           "load_candidate", "load_candidate_unchecked"]


def load_candidate(path: str | Path) -> Candidate:
    report = check_static(path)
    if not report.passed:
        raise CandidateCheckError(report)
    return load_candidate_unchecked(path)
