"""Source association environment for exact source-to-compiled observations."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ladon.lean_toolchain import LeanToolchainContext, verify_toolchain_identities
from ladon.proofir_v3 import (
    validate_envelope_batch,
)
from ladon.source_association_io import _AssociationError, _strict_json
from ladon.stored_candidate_type import candidate_type_evidence

if TYPE_CHECKING:
    from ladon.source_association import SourceAssociationRequest


def _repo_root(request: SourceAssociationRequest) -> Path:
    root = request.repo_root.resolve(strict=True)
    if not root.is_dir() or root != request.toolchain.repo_root.resolve(strict=True):
        raise _AssociationError("unavailable", "repo-root-mismatch", "repository root does not match the selected toolchain")
    if request.toolchain.selection_mode != "explicit":
        raise _AssociationError("unavailable", "ambient-toolchain", "source association requires an explicitly selected toolchain")
    return root


def _select_subject(
    request: SourceAssociationRequest, artifacts: Sequence[Mapping[str, Any]]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    copied = [dict(artifact) for artifact in artifacts]
    validate_envelope_batch(copied)
    owner = _selected_owner(request, copied)
    declaration = _selected_declaration(owner, request.candidate)
    environment = _selected_environment(owner, copied)
    _validate_declaration_input(owner, declaration)
    return owner, environment, declaration


def _selected_owner(request: SourceAssociationRequest, artifacts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    owners = [
        artifact
        for artifact in artifacts
        if artifact.get("artifactId") == request.subject_artifact_id
        and artifact.get("artifactKind") == "proofir.check-run"
    ]
    if len(owners) != 1:
        raise _AssociationError("unavailable", "owner-selection", "selected checked owner is absent or ambiguous")
    return owners[0]


def _selected_declaration(owner: Mapping[str, Any], candidate: str) -> dict[str, Any]:
    subjects = [
        row for row in owner["subjectRefs"]
        if row.get("kind") == "declaration"
        and row.get("display") == candidate
        and isinstance(row.get("fingerprint"), Mapping)
        and isinstance(row.get("searchShape"), Mapping)
    ]
    if len(subjects) != 1:
        raise _AssociationError("unavailable", "declaration-selection", "selected owner has no unique structurally identified declaration")
    declaration = subjects[0]
    try:
        candidate_type_evidence(owner, candidate)
    except (ValueError, TypeError, KeyError) as exc:
        raise _AssociationError("unavailable", "declaration-type-unavailable", str(exc)) from exc
    return declaration


def _selected_environment(owner: Mapping[str, Any], artifacts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    environments = [
        artifact for artifact in artifacts
        if artifact.get("artifactKind") == "proofir.environment"
        and artifact.get("environmentRef") == owner["environmentRef"]
    ]
    if len(environments) != 1:
        raise _AssociationError("unavailable", "environment-selection", "checked owner has no unique canonical environment")
    return environments[0]


def _validate_declaration_input(owner: Mapping[str, Any], declaration: Mapping[str, Any]) -> None:
    if owner["environmentRef"] != owner["payload"]["inputs"]["environmentRef"]:
        raise _AssociationError("stale", "owner-environment-mismatch", "checked owner inputs use another environment")
    declaration_ref = {"kind": "declaration", "localId": declaration["localId"]}
    if declaration_ref not in owner["payload"]["inputs"]["subjectRefs"]:
        raise _AssociationError("unavailable", "declaration-not-checked", "selected declaration is outside the stored check inputs")


def _verify_toolchain(context: LeanToolchainContext) -> None:
    try:
        verify_toolchain_identities(context)
    except (OSError, ValueError) as exc:
        raise _AssociationError("stale", "toolchain-changed", "selected toolchain or source tree changed during association") from exc


def _validate_toolchain(context: LeanToolchainContext, environment: Mapping[str, Any]) -> None:
    payload = environment["payload"]
    _validate_toolchain_release(context, payload)
    _validate_recorded_context(context, payload["options"])


def _validate_toolchain_release(context: LeanToolchainContext, payload: Mapping[str, Any]) -> None:
    prover = payload["prover"]
    toolchain = payload["toolchain"]
    expected_version = context.pin_content.rsplit(":v", 1)[-1]
    observed_versions = set(re.findall(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?)(?![0-9])", str(prover["version"])))
    if (
        toolchain["name"] != "Lean"
        or prover["name"] != "Lean"
        or toolchain["version"] != prover["version"]
        or observed_versions != {expected_version}
        or context.lean_release != expected_version
        or (context.lean_commit is not None and toolchain["commit"] != context.lean_commit)
        or payload["options"].get("observedLeanExecutableDigest") != context.lean_identity
    ):
        raise _AssociationError("stale", "toolchain-mismatch", "selected Lean executable or version differs from the recorded environment")


def _validate_recorded_context(context: LeanToolchainContext, options: Mapping[str, Any]) -> None:
    encoded_context = options.get("toolchainContext")
    try:
        recorded_context = _strict_json(encoded_context) if isinstance(encoded_context, str) else {}
    except json.JSONDecodeError as exc:
        raise _AssociationError("stale", "toolchain-context-mismatch", "recorded Lean toolchain context is malformed") from exc
    if (
        not isinstance(recorded_context, dict)
        or recorded_context.get("selectionMode") != "explicit"
        or recorded_context.get("leanPath") != str(context.lean_path)
        or recorded_context.get("libraryRoots") != [str(path) for path in context.library_roots]
    ):
        raise _AssociationError("stale", "toolchain-mismatch", "selected Lean executable or version differs from the recorded environment")

