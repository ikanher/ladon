"""Data contracts and committed constants for the large-inventory gate."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ladon.benchmark_process import MeasuredProcess

LARGE_INVENTORY_GATE_SCHEMA = "ladon-large-inventory-gate-v1"
REQUIRED_SAMPLE_COUNT = 3
REQUIRED_MODULE_COUNT = 2_600
REQUIRED_SOURCE_LINE_COUNT = 1_500_000
REQUIRED_DECLARATION_COUNT = 100_000
REPRESENTATIONS = ("json", "text")
ANALYSIS_COMMAND_TEMPLATE = (
    "ladon",
    "--repo-root",
    "{fixture}",
    "--root",
    "Fixture",
    "--scope",
    "inventory",
    "--cache-dir",
    "{cache}",
    "--report-version",
    "v3",
    "--projection",
    "review",
    "--progress",
    "json",
    "--format",
    "{representation}",
    "--output",
    "{output}",
)


class LargeInventoryGateError(RuntimeError):
    """Raised when the measurement protocol itself cannot produce evidence."""


class MeasuredRunner(Protocol):
    """Injectable interface matching the shared benchmark process runner."""

    def __call__(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_seconds: float,
    ) -> MeasuredProcess: ...


ReportValidator = Callable[[Mapping[str, Any]], None]


@dataclass(frozen=True)
class ScaleCeilings:
    """Exact, independently enforced large-inventory resource ceilings."""

    cold_wall_seconds: float = 20.0
    warm_wall_seconds: float = 5.0
    peak_rss_mib: float = 512.0
    canonical_json_bytes: int = 32_000_000
    compact_text_bytes: int = 500_000

    def __post_init__(self) -> None:
        values = (
            self.cold_wall_seconds,
            self.warm_wall_seconds,
            self.peak_rss_mib,
            self.canonical_json_bytes,
            self.compact_text_bytes,
        )
        if any(value <= 0 for value in values):
            raise ValueError("large-inventory ceilings must be positive")

    def to_dict(self) -> dict[str, float | int]:
        """Return the committed metric names without an aggregate score."""

        return {
            "coldWallSeconds": self.cold_wall_seconds,
            "warmWallSeconds": self.warm_wall_seconds,
            "peakRssMiB": self.peak_rss_mib,
            "canonicalJsonBytes": self.canonical_json_bytes,
            "compactTextBytes": self.compact_text_bytes,
        }


@dataclass(frozen=True)
class CacheEvidence:
    """Cache counters observed on the CLI diagnostic channel."""

    hit_count: int
    miss_count: int
    rebuilt_count: int
    keys: tuple[str, ...]

    @property
    def observed(self) -> bool:
        """Whether the run exposed an inspectable cache decision."""

        return bool(self.keys)

    def to_dict(self) -> dict[str, Any]:
        """Return a bounded cache-evidence row."""

        return {
            "observed": self.observed,
            "hitCount": self.hit_count,
            "missCount": self.miss_count,
            "rebuiltCount": self.rebuilt_count,
            "keys": list(self.keys),
        }


@dataclass(frozen=True)
class RepresentationRun:
    """One measured public-CLI representation."""

    temperature: str
    sample: int
    representation: str
    process: MeasuredProcess
    output_bytes: int
    output_sha256: str
    cache: CacheEvidence
    normalized_sha256: str | None = None
    normalized_bytes: int | None = None
    analysis_fingerprint: str | None = None
    normalized_fields: tuple[str, ...] = ()
    error: str | None = None
    phase_progress: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return portable evidence without embedding output-sized content."""

        payload = {
            "representation": self.representation,
            "successful": self.error is None,
            "process": self.process.to_json(),
            "outputBytes": self.output_bytes,
            "outputSha256": self.output_sha256,
            "cache": self.cache.to_dict(),
            "phaseProgress": [dict(row) for row in self.phase_progress],
            "outsideProgressWallSeconds": round(
                max(
                    0.0,
                    self.process.wall_seconds
                    - sum(
                        float(row.get("elapsedSeconds", 0.0) or 0.0)
                        for row in self.phase_progress
                    ),
                ),
                6,
            ),
        }
        if self.error is not None:
            payload["error"] = self.error
        if self.normalized_sha256 is not None:
            payload["normalizedReport"] = {
                "bytes": self.normalized_bytes,
                "sha256": self.normalized_sha256,
                "normalizedFields": list(self.normalized_fields),
            }
        if self.analysis_fingerprint is not None:
            payload["analysisFingerprint"] = self.analysis_fingerprint
        return payload


__all__ = [
    "ANALYSIS_COMMAND_TEMPLATE",
    "LARGE_INVENTORY_GATE_SCHEMA",
    "REPRESENTATIONS",
    "REQUIRED_DECLARATION_COUNT",
    "REQUIRED_MODULE_COUNT",
    "REQUIRED_SAMPLE_COUNT",
    "REQUIRED_SOURCE_LINE_COUNT",
    "CacheEvidence",
    "LargeInventoryGateError",
    "MeasuredRunner",
    "ReportValidator",
    "RepresentationRun",
    "ScaleCeilings",
]
