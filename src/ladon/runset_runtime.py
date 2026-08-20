"""Runtime values shared by the serial runset orchestrator."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ladon.runset_contract import (
    EntryValidity,
    RunsetBundle,
    RunsetEntry,
    RunsetResources,
    require_sha256,
)

TERMINAL_ANALYSIS_STATUSES = frozenset(
    {"complete", "partial", "failed", "interrupted"}
)
REUSABLE_ARTIFACTS = {
    "source-index": "source_index_fingerprint",
    "lean-cache": "lean_cache_fingerprint",
}


@dataclass(frozen=True)
class AnalysisOutcome:
    """One ordinary analyzer result awaiting atomic bundle publication."""

    status: str
    report_bytes: bytes | None = None
    diagnostics: tuple[Mapping[str, Any], ...] = ()
    resource_counters: Mapping[str, int] = field(default_factory=dict)
    reusable_artifacts: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in TERMINAL_ANALYSIS_STATUSES:
            raise ValueError(f"unsupported analysis outcome {self.status!r}")
        if self.status == "complete" and self.report_bytes is None:
            raise ValueError("complete analysis outcome requires canonical report bytes")
        validate_counters(self.resource_counters)
        unknown = set(self.reusable_artifacts) - set(REUSABLE_ARTIFACTS)
        if unknown:
            raise ValueError(f"unknown reusable artifact kinds: {sorted(unknown)}")
        invalid = [
            kind
            for kind, artifact in self.reusable_artifacts.items()
            if not isinstance(artifact, ReusableArtifact)
        ]
        if invalid:
            raise ValueError(
                "reusable artifacts require explicit fingerprint evidence: "
                f"{sorted(invalid)}"
            )


@dataclass(frozen=True)
class ReusableArtifact:
    """An immutable reuse handle returned with its exact validity identity."""

    fingerprint: str
    value: Any

    def __post_init__(self) -> None:
        require_sha256(self.fingerprint, "reusable artifact fingerprint")


@dataclass(frozen=True)
class RunsetAnalysisRequest:
    """Inputs passed to the existing ordinary-analysis integration."""

    entry: RunsetEntry
    repository_root: Path
    validity: EntryValidity
    resources: RunsetResources
    cancel_event: threading.Event
    shared_artifacts: Mapping[str, Any]


@dataclass(frozen=True)
class RunsetExecutionResult:
    """Published bundle plus aggregate process-policy classification."""

    bundle: RunsetBundle
    bundle_path: Path
    state_path: Path
    exit_code: int
    analyzer_launches: int
    resume_hits: int


class SharedArtifactPool:
    """In-memory artifacts keyed by exact full reuse fingerprints."""

    def __init__(self) -> None:
        self._artifacts: dict[tuple[str, str], Any] = {}

    def compatible(self, validity: EntryValidity) -> dict[str, Any]:
        """Return only artifacts whose kind and fingerprint both agree."""

        found: dict[str, Any] = {}
        for kind, attribute in REUSABLE_ARTIFACTS.items():
            fingerprint = getattr(validity, attribute)
            if fingerprint is None:
                continue
            key = (kind, fingerprint)
            if key in self._artifacts:
                found[kind] = self._artifacts[key]
        return found

    def publish(
        self,
        validity: EntryValidity,
        artifacts: Mapping[str, Any],
    ) -> None:
        """Publish complete-run artifacts without cross-fingerprint fallback."""

        for kind, raw in artifacts.items():
            if not isinstance(raw, ReusableArtifact):
                raise TypeError(
                    f"analysis returned {kind} without fingerprint evidence"
                )
            attribute = REUSABLE_ARTIFACTS[kind]
            fingerprint = getattr(validity, attribute)
            if fingerprint is None:
                raise ValueError(
                    f"analysis returned {kind} without its validity fingerprint"
                )
            if raw.fingerprint != fingerprint:
                raise ValueError(
                    f"analysis returned {kind} with a mismatched fingerprint"
                )
            self._artifacts[(kind, fingerprint)] = raw.value


AnalysisRunner = Callable[[RunsetAnalysisRequest], AnalysisOutcome]
ValidityResolver = Callable[[RunsetEntry, Path], EntryValidity]
EventSink = Callable[[Mapping[str, Any]], None]


def validate_counters(counters: Mapping[str, int]) -> None:
    """Require bounded JSON integer counters at the bundle boundary."""

    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in counters.values()
    ):
        raise ValueError("resource counters must be non-negative integers")
