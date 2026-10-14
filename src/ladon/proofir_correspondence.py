"""Native, source-bound correspondence producers; validation does not certify truth."""

from __future__ import annotations

import copy
import hashlib
import math
from collections.abc import Mapping, Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from ladon.correspondence_interpretation import (
    LOWERING_PROFILE,
    UnsupportedInterpretation,
    lower_formula,
    validate_interpretation,
)
from ladon.correspondence_source import source_positions
from ladon.proof_slice import digest as _digest
from ladon.proofir_correspondence_payloads import (
    DIMENSION_KEYS,
    validate_correspondence_payload,
    validate_interpretation_payload,
    validate_native_interpretation_batch,
)
from ladon.proofir_v3 import canonical_bytes, make_envelope, validate_envelope_batch

PRODUCER = {
    "name": "ladon-correspondence",
    "version": "typed-operators-v2",
    "implementation": "python",
    "buildDigest": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
_LIMITATION = {
    "id": "attributed-interpretation",
    "message": "Structured interpretation is attributed; no prose-fidelity review or proof authority is implied.",
}


def _native_envelope(
    kind: str,
    payload: Mapping[str, Any],
    environment_ref: str,
    subjects: Sequence[Mapping[str, str]],
    *,
    limitations: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    """Construct through the public ProofIR v3 builder and registered validators."""
    artifact = make_envelope(
        artifact_kind=kind,
        producer=PRODUCER,
        environment_ref=environment_ref,
        subject_refs=list(subjects),
        payload=dict(payload),
        coverage={
            "status": "complete",
            "population": {"kind": "artifact-subjects", "selector": {}},
            "universeKnown": True,
            "expected": len(subjects),
            "discovered": len(subjects),
            "decoded": len(subjects),
            "valid": len(subjects),
            "projected": len(subjects),
            "queryMatched": len(subjects),
            "omitted": [],
            "bounds": {"maxSubjects": 1000},
        },
        limitations=list(limitations),
    ).to_dict()
    return artifact


def interpretation_artifacts(
    record: Mapping[str, Any], environment_ref: str, *, source_root: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the exact attributed source-map and interpretation envelope pair."""
    root = source_root.resolve(strict=True)
    owned_record = validate_interpretation(dict(record), root)
    if not isinstance(environment_ref, str) or not environment_ref.startswith("sha256:"):
        raise ValueError("environment_ref must be a native sha256 environment identity")
    source_map_id = "source-map:" + owned_record["id"]
    interpretation_id = owned_record["id"]
    start, end, _quote = source_positions(owned_record, root)
    policy = {"version": "m1-explicit-path-range-v1"}
    policy_digest = "sha256:" + hashlib.sha256(canonical_bytes(policy)).hexdigest()
    source_map = make_envelope(
        artifact_kind="proofir.source-map",
        producer=PRODUCER,
        environment_ref=environment_ref,
        subject_refs=[
            {"kind": "source-map", "localId": source_map_id},
            {"kind": "interpretation", "localId": interpretation_id},
        ],
        payload={
            "sourceMapId": source_map_id,
            "anchors": [
                {
                    "subjectRef": {"kind": "interpretation", "localId": interpretation_id},
                    "sourcePath": owned_record["source"]["path"],
                    "module": "prose-source",
                    "declName": interpretation_id,
                    "start": start,
                    "end": end,
                    "contentDigest": "sha256:" + owned_record["source"]["sha256"],
                    "matchMethod": "path-range",
                }
            ],
            "policy": {**policy, "digest": policy_digest},
        },
        coverage={
            "status": "complete",
            "population": {"kind": "artifact-subjects", "selector": {}},
            "universeKnown": True,
            "expected": 1,
            "discovered": 1,
            "decoded": 1,
            "valid": 1,
            "projected": 1,
            "queryMatched": 1,
            "omitted": [],
            "bounds": {"maxSubjects": 1000},
        },
        limitations=[
            {
                "id": "authored-source-map",
                "message": "The quoted span and digest were revalidated at production time; this anchor does not review interpretation fidelity.",
            }
        ],
    ).to_dict()
    try:
        lowered = lower_formula(owned_record["formula"], owned_record["symbols"])
    except UnsupportedInterpretation:
        lowered = None
    payload = {
        "interpretationId": interpretation_id,
        "loweringProfile": LOWERING_PROFILE,
        "record": owned_record,
        "loweredFormula": lowered,
        "fidelity": "attributed-unreviewed",
        "sourceRef": {
            "artifactRef": source_map["artifactId"],
            "kind": "source-map",
            "localId": source_map_id,
        },
    }
    validate_interpretation_payload(payload)
    interpretation = _native_envelope(
        "proofir.interpretation",
        payload,
        environment_ref,
        [{"kind": "interpretation", "localId": interpretation_id}],
        limitations=[_LIMITATION],
    )
    return source_map, interpretation


def _as_exact_decimal_strings(value: Any) -> Any:
    """Copy receipt values, converting binary floats to exact decimal text."""
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite receipt float")
        return format(Decimal.from_float(value), "f")
    if isinstance(value, dict):
        return {key: _as_exact_decimal_strings(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_as_exact_decimal_strings(item) for item in value]
    if isinstance(value, tuple):
        return [_as_exact_decimal_strings(item) for item in value]
    return copy.deepcopy(value)


def _dimensions(result: Mapping[str, Any] | None) -> dict[str, str]:
    if result is None:
        return {
            "conditionalValidity": "unresolved",
            "premiseEstablishment": "unresolved",
            "parentSupport": "unresolved",
            "interpretationFidelity": "attributed-unreviewed",
            "methodCorrespondence": "unreviewed",
            "extractionCompleteness": "selected-application",
            "checkerAuthority": "none",
        }
    dimensions = {key: result[key] for key in DIMENSION_KEYS if key in result}
    if set(dimensions) != DIMENSION_KEYS:
        raise ValueError("checker result must explicitly provide all seven dimensions")
    # The current checker has no independent review artifact input. Never let a
    # caller-provided label promote this dimension or the interpretation payload.
    if dimensions["interpretationFidelity"] == "reviewed-qualified":
        raise ValueError("reviewed-qualified requires separate review evidence not present in M1")
    return dimensions


def correspondence_artifacts(
    plan: Mapping[str, Any],
    result: Mapping[str, Any] | None = None,
    *,
    environment_ref: str | None = None,
) -> dict[str, Any]:
    """Produce one native correspondence envelope from the immutable prepared plan.

    `plan` must retain the exact native `interpretationRef` bound during prepare;
    callers cannot supply a second independently authored interpretation record.
    """
    if not isinstance(plan, Mapping) or not isinstance(plan.get("planId"), str):
        raise TypeError("correspondence requires an identity-bearing prepared plan")
    interpretation_ref = plan.get("interpretationRef")
    if interpretation_ref is None:
        raise ValueError("prepared plan is missing its batch-validated interpretationRef")
    environment = environment_ref or plan.get("slice", {}).get("environment")
    if not isinstance(environment, str) or not environment.startswith("sha256:"):
        raise ValueError("correspondence requires the extracted slice environment identity")
    payload = _correspondence_payload(plan, result)
    validate_correspondence_payload(payload)
    return _native_envelope(
        "proofir.correspondence",
        payload,
        environment,
        [{"kind": "correspondence", "localId": payload["correspondenceId"]}],
        limitations=[
            {
                "id": "structural-correspondence-only",
                "message": "Payload validation establishes structure and references, not truth, fidelity, completeness, or checker authority.",
            }
        ],
    )


def _correspondence_payload(
    plan: Mapping[str, Any], result: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Copy plan evidence and attach only references and statuses from a result."""
    result_copy = _as_exact_decimal_strings(dict(result)) if result is not None else None
    check_refs = [] if result_copy is None else result_copy.get("checkRunRefs", [])
    if result_copy is not None and result_copy.get("checks") and not check_refs:
        raise ValueError(
            "checked results require existing native check-run refs; no receipts are fabricated"
        )
    payload = {
        "correspondenceId": "correspondence:" + plan["planId"],
        "interpretationRef": copy.deepcopy(plan["interpretationRef"]),
        "slice": _as_exact_decimal_strings(plan["slice"]),
        "objectMap": copy.deepcopy(plan["objectMap"]),
        "obligations": copy.deepcopy(plan["obligations"]),
        "residuals": copy.deepcopy(plan["residuals"] if result is None else result["residuals"]),
        "dimensions": _dimensions(result_copy),
        "checkRunRefs": copy.deepcopy(check_refs),
    }
    statuses = {row["obligation"]: row["status"] for row in (result or {}).get("checks", [])}
    for row in payload["obligations"]:
        row["status"] = statuses.get(row["id"], "open")
    return payload


def bind_native_interpretation(
    plan: Mapping[str, Any], artifacts: list[Mapping[str, Any]], *, source_root: Path
) -> dict[str, Any]:
    """Bind a prepared plan only to its exact interpretation in the validated batch."""
    validate_envelope_batch(artifacts)
    owned = copy.deepcopy(dict(plan))
    proof_slice = owned.get("slice")
    environment = proof_slice.get("environment") if isinstance(proof_slice, Mapping) else None
    ref = validate_native_interpretation_batch(
        owned.get("interpretation"), artifacts, environment, source_root=source_root
    )
    native = next(row for row in artifacts if row["artifactId"] == ref["artifactRef"])
    if native["payload"].get("loweringProfile") != LOWERING_PROFILE:
        raise ValueError("native lowering profile requires fresh typed interpretation production")
    previous = owned.get("interpretationRef")
    if previous is not None and previous != ref:
        raise ValueError("prepared plan's interpretationRef does not match its interpretation")
    owned["interpretationRef"] = ref
    unsigned = {key: value for key, value in owned.items() if key != "planId"}
    owned["planId"] = _digest(unsigned)
    return owned


__all__ = [
    "bind_native_interpretation",
    "correspondence_artifacts",
    "interpretation_artifacts",
]
