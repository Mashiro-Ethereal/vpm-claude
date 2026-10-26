"""The candidate-facing API."""

from . import geometry as G
from .predicate import predicate, signed

__all__ = ["predicate", "signed", "G"]
