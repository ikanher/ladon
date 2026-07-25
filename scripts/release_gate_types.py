"""Small shared value types for Ladon's release gates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class GateError(RuntimeError):
    """A deterministic release-gate failure."""


@dataclass(frozen=True)
class MaterializedCandidate:
    """One candidate copied into an outside-checkout temporary root."""

    root: Path
    kind: str


@dataclass(frozen=True)
class DistributionArtifacts:
    """The single constrained sdist and wheel produced by a build."""

    sdist: Path
    wheel: Path


@dataclass(frozen=True)
class InstalledEnvironment:
    """An isolated virtual environment containing the candidate wheel."""

    root: Path
    python: Path
    scripts: Path
