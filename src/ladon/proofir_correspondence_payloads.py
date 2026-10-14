"""Scratch proposal: closed ProofIR payload validators for M1 correspondence.

These validators check evidence structure and identity only. They do not inspect
Lean source, rerun a checker, or turn attributed labels into proof authority.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ladon.correspondence_interpretation import (
    UnsupportedInterpretation,
    lower_formula,
    validate_interpretation,
)
from ladon.correspondence_maps import validate_object_map
from ladon.proof_slice import slice_identity

_SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")
_LOCAL_ID = re.compile(r"[^\s\x00-\x1f]{1,512}\Z")
_MAX_ROWS = 4096
_MAX_TEXT_BYTES = 1024 * 1024

INTERPRETATION_KEYS = frozenset(
    {"interpretationId", "record", "loweredFormula", "fidelity", "sourceRef"}
)
CORRESPONDENCE_KEYS = frozenset(
    {
        "correspondenceId",
        "interpretationRef",
        "slice",
        "objectMap",
        "obligations",
        "residuals",
        "dimensions",
        "checkRunRefs",
    }
)
DIMENSION_KEYS = frozenset(
    {
        "conditionalValidity",
        "premiseEstablishment",
        "parentSupport",
        "interpretationFidelity",
        "methodCorrespondence",
        "extractionCompleteness",
        "checkerAuthority",
    }
)
DIMENSION_VALUES = {
    "conditionalValidity": {"unresolved", "supported", "refuted"},
    "premiseEstablishment": {"unresolved", "supported", "refuted"},
    "parentSupport": {
        "unresolved",
        "supported-for-attributed-interpretation",
        "refuted-correspondence",
    },
    # M1 has no independent review artifact; only the non-promoting value is
    # currently accepted in correspondence dimensions.
    "interpretationFidelity": {"attributed-unreviewed"},
    "methodCorrespondence": {"unreviewed", "unresolved", "supported", "refuted"},
    "extractionCompleteness": {"selected-application", "incomplete", "complete"},
    "checkerAuthority": {"none", "lean-worker", "unavailable"},
}
OBLIGATION_KINDS = {
    "welltypedness",
    "conditional-validity",
    "representation-transport",
    "premise-supply",
    "premise-provider-validity",
    "conclusion-transfer",
}
OBLIGATION_STATES = {"open", "supported", "refuted", "unresolved"}


def _closed(value: Any, keys: frozenset[str], pointer: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ValueError(f"{pointer} requires exactly {sorted(keys)}")
    return value


def _identifier(value: Any, pointer: str) -> str:
    if not isinstance(value, str) or not _LOCAL_ID.fullmatch(value):
        raise ValueError(f"{pointer} must be a bounded non-empty identifier")
    return value


def _reference(value: Any, kind: str, pointer: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"artifactRef", "kind", "localId"}:
        raise ValueError(f"{pointer} requires an external typed artifact reference")
    if not isinstance(value["artifactRef"], str) or not _SHA256.fullmatch(value["artifactRef"]):
        raise ValueError(f"{pointer}/artifactRef must be a sha256 artifact identity")
    if value["kind"] != kind:
        raise ValueError(f"{pointer}/kind must be {kind}")
    return {
        "artifactRef": value["artifactRef"],
        "kind": kind,
        "localId": _identifier(value["localId"], pointer + "/localId"),
    }


def validate_interpretation_payload(payload: Any) -> dict[str, Any]:
    """Validate one closed attributed interpretation payload."""
    from ladon.correspondence_interpretation import LEGACY_PROFILE, LOWERING_PROFILE

    keys = INTERPRETATION_KEYS | ({"loweringProfile"} if isinstance(payload, dict)
                                and "loweringProfile" in payload else set())
    _closed(payload, keys, "/payload")
    profile = payload.get("loweringProfile", LEGACY_PROFILE)
    if profile not in {LEGACY_PROFILE, LOWERING_PROFILE}:
        raise ValueError("unsupported lowering profile")
    record = validate_interpretation(payload["record"], None, _profile=profile)
    identity = _identifier(payload["interpretationId"], "/payload/interpretationId")
    if identity != record["id"]:
        raise ValueError("interpretationId must equal the closed record id")
    fidelity = payload["fidelity"]
    if fidelity not in {"attributed-unreviewed", "reviewed-qualified"}:
        raise ValueError("unsupported interpretation fidelity label")
    try:
        lowered = lower_formula(record["formula"], record["symbols"], _profile=profile)
    except UnsupportedInterpretation:
        lowered = None
    if payload["loweredFormula"] != lowered:
        raise ValueError("loweredFormula must equal deterministic lowering or its opaque null")
    source_ref = _reference(payload["sourceRef"], "source-map", "/payload/sourceRef")
    result = {
        "interpretationId": identity,
        "record": record,
        "loweredFormula": lowered,
        "fidelity": fidelity,
        "sourceRef": source_ref,
    }

    if "loweringProfile" in payload:
        result["loweringProfile"] = profile
    return result


def _slice(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != "ladon-proof-slice-v1":
        raise ValueError("slice must be an actual ladon-proof-slice-v1 observation")
    if value.get("status") != "extracted" or value.get("complete") is not True:
        raise ValueError("slice must be complete actual extraction")
    from ladon.proof_slice_validation import validate_slice_shape

    validate_slice_shape(value)
    if not isinstance(value.get("sliceId"), str) or value["sliceId"] != slice_identity(value):
        raise ValueError("sliceId does not match the stable extraction identity")
    _validate_slice_receipts(value.get("processReceipts"))
    return copy.deepcopy(value)


def _validate_slice_receipts(receipts: Any) -> None:
    """Require bounded successful extraction receipts."""
    if (
        not isinstance(receipts, list)
        or not receipts
        or any(not isinstance(row, dict) or row.get("returncode") != 0 for row in receipts)
    ):
        raise ValueError("slice requires successful process receipts")
    if len(receipts) > 64:
        raise ValueError("slice has too many process receipts")


def validate_correspondence_payload(payload: Any) -> dict[str, Any]:
    """Validate correspondence structure without checking proposition truth."""
    _closed(payload, CORRESPONDENCE_KEYS, "/payload")
    identity = _identifier(payload["correspondenceId"], "/payload/correspondenceId")
    interpretation_ref = _reference(
        payload["interpretationRef"], "interpretation", "/payload/interpretationRef"
    )
    observed_slice = _slice(payload["slice"])
    object_map = validate_object_map(payload["objectMap"])
    if not isinstance(object_map, dict) or len(object_map) > _MAX_ROWS:
        raise ValueError("objectMap must be a bounded object")
    owned_map = {}
    for name, binder in object_map.items():
        owned_map[_identifier(name, "/payload/objectMap key")] = (
            _identifier(binder, f"/payload/objectMap/{name}") if isinstance(binder, str) else binder
        )
    owned_obligations = _obligations(payload["obligations"])
    owned_residuals = _residuals(payload["residuals"])
    owned_dimensions = _dimensions(payload["dimensions"])
    owned_checks = _check_refs(payload["checkRunRefs"])
    return {
        "correspondenceId": identity,
        "interpretationRef": interpretation_ref,
        "slice": observed_slice,
        "objectMap": owned_map,
        "obligations": owned_obligations,
        "residuals": owned_residuals,
        "dimensions": owned_dimensions,
        "checkRunRefs": owned_checks,
    }


def _obligations(obligations: Any) -> list[dict[str, Any]]:
    """Validate ordered obligation records and their bounded goals."""
    if not isinstance(obligations, list) or len(obligations) > _MAX_ROWS:
        raise ValueError("obligations must be a bounded ordered array")
    owned_obligations = []
    seen = set()
    for i, row in enumerate(obligations):
        pointer = f"/payload/obligations/{i}"
        _closed(row, frozenset({"id", "kind", "goal", "status"}), pointer)
        row_id = _identifier(row["id"], pointer + "/id")
        if row_id in seen:
            raise ValueError(f"{pointer}/id is duplicated")
        seen.add(row_id)
        if row["kind"] not in OBLIGATION_KINDS or row["status"] not in OBLIGATION_STATES:
            raise ValueError(f"{pointer} has an unsupported kind or status")
        if (
            not isinstance(row["goal"], str)
            or not row["goal"]
            or len(row["goal"].encode()) > _MAX_TEXT_BYTES
        ):
            raise ValueError(f"{pointer}/goal must be bounded non-empty text")
        owned_obligations.append(dict(row))
    return owned_obligations


def _residuals(residuals: Any) -> list[dict[str, Any]]:
    """Validate opaque residual records without interpreting their contents."""
    if not isinstance(residuals, list) or len(residuals) > _MAX_ROWS:
        raise ValueError("residuals must be a bounded ordered array")
    for i, row in enumerate(residuals):
        if not isinstance(row, dict) or not row or len(row) > 16:
            raise ValueError(f"/payload/residuals/{i} must be a bounded object")
    return copy.deepcopy(residuals)


def _dimensions(dimensions: Any) -> dict[str, str]:
    """Validate the closed set of correspondence evidence dimensions."""
    _closed(dimensions, DIMENSION_KEYS, "/payload/dimensions")
    owned_dimensions = {}
    for key, allowed in DIMENSION_VALUES.items():
        value = dimensions[key]
        if not isinstance(value, str) or value not in allowed:
            raise ValueError(f"/payload/dimensions/{key} is outside its closed enum")
        owned_dimensions[key] = value
    return owned_dimensions


def _check_refs(checks: Any) -> list[dict[str, str]]:
    """Validate unique references to existing native checker runs."""
    if not isinstance(checks, list) or len(checks) > _MAX_ROWS:
        raise ValueError("checkRunRefs must be a bounded ordered array")
    owned_checks = [
        _reference(row, "check-run", f"/payload/checkRunRefs/{i}") for i, row in enumerate(checks)
    ]
    if len({(row["artifactRef"], row["kind"], row["localId"]) for row in owned_checks}) != len(
        owned_checks
    ):
        raise ValueError("checkRunRefs must not contain duplicate references")
    return owned_checks


def validate_native_interpretation_batch(
    record: Mapping[str, Any],
    artifacts: list[Mapping[str, Any]],
    environment_ref: str,
    *,
    source_root: Path,
) -> dict[str, str]:
    """Find exactly one native interpretation matching the supplied record.

    This is the checker-boundary guard against a second, manually transcribed
    native interpretation. The returned ref is safe to retain in the plan; full
    envelope and external-reference closure remains validate_envelope_batch's job.
    """
    if source_root is None:
        raise ValueError("native source binding requires explicit source_root")
    expected = validate_interpretation(dict(record), source_root)
    by_id = {row.get("artifactId"): row for row in artifacts if isinstance(row, Mapping)}
    matches = [
        match
        for artifact in artifacts
        if (
            match := _matching_interpretation(
                artifact, by_id, expected, environment_ref, source_root
            )
        )
    ]
    if len(matches) != 1:
        raise ValueError("batch must contain exactly one matching native interpretation artifact")
    return matches[0]


def _matching_interpretation(
    artifact: Any,
    by_id: Mapping[str, Any],
    expected: Mapping[str, Any],
    environment_ref: str,
    source_root: Path,
) -> dict[str, str] | None:
    """Return a candidate reference only when its identity and source map agree."""
    if not _interpretation_envelope(artifact, environment_ref):
        return None
    from ladon.proofir_v3 import detached_content_id

    try:
        if artifact.get("artifactId") != detached_content_id(artifact):
            return None
        payload = validate_interpretation_payload(artifact.get("payload"))
        if payload["record"] != expected:
            return None
        source_ref = payload["sourceRef"]
        source_map = by_id.get(source_ref["artifactRef"])
        if not _source_map_matches(source_map, source_ref, expected, environment_ref, source_root):
            return None
    except (TypeError, ValueError):
        return None
    return _interpretation_reference(artifact, expected)


def _interpretation_envelope(artifact: Any, environment_ref: str) -> bool:
    """Check the candidate envelope kind and environment."""
    return (
        isinstance(artifact, Mapping)
        and artifact.get("artifactKind") == "proofir.interpretation"
        and artifact.get("environmentRef") == environment_ref
    )


def _interpretation_reference(
    artifact: Mapping[str, Any], expected: Mapping[str, Any]
) -> dict[str, str] | None:
    """Check the candidate identity and declared interpretation subject."""
    artifact_id, descriptors = artifact.get("artifactId"), artifact.get("subjectRefs")
    if not isinstance(artifact_id, str) or not _SHA256.fullmatch(artifact_id):
        return None
    if not isinstance(descriptors, list) or not any(
        isinstance(row, Mapping)
        and row.get("kind") == "interpretation"
        and row.get("localId") == expected["id"]
        for row in descriptors
    ):
        return None
    return {"artifactRef": artifact_id, "kind": "interpretation", "localId": expected["id"]}


def _source_map_matches(
    source_map: Any,
    source_ref: Mapping[str, str],
    expected: Mapping[str, Any],
    environment_ref: str,
    source_root: Path,
) -> bool:
    """Check source-map envelope identity, subject membership, and exact byte anchor."""
    if not _valid_source_map_envelope(source_map, environment_ref):
        return False
    subjects, body = source_map.get("subjectRefs"), source_map.get("payload")
    if not isinstance(subjects, list) or not isinstance(body, Mapping):
        return False
    if body.get("sourceMapId") != source_ref["localId"] or not any(
        isinstance(row, Mapping)
        and row.get("kind") == "source-map"
        and row.get("localId") == source_ref["localId"]
        for row in subjects
    ):
        return False
    return _has_exact_anchor(body.get("anchors"), expected, source_root)


def _valid_source_map_envelope(source_map: Any, environment_ref: str) -> bool:
    """Check source map kind, environment, and detached content identity."""
    if not isinstance(source_map, Mapping):
        return False
    if source_map.get("artifactKind") != "proofir.source-map":
        return False
    if source_map.get("environmentRef") != environment_ref:
        return False
    from ladon.proofir_v3 import detached_content_id

    try:
        return source_map.get("artifactId") == detached_content_id(source_map)
    except (TypeError, ValueError):
        return False


def _has_exact_anchor(anchors: Any, expected: Mapping[str, Any], source_root: Path) -> bool:
    """Require one anchor matching the source path, range, and UTF-8 digest."""
    if not isinstance(anchors, list):
        return False
    from ladon.correspondence_source import source_positions

    start, end, _ = source_positions(expected, source_root)
    source = expected["source"]
    return (
        sum(
            isinstance(row, Mapping)
            and row.get("subjectRef") == {"kind": "interpretation", "localId": expected["id"]}
            and row.get("sourcePath") == source["path"]
            and row.get("start") == start
            and row.get("end") == end
            and row.get("contentDigest") == "sha256:" + source["sha256"]
            for row in anchors
        )
        == 1
    )
