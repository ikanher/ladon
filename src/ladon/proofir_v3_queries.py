"""Bounded read-only queries over the validated ProofIR v3 projection."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from ladon.proofir_fingerprint_registry import is_exact_scheme

# The registry is deliberately explicit: a scheme is searchable only after its
# producer and comparison semantics are registered here.  The semantic worker's
# structural/v2 fingerprints are exact within one Lean environment and therefore
# are a supported search key, but are never silently equated with lean-expr/v1.
MAX_QUERY_LIMIT = 10_000


def _validate_limit(limit: int) -> None:
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_QUERY_LIMIT:
        raise ValueError(f"invalid query limit: expected 1..{MAX_QUERY_LIMIT}")


def query_v3_semantic_candidates(
    connection: sqlite3.Connection, subject: dict[str, Any], *, limit: int
) -> list[dict[str, Any]]:
    """Return non-merging, owner-qualified candidates for a supported fingerprint.

    This is deliberately a search aid rather than an identity resolver: every
    result retains its distinct owner/local descriptor and no rows are collapsed.
    Unknown opaque fingerprint schemes cannot establish a candidate relation.
    """

    _validate_limit(limit)
    if set(subject) != {"ownerArtifactId", "kind", "localId"}:
        return []
    owner, kind, local_id = (
        subject["ownerArtifactId"],
        subject["kind"],
        subject["localId"],
    )
    source = connection.execute(
        "SELECT fingerprint_scheme_name,fingerprint_scheme_version,fingerprint_digest "
        "FROM proofir_v3_subjects WHERE owner_content_artifact_id=? "
        "AND subject_kind=? AND local_id=?",
        (owner, kind, local_id),
    ).fetchone()
    if (
        source is None
        or not is_exact_scheme(source[0], source[1])
    ):
        return []
    rows = connection.execute(
        "SELECT candidate.owner_content_artifact_id,candidate.subject_kind,candidate.local_id "
        "FROM proofir_v3_subjects AS candidate "
        "JOIN proofir_v3_artifacts AS candidate_artifact "
        "ON candidate_artifact.content_artifact_id=candidate.owner_content_artifact_id "
        "JOIN proofir_v3_artifacts AS source_artifact "
        "ON source_artifact.content_artifact_id=? "
        "WHERE candidate.owner_content_artifact_id<>? AND candidate.subject_kind=? "
        "AND candidate.fingerprint_scheme_name=? AND candidate.fingerprint_scheme_version=? "
        "AND candidate.fingerprint_digest=? "
        "AND candidate_artifact.environment_ref=source_artifact.environment_ref "
        "ORDER BY candidate.owner_content_artifact_id,candidate.subject_kind,candidate.local_id LIMIT ?",
        (owner, owner, kind, source[0], source[1], source[2], limit),
    )
    return [
        {
            "ownerArtifactId": row[0],
            "kind": row[1],
            "localId": row[2],
            "basis": "supported-fingerprint",
        }
        for row in rows
    ]


def query_v3_theorem_evidence(
    connection: sqlite3.Connection, theorem: str, *, limit: int
) -> dict[str, Any]:
    """Return subject-scoped v3 evidence without promoting checker claims."""

    _validate_limit(limit)
    if not _has_table(connection, "proofir_v3_subjects"):
        return _unavailable(theorem, limit)
    subjects = _subjects(connection, theorem, limit)
    claims = _claims(connection, subjects, limit)
    observations = _observations(connection, subjects, limit)
    derivations = _derivations(connection, subjects, limit)
    attachments = _attachments(connection, subjects, limit)
    navigation = _navigation(connection, subjects, limit)
    coverage = _coverage(connection, theorem, limit)
    omissions = _omissions(connection, _artifact_ids(coverage), limit)
    coverage_section = _section(coverage, limit)
    if coverage:
        coverage_section["applicability"] = "applicable"
    else:
        coverage_section["applicability"] = "unavailable"
        coverage_section["reason"] = "no exact theorem selector"
    sections = {
        "subjects": _section(subjects, limit),
        "claims": _section(claims, limit),
        "observations": _section(observations, limit),
        "derivations": _section(derivations, limit),
        "attachments": _section(attachments, limit),
        "navigation": _section(navigation, limit),
    }
    if sections["subjects"]["truncated"]:
        # Child queries intentionally operate on the visible parent slice.  They
        # must not claim an exact population when unseen subjects may own rows.
        for section in sections.values():
            section["matchedExact"] = False
            section["parentTruncated"] = True
    return {
        "schema": "ladon-proofir-v3-theorem-evidence-v1",
        "theorem": theorem,
        "status": "observed" if subjects else "not-observed",
        **sections,
        "coverage": coverage_section,
        "omissions": _section(omissions, limit),
        "limitations": _section(
            _limitations_for_artifacts(
                connection,
                _artifact_ids(claims + observations + derivations + attachments + navigation),
            ),
            limit,
        ),
        "nonclaims": [
            "ProofIR records environment-scoped evidence, not unqualified theorem truth.",
            "Navigation rows are not complete derivation slices.",
        ],
    }


def query_v3_triage(
    connection: sqlite3.Connection, *, limit: int
) -> list[dict[str, Any]]:
    """Return attributable v3 omission and rejected-observation findings."""

    _validate_limit(limit)
    if not _has_table(connection, "proofir_v3_artifacts"):
        return []
    omissions = [
        {
            "identity": row[0],
            "subject": row[1],
            "reason": row[3],
            "stage": row[2],
            "ruleId": "v3_omission",
        }
        for row in connection.execute(
            "SELECT content_artifact_id,source_pointer,stage,reason_code "
            "FROM proofir_v3_omissions "
            "ORDER BY stage,reason_code,content_artifact_id LIMIT ?",
            (limit,),
        )
    ]
    rejected = [
        {
            "artifactId": row[0],
            "observationId": row[1],
            "subject": {
                "ownerArtifactId": row[2],
                "kind": row[3],
                "localId": row[4],
            },
            "result": row[5],
            "semanticValidation": row[6],
            "ruleId": "v3_observation_issue",
        }
        for row in connection.execute(
            "SELECT content_artifact_id,observation_id,owner_content_artifact_id,"
            "subject_kind,subject_local_id,result,"
            "json_extract(dimensions_json,'$.semanticValidation') "
            "FROM proofir_v3_observations WHERE "
            "json_extract(dimensions_json,'$.semanticValidation') IN ('rejected','failed') "
            "ORDER BY json_extract(dimensions_json,'$.semanticValidation'),observation_id LIMIT ?",
            (limit,),
        )
    ]
    return (omissions + rejected)[:limit]


def query_v3_artifacts(
    connection: sqlite3.Connection, artifact: str, *, limit: int
) -> list[dict[str, Any]]:
    _validate_limit(limit)
    if not _has_table(connection, "proofir_v3_artifacts"):
        return []
    return [
        dict(row)
        for row in connection.execute(
            "SELECT content_artifact_id AS artifactId,artifact_kind AS artifactKind,proofir_version AS proofirVersion,environment_ref AS environmentRef FROM proofir_v3_artifacts WHERE content_artifact_id=? OR artifact_kind=? ORDER BY content_artifact_id LIMIT ?",
            (artifact, artifact, limit),
        )
    ]


def _subjects(
    connection: sqlite3.Connection, theorem: str, limit: int
) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT subject.owner_content_artifact_id,artifact.environment_ref,"
        "subject.subject_kind,subject.local_id FROM proofir_v3_subjects AS subject "
        "JOIN proofir_v3_artifacts AS artifact ON "
        "artifact.content_artifact_id=subject.owner_content_artifact_id "
        "WHERE subject.subject_kind='statement' AND (subject.local_id=? OR "
        "json_extract(subject.search_shape_json,'$.declarationName')=?) "
        "ORDER BY subject.owner_content_artifact_id,"
        "subject.subject_kind,subject.local_id LIMIT ?",
        (theorem, theorem, limit + 1),
    )
    return [
        {
            "ownerArtifactId": row[0],
            "environmentRef": row[1],
            "kind": row[2],
            "localId": row[3],
        }
        for row in rows
    ]


def _claims(
    connection: sqlite3.Connection, subjects: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    where, parameters = _subject_predicate(connection, subjects[:limit], "statement_owner_artifact_id", "statement_kind", "statement_local_id")
    return [
        {"artifactId": row[0], "claimId": row[1], "assertionState": row[2], "pointer": row[3]}
        for row in connection.execute(
            "SELECT content_artifact_id,claim_id,assertion_state,source_pointer "
            f"FROM proofir_v3_claims WHERE {where} ORDER BY content_artifact_id,claim_id LIMIT ?",
            (*parameters, limit + 1),
        )
    ]


def _observations(
    connection: sqlite3.Connection, subjects: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    where, parameters = _subject_predicate(connection, subjects[:limit], "observation.owner_content_artifact_id", "observation.subject_kind", "observation.subject_local_id")
    result = []
    rows = connection.execute(
        "SELECT observation.observation_id,observation.content_artifact_id,"
        "observation.observation_kind,observation.result,observation.authority_basis,"
        "observation.guarantee_scope,observation.details_json,observation.dimensions_json,"
        "artifact.environment_ref,artifact.canonical_json,observation.source_pointer "
        "FROM proofir_v3_observations AS observation JOIN proofir_v3_artifacts AS artifact "
        "ON artifact.content_artifact_id=observation.content_artifact_id "
        f"WHERE {where} ORDER BY observation.observation_id LIMIT ?",
        (*parameters, limit + 1),
    )
    for row in rows:
        artifact = json.loads(row[9])
        result.append({"observationId": row[0], "artifactId": row[1], "kind": row[2], "result": row[3], "authorityBasis": row[4], "guaranteeScope": row[5], "details": json.loads(row[6]), "dimensions": json.loads(row[7]), "environmentRef": row[8], "producer": artifact["producer"], "supportingArtifactId": row[1], "limitations": artifact["limitations"], "sourcePointer": row[10]})
    return result


def _derivations(
    connection: sqlite3.Connection, subjects: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    where, parameters = _subject_predicate(connection, subjects[:limit], "conclusion.owner_content_artifact_id", "conclusion.subject_kind", "conclusion.subject_local_id")
    rows = connection.execute(
        "SELECT step.content_artifact_id,step.step_local_id,step.step_kind,conclusion.source_pointer,"
        "step.rule_owner_artifact_id,step.rule_kind,step.rule_local_id,"
        "step.context_owner_artifact_id,step.context_kind,step.context_local_id,"
        "step.check_owner_artifact_id,step.check_kind,step.check_local_id,"
        "conclusion.owner_content_artifact_id,conclusion.subject_kind,conclusion.subject_local_id,"
        "COALESCE((SELECT json_group_array(json(value)) FROM (SELECT json_object('ownerArtifactId',p.owner_content_artifact_id,'kind',p.subject_kind,'localId',p.subject_local_id) AS value FROM proofir_v3_step_premises AS p WHERE p.content_artifact_id=step.content_artifact_id AND p.step_local_id=step.step_local_id ORDER BY p.ordinal)),'[]'),"
        "COALESCE((SELECT json_group_array(json(value)) FROM (SELECT json_object('variable',s.variable,'termRef',json_object('artifactRef',s.owner_content_artifact_id,'kind',s.term_kind,'localId',s.term_local_id)) AS value FROM proofir_v3_substitutions AS s WHERE s.content_artifact_id=step.content_artifact_id AND s.step_local_id=step.step_local_id ORDER BY s.ordinal)),'[]') "
        "FROM proofir_v3_step_conclusions AS conclusion JOIN proofir_v3_derivation_steps AS step "
        "ON step.content_artifact_id=conclusion.content_artifact_id AND step.step_local_id=conclusion.step_local_id "
        f"WHERE {where} ORDER BY step.content_artifact_id,step.step_local_id LIMIT ?",
        (*parameters, limit + 1),
    )
    return [_derivation_row(row) for row in rows]


def _derivation_row(row: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "artifactId": row[0],
        "stepId": row[1],
        "kind": row[2],
        "pointer": row[3],
        "ruleRef": {"artifactRef": row[4], "kind": row[5], "localId": row[6]},
        "localContextRef": {"artifactRef": row[7], "kind": row[8], "localId": row[9]},
        "checkRunRef": {"artifactRef": row[10], "kind": row[11], "localId": row[12]},
        "conclusionRef": {"artifactRef": row[13], "kind": row[14], "localId": row[15]},
        "premiseRefs": json.loads(row[16]),
        "substitutions": json.loads(row[17]),
    }


def _attachments(
    connection: sqlite3.Connection, subjects: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    where, parameters = _subject_predicate(connection, subjects[:limit], "subject_owner_artifact_id", "subject_kind", "subject_local_id")
    return [
        {"artifactId": row[0], "attachmentSetId": row[1], "ordinal": row[2], "selectionDecision": row[3], "selectedCandidateId": row[4], "freshness": row[5], "decisiveEvidence": json.loads(row[6]), "rejectionReasons": json.loads(row[7]), "semanticAcceptance": False, "pointer": row[8]}
        for row in connection.execute(
            "SELECT content_artifact_id,attachment_set_id,ordinal,selection_decision,selected_candidate_id,freshness,decisive_evidence_json,rejection_reasons_json,source_pointer "
            f"FROM proofir_v3_attachments WHERE {where} ORDER BY content_artifact_id,attachment_set_id,ordinal LIMIT ?",
            (*parameters, limit + 1),
        )
    ]


def _navigation(
    connection: sqlite3.Connection, subjects: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    where, parameters = _subject_predicate(connection, subjects[:limit], "owner_content_artifact_id", "subject_kind", "subject_local_id")
    return [
        {"artifactId": row[0], "ordinal": row[1], "pointer": row[2]}
        for row in connection.execute(
            "SELECT content_artifact_id,ordinal,source_pointer FROM proofir_v3_artifact_subjects "
            f"WHERE {where} ORDER BY content_artifact_id,ordinal LIMIT ?",
            (*parameters, limit + 1),
        )
    ]


def _subject_predicate(
    connection: sqlite3.Connection,
    subjects: list[dict[str, Any]], owner: str, kind: str, local_id: str
) -> tuple[str, list[str]]:
    if not subjects:
        return "0", []
    # A temporary relation avoids SQLite host-parameter limits for large theorem
    # slices. It is connection-local, deterministic, and disposable with the
    # read-only connection; no optional JSON extension is required.
    connection.execute(
        "CREATE TEMP TABLE IF NOT EXISTS ladon_v3_query_subjects (owner TEXT NOT NULL, kind TEXT NOT NULL, local_id TEXT NOT NULL, PRIMARY KEY(owner,kind,local_id))"
    )
    connection.execute("DELETE FROM ladon_v3_query_subjects")
    connection.executemany(
        "INSERT OR IGNORE INTO ladon_v3_query_subjects(owner,kind,local_id) VALUES(?,?,?)",
        [(subject["ownerArtifactId"], subject["kind"], subject["localId"]) for subject in subjects],
    )
    owner_column = owner.rsplit(".", 1)[-1]
    kind_column = kind.rsplit(".", 1)[-1]
    local_column = local_id.rsplit(".", 1)[-1]
    return (
        f"EXISTS (SELECT 1 FROM ladon_v3_query_subjects AS q WHERE q.owner={owner_column} AND q.kind={kind_column} AND q.local_id={local_column})",
        [],
    )


def _coverage(
    connection: sqlite3.Connection, theorem: str, limit: int
) -> list[dict[str, Any]]:
    selector = json.dumps({"theorem": theorem}, sort_keys=True, separators=(",", ":"))
    rows = connection.execute(
        "SELECT content_artifact_id,status,population_kind,selector_json,universe_known,"
        "expected,discovered,decoded,valid,projected,query_matched,bounds_json "
        "FROM proofir_v3_coverage WHERE population_kind IN "
        "('theorem-evidence','artifact-subjects') "
        "AND selector_json=? ORDER BY content_artifact_id LIMIT ?",
        (selector, limit + 1),
    )
    return [
        {
            "artifactId": row[0],
            "status": row[1],
            "populationKind": row[2],
            "selector": json.loads(row[3]),
            "universeKnown": bool(row[4]),
            "expected": row[5],
            "discovered": row[6],
            "decoded": row[7],
            "valid": row[8],
            "projected": row[9],
            "queryMatched": row[10],
            "bounds": json.loads(row[11]),
        }
        for row in rows
    ]


def _omissions(
    connection: sqlite3.Connection, artifacts: list[str], limit: int
) -> list[dict[str, Any]]:
    if not artifacts:
        return []
    marks = ",".join("?" for _ in artifacts)
    rows = connection.execute(
        f"SELECT content_artifact_id,source_pointer,stage,reason_code,details_json "
        f"FROM proofir_v3_omissions WHERE content_artifact_id IN ({marks}) "
        f"ORDER BY stage,reason_code,source_pointer LIMIT ?",
        (*artifacts, limit + 1),
    )
    return [
        {
            "artifactId": row[0],
            "pointer": row[1],
            "stage": row[2],
            "reasonCode": row[3],
            "details": json.loads(row[4]),
        }
        for row in rows
    ]


def _artifact_ids(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({str(row["artifactId"]) for row in rows})


def _limitations_for_artifacts(
    connection: sqlite3.Connection, artifact_ids: list[str]
) -> list[dict[str, str]]:
    rows = {
        row["id"]: row
        for artifact_id in artifact_ids
        for row in json.loads(
            connection.execute(
                "SELECT canonical_json FROM proofir_v3_artifacts WHERE content_artifact_id=?",
                (artifact_id,),
            ).fetchone()[0]
        ).get("limitations", [])
    }
    rows.setdefault(
        "evidence-not-theorem-truth",
        {
            "id": "evidence-not-theorem-truth",
            "message": "ProofIR evidence is not unqualified theorem truth.",
        },
    )
    rows.setdefault(
        "navigation-not-complete-proof-slice",
        {
            "id": "navigation-not-complete-proof-slice",
            "message": "A navigation route is not a complete derivation slice.",
        },
    )
    return [rows[key] for key in sorted(rows)]


def _section(rows: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    truncated = len(rows) > limit
    return {
        "rows": rows[:limit],
        "matched": len(rows),
        "matchedLowerBound": len(rows),
        "returned": min(len(rows), limit),
        "truncated": truncated,
        "matchedExact": not truncated,
        "cap": limit,
    }


def _unavailable(theorem: str, limit: int) -> dict[str, Any]:
    unavailable_coverage = {
        **_section([], limit),
        "applicability": "unavailable",
        "reason": "v3 projection unavailable",
    }
    return {
        "schema": "ladon-proofir-v3-theorem-evidence-v1",
        "theorem": theorem,
        "status": "unavailable",
        "subjects": _section([], limit),
        "claims": _section([], limit),
        "observations": _section([], limit),
        "derivations": _section([], limit),
        "attachments": _section([], limit),
        "coverage": unavailable_coverage,
        "omissions": _section([], limit),
        "navigation": _section([], limit),
        "limitations": _section([], limit),
        "nonclaims": ["The v3 projection is unavailable in this database."],
    }


def _has_table(connection: sqlite3.Connection, table: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        is not None
    )


__all__ = [
    "query_v3_artifacts",
    "query_v3_semantic_candidates",
    "query_v3_theorem_evidence",
    "query_v3_triage",
]
