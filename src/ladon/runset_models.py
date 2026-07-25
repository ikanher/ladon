"""Typed normalized models for runset, validity, and bundle artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping

from ladon.runset_validation import (
    ENTRY_ID_PATTERN,
    SUPPORTED_BACKENDS,
    SUPPORTED_PROJECTIONS,
    RunsetManifestError,
    copy_json_mapping,
    nonnegative_integer_mapping,
    positive_optional_integer,
    positive_optional_number,
    require_optional_sha256,
    require_portable_relative_path,
    require_sha256,
    validate_diagnostics,
    validate_entry_collection,
    validate_portable_options,
    validate_scope,
)


RUNSET_ARTIFACT_KIND = "ladon_analysis_runset"
BUNDLE_ARTIFACT_KIND = "ladon_analysis_bundle"
STATE_ARTIFACT_KIND = "ladon_analysis_runset_state"
RUNSET_SCHEMA_VERSION = 1
BUNDLE_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1
RUNSET_SCHEMA = "ladon-analysis-runset-v1"
BUNDLE_SCHEMA = "ladon-analysis-bundle-v1"
STATE_SCHEMA = "ladon-analysis-runset-state-v1"
ENTRY_STATUSES = frozenset(
    {
        "complete",
        "resume-hit",
        "skipped",
        "partial",
        "failed",
        "interrupted",
    }
)
REPORT_VERSION_NAMES = {
    "v2": "ladon-report-v2",
    "v3": "ladon-report-v3",
}


@dataclass(frozen=True)
class RunsetPolicy:
    """Finite execution and failure policy for one runset."""

    stop_on_required_failure: bool = True
    continue_on_advisory_failure: bool = True
    concurrency: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.stop_on_required_failure, bool):
            raise RunsetManifestError("stopOnRequiredFailure must be boolean")
        if not isinstance(self.continue_on_advisory_failure, bool):
            raise RunsetManifestError("continueOnAdvisoryFailure must be boolean")
        if self.concurrency != 1:
            raise RunsetManifestError(
                "runset concurrency must be 1; no bounded parallel mode is supported"
            )

    def to_payload(self) -> dict[str, Any]:
        """Return the normalized policy shape."""

        return {
            "concurrency": self.concurrency,
            "stopOnRequiredFailure": self.stop_on_required_failure,
            "continueOnAdvisoryFailure": self.continue_on_advisory_failure,
        }


@dataclass(frozen=True)
class RunsetResources:
    """Optional finite resource ceilings forwarded to ordinary analyses."""

    overall_timeout_seconds: float | None = None
    max_rss_mib: int | None = None
    max_report_bytes: int | None = None

    def __post_init__(self) -> None:
        positive_optional_number(
            self.overall_timeout_seconds,
            "resources.overallTimeoutSeconds",
        )
        positive_optional_integer(self.max_rss_mib, "resources.maxRssMiB")
        positive_optional_integer(
            self.max_report_bytes,
            "resources.maxReportBytes",
        )

    def to_payload(self) -> dict[str, Any]:
        """Return all explicit resource fields in stable order."""

        return {
            "maxReportBytes": self.max_report_bytes,
            "maxRssMiB": self.max_rss_mib,
            "overallTimeoutSeconds": self.overall_timeout_seconds,
        }


@dataclass(frozen=True)
class RunsetEntry:
    """One ordinary single-root analysis requested by a runset."""

    identifier: str
    root: str
    scope: Mapping[str, Any]
    backend: str
    projection: str
    output: str
    required: bool
    report_version: str = "v3"
    options: Mapping[str, Any] = field(default_factory=dict)
    depends_on: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not ENTRY_ID_PATTERN.fullmatch(self.identifier):
            raise RunsetManifestError(
                f"invalid runset entry id {self.identifier!r}"
            )
        require_portable_relative_path(self.root, f"entry {self.identifier} root")
        require_portable_relative_path(
            self.output,
            f"entry {self.identifier} output",
        )
        self._validate_report_selection()
        validate_scope(self.identifier, self.scope)
        copy_json_mapping(self.options, f"entry {self.identifier} options")
        validate_portable_options(self.identifier, self.options)
        if len(set(self.depends_on)) != len(self.depends_on):
            raise RunsetManifestError(
                f"entry {self.identifier} has duplicate dependencies"
            )
        if not isinstance(self.required, bool):
            raise RunsetManifestError(
                f"entry {self.identifier} required must be boolean"
            )

    def _validate_report_selection(self) -> None:
        if not self.output.endswith(".json"):
            raise RunsetManifestError(
                f"entry {self.identifier} output must be a JSON file"
            )
        if self.backend not in SUPPORTED_BACKENDS:
            raise RunsetManifestError(
                f"entry {self.identifier} has unsupported backend {self.backend!r}"
            )
        if self.projection not in SUPPORTED_PROJECTIONS:
            raise RunsetManifestError(
                f"entry {self.identifier} has unsupported projection "
                f"{self.projection!r}"
            )
        if self.report_version not in REPORT_VERSION_NAMES:
            raise RunsetManifestError(
                f"entry {self.identifier} has unsupported reportVersion "
                f"{self.report_version!r}"
            )
        if self.report_version != "v3" and self.projection != "review":
            raise RunsetManifestError(
                f"entry {self.identifier} projection requires reportVersion v3"
            )

    @property
    def run_identity(self) -> str:
        """Return a stable identity that distinguishes root/scope/backend."""

        digest = payload_digest(self.to_payload())[:24]
        return f"run:{self.identifier}:{digest}"

    def to_payload(self) -> dict[str, Any]:
        """Return the normalized manifest entry shape."""

        return {
            "backend": self.backend,
            "dependsOn": list(self.depends_on),
            "id": self.identifier,
            "options": copy_json_mapping(
                self.options,
                f"entry {self.identifier} options",
            ),
            "output": self.output,
            "projection": self.projection,
            "reportVersion": self.report_version,
            "required": self.required,
            "root": self.root,
            "scope": copy_json_mapping(
                self.scope,
                f"entry {self.identifier} scope",
            ),
        }


@dataclass(frozen=True)
class RunsetManifest:
    """Validated v1 plan with deterministic normalized identity."""

    name: str
    repository: str
    entries: tuple[RunsetEntry, ...]
    policy: RunsetPolicy = field(default_factory=RunsetPolicy)
    resources: RunsetResources = field(default_factory=RunsetResources)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    artifact_kind: str = RUNSET_ARTIFACT_KIND
    schema_version: int = RUNSET_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.artifact_kind != RUNSET_ARTIFACT_KIND:
            raise RunsetManifestError(
                f"unsupported runset artifactKind {self.artifact_kind!r}"
            )
        if (
            not isinstance(self.schema_version, int)
            or isinstance(self.schema_version, bool)
            or self.schema_version != RUNSET_SCHEMA_VERSION
        ):
            raise RunsetManifestError(
                f"unsupported runset schemaVersion {self.schema_version!r}; "
                f"supported major is {RUNSET_SCHEMA_VERSION}"
            )
        if not self.name:
            raise RunsetManifestError("runset name must be non-empty")
        require_portable_relative_path(self.repository, "runset repository")
        if not self.entries:
            raise RunsetManifestError("runset must contain at least one entry")
        copy_json_mapping(self.metadata, "runset metadata")
        validate_entry_collection(self.entries)

    @property
    def fingerprint(self) -> str:
        """Return the normalized manifest fingerprint."""

        return f"sha256:{payload_digest(self.to_payload())}"

    @property
    def execution_order(self) -> tuple[RunsetEntry, ...]:
        """Return stable dependency order, preserving manifest ties."""

        by_id = {entry.identifier: entry for entry in self.entries}
        visited: set[str] = set()
        ordered: list[RunsetEntry] = []

        def visit(entry: RunsetEntry) -> None:
            if entry.identifier in visited:
                return
            for dependency in entry.depends_on:
                visit(by_id[dependency])
            visited.add(entry.identifier)
            ordered.append(entry)

        for entry in self.entries:
            visit(entry)
        return tuple(ordered)

    def to_payload(self) -> dict[str, Any]:
        """Return the schema-facing normalized manifest."""

        return {
            "artifactKind": self.artifact_kind,
            "schemaVersion": self.schema_version,
            "name": self.name,
            "repository": self.repository,
            "policy": self.policy.to_payload(),
            "resources": self.resources.to_payload(),
            "metadata": copy_json_mapping(self.metadata, "runset metadata"),
            "entries": [entry.to_payload() for entry in self.entries],
        }


@dataclass(frozen=True)
class EntryValidity:
    """Full fingerprints used for report validity and compatible cache reuse."""

    input_fingerprint: str
    source_index_fingerprint: str | None = None
    lean_cache_fingerprint: str | None = None
    components: Mapping[str, str] = field(default_factory=dict)
    reuse_unavailable_reasons: Mapping[str, str] = field(default_factory=dict)
    reuse_bypass_reasons: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_sha256(self.input_fingerprint, "input fingerprint")
        require_optional_sha256(
            self.source_index_fingerprint,
            "source-index fingerprint",
        )
        require_optional_sha256(
            self.lean_cache_fingerprint,
            "Lean-cache fingerprint",
        )
        for name, value in self.components.items():
            if not name:
                raise ValueError("validity component names must be non-empty")
            require_sha256(value, f"validity component {name}")
        self._validate_reuse_reasons()

    def _validate_reuse_reasons(self) -> None:
        """Require one explicit, non-conflicting reason per unsupported cache."""

        overlap = (
            set(self.reuse_unavailable_reasons)
            & set(self.reuse_bypass_reasons)
        )
        if overlap:
            raise ValueError(
                f"reuse kinds cannot be unavailable and bypassed: {sorted(overlap)}"
            )
        fingerprinted = {
            "source-index": self.source_index_fingerprint,
            "lean-cache": self.lean_cache_fingerprint,
        }
        for status, reasons in (
            ("unavailable", self.reuse_unavailable_reasons),
            ("bypassed", self.reuse_bypass_reasons),
        ):
            for kind, reason in reasons.items():
                if kind not in fingerprinted:
                    raise ValueError(f"unknown {status} reuse kind {kind!r}")
                if fingerprinted[kind] is not None:
                    raise ValueError(
                        f"fingerprinted reuse kind {kind!r} cannot be {status}"
                    )
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError(
                        f"{status} reuse kind {kind!r} requires a reason"
                    )

    def to_payload(self) -> dict[str, Any]:
        """Return all inspectible validity and reuse identities."""

        return {
            "components": dict(sorted(self.components.items())),
            "inputFingerprint": self.input_fingerprint,
            "leanCacheFingerprint": self.lean_cache_fingerprint,
            "sourceIndexFingerprint": self.source_index_fingerprint,
        }

    def analysis_payload(self) -> dict[str, Any]:
        """Return only semantic inputs that determine resume validity."""

        return {
            "components": dict(sorted(self.components.items())),
            "inputFingerprint": self.input_fingerprint,
        }


@dataclass(frozen=True)
class ReportReference:
    """Portable identity of one atomically published canonical report."""

    path: str
    version: str
    sha256: str
    bytes: int

    def __post_init__(self) -> None:
        require_portable_relative_path(self.path, "bundle report path")
        if self.version not in REPORT_VERSION_NAMES.values():
            raise ValueError(f"unsupported canonical report version {self.version!r}")
        require_sha256(self.sha256, "report content hash")
        if (
            not isinstance(self.bytes, int)
            or isinstance(self.bytes, bool)
            or self.bytes < 0
        ):
            raise ValueError("report byte count must be non-negative")

    def to_payload(self) -> dict[str, Any]:
        """Return the deterministic bundle report reference."""

        return {
            "bytes": self.bytes,
            "path": self.path,
            "sha256": self.sha256,
            "version": self.version,
        }


@dataclass(frozen=True)
class BundleEntry:
    """One terminal, independently authoritative bundle entry."""

    identifier: str
    run_identity: str
    root: str
    scope: Mapping[str, Any]
    required: bool
    status: str
    entry_fingerprint: str
    validity: EntryValidity
    report: ReportReference | None
    reuse: Mapping[str, Any]
    phase_summary: Mapping[str, int]
    resource_counters: Mapping[str, int]
    diagnostics: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.status not in ENTRY_STATUSES:
            raise ValueError(f"unsupported bundle entry status {self.status!r}")
        require_sha256(self.entry_fingerprint, "entry fingerprint")
        nonnegative_integer_mapping(self.phase_summary, "phase summary")
        nonnegative_integer_mapping(
            self.resource_counters,
            "resource counters",
        )
        validate_diagnostics(self.diagnostics)
        if self.status in {"complete", "resume-hit"} and self.report is None:
            raise ValueError(f"{self.status} bundle entry requires a report")

    def to_payload(self) -> dict[str, Any]:
        """Return one normalized bundle entry without volatile timing."""

        return {
            "diagnostics": [
                copy_json_mapping(row, "bundle diagnostic")
                for row in self.diagnostics
            ],
            "entryFingerprint": self.entry_fingerprint,
            "id": self.identifier,
            "phaseSummary": dict(sorted(self.phase_summary.items())),
            "report": self.report.to_payload() if self.report else None,
            "required": self.required,
            "resourceCounters": dict(sorted(self.resource_counters.items())),
            "reuse": copy_json_mapping(self.reuse, "bundle reuse record"),
            "root": self.root,
            "runIdentity": self.run_identity,
            "scope": copy_json_mapping(self.scope, "bundle scope"),
            "status": self.status,
            "validity": self.validity.to_payload(),
        }


@dataclass(frozen=True)
class RunsetBundle:
    """Deterministic relative-path index over independent reports."""

    name: str
    runset_fingerprint: str
    entries: tuple[BundleEntry, ...]
    schema: str = BUNDLE_SCHEMA
    artifact_kind: str = BUNDLE_ARTIFACT_KIND
    schema_version: int = BUNDLE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        require_sha256(self.runset_fingerprint, "runset fingerprint")
        if self.schema != BUNDLE_SCHEMA:
            raise ValueError(f"unsupported bundle schema {self.schema!r}")

    @property
    def completeness(self) -> str:
        """Summarize terminal entry states without hiding advisory failures."""

        statuses = {entry.status for entry in self.entries}
        if "interrupted" in statuses:
            return "interrupted"
        if statuses <= {"complete", "resume-hit"}:
            return "complete"
        return "partial"

    def to_payload(self) -> dict[str, Any]:
        """Return stable bundle bytes independent of host and wall time."""

        return {
            "artifactKind": self.artifact_kind,
            "schema": self.schema,
            "schemaVersion": self.schema_version,
            "name": self.name,
            "runsetFingerprint": self.runset_fingerprint,
            "completeness": self.completeness,
            "entries": [entry.to_payload() for entry in self.entries],
        }

    def to_bytes(self) -> bytes:
        """Serialize deterministic indented UTF-8 JSON."""

        return canonical_json_bytes(self.to_payload())


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Return stable JSON bytes for manifests, state, and bundles."""

    return (
        json.dumps(payload, indent=2, sort_keys=True, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def content_sha256(content: bytes) -> str:
    """Return the labeled SHA-256 used at artifact boundaries."""

    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def payload_digest(payload: Mapping[str, Any]) -> str:
    """Return an unlabeled digest for compact embedded identities."""

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
