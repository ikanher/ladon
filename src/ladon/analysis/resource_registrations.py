"""Policy-bounded producer registrations for lexical resource settings."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon.coverage import (
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)
from ladon.finding_evidence import json_pointer_token
from ladon.resource_policy import (
    ResourceThreshold,
    ResourceThresholdPolicyError,
    matching_resource_threshold,
    normalize_resource_thresholds,
)


RESOURCE_REVIEW_COVERAGE = "module_dag.resource_review_inputs"
FINITE_RESOURCE_KIND = "policy_backed_finite_resource_setting"
_RESOURCE_POLICY_POINTER = "#/sections/module_dag/resourceReviewPolicy/thresholds"
_RESOURCE_POLICY_NONCLAIM = (
    "Repository review threshold only; not measured runtime, budget "
    "consumption, proof failure, proof authority, or theorem truth."
)


@dataclass(frozen=True)
class ResourcePolicyBinding:
    """One validated repository-backed finite-resource policy capture."""

    identity: str
    source: str
    path: str | None
    sha256: str
    thresholds: tuple[ResourceThreshold, ...]

    def threshold_ref(self, threshold: ResourceThreshold) -> str:
        """Return the canonical report pointer for one bound threshold."""

        return (
            f"{_RESOURCE_POLICY_POINTER}/"
            f"{json_pointer_token(threshold.identifier)}"
        )


def bind_resource_policy(
    payload: Mapping[str, Any] | None,
    identity: Mapping[str, Any] | None,
) -> ResourcePolicyBinding | None:
    """Bind only digest-matched explicit/discovered repository thresholds."""

    if payload is None or not _eligible_policy_identity(identity):
        return None
    thresholds = _normalized_thresholds(payload)
    if thresholds is None or not thresholds:
        return None
    normalized = [row.to_dict() for row in thresholds]
    if identity.get("resourceThresholds") != normalized:
        return None
    digest = _policy_payload_digest(payload)
    if digest is None or identity.get("sha256") != digest:
        return None
    return _policy_binding(payload, identity, digest, thresholds)


def attach_resource_policy_evidence(
    dag: dict[str, Any],
    policy: ResourcePolicyBinding | None,
) -> None:
    """Attach the canonical digest-bearing threshold rows used by producers."""

    if policy is None:
        dag.pop("resourceReviewPolicy", None)
        return
    dag["resourceReviewPolicy"] = {
        "id": policy.identity,
        "status": "selected",
        "source": policy.source,
        "path": policy.path,
        "sha256": policy.sha256,
        "authority": "repository_policy",
        "nonclaims": [_RESOURCE_POLICY_NONCLAIM],
        "thresholds": {
            threshold.identifier: _threshold_evidence(policy, threshold)
            for threshold in policy.thresholds
        },
    }


def register_resource_settings(
    registry: ProducerRegistry,
    surface: Mapping[str, Any],
    surface_index: int,
    *,
    policy: ResourcePolicyBinding | None,
) -> tuple[ProducerRegistry, int]:
    """Register unlimited rows and exact finite policy matches."""

    directives = surface.get("resourceDirectives")
    if not isinstance(directives, list):
        return registry, 0
    added = 0
    for directive_index, directive in enumerate(directives):
        registration = _resource_registration(
            directive,
            pointer=_resource_pointer(surface_index, directive_index),
            policy=policy,
        )
        if registration is None:
            continue
        registry = registry.register_producer(registration)
        added += 1
    return registry, added


def resource_registration_authority(registry: ProducerRegistry) -> str:
    """Return the bounded producer population's combined authority."""

    if any(row.kind == FINITE_RESOURCE_KIND for row in registry.producers.values()):
        return "lexical_text_and_repository_policy"
    return "lexical_text"


def _resource_registration(
    value: Any,
    *,
    pointer: str,
    policy: ResourcePolicyBinding | None,
) -> ProducerRegistration | None:
    if not _is_parsed_resource(value):
        return None
    if value.get("normalizedMeaning") == "unlimited":
        return _unlimited_resource_registration(value, pointer)
    return _finite_resource_registration(value, pointer, policy)


def _finite_resource_registration(
    value: Mapping[str, Any],
    pointer: str,
    policy: ResourcePolicyBinding | None,
) -> ProducerRegistration | None:
    if policy is None or not isinstance(value, dict):
        return None
    threshold = matching_resource_threshold(value, policy.thresholds)
    if threshold is None:
        return None
    policy_ref = policy.threshold_ref(threshold)
    value["pressure"] = "policy_backed"
    value["policyMatch"] = _policy_match(policy, threshold, policy_ref)
    return ProducerRegistration(
        identity=f"{value['id']}.review",
        kind=FINITE_RESOURCE_KIND,
        evidence_refs=(pointer, policy_ref),
        coverage_ref=RESOURCE_REVIEW_COVERAGE,
        authority="lexical_text_and_repository_policy",
        nonclaims=_policy_resource_nonclaims(value),
        action=InspectionAction(
            noun="resources",
            stable_id=str(value["id"]),
        ),
    )


def _unlimited_resource_registration(
    value: Mapping[str, Any],
    pointer: str,
) -> ProducerRegistration:
    return ProducerRegistration(
        identity=f"{value['id']}.review",
        kind="normalized_unlimited_resource_setting",
        evidence_refs=(pointer,),
        coverage_ref=RESOURCE_REVIEW_COVERAGE,
        authority=str(value.get("authority") or "lexical_text"),
        nonclaims=_row_nonclaims(value),
        action=InspectionAction(
            noun="resources",
            stable_id=str(value["id"]),
        ),
    )


def _policy_match(
    policy: ResourcePolicyBinding,
    threshold: ResourceThreshold,
    policy_ref: str,
) -> dict[str, Any]:
    return {
        "status": "matched",
        "policyId": policy.identity,
        "policySha256": policy.sha256,
        "thresholdId": threshold.identifier,
        "thresholdRef": policy_ref,
        "option": threshold.option,
        "minimumValue": threshold.minimum_value,
        "authority": "repository_policy",
        "nonclaim": _RESOURCE_POLICY_NONCLAIM,
    }


def _threshold_evidence(
    policy: ResourcePolicyBinding,
    threshold: ResourceThreshold,
) -> dict[str, Any]:
    return {
        **threshold.to_dict(),
        "policyId": policy.identity,
        "policySha256": policy.sha256,
        "authority": "repository_policy",
        "nonclaim": _RESOURCE_POLICY_NONCLAIM,
    }


def _resource_pointer(surface_index: int, directive_index: int) -> str:
    return (
        "#/sections/module_dag/audit_surfaces/"
        f"{surface_index}/resourceDirectives/{directive_index}"
    )


def _is_parsed_resource(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and bool(value.get("id"))
        and value.get("status") in {"parsed", "complete"}
    )


def _policy_resource_nonclaims(
    row: Mapping[str, Any],
) -> tuple[str, ...]:
    return tuple(dict.fromkeys((*_row_nonclaims(row), _RESOURCE_POLICY_NONCLAIM)))


def _row_nonclaims(row: Mapping[str, Any]) -> tuple[str, ...]:
    values = (
        row.get("nonclaim"),
        row.get("resultNonclaim"),
    )
    selected = tuple(str(value) for value in values if isinstance(value, str) and value)
    return selected or ("Lexical navigation evidence only.",)


def _normalized_thresholds(
    payload: Mapping[str, Any],
) -> tuple[ResourceThreshold, ...] | None:
    try:
        return normalize_resource_thresholds(payload)
    except ResourceThresholdPolicyError:
        return None


def _eligible_policy_identity(
    identity: Mapping[str, Any] | None,
) -> bool:
    return bool(
        identity is not None
        and identity.get("status") == "selected"
        and identity.get("source") in {"explicit", "discovered"}
    )


def _policy_payload_digest(payload: Mapping[str, Any]) -> str | None:
    try:
        encoded = json.dumps(
            dict(payload),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _policy_binding(
    payload: Mapping[str, Any],
    identity: Mapping[str, Any],
    digest: str,
    thresholds: tuple[ResourceThreshold, ...],
) -> ResourcePolicyBinding:
    policy_id = payload.get("id")
    selected_id = (
        policy_id
        if isinstance(policy_id, str) and policy_id
        else f"source-pattern-policy:{digest.removeprefix('sha256:')[:16]}"
    )
    path = identity.get("path")
    return ResourcePolicyBinding(
        identity=selected_id,
        source=str(identity["source"]),
        path=path if isinstance(path, str) else None,
        sha256=digest,
        thresholds=thresholds,
    )


__all__ = [
    "FINITE_RESOURCE_KIND",
    "RESOURCE_REVIEW_COVERAGE",
    "ResourcePolicyBinding",
    "attach_resource_policy_evidence",
    "bind_resource_policy",
    "register_resource_settings",
    "resource_registration_authority",
]
