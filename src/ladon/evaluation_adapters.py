"""Comparable, availability-aware baselines for discovery evaluation."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationAdapter:
    name: str
    command: str
    available: bool
    nonclaims: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": self.command,
            "available": self.available,
            "nonclaims": list(self.nonclaims),
        }


def build_evaluation_adapters(repo_root: Path) -> tuple[EvaluationAdapter, ...]:
    """Describe comparable methods without treating unavailable tools as failures."""
    lean_available = shutil.which("lake") is not None
    rg_available = shutil.which("rg") is not None
    return (
        EvaluationAdapter("ladon", "ladon proof-search discover", True, ("Ladon output is bounded observation evidence.",)),
        EvaluationAdapter("exact?", "Lean exact?", lean_available, ("exact? availability is repository/toolchain dependent.",)),
        EvaluationAdapter("apply?", "Lean apply?", lean_available, ("apply? availability is repository/toolchain dependent.",)),
        EvaluationAdapter("#check", "Lean #check", lean_available, ("#check reports declaration elaboration, not ranked discovery.",)),
        EvaluationAdapter("rg", "rg", rg_available, ("rg is textual search and cannot establish Lean applicability.",)),
        EvaluationAdapter("editor-search", "editor semantic search", False, ("No editor protocol is available in this batch evaluation.",)),
    )


def evaluate_retrieval(found: set[str], expected: set[str]) -> dict[str, object]:
    """Compute recall and incorrect-suggestion rate without hiding empty sets."""
    true_positive = len(found & expected)
    false_positive = len(found - expected)
    return {
        "expected": len(expected),
        "found": len(found),
        "truePositive": true_positive,
        "falsePositive": false_positive,
        "recall": true_positive / len(expected) if expected else None,
        "recallStatus": "assessed" if expected else "not-assessed",
        "incorrectSuggestionRate": false_positive / len(found) if found else 0.0,
    }


__all__ = ["EvaluationAdapter", "build_evaluation_adapters", "evaluate_retrieval"]
