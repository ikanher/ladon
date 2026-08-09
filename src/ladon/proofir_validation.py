"""Shared bounded validation stages and attributable diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

VALIDATION_STAGES = (
    "discovered",
    "decoded",
    "envelope-valid",
    "kind-schema-valid",
    "reference-valid",
    "semantic-valid",
    "projected",
)


@dataclass(frozen=True)
class ProofIRDiagnostic:
    """One stable, attributable validation or omission record."""

    artifact_id: str
    stage: str
    code: str
    message: str
    pointer: str = ""
    retained: bool = False

    def __post_init__(self) -> None:
        if self.stage not in VALIDATION_STAGES:
            raise ValueError(f"unsupported ProofIR validation stage: {self.stage}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifactId": self.artifact_id,
            "stage": self.stage,
            "code": self.code,
            "message": self.message,
            "pointer": self.pointer,
            "retained": self.retained,
        }


def omission(
    artifact_id: str,
    *,
    stage: str,
    code: str,
    message: str,
    pointer: str,
) -> ProofIRDiagnostic:
    """Create a row-level omission with explicit retention disposition."""

    return ProofIRDiagnostic(artifact_id, stage, code, message, pointer, retained=False)


def catalog_diagnostic_code(state: str, diagnostic: str | None) -> str:
    """Map catalog failures to stable machine-readable codes."""

    if diagnostic:
        try:
            decoded = json.loads(diagnostic)
        except (TypeError, json.JSONDecodeError):
            decoded = None
        if isinstance(decoded, dict) and isinstance(decoded.get("code"), str):
            return decoded["code"]
    if state == "unsupported":
        return "unsupported-kind-version"
    if state == "malformed":
        return "decode-failed"
    if diagnostic == "catalog metadata truncated":
        return "metadata-truncated"
    return "catalog-diagnostic"


def v3_diagnostics(value: Any) -> list[ProofIRDiagnostic]:
    """Return deterministic envelope diagnostics without raising or projecting."""

    artifact_id = (
        str(value.get("artifactId", "<unbound>"))
        if isinstance(value, dict)
        else "<unbound>"
    )
    if not isinstance(value, dict):
        return [
            omission(
                artifact_id,
                stage="decoded",
                code="decode-failed",
                message="artifact is not an object",
                pointer="",
            )
        ]
    if value.get("proofirVersion") != "3.0":
        return [
            omission(
                artifact_id,
                stage="envelope-valid",
                code="unsupported-version",
                message="unsupported ProofIR version",
                pointer="/proofirVersion",
            )
        ]
    if not isinstance(value.get("artifactKind"), str) or not value["artifactKind"]:
        return [
            omission(
                artifact_id,
                stage="kind-schema-valid",
                code="invalid-artifact-kind",
                message="artifactKind must be a non-empty string",
                pointer="/artifactKind",
            )
        ]
    return []


__all__ = [
    "VALIDATION_STAGES",
    "ProofIRDiagnostic",
    "catalog_diagnostic_code",
    "omission",
    "v3_diagnostics",
]
