"""Validate authored result guide annotations and classify their revision scope."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from typing import Any

from ladon._result_manifest_shape import validate_document_shape
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import MAX_MANIFEST_BYTES, ResultManifestError, canonical_json

_MAX_AGGREGATE_ENTRIES = 100_000


def _schema() -> dict[str, Any]:
    try:
        return json.loads(files("ladon.schemas").joinpath("ladon-result-guide-v1.schema.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("result guide schema is unavailable or invalid") from exc


def guide_revision(kind: str, row: dict[str, Any]) -> str:
    """Return the domain-separated digest of a step or citation, excluding revision."""
    if kind not in {"step", "citation"}:
        raise ValueError("guide revision kind must be step or citation")
    if not isinstance(row, dict):
        raise TypeError("guide revision row must be an object")
    content = {key: value for key, value in row.items() if key != "revision"}
    encoded = canonical_json(content)
    prefix = f"ladon-result-guide-v1/{kind}\0".encode()
    return "sha256:" + hashlib.sha256(prefix + encoded).hexdigest()


def validate_result_guide(value: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate and detach a guide-input companion against a valid manifest."""
    owned_manifest = validate_result_manifest(manifest)
    if not isinstance(value, dict):
        raise ResultManifestError("guide inputs: expected object")
    encoded = canonical_json(value)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise ResultManifestError("guide inputs exceed the 16 MiB input limit")
    validate_document_shape(value, _schema())
    _aggregate_limits(value)
    if value["resultId"] != owned_manifest["resultId"]:
        raise ResultManifestError("guide inputs: result ID does not match manifest")
    _validate_rows(value, owned_manifest)
    return json.loads(encoded)


def _aggregate_limits(value: dict[str, Any]) -> None:
    entries = len(value["steps"]) + len(value["citations"]) + len(value["reviews"])
    for row in value["steps"]:
        entries += len(row["targetRevisions"]) + len(row["sources"]) + len(row["prerequisites"])
    for row in value["reviews"]:
        entries += len(row["targetRevisions"])
    for row in value["citations"]:
        entries += len(row["work"]["authors"])
    if entries > _MAX_AGGREGATE_ENTRIES:
        raise ResultManifestError("guide inputs exceed the 100,000 aggregate collection-entry limit")


def _validate_rows(value: dict[str, Any], manifest: dict[str, Any]) -> None:
    claims = {row["id"]: row for row in manifest["claims"]}
    targets = {row["id"]: row for row in manifest["targets"]}
    step_rows: dict[str, dict[str, Any]] = {}
    for row in value["steps"]:
        _validate_step(row, claims, targets, step_rows)
        step_rows[row["id"]] = row

    citation_rows: dict[str, dict[str, Any]] = {}
    for row in value["citations"]:
        _validate_citation(row, step_rows, citation_rows)
        citation_rows[row["id"]] = row

    review_ids: set[str] = set()
    for row in value["reviews"]:
        _validate_review(row, review_ids, step_rows, citation_rows, targets)


def _validate_step(row, claims, targets, earlier_steps):
    if row["id"] in earlier_steps:
        raise ResultManifestError("guide inputs: duplicate step ID")
    claim = claims.get(row["claimId"])
    if claim is None:
        raise ResultManifestError("guide step: unknown claim")
    _validate_revision("step", row)
    _validate_unique_known([item["targetId"] for item in row["targetRevisions"]], targets, "guide step target")
    prerequisite_ids = [item["stepId"] for item in row["prerequisites"]]
    if len(set(prerequisite_ids)) != len(prerequisite_ids):
        raise ResultManifestError("guide step: duplicate prerequisite")
    # Authored order defines validity: references may only point backward.
    if any(item not in earlier_steps for item in prerequisite_ids):
        raise ResultManifestError("guide step: prerequisite must name an earlier step")


def _validate_unique_known(identifiers, known, label):
    if len(set(identifiers)) != len(identifiers) or any(identifier not in known for identifier in identifiers):
        raise ResultManifestError(f"{label}: duplicate or unknown ID")


def _validate_citation(row, steps, citations):
    if row["id"] in citations:
        raise ResultManifestError("guide inputs: duplicate citation ID")
    _validate_revision("citation", row)
    step = steps.get(row["stepId"])
    if step is None:
        raise ResultManifestError("guide citation: unknown step")
    return step


def _validate_review(row, review_ids, steps, citations, targets):
    if row["id"] in review_ids:
        raise ResultManifestError("guide inputs: duplicate review ID")
    review_ids.add(row["id"])
    step = steps.get(row["stepId"])
    if step is None:
        raise ResultManifestError("guide review: unknown step")
    _validate_unique_known([entry["targetId"] for entry in row["targetRevisions"]], targets, "guide review target")
    _validate_review_citation(row, citations)
    if (row["stepRevision"] == step["revision"]
            and _revision_map(row["targetRevisions"]) != _revision_map(step["targetRevisions"])):
        raise ResultManifestError("guide review: current step target bindings contradict")


def _validate_review_citation(row, citations):
    has_id = "citationId" in row
    has_revision = "citationRevision" in row
    if has_id != has_revision or (row["scope"] == "attribution") != has_id:
        raise ResultManifestError("guide review: attribution citation binding mismatch")
    if has_id:
        citation = citations.get(row["citationId"])
        if citation is None or citation["stepId"] != row["stepId"]:
            raise ResultManifestError("guide review: unknown or mismatched citation")


def _validate_revision(kind: str, row: dict[str, Any]) -> None:
    if guide_revision(kind, row) != row["revision"]:
        raise ResultManifestError(f"guide {kind}: revision digest mismatch")


def guide_currencies(companion: dict[str, Any], manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Validate every supplied row and return current/historical status by row ID."""
    value = validate_result_guide(companion, manifest)
    step_states, step_rows = _step_currencies(value, manifest)
    citation_states, citation_rows = _citation_currencies(value, step_states, step_rows)
    review_states = _review_currencies(value, step_states, step_rows, citation_states, citation_rows)
    return {"steps": step_states, "citations": citation_states, "reviews": review_states}


def _step_currencies(value, manifest):
    claims = {row["id"]: row for row in manifest["claims"]}
    targets = {row["id"]: row for row in manifest["targets"]}
    states, rows = {}, {}
    for row in value["steps"]:
        current = _step_current(row, value, manifest, claims, targets, states, rows)
        rows[row["id"]] = row
        states[row["id"]] = "current" if current else "historical"
    return states, rows


def _step_current(row, value, manifest, claims, targets, states, rows):
    current = value["manifestRevision"] == manifest["revision"] and row["claimRevision"] == claims[row["claimId"]]["revision"]
    bindings = all(targets[item["targetId"]]["revision"] == item["revision"] for item in row["targetRevisions"])
    prerequisites = all(states[item["stepId"]] == "current" and rows[item["stepId"]]["revision"] == item["revision"]
                        for item in row["prerequisites"])
    return current and bindings and prerequisites


def _citation_currencies(value, step_states, step_rows):
    rows = {row["id"]: row for row in value["citations"]}
    states = {row["id"]: ("current" if step_states[row["stepId"]] == "current" and row["stepRevision"] == step_rows[row["stepId"]]["revision"] else "historical") for row in value["citations"]}
    return states, rows


def _review_currencies(value, step_states, step_rows, citation_states, citation_rows):
    states = {}
    for row in value["reviews"]:
        step = step_rows[row["stepId"]]
        current = step_states[row["stepId"]] == "current" and row["stepRevision"] == step["revision"]
        current = current and _revision_map(row["targetRevisions"]) == _revision_map(step["targetRevisions"])
        if "citationId" in row:
            citation = citation_rows[row["citationId"]]
            current = current and citation_states[row["citationId"]] == "current" and row["citationRevision"] == citation["revision"]
        states[row["id"]] = "current" if current else "historical"
    return states


def _revision_map(bindings):
    return {item["targetId"]: item["revision"] for item in bindings}
