"""Small, prover-neutral ProofIR v3 evidence kernel.

This module deliberately does not parse Lean terms.  Lean workers provide
environment-scoped opaque subject identities; Ladon owns the envelope,
canonical identity, bounds, and reference-shape checks around them.

ladon-quality: reviewed-schema-hotspot
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, NoReturn

from ladon.bounded_graph import cyclic_components
from ladon.proofir_v3_batch import preflight as _preflight_batch
from ladon.proofir_v3_batch import resolve_limits as _resolve_batch_limits

PROOFIR_V3_VERSION = "3.0"
SAFE_INTEGER_MIN = -(2**53 - 1)
SAFE_INTEGER_MAX = 2**53 - 1
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024
MAX_BATCH_BYTES = 32 * 1024 * 1024
MAX_ARTIFACTS = 10_000
# Compatibility name for callers that only configure one canonical artifact.
MAX_CANONICAL_BYTES = MAX_ARTIFACT_BYTES
MAX_DEPTH = 64
MAX_COLLECTION_ITEMS = 10_000
MAX_COMPILED_MODULES = 32_768
MAX_STRING_BYTES = 1 * 1024 * 1024
REQUIRED_ENVELOPE_KEYS = frozenset(
    {
        "proofirVersion",
        "artifactKind",
        "artifactId",
        "producer",
        "environmentRef",
        "subjectRefs",
        "coverage",
        "payload",
        "limitations",
        "extensions",
    }
)
# This is deliberately closed: adding a semantic kind requires an explicit
# schema/validator rather than silently accepting an arbitrary payload.
SUPPORTED_ARTIFACT_KINDS = frozenset(
    {
        "proofir.claim",
        "proofir.derivation",
        "proofir.plan",
        "proofir.attempt-log",
        "proofir.environment",
        "proofir.check-run",
        "proofir.source-map",
        "proofir.attachment-set",
        "proofir.governance-observation",
    }
)
LEGACY_ARTIFACT_KINDS = frozenset(
    {
        "proofir_bridge_index",
        "proof_ir_lean_surface_bundle",
        "proof_ir_lean_replay_provenance",
        "proof_ir_v2_obligation_dag",
        "proof_ir_v2_obligation_dag_check_witness",
        "proof_surface_witness",
        "ladon_proof_surface_witness",
    }
)


@dataclass(frozen=True)
class ProofIRV3Diagnostic:
    stage: str
    code: str
    pointer: str
    message: str
    artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "code": self.code,
            "pointer": self.pointer,
            "message": self.message,
            "artifactId": self.artifact_id,
        }


class ProofIRV3Error(ValueError):
    """A v3 envelope is malformed or exceeds a configured bound."""

    def __init__(self, message: str, diagnostic: ProofIRV3Diagnostic | None = None):
        super().__init__(message)
        self.diagnostic = diagnostic or ProofIRV3Diagnostic(
            "envelope-valid", "invalid-envelope", "", message
        )


def _escape(part: str) -> str:
    return str(part).replace("~", "~0").replace("/", "~1")


def _fail(
    stage: str,
    code: str,
    pointer: str,
    message: str,
    value: Mapping[str, Any] | None = None,
) -> None:
    artifact_id = value.get("artifactId") if value is not None else None
    raise ProofIRV3Error(
        message, ProofIRV3Diagnostic(stage, code, pointer, message, artifact_id)
    )


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({_freeze(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


@dataclass(frozen=True)
class ProofIRV3Artifact:
    """Validated envelope with canonical content identity."""

    payload: dict[str, Any]
    content_id: str

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(_thaw(self.payload))


def canonical_bytes(value: Any, *, max_bytes: int = MAX_CANONICAL_BYTES) -> bytes:
    """Encode a value deterministically using the ProofIR JSON profile."""

    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise ProofIRV3Error(
            "invalid canonical byte bound",
            ProofIRV3Diagnostic(
                "envelope-valid", "invalid-bound", "", "canonical byte bound must be positive"
            ),
        )
    _validate_bounds(
        value,
        manifest_context=_is_environment_manifest(value),
        envelope_context=_is_environment_envelope(value),
    )
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        code = "invalid-unicode" if isinstance(exc, UnicodeError) else "invalid-canonical-value"
        raise ProofIRV3Error(
            f"value is not canonically representable: {exc}",
            ProofIRV3Diagnostic(
                "envelope-valid", code, "", "value is not canonically representable"
            ),
        ) from exc
    if len(encoded) > max_bytes:
        raise ProofIRV3Error(f"canonical payload exceeds byte limit: {len(encoded)} > {max_bytes}")
    return encoded



def _validate_bounds(
    value: Any, *, depth: int = 0, manifest_context: bool = False, envelope_context: bool = False
) -> None:
    """Enforce the bounded cross-language JSON profile recursively.

    Rejection happens before serialization so Python-only values cannot acquire a
    platform-dependent spelling or silently cross the safe-integer boundary.
    """

    if depth > MAX_DEPTH:
        raise ProofIRV3Error(f"canonical payload exceeds nesting limit: {MAX_DEPTH}")
    if isinstance(value, str):
        _validate_string_bound(value)
        return
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        _validate_integer_bound(value)
        return
    if isinstance(value, float):
        _reject_float(value)
    if isinstance(value, tuple):
        raise ProofIRV3Error("tuples are not part of the canonical JSON profile")
    if isinstance(value, list):
        _validate_list_bounds(
            value,
            depth,
            max_items=MAX_COMPILED_MODULES if manifest_context else MAX_COLLECTION_ITEMS,
        )
        return
    if isinstance(value, dict):
        _validate_object_bounds(
            value, depth, manifest_context=manifest_context, envelope_context=envelope_context
        )
        return
    raise ProofIRV3Error(f"value of type {type(value).__name__} is not canonically representable")



def _validate_string_bound(value: str) -> None:
    try:
        encoded_length = len(value.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise ProofIRV3Error(
            "string contains an invalid Unicode scalar",
            ProofIRV3Diagnostic("envelope-valid", "invalid-unicode", "", "string contains an invalid Unicode scalar"),
        ) from exc
    if encoded_length > MAX_STRING_BYTES:
        raise ProofIRV3Error(f"string exceeds byte limit: {MAX_STRING_BYTES}")


def _validate_integer_bound(value: int) -> None:
    if value < SAFE_INTEGER_MIN or value > SAFE_INTEGER_MAX:
        raise ProofIRV3Error(
            f"integer is outside the JSON safe integer range [{SAFE_INTEGER_MIN}, {SAFE_INTEGER_MAX}]"
        )


def _reject_float(value: float) -> NoReturn:
    # Floats are excluded even when integral-looking: their spelling and rounding
    # are not portable across the Python, Rust, JSON, and SQLite boundaries.
    if not math.isfinite(value):
        raise ProofIRV3Error(
            "value is not canonically representable: non-finite number"
        )
    raise ProofIRV3Error(
        "non-integral decimal string/float values are not canonically representable"
    )


def _validate_list_bounds(
    value: list[Any], depth: int, *, max_items: int = MAX_COLLECTION_ITEMS
) -> None:
    if len(value) > max_items:
        raise ProofIRV3Error(f"collection exceeds item limit: {max_items}")
    for item in value:
        _validate_bounds(item, depth=depth + 1)



def _validate_object_bounds(
    value: dict[Any, Any],
    depth: int,
    *,
    manifest_context: bool = False,
    envelope_context: bool = False,
) -> None:
    """Validate object cardinality, string-only keys, and descendant depth.

    String-key enforcement prevents Python mappings from canonicalizing differently
    from JSON objects in other implementations.
    """

    if len(value) > MAX_COLLECTION_ITEMS:
        raise ProofIRV3Error(f"object exceeds item limit: {MAX_COLLECTION_ITEMS}")
    for key, item in value.items():
        if not isinstance(key, str):
            raise ProofIRV3Error("object keys must be strings in the canonical profile")
        _validate_bounds(key, depth=depth + 1)
        child_manifest_context = (
            envelope_context and key == "payload" and _is_environment_manifest(item)
        )
        child_large_modules = manifest_context and key == "compiledModules"
        _validate_bounds(
            item, depth=depth + 1, manifest_context=(child_manifest_context or child_large_modules)
        )




def _is_environment_manifest(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and len(value) == 7
        and set(value)
        == {
            "prover",
            "toolchain",
            "dependencies",
            "compiledModules",
            "options",
            "trust",
            "fingerprintScheme",
        }
        and isinstance(value.get("compiledModules"), list)
    )



def _is_environment_envelope(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and value.get("proofirVersion") == PROOFIR_V3_VERSION
        and value.get("artifactKind") == "proofir.environment"
        and _is_environment_manifest(value.get("payload"))
    )



def detached_content_id(envelope: Mapping[str, Any]) -> str:
    """Hash an envelope after removing its self-referential artifact ID."""

    detached = dict(envelope)
    detached.pop("artifactId", None)
    return "sha256:" + hashlib.sha256(canonical_bytes(detached)).hexdigest()


def validate_envelope(
    value: Any,
    *,
    max_bytes: int | None = None,
    max_artifact_bytes: int = MAX_ARTIFACT_BYTES,
) -> ProofIRV3Artifact:
    """Validate the common v3 envelope and return its checked identity."""

    if max_bytes is not None:
        max_artifact_bytes = max_bytes
    owned, encoded = _prepare_envelope(value, max_artifact_bytes)
    return _validate_owned_envelope(owned, encoded)


def _prepare_envelope(value: Any, max_artifact_bytes: int) -> tuple[dict[str, Any], bytes]:
    """Own the serialized tree before validating its semantics and identity."""
    try:
        encoded = canonical_bytes(value, max_bytes=max_artifact_bytes)
    except ProofIRV3Error:
        # Keep the established shape-first diagnostic on malformed inputs.
        _validate_envelope_shape(value)
        raise
    owned = json.loads(encoded, object_pairs_hook=_own_object_pairs)
    _validate_envelope_shape(owned)
    # Recheck the parsed tree: custom input hooks need not preserve its profile.
    encoded = canonical_bytes(owned, max_bytes=max_artifact_bytes)
    return owned, encoded


def _own_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    owned = dict(pairs)
    if len(owned) != len(pairs):
        raise ProofIRV3Error("duplicate serialized object key")
    return owned


def _validate_owned_envelope(value: dict[str, Any], encoded: bytes) -> ProofIRV3Artifact:
    # Closed envelope keys sort artifactId first. Both tree and encoding were
    # prepared together, and removing this field cannot enlarge profile bounds.
    prefix = b'{"artifactId":' + json.dumps(value["artifactId"]).encode() + b','
    if not encoded.startswith(prefix):
        raise ProofIRV3Error("prepared envelope has inconsistent canonical encoding")
    detached = b'{' + encoded[len(prefix):]
    expected = "sha256:" + hashlib.sha256(detached).hexdigest()
    _validate_declared_id(value, expected)
    return ProofIRV3Artifact(_freeze(value), expected)


def validate_envelope_batch(
    values: list[dict[str, Any]],
    *,
    max_bytes: int | None = None,
    max_artifact_bytes: int = MAX_ARTIFACT_BYTES,
    max_batch_bytes: int = MAX_BATCH_BYTES,
    max_artifacts: int = MAX_ARTIFACTS,
) -> tuple[ProofIRV3Artifact, ...]:
    """Validate a closed set of content artifacts before any projection work.

    A compact reference is local to its enclosing artifact.  A reference with an
    ``artifactRef`` is deliberately different: it can name only another artifact
    supplied in this batch, and it must resolve to an exact descriptor there.
    Keeping that closure check here prevents a database projector from partially
    mutating a store while discovering a dangling cross-artifact edge.
    """

    if type(values) is not list:
        raise ProofIRV3Error("v3 envelope batch must be an array")
    max_artifact_bytes, max_batch_bytes = _resolve_batch_limits(
        max_bytes, max_artifact_bytes, max_batch_bytes, max_artifacts
    )
    owned_values, artifacts = _preflight_batch(values, max_artifact_bytes, max_batch_bytes, max_artifacts)
    for owner_id, artifact in artifacts.items():
        _validate_external_references(owner_id, artifact, artifacts)
    return tuple(_validate_owned_envelope(value, encoded) for value, encoded in owned_values)


def _validate_envelope_shape(value: Any) -> None:
    """Validate the closed common envelope before kind-specific semantics.

    This stage owns producer, coverage, extension, and subject-registry shape. It
    does not treat a structurally valid derivation as checker-accepted evidence.
    """

    if not isinstance(value, dict):
        raise ProofIRV3Error("v3 artifact must be a JSON object")
    _validate_envelope_header(value)
    _validate_producer(value)
    _validate_common_shapes(value)
    _validate_coverage(value["coverage"], value)
    _validate_limitations(value["limitations"], value)
    _validate_extensions(value["extensions"], value)
    _validate_subject_references(value)
    _validate_kind_payload(value)


def _validate_envelope_header(value: dict[str, Any]) -> None:
    """Validate required keys, native kind/version, and environment identity."""

    missing = sorted(REQUIRED_ENVELOPE_KEYS - value.keys())
    if missing:
        raise ProofIRV3Error(f"v3 envelope missing keys: {', '.join(missing)}")
    if value.get("proofirVersion") != PROOFIR_V3_VERSION:
        raise ProofIRV3Error(
            f"unsupported ProofIR version: {value.get('proofirVersion')!r}"
        )
    _validate_artifact_kind(value)
    _validate_top_level_keys(value)
    _validate_environment_ref(value)


def _validate_artifact_kind(value: Mapping[str, Any]) -> None:
    """Reject empty, unknown, and explicitly retired artifact kinds."""

    if not isinstance(value.get("artifactKind"), str) or not value["artifactKind"]:
        raise ProofIRV3Error("artifactKind must be a non-empty string")
    if value["artifactKind"] not in SUPPORTED_ARTIFACT_KINDS:
        legacy = value["artifactKind"] in LEGACY_ARTIFACT_KINDS
        code = "legacy-artifact-kind" if legacy else "unsupported-artifact-kind"
        message = (
            f"legacy ProofIR artifact kind is unsupported: {value['artifactKind']}"
            if legacy
            else f"unsupported ProofIR artifact kind: {value['artifactKind']!r}"
        )
        _fail(
            "kind-schema-valid",
            code,
            "/artifactKind",
            message,
            value,
        )


def _validate_top_level_keys(value: Mapping[str, Any]) -> None:
    """Reject the first unexpected envelope key with an escaped pointer."""

    if set(value) - REQUIRED_ENVELOPE_KEYS:
        extras = sorted(set(value) - REQUIRED_ENVELOPE_KEYS)
        key = extras[0]
        _fail(
            "envelope-valid",
            "unexpected-envelope-key",
            "/" + _escape(key),
            f"unexpected top-level envelope key: {key}",
            value,
        )


def _validate_environment_ref(value: Mapping[str, Any]) -> None:
    """Require the envelope environment identity to be an exact SHA-256 digest."""

    if not isinstance(value.get("environmentRef"), str) or not _digest(
        value["environmentRef"]
    ):
        _fail(
            "envelope-valid",
            "invalid-content-digest",
            "/environmentRef",
            "environmentRef must be a sha256 digest",
            value,
        )


def _validate_producer(value: Mapping[str, Any]) -> None:
    """Validate attributable producer identity and its build digest."""

    _closed_object(
        value["producer"],
        {"name", "version", "implementation", "buildDigest"},
        "/producer",
        value,
        "producer",
    )
    for key in ("name", "version", "implementation"):
        if not isinstance(value["producer"][key], str) or not value["producer"][key]:
            _fail(
                "envelope-valid",
                "invalid-producer-field",
                f"/producer/{key}",
                "producer field must be non-empty",
                value,
            )
    if not _digest(value["producer"]["buildDigest"]):
        _fail(
            "envelope-valid",
            "invalid-content-digest",
            "/producer/buildDigest",
            "invalid content digest",
            value,
        )


def _validate_common_shapes(value: Mapping[str, Any]) -> None:
    """Establish container types before downstream validators index their fields."""

    if not isinstance(value.get("coverage"), dict):
        _fail(
            "envelope-valid",
            "invalid-coverage",
            "/coverage",
            "coverage must be an object",
            value,
        )
    if (
        not isinstance(value.get("subjectRefs"), list)
        or not isinstance(value.get("limitations"), list)
        or not isinstance(value.get("extensions"), dict)
    ):
        raise ProofIRV3Error(
            "subjectRefs and limitations must be arrays and extensions an object"
        )
    if not isinstance(value.get("payload"), dict):
        raise ProofIRV3Error("payload must be an object")


def _typed_reference(value: Any, *, pointer: str) -> tuple[str, str]:
    """Parse a compact local reference or explicit batch-closed external one."""

    if not isinstance(value, dict) or set(value) not in (
        {"kind", "localId"},
        {"artifactRef", "kind", "localId"},
    ):
        raise ProofIRV3Error(
            f"{pointer} invalid reference shape",
            ProofIRV3Diagnostic(
                "reference-valid",
                "invalid-reference-shape",
                pointer,
                f"{pointer} must contain kind/localId or artifactRef/kind/localId",
            ),
        )
    if (
        not isinstance(value.get("kind"), str)
        or not isinstance(value.get("localId"), str)
        or ("artifactRef" in value and not _digest(value["artifactRef"]))
    ):
        raise ProofIRV3Error(
            f"{pointer} invalid reference shape",
            ProofIRV3Diagnostic(
                "reference-valid",
                "invalid-reference-shape",
                pointer,
                f"{pointer} has invalid fields",
            ),
        )
    if not value["kind"] or not value["localId"]:
        raise ProofIRV3Error(
            f"{pointer} typed reference kind and localId must be non-empty"
        )
    return value["kind"], value["localId"]


def _subject_descriptor(value: Any, *, pointer: str) -> tuple[str, str]:
    """Validate one artifact-owned subject descriptor without an environment dialect."""

    if not isinstance(value, dict) or not {"kind", "localId"} <= set(value):
        _fail(
            "reference-valid",
            "invalid-subject-descriptor",
            pointer,
            "subject descriptor requires kind and localId",
        )
    allowed = {
        "kind",
        "localId",
        "fingerprint",
        "display",
        "searchShape",
        "opaquePayloadRef",
    }
    extra = sorted(set(value) - allowed)
    if extra:
        _fail(
            "reference-valid",
            "invalid-subject-descriptor",
            pointer + "/" + _escape(extra[0]),
            "subject descriptor contains an unsupported field",
        )
    kind, local_id = _typed_reference(
        {"kind": value.get("kind"), "localId": value.get("localId")}, pointer=pointer
    )
    _validate_subject_metadata(value, pointer)
    if "fingerprint" in value:
        _validate_subject_fingerprint(value["fingerprint"], pointer)
    return kind, local_id


def _validate_subject_metadata(value: Mapping[str, Any], pointer: str) -> None:
    if "display" in value and (
        not isinstance(value["display"], str) or not value["display"]
    ):
        _fail(
            "reference-valid",
            "invalid-subject-descriptor",
            pointer + "/display",
            "display must be a non-empty string",
        )
    if "searchShape" in value and not isinstance(value["searchShape"], dict):
        _fail(
            "reference-valid",
            "invalid-subject-descriptor",
            pointer + "/searchShape",
            "searchShape must be an object",
        )
    if "opaquePayloadRef" in value and not _digest(value["opaquePayloadRef"]):
        _fail(
            "reference-valid",
            "invalid-subject-descriptor",
            pointer + "/opaquePayloadRef",
            "opaquePayloadRef must be a sha256 digest",
        )


def _validate_subject_fingerprint(fingerprint: Any, pointer: str) -> None:
    if not isinstance(fingerprint, dict) or set(fingerprint) != {"scheme", "digest"}:
        _fail(
            "reference-valid",
            "invalid-subject-fingerprint",
            pointer + "/fingerprint",
            "fingerprint must contain scheme and digest",
        )
    scheme = fingerprint["scheme"]
    valid_scheme = (
        isinstance(scheme, dict)
        and set(scheme) == {"name", "version"}
        and all(
            isinstance(scheme.get(key), str) and scheme[key]
            for key in ("name", "version")
        )
    )
    if not valid_scheme:
        _fail(
            "reference-valid",
            "invalid-subject-fingerprint",
            pointer + "/fingerprint/scheme",
            "fingerprint scheme must contain non-empty name and version",
        )
    if not _digest(fingerprint["digest"]):
        _fail(
            "reference-valid",
            "invalid-subject-fingerprint",
            pointer + "/fingerprint/digest",
            "fingerprint digest must be a sha256 digest",
        )


def _digest(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(c in "0123456789abcdef" for c in value[7:])
    )


def _closed_object(
    obj: Any,
    keys: set[str],
    pointer: str,
    value: Mapping[str, Any],
    label: str = "object",
) -> None:
    """Require an exact object key set and preserve stable first-error ordering.

    Missing keys are reported before extras so independent producers receive one
    deterministic diagnostic for the same malformed record.
    """

    if not isinstance(obj, dict):
        _fail(
            "envelope-valid",
            f"invalid-{label}",
            pointer,
            f"{label} must be an object",
            value,
        )
    missing = sorted(keys - obj.keys())
    if missing:
        code = "missing-producer-key" if label == "producer" else "missing-payload-key"
        _fail(
            "envelope-valid" if label == "producer" else "kind-schema-valid",
            code,
            pointer + "/" + _escape(missing[0]),
            f"missing required key: {missing[0]}",
            value,
        )
    extra = sorted(set(obj) - keys)
    if extra:
        code = "unexpected-payload-key" if label == "payload" else "unexpected-key"
        _fail(
            "kind-schema-valid",
            code,
            pointer + "/" + _escape(extra[0]),
            f"unexpected key: {extra[0]}",
            value,
        )


def _validate_coverage(c: dict[str, Any], value: Mapping[str, Any]) -> None:
    """Validate the closed coverage ledger and its bounded counter fields.

    Coverage describes an inspected population; it does not establish a proof or
    extend applicability beyond the explicit population selector.
    """

    keys = {
        "status",
        "population",
        "universeKnown",
        "expected",
        "discovered",
        "decoded",
        "valid",
        "projected",
        "queryMatched",
        "omitted",
        "bounds",
    }
    _closed_object(c, keys, "/coverage", value, "coverage")
    _validate_coverage_population(c["population"], value)
    _validate_coverage_universe(c["universeKnown"], value)
    _validate_coverage_counters(c, value)
    if not isinstance(c["omitted"], list) or not isinstance(c["bounds"], dict):
        _fail(
            "envelope-valid",
            "invalid-coverage",
            "/coverage",
            "invalid coverage fields",
            value,
        )
    for index, omission in enumerate(c["omitted"]):
        pointer = f"/coverage/omitted/{index}"
        if not isinstance(omission, dict) or set(omission) != {
            "pointer",
            "stage",
            "reasonCode",
        } or any(
            not isinstance(omission[field], str) or not omission[field]
            for field in ("pointer", "stage", "reasonCode")
        ):
            _fail(
                "envelope-valid",
                "invalid-coverage-omission",
                pointer,
                "coverage omissions must contain pointer, stage, and reasonCode strings",
                value,
            )
    _validate_coverage_semantics(c, value)


def _validate_coverage_population(population: Any, value: Mapping[str, Any]) -> None:
    """Require an attributable population kind and an explicit selector field."""

    if not isinstance(population, dict) or set(population) != {
        "kind",
        "selector",
    }:
        _fail(
            "envelope-valid",
            "invalid-coverage-population",
            "/coverage/population",
            "invalid coverage population",
            value,
        )
    if not isinstance(population["kind"], str) or not population["kind"]:
        _fail(
            "envelope-valid",
            "invalid-coverage-population",
            "/coverage/population/kind",
            "invalid population kind",
            value,
        )


def _validate_coverage_universe(universe_known: Any, value: Mapping[str, Any]) -> None:
    """Keep known-universe state Boolean rather than accepting integer aliases.

    Python bool is a subclass of int, so this explicit boundary prevents 0/1 counter
    values from masquerading as coverage knowledge.
    """

    if not isinstance(universe_known, bool):
        _fail(
            "envelope-valid",
            "invalid-coverage-boolean",
            "/coverage/universeKnown",
            "universeKnown must be boolean",
            value,
        )


def _validate_coverage_counters(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    """Reject booleans, negatives, and unsafe integers in coverage counters."""

    for k in (
        "expected",
        "discovered",
        "decoded",
        "valid",
        "projected",
        "queryMatched",
    ):
        counter = coverage[k]
        if (
            not isinstance(counter, int)
            or isinstance(counter, bool)
            or counter < 0
            or counter > SAFE_INTEGER_MAX
        ):
            _fail(
                "envelope-valid",
                "invalid-coverage-counter",
                f"/coverage/{k}",
                "coverage counter must be non-negative",
                value,
            )


def _validate_coverage_semantics(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    """Reject contradictory status and monotonicity claims before projection."""

    _validate_coverage_status(coverage, value)
    _validate_coverage_monotonicity(coverage, value)
    _validate_complete_coverage(coverage, value)
    _validate_unavailable_coverage(coverage, value)


def _validate_coverage_status(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    if coverage["status"] not in {"complete", "partial", "unavailable"}:
        _fail(
            "envelope-valid",
            "invalid-coverage-status",
            "/coverage/status",
            "unsupported coverage status",
            value,
        )


def _validate_coverage_monotonicity(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    counters = [
        coverage[key]
        for key in ("expected", "discovered", "decoded", "valid", "projected")
    ]
    if (
        counters != sorted(counters, reverse=True)
        or coverage["queryMatched"] > coverage["projected"]
    ):
        _fail(
            "semantic-valid",
            "contradictory-coverage-counts",
            "/coverage",
            "coverage counters must be monotone and query-scoped",
            value,
        )


def _validate_complete_coverage(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    counters = [
        coverage[key]
        for key in ("expected", "discovered", "decoded", "valid", "projected")
    ]
    if coverage["status"] == "complete" and (
        not coverage["universeKnown"] or coverage["omitted"] or len(set(counters)) != 1
    ):
        _fail(
            "semantic-valid",
            "contradictory-coverage-status",
            "/coverage/status",
            "complete coverage requires a known omission-free population",
            value,
        )


def _validate_unavailable_coverage(
    coverage: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    unavailable = [
        coverage[key]
        for key in ("discovered", "decoded", "valid", "projected", "queryMatched")
    ]
    if coverage["status"] == "unavailable" and any(unavailable):
        _fail(
            "semantic-valid",
            "contradictory-coverage-status",
            "/coverage/status",
            "unavailable coverage cannot report observed or projected evidence",
            value,
        )


def _validate_limitations(rows: list[Any], value: Mapping[str, Any]) -> None:
    """Require every declared support limitation to carry an ID and message.

    Limitations bound interpretation of valid evidence; consumers must not discard
    them when making semantic decisions.
    """

    for i, row in enumerate(rows):
        if (
            not isinstance(row, dict)
            or set(row) != {"id", "message"}
            or not all(
                isinstance(row.get(k), str) and row[k] for k in ("id", "message")
            )
        ):
            _fail(
                "envelope-valid",
                "invalid-limitation",
                f"/limitations/{i}/id",
                "limitation must contain id and message",
                value,
            )


def _validate_extensions(ext: dict[str, Any], value: Mapping[str, Any]) -> None:
    """Confine opaque extension data to explicit namespace/version keys.

    Namespacing preserves unknown payloads without admitting them into core
    validation, authority, ranking, or coverage decisions.
    """

    for key in ext:
        if (
            not isinstance(key, str)
            or "/" not in key
            or not key.split("/", 1)[0]
            or not key.split("/", 1)[1]
        ):
            _fail(
                "envelope-valid",
                "invalid-extension-namespace",
                f"/extensions/{_escape(str(key))}",
                "extension key must be namespaced",
                value,
            )


def _require_ref(
    ref: Any,
    pointer: str,
    subjects: set[tuple[str, str]],
    env: str,
    value: Mapping[str, Any],
    kind: str | None = None,
) -> None:
    """Resolve a compact local reference against the owner-local registry.

    External reference closure is intentionally a batch operation.  The
    individual envelope validator can still establish reference shape, while
    ``validate_envelope_batch`` proves the target artifact and descriptor exist.
    """

    actual = _typed_reference(ref, pointer=pointer)
    if "artifactRef" not in ref and kind and actual[0] != kind:
        _fail(
            "reference-valid",
            "unexpected-reference-kind",
            pointer + "/kind",
            "unexpected reference kind",
            value,
        )
    if "artifactRef" not in ref and actual not in subjects:
        _fail(
            "reference-valid",
            "dangling-local-reference",
            pointer,
            f"dangling reference: {actual[0]}:{actual[1]}",
            value,
        )


def _validate_kind_payload(value: Mapping[str, Any]) -> None:
    """Validate the closed payload dialect after envelope identity checks."""

    from ladon.proofir_v3_payloads import validate_kind_payload

    validate_kind_payload(value)


def _validate_subject_references(value: Mapping[str, Any]) -> None:
    """Build a duplicate-free registry owned by this exact content artifact."""

    seen: set[tuple[str, str]] = set()
    for index, ref in enumerate(value["subjectRefs"]):
        identity = _subject_descriptor(ref, pointer=f"/subjectRefs/{index}")
        if identity in seen:
            _fail(
                "reference-valid",
                "duplicate-subject-reference",
                f"/subjectRefs/{index}",
                "duplicate subject reference",
                value,
            )
        seen.add(identity)


def _external_references(value: Any, pointer: str) -> list[tuple[str, dict[str, Any]]]:
    """Return every explicit external subject reference in deterministic order."""

    if isinstance(value, dict):
        if set(value) == {"artifactRef", "kind", "localId"}:
            return [(pointer, value)]
        rows: list[tuple[str, dict[str, Any]]] = []
        for key in sorted(value):
            rows.extend(_external_references(value[key], pointer + "/" + _escape(key)))
        return rows
    if isinstance(value, list):
        rows = []
        for index, item in enumerate(value):
            rows.extend(_external_references(item, pointer + f"/{index}"))
        return rows
    return []


def _expected_external_kind(pointer: str) -> str | None:
    """Return the field-owned target kind for a typed external reference.

    Local references are checked at payload validation time.  External
    references must carry the same field semantics, so this small registry is
    shared by batch and incremental closure rather than trusting a producer's
    self-declared ``kind``.
    """

    fields = {
        "ruleRef": "declaration",
        "declarationRef": "declaration",
        "conclusionRef": "statement",
        "premiseRefs": "statement",
        "residualPremiseRefs": "statement",
        "goalRef": "statement",
        "statementRef": "statement",
        "termRef": "term",
        "localContextRef": "local-context",
        "checkRunRef": "check-run",
        "surfaceRef": "surface",
        "sourceMapRef": "source-map",
        "attachmentSetRef": "attachment-set",
    }
    for field, kind in fields.items():
        if f"/{field}" in pointer:
            return kind
    return None


def _validate_external_references(
    owner_id: str,
    artifact: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
) -> None:
    """Close external references over the supplied batch and exact owner identity."""

    for pointer, reference in _external_references(artifact["payload"], "/payload"):
        _validate_one_external_reference(owner_id, artifact, artifacts, pointer, reference)

    inputs = artifact.get("payload", {}).get("inputs")
    if artifact.get("artifactKind") == "proofir.check-run" and isinstance(inputs, Mapping):
        for index, target_id in enumerate(inputs.get("artifactRefs", [])):
            if target_id not in artifacts:
                _fail(
                    "reference-valid",
                    "external-artifact-not-in-batch",
                    f"/payload/inputs/artifactRefs/{index}",
                    "input artifact reference is not present in the validated artifact set",
                    artifact,
                )
            target = artifacts[target_id]
            if target["environmentRef"] != artifact["environmentRef"]:
                _fail(
                    "reference-valid",
                    "external-reference-environment-mismatch",
                    f"/payload/inputs/artifactRefs/{index}",
                    "external reference crosses environments",
                    artifact,
                )


def _validate_one_external_reference(
    owner_id: str,
    artifact: Mapping[str, Any],
    artifacts: Mapping[str, Mapping[str, Any]],
    pointer: str,
    reference: Mapping[str, Any],
) -> None:
    target_id = reference["artifactRef"]
    if target_id == owner_id:
        _fail(
            "reference-valid",
            "self-external-reference",
            pointer + "/artifactRef",
            "external references must not name their enclosing artifact",
            artifact,
        )
    target = artifacts.get(target_id)
    if target is None:
        _fail(
            "reference-valid",
            "external-artifact-not-in-batch",
            pointer + "/artifactRef",
            "external reference owner is not present in this batch",
            artifact,
        )
    if target["environmentRef"] != artifact["environmentRef"]:
        _fail(
            "reference-valid",
            "external-reference-environment-mismatch",
            pointer,
            "external reference crosses environments",
            artifact,
        )
    expected_kind = _expected_external_kind(pointer)
    if expected_kind is not None and reference["kind"] != expected_kind:
        _fail(
            "reference-valid",
            "unexpected-reference-kind",
            pointer + "/kind",
            "unexpected reference kind",
            artifact,
        )
    target_subjects = {
        _subject_descriptor(subject, pointer="/subjectRefs")
        for subject in target["subjectRefs"]
    }
    if (reference["kind"], reference["localId"]) not in target_subjects:
        _fail(
            "reference-valid",
            "external-subject-not-found",
            pointer,
            "external reference does not name a target descriptor",
            artifact,
        )


def _validate_derivation_graph(
    payload: Mapping[str, Any], value: Mapping[str, Any]
) -> None:
    """Check acyclic promises or exact declared recursive SCC membership.

    Multiple steps may conclude the same statement and represent OR alternatives.
    Dependency traversal unions their edges conservatively.  Recursive metadata is
    structural only and does not assert that any fixed point is checker-accepted.
    """

    dependencies = _derivation_dependencies(payload["steps"])
    actual = cyclic_components(dependencies)
    if payload["acyclic"]:
        if actual:
            _fail(
                "semantic-valid",
                "derivation-cycle",
                "/payload/steps",
                "derivation cycle detected",
                value,
            )
        return
    declared = tuple(
        sorted(
            tuple(
                sorted(
                    _typed_reference(row, pointer="/payload/recursion/components")
                    for row in component["statementRefs"]
                )
            )
            for component in payload["recursion"]["components"]
        )
    )
    if declared != actual:
        _fail(
            "semantic-valid",
            "scc-metadata-mismatch",
            "/payload/recursion/components",
            "declared recursive components do not match graph SCCs",
            value,
        )


def _derivation_dependencies(
    steps: list[dict[str, Any]],
) -> dict[tuple[str, str], set[tuple[str, str]]]:
    """Return structural conclusion-to-premise edges from validated step rows."""

    dependencies: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for step in steps:
        conclusion = _typed_reference(
            step["conclusionRef"], pointer="/payload/steps/conclusionRef"
        )
        premises = dependencies.setdefault(conclusion, set())
        premises.update(
            _typed_reference(premise, pointer="/payload/steps/premiseRefs")
            for premise in step["premiseRefs"]
        )
    return dependencies


def _validate_declared_id(value: Mapping[str, Any], expected: str) -> None:
    """Reject mutation or copying that leaves a detached content ID stale.

    Identity is recomputed from canonical content and never trusted merely because an
    input string has the syntactic shape of a digest.
    """

    if value.get("artifactId") != expected:
        raise ProofIRV3Error("artifactId does not match detached canonical content")


def make_envelope(
    *,
    artifact_kind: str,
    producer: Mapping[str, Any],
    environment_ref: str,
    subject_refs: list[Mapping[str, Any]],
    coverage: Mapping[str, Any],
    payload: Mapping[str, Any],
    limitations: list[Any] | None = None,
    extensions: Mapping[str, Any] | None = None,
) -> ProofIRV3Artifact:
    """Construct and validate a canonical v3 envelope.

    This convenience builder completes older partial producer/coverage inputs
    into explicit native-v3 records. Directly supplied envelopes remain strict.
    """

    completed_producer = dict(producer)
    completed_producer.setdefault("version", "unspecified")
    completed_producer.setdefault("implementation", "unspecified")
    if "buildDigest" not in completed_producer:
        completed_producer["buildDigest"] = (
            "sha256:" + hashlib.sha256(canonical_bytes(completed_producer)).hexdigest()
        )

    completed_coverage = dict(coverage)
    observed = completed_coverage.pop("observed", None)
    if "omissions" in completed_coverage and "omitted" not in completed_coverage:
        completed_coverage["omitted"] = completed_coverage.pop("omissions")
    completed_coverage.setdefault("status", "partial")
    completed_coverage.setdefault(
        "population", {"kind": "artifact-subjects", "selector": {}}
    )
    completed_coverage.setdefault(
        "universeKnown", completed_coverage["status"] == "complete"
    )
    for key in (
        "expected",
        "discovered",
        "decoded",
        "valid",
        "projected",
        "queryMatched",
    ):
        completed_coverage.setdefault(
            key,
            observed
            if isinstance(observed, int) and not isinstance(observed, bool)
            else 0,
        )
    completed_coverage.setdefault("omitted", [])
    completed_coverage.setdefault("bounds", {})

    envelope: dict[str, Any] = {
        "proofirVersion": PROOFIR_V3_VERSION,
        "artifactKind": artifact_kind,
        "artifactId": None,
        "producer": completed_producer,
        "environmentRef": environment_ref,
        "subjectRefs": [dict(row) for row in subject_refs],
        "coverage": completed_coverage,
        "payload": dict(payload),
        "limitations": list(limitations or []),
        "extensions": dict(extensions or {}),
    }
    envelope["artifactId"] = detached_content_id(envelope)
    return validate_envelope(envelope)


__all__ = [
    "MAX_ARTIFACTS",
    "MAX_ARTIFACT_BYTES",
    "MAX_BATCH_BYTES",
    "MAX_CANONICAL_BYTES",
    "MAX_COLLECTION_ITEMS",
    "MAX_COMPILED_MODULES",
    "MAX_DEPTH",
    "MAX_STRING_BYTES",
    "PROOFIR_V3_VERSION",
    "SAFE_INTEGER_MAX",
    "SAFE_INTEGER_MIN",
    "SUPPORTED_ARTIFACT_KINDS",
    "ProofIRV3Artifact",
    "ProofIRV3Diagnostic",
    "ProofIRV3Error",
    "canonical_bytes",
    "detached_content_id",
    "make_envelope",
    "validate_envelope",
    "validate_envelope_batch",
]
