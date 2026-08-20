"""Generic report-producer and evidence-stratum registrations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from ladon.coverage_base import CoverageError


@dataclass(frozen=True)
class InspectionAction:
    """One caller-neutral ordinary CLI action attached to producer evidence."""

    noun: str
    filters: tuple[tuple[str, str], ...] = ()
    stable_id: str | None = None

    def __post_init__(self) -> None:
        if not self.noun:
            raise CoverageError("inspection action noun must be non-empty")
        if any(not key or not value for key, value in self.filters):
            raise CoverageError("inspection filters must be non-empty pairs")

    def to_dict(self) -> dict[str, Any]:
        """Return a structured `ladon inspect` action."""

        arguments = [
            "inspect",
            self.noun,
            *(
                item
                for key, value in self.filters
                for item in ("--filter", f"{key}={value}")
            ),
        ]
        if self.stable_id:
            arguments.extend(("--id", self.stable_id))
        return {"command": "ladon", "arguments": arguments}


@dataclass(frozen=True)
class ProducerRegistration:
    """Generic row consumed later by report-owned review-region synthesis."""

    identity: str
    kind: str
    evidence_refs: tuple[str, ...]
    coverage_ref: str
    authority: str
    nonclaims: tuple[str, ...]
    action: InspectionAction

    def __post_init__(self) -> None:
        if not all((self.identity, self.kind, self.coverage_ref, self.authority)):
            raise CoverageError(
                "producer registration identity fields must be non-empty"
            )
        if not self.evidence_refs or any(not ref for ref in self.evidence_refs):
            raise CoverageError(
                "producer registration requires canonical evidence references"
            )
        if not self.nonclaims or any(not row for row in self.nonclaims):
            raise CoverageError(
                "producer registration requires explicit nonclaims"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return the generic producer registration shape."""

        return {
            "id": self.identity,
            "kind": self.kind,
            "evidenceRefs": list(self.evidence_refs),
            "coverageRef": self.coverage_ref,
            "authority": self.authority,
            "nonclaims": list(self.nonclaims),
            "inspectionAction": self.action.to_dict(),
        }


@dataclass(frozen=True)
class EvidenceStratumRegistration:
    """Finite, producer-neutral review stratum registered before projection."""

    identity: str
    evidence_kind: str
    severity: str
    status: str
    population: str
    role: str
    coverage_ref: str
    authority: str

    def __post_init__(self) -> None:
        values = (
            self.identity,
            self.evidence_kind,
            self.severity,
            self.status,
            self.population,
            self.role,
            self.coverage_ref,
            self.authority,
        )
        if any(not value for value in values):
            raise CoverageError(
                "evidence-stratum registration fields must be non-empty"
            )

    def to_dict(self) -> dict[str, str]:
        """Return one producer-neutral stratum descriptor."""

        return {
            "id": self.identity,
            "evidenceKind": self.evidence_kind,
            "severity": self.severity,
            "status": self.status,
            "population": self.population,
            "role": self.role,
            "coverageRef": self.coverage_ref,
            "authority": self.authority,
        }


@dataclass(frozen=True)
class ProducerRegistry:
    """Immutable registrations consumed by later report-owned integration."""

    producers: Mapping[str, ProducerRegistration] = field(default_factory=dict)
    strata: Mapping[str, EvidenceStratumRegistration] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        producer_rows = dict(self.producers)
        stratum_rows = dict(self.strata)
        _validate_registration_keys(producer_rows, "producer")
        _validate_registration_keys(stratum_rows, "stratum")
        object.__setattr__(
            self,
            "producers",
            MappingProxyType(dict(sorted(producer_rows.items()))),
        )
        object.__setattr__(
            self,
            "strata",
            MappingProxyType(dict(sorted(stratum_rows.items()))),
        )

    def register_producer(
        self,
        registration: ProducerRegistration,
    ) -> ProducerRegistry:
        """Return a registry containing one unique producer registration."""

        return ProducerRegistry(
            producers=_registered_row(
                self.producers,
                registration.identity,
                registration,
                "producer",
            ),
            strata=self.strata,
        )

    def register_stratum(
        self,
        registration: EvidenceStratumRegistration,
    ) -> ProducerRegistry:
        """Return a registry containing one unique stratum registration."""

        return ProducerRegistry(
            producers=self.producers,
            strata=_registered_row(
                self.strata,
                registration.identity,
                registration,
                "stratum",
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return deterministic generic producer and stratum registrations."""

        return {
            "producers": {
                identity: row.to_dict()
                for identity, row in self.producers.items()
            },
            "strata": {
                identity: row.to_dict()
                for identity, row in self.strata.items()
            },
        }


def _validate_registration_keys(
    rows: Mapping[str, Any],
    label: str,
) -> None:
    for identity, row in rows.items():
        if identity != row.identity:
            raise CoverageError(
                f"{label} registry key must match registration identity"
            )


def _registered_row(
    rows: Mapping[str, Any],
    identity: str,
    registration: Any,
    label: str,
) -> dict[str, Any]:
    result = dict(rows)
    existing = result.get(identity)
    if existing is not None and existing != registration:
        raise CoverageError(
            f"{label} identity already registered: {identity}"
        )
    result[identity] = registration
    return result


__all__ = [
    "EvidenceStratumRegistration",
    "InspectionAction",
    "ProducerRegistration",
    "ProducerRegistry",
]
