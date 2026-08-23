"""Canonical artifact and reference persistence for semantic evidence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping, Sequence
from typing import Any

from ladon._semantic_evidence_registry_types import (
    SemanticEvidenceRegistryConflict,
    SemanticEvidenceRegistryNotFound,
)
from ladon.proofir_v3 import (
    MAX_ARTIFACTS,
    ProofIRV3Error,
    canonical_bytes,
    validate_envelope,
)


def validated_incoming(
    artifacts: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Validate and deduplicate one incoming artifact bundle."""

    incoming: dict[str, dict[str, Any]] = {}
    encodings: dict[str, bytes] = {}
    for raw in artifacts:
        checked = validate_envelope(dict(raw)).to_dict()
        artifact_ref = str(checked["artifactId"])
        encoded = canonical_bytes(checked)
        prior = encodings.get(artifact_ref)
        if prior is not None and prior != encoded:
            raise SemanticEvidenceRegistryConflict(
                f"conflicting bundle artifacts share {artifact_ref}"
            )
        incoming[artifact_ref] = checked
        encodings[artifact_ref] = encoded
    if len(incoming) > MAX_ARTIFACTS:
        raise ProofIRV3Error(f"semantic evidence bundle exceeds artifact limit: {MAX_ARTIFACTS}")
    return incoming


def registration_result(
    incoming: Mapping[str, Mapping[str, Any]],
    inserted: list[str],
    existing: list[str],
) -> dict[str, Any]:
    """Project one successful transaction into the stable public result."""

    check_refs = [
        {
            "artifactRef": artifact_ref,
            "kind": "check-run",
            "localId": str(artifact["payload"]["checkRunId"]),
        }
        for artifact_ref, artifact in sorted(incoming.items())
        if artifact["artifactKind"] == "proofir.check-run"
    ]
    return {
        "schema": "ladon-semantic-evidence-registration-v1",
        "insertedArtifactRefs": inserted,
        "existingArtifactRefs": existing,
        "environmentRefs": sorted(
            {str(artifact["environmentRef"]) for artifact in incoming.values()}
        ),
        "checkRunRefs": check_refs,
    }


class SemanticArtifactRepository:
    """Read and append canonical ProofIR rows through one transaction."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def hydrate_reference_closure(
        self,
        incoming: Mapping[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Hydrate external owners from already registered artifacts."""

        closure = dict(incoming)
        while True:
            required = self._required_artifact_refs(closure)
            missing = sorted(required - closure.keys())
            if not missing:
                return closure
            if len(closure) + len(missing) > MAX_ARTIFACTS:
                raise ProofIRV3Error(
                    f"semantic evidence closure exceeds artifact limit: {MAX_ARTIFACTS}"
                )
            for artifact_ref in missing:
                closure[artifact_ref] = self.load_artifact(artifact_ref)

    def load_artifact(self, artifact_ref: str) -> dict[str, Any]:
        """Load and revalidate one canonical artifact row."""

        row = self.connection.execute(
            "SELECT artifact_kind,proofir_version,environment_ref,canonical_json,"
            "canonical_byte_count FROM artifacts WHERE artifact_ref=?",
            (artifact_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryNotFound(
                f"semantic artifact is not registered: {artifact_ref}"
            )
        artifact, raw = _decode_stored_artifact(row, artifact_ref)
        if not _stored_metadata_matches(row, artifact_ref, artifact, raw):
            raise SemanticEvidenceRegistryConflict(
                f"stored semantic artifact metadata is inconsistent: {artifact_ref}"
            )
        return artifact

    def insert_artifacts(
        self,
        incoming: Mapping[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        """Append artifact rows and their immutable lookup projections."""

        inserted: list[str] = []
        existing: list[str] = []
        for artifact_ref in sorted(incoming):
            artifact = incoming[artifact_ref]
            if self._insert_artifact_row(artifact_ref, artifact):
                inserted.append(artifact_ref)
            else:
                existing.append(artifact_ref)
        for artifact_ref in sorted(incoming):
            artifact = incoming[artifact_ref]
            if artifact["artifactKind"] == "proofir.environment":
                self._insert_environment(artifact)
            self._insert_typed_refs(artifact)
        return inserted, existing

    def resolve_environment(self, environment_ref: str) -> dict[str, Any]:
        """Resolve an environment identity to its canonical owner artifact."""

        row = self.connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryNotFound(
                f"semantic environment is not registered: {environment_ref}"
            )
        artifact = self.load_artifact(str(row[0]))
        if (
            artifact["artifactKind"] != "proofir.environment"
            or artifact["environmentRef"] != environment_ref
        ):
            raise SemanticEvidenceRegistryConflict(
                f"semantic environment mapping is inconsistent: {environment_ref}"
            )
        self.validate_registered_environment(artifact)
        return artifact

    def resolve_typed_ref(
        self,
        artifact_ref: str,
        kind: str,
        local_id: str,
    ) -> dict[str, Any]:
        """Resolve one validated typed reference to its owner artifact."""

        row = self.connection.execute(
            "SELECT source_pointer FROM typed_refs "
            "WHERE artifact_ref=? AND kind=? AND local_id=?",
            (artifact_ref, kind, local_id),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryNotFound("semantic typed reference is not registered")
        artifact = self.load_artifact(artifact_ref)
        _validate_resolved_typed_ref(artifact, kind, local_id)
        self.validate_registered_environment(artifact)
        return {
            "reference": {
                "artifactRef": artifact_ref,
                "kind": kind,
                "localId": local_id,
            },
            "sourcePointer": str(row[0]),
            "artifact": artifact,
        }

    def validate_all_environment_bindings(
        self,
        incoming: Mapping[str, Mapping[str, Any]],
    ) -> None:
        """Require every appended artifact to resolve through the environment table."""

        for artifact in incoming.values():
            row = self.connection.execute(
                "SELECT environment.artifact_ref FROM environments AS environment "
                "JOIN artifacts AS artifact "
                "ON artifact.artifact_ref=environment.artifact_ref "
                "WHERE environment.environment_ref=? "
                "AND artifact.artifact_kind='proofir.environment' "
                "AND artifact.environment_ref=environment.environment_ref",
                (artifact["environmentRef"],),
            ).fetchone()
            if row is None:
                raise SemanticEvidenceRegistryNotFound(
                    f"semantic environment is not registered: {artifact['environmentRef']}"
                )

    def validate_registered_environment(self, artifact: Mapping[str, Any]) -> None:
        """Require an artifact's environment owner to remain canonical."""

        environment_ref = str(artifact["environmentRef"])
        row = self.connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryConflict(
                f"artifact environment is unresolved: {environment_ref}"
            )
        environment = self.load_artifact(str(row[0]))
        if (
            environment["artifactKind"] != "proofir.environment"
            or environment["environmentRef"] != environment_ref
        ):
            raise SemanticEvidenceRegistryConflict(
                f"artifact environment mapping is inconsistent: {environment_ref}"
            )

    def _required_artifact_refs(
        self,
        artifacts: Mapping[str, Mapping[str, Any]],
    ) -> set[str]:
        required: set[str] = set()
        environments = {
            str(row["environmentRef"]): artifact_ref
            for artifact_ref, row in artifacts.items()
            if row["artifactKind"] == "proofir.environment"
        }
        for artifact in artifacts.values():
            required.update(_external_artifact_refs(artifact))
            if artifact["artifactKind"] == "proofir.environment":
                continue
            environment_ref = str(artifact["environmentRef"])
            required.add(self._environment_artifact_ref(environments, environment_ref))
        return required

    def _environment_artifact_ref(
        self,
        incoming_environments: Mapping[str, str],
        environment_ref: str,
    ) -> str:
        artifact_ref = incoming_environments.get(environment_ref)
        if artifact_ref is not None:
            return artifact_ref
        row = self.connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            raise SemanticEvidenceRegistryNotFound(
                f"semantic environment is not registered: {environment_ref}"
            )
        return str(row[0])

    def _insert_artifact_row(
        self,
        artifact_ref: str,
        artifact: Mapping[str, Any],
    ) -> bool:
        encoded = canonical_bytes(artifact)
        row = self.connection.execute(
            "SELECT 1 FROM artifacts WHERE artifact_ref=?",
            (artifact_ref,),
        ).fetchone()
        if row is not None:
            stored = self.load_artifact(artifact_ref)
            if canonical_bytes(stored) != encoded:
                raise SemanticEvidenceRegistryConflict(
                    f"stored semantic artifact conflicts with {artifact_ref}"
                )
            self._validate_existing_projection(artifact)
            return False
        self.connection.execute(
            "INSERT INTO artifacts(artifact_ref,artifact_kind,proofir_version,"
            "environment_ref,canonical_json,canonical_byte_count) "
            "VALUES(?,?,?,?,?,?)",
            (
                artifact_ref,
                artifact["artifactKind"],
                artifact["proofirVersion"],
                artifact["environmentRef"],
                encoded.decode("utf-8"),
                len(encoded),
            ),
        )
        return True

    def _insert_environment(self, artifact: Mapping[str, Any]) -> None:
        environment_ref = str(artifact["environmentRef"])
        artifact_ref = str(artifact["artifactId"])
        row = self.connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if row is None:
            self.connection.execute(
                "INSERT INTO environments(environment_ref,artifact_ref) VALUES(?,?)",
                (environment_ref, artifact_ref),
            )
        elif str(row[0]) != artifact_ref:
            raise SemanticEvidenceRegistryConflict(
                f"multiple environment artifacts claim {environment_ref}"
            )

    def _insert_typed_refs(self, artifact: Mapping[str, Any]) -> None:
        artifact_ref = str(artifact["artifactId"])
        for (kind, local_id), pointer in sorted(_typed_reference_rows(artifact).items()):
            row = self.connection.execute(
                "SELECT source_pointer FROM typed_refs "
                "WHERE artifact_ref=? AND kind=? AND local_id=?",
                (artifact_ref, kind, local_id),
            ).fetchone()
            if row is None:
                self.connection.execute(
                    "INSERT INTO typed_refs(artifact_ref,kind,local_id,source_pointer) "
                    "VALUES(?,?,?,?)",
                    (artifact_ref, kind, local_id, pointer),
                )
            elif str(row[0]) != pointer:
                raise SemanticEvidenceRegistryConflict(
                    f"typed reference projection conflicts for {artifact_ref}"
                )

    def _validate_existing_projection(self, artifact: Mapping[str, Any]) -> None:
        artifact_ref = str(artifact["artifactId"])
        stored = {
            (str(row[0]), str(row[1])): str(row[2])
            for row in self.connection.execute(
                "SELECT kind,local_id,source_pointer FROM typed_refs WHERE artifact_ref=?",
                (artifact_ref,),
            )
        }
        if stored != _typed_reference_rows(artifact):
            raise SemanticEvidenceRegistryConflict(
                f"typed reference projection is inconsistent for {artifact_ref}"
            )
        if artifact["artifactKind"] == "proofir.environment":
            self._validate_existing_environment_projection(artifact_ref, artifact)

    def _validate_existing_environment_projection(
        self,
        artifact_ref: str,
        artifact: Mapping[str, Any],
    ) -> None:
        row = self.connection.execute(
            "SELECT artifact_ref FROM environments WHERE environment_ref=?",
            (artifact["environmentRef"],),
        ).fetchone()
        if row is None or str(row[0]) != artifact_ref:
            raise SemanticEvidenceRegistryConflict(
                f"environment projection is inconsistent for {artifact_ref}"
            )


def _decode_stored_artifact(
    row: sqlite3.Row,
    artifact_ref: str,
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = str(row[3]).encode("utf-8")
        artifact = validate_envelope(json.loads(raw)).to_dict()
    except (UnicodeError, json.JSONDecodeError, ProofIRV3Error) as error:
        raise SemanticEvidenceRegistryConflict(
            f"stored semantic artifact is invalid: {artifact_ref}"
        ) from error
    return artifact, raw


def _stored_metadata_matches(
    row: sqlite3.Row,
    artifact_ref: str,
    artifact: Mapping[str, Any],
    raw: bytes,
) -> bool:
    return (
        len(raw) == int(row[4])
        and raw == canonical_bytes(artifact)
        and artifact["artifactId"] == artifact_ref
        and artifact["artifactKind"] == row[0]
        and artifact["proofirVersion"] == row[1]
        and artifact["environmentRef"] == row[2]
    )


def _validate_resolved_typed_ref(
    artifact: Mapping[str, Any],
    kind: str,
    local_id: str,
) -> None:
    if kind == "check-run":
        if (
            artifact["artifactKind"] != "proofir.check-run"
            or artifact["payload"].get("checkRunId") != local_id
        ):
            raise SemanticEvidenceRegistryConflict(
                "typed check reference does not match its check artifact"
            )
        return
    identities = {(str(row["kind"]), str(row["localId"])) for row in artifact["subjectRefs"]}
    if (kind, local_id) not in identities:
        raise SemanticEvidenceRegistryConflict(
            "typed subject reference does not match its owner artifact"
        )


def _external_artifact_refs(artifact: Mapping[str, Any]) -> set[str]:
    """Return the explicit external owners checked by ProofIR batch validation."""

    references: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            if set(value) == {"artifactRef", "kind", "localId"}:
                references.add(str(value["artifactRef"]))
                return
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    payload = artifact["payload"]
    visit(payload)
    if artifact["artifactKind"] == "proofir.check-run":
        inputs = payload.get("inputs")
        if isinstance(inputs, Mapping):
            references.update(str(item) for item in inputs.get("artifactRefs", []))
    return references


def _typed_reference_rows(
    artifact: Mapping[str, Any],
) -> dict[tuple[str, str], str]:
    rows = {
        (str(subject["kind"]), str(subject["localId"])): f"/subjectRefs/{index}"
        for index, subject in enumerate(artifact["subjectRefs"])
    }
    if artifact["artifactKind"] == "proofir.check-run":
        rows[("check-run", str(artifact["payload"]["checkRunId"]))] = "/payload/checkRunId"
    return rows
