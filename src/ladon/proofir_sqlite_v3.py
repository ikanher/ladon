"""Disposable, normalized SQLite projection for canonical ProofIR v3 artifacts.

ladon-quality: reviewed-schema-hotspot
The normalized schema and projector remain together so constraints, foreign
keys, insertion order, and query-plan gates are reviewed as one contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from ladon.proofir_v3 import (
    _validate_external_references,
    canonical_bytes,
    validate_envelope,
    validate_envelope_batch,
)
from ladon.sqlite_publication import (
    PublicationLock,
    PublicationLockBusy,
    acquire_publication_lock,
    durable_replace,
    release_publication_lock,
)

V3_SCHEMA_VERSION = 8
MAX_EXTENSION_BYTES = 64 * 1024
DEFAULT_MAX_DATABASE_BYTES = 512 * 1024 * 1024


_V3Lock = PublicationLock


def _acquire_v3_lock(destination: Path) -> _V3Lock:
    """Acquire the shared ownership-safe SQLite publication lock."""

    try:
        return acquire_publication_lock(destination)
    except PublicationLockBusy as error:
        raise RuntimeError("ProofIR v3 database build already active") from error


def _release_v3_lock(lock: _V3Lock) -> None:
    """Release shared kernel ownership without unlinking the metadata path."""

    release_publication_lock(lock)


def _durable_v3_replace(temporary: Path, destination: Path) -> None:
    durable_replace(temporary, destination)

REQUIRED_TABLES = frozenset(
    {
        "proofir_v3_artifacts",
        "proofir_v3_environments",
        "proofir_v3_subjects",
        "proofir_v3_artifact_subjects",
        "proofir_v3_claims",
        "proofir_v3_derivations",
        "proofir_v3_derivation_sccs",
        "proofir_v3_scc_members",
        "proofir_v3_derivation_steps",
        "proofir_v3_step_premises",
        "proofir_v3_step_conclusions",
        "proofir_v3_substitutions",
        "proofir_v3_plans",
        "proofir_v3_plan_steps",
        "proofir_v3_attempt_logs",
        "proofir_v3_attempts",
        "proofir_v3_attempt_residuals",
        "proofir_v3_check_runs",
        "proofir_v3_check_results",
        "proofir_v3_source_maps",
        "proofir_v3_surfaces",
        "proofir_v3_attachment_sets",
        "proofir_v3_attachments",
        "proofir_v3_attachment_candidates",
        "proofir_v3_observations",
        "proofir_v3_coverage",
        "proofir_v3_omissions",
        "proofir_v3_extensions",
    }
)

REQUIRED_INDEXES = frozenset(
    {
        "idx_v3_artifact_environment",
        "idx_v3_artifacts_kind",
        "idx_v3_environment_manifest",
        "idx_v3_subject_local_id",
        "idx_v3_artifact_subject_identity",
        "idx_v3_claim_subject",
        "idx_v3_derivation_recursive",
        "idx_v3_scc_member_subject",
        "idx_v3_step_rule",
        "idx_v3_step_context",
        "idx_v3_step_check",
        "idx_v3_premise_subject",
        "idx_v3_conclusion_subject",
        "idx_v3_substitution_subject",
        "idx_v3_plan_step_rule",
        "idx_v3_plan_step_context",
        "idx_v3_plan_step_conclusion",
        "idx_v3_attempt_goal",
        "idx_v3_attempt_step",
        "idx_v3_attempt_rule",
        "idx_v3_attempt_conclusion",
        "idx_v3_attempt_check",
        "idx_v3_residual_subject",
        "idx_v3_check_result_subject",
        "idx_v3_surface_subject",
        "idx_v3_attachment_subject",
        "idx_v3_attachment_source",
        "idx_v3_attachment_selected_candidate",
        "idx_v3_candidate_source",
        "idx_v3_observation_subject",
        "idx_v3_coverage_selector",
        "idx_v3_omission_artifact",
        "idx_v3_omission_triage",
        "idx_v3_extension_namespace",
    }
)

V3_QUERY_SHAPES = {
    "artifact.identity": "SELECT content_artifact_id FROM proofir_v3_artifacts WHERE artifact_kind=? AND proofir_version=? ORDER BY content_artifact_id LIMIT ?",
    "dossier.subject": "SELECT owner_content_artifact_id FROM proofir_v3_subjects WHERE local_id=? AND subject_kind=? ORDER BY owner_content_artifact_id LIMIT ?",
    "dossier.claim": "SELECT claim_id FROM proofir_v3_claims WHERE statement_owner_artifact_id=? AND statement_kind=? AND statement_local_id=? ORDER BY content_artifact_id,claim_id LIMIT ?",
    "dossier.observation": "SELECT observation_id FROM proofir_v3_observations WHERE owner_content_artifact_id=? AND subject_kind=? AND subject_local_id=? ORDER BY content_artifact_id,observation_id LIMIT ?",
    "derivation.conclusion": "SELECT content_artifact_id,step_local_id FROM proofir_v3_step_conclusions WHERE owner_content_artifact_id=? AND subject_kind=? AND subject_local_id=? ORDER BY content_artifact_id,step_local_id LIMIT ?",
    "derivation.slice": "SELECT ordinal,subject_local_id FROM proofir_v3_step_premises WHERE content_artifact_id=? AND step_local_id=? ORDER BY ordinal LIMIT ?",
    "derivation.recursive-seed": "SELECT content_artifact_id,component_id FROM proofir_v3_scc_members WHERE owner_content_artifact_id=? AND subject_kind=? AND subject_local_id=? ORDER BY content_artifact_id,component_id LIMIT ?",
    "attachment.subject": "SELECT content_artifact_id,attachment_set_id,ordinal FROM proofir_v3_attachments WHERE subject_owner_artifact_id=? AND subject_kind=? AND subject_local_id=? ORDER BY content_artifact_id,attachment_set_id,ordinal LIMIT ?",
    "attachment.candidate-source": "SELECT content_artifact_id,attachment_set_id,attachment_ordinal,ordinal FROM proofir_v3_attachment_candidates WHERE source_owner_artifact_id=? AND source_kind=? AND source_local_id=? ORDER BY content_artifact_id,attachment_set_id,attachment_ordinal,ordinal LIMIT ?",
    "check.results": "SELECT ordinal,result FROM proofir_v3_check_results WHERE content_artifact_id=? AND check_run_id=? ORDER BY ordinal LIMIT ?",
    "dossier.coverage": "SELECT content_artifact_id FROM proofir_v3_coverage WHERE selector_json=? AND population_kind IN ('theorem-evidence','artifact-subjects') ORDER BY content_artifact_id LIMIT ?",
    "omissions.artifact": "SELECT source_pointer,reason_code FROM proofir_v3_omissions WHERE content_artifact_id=? ORDER BY stage,reason_code,source_pointer LIMIT ?",
    "omissions.triage": "SELECT content_artifact_id FROM proofir_v3_omissions ORDER BY stage,reason_code,content_artifact_id LIMIT ?",
    "extensions.namespace": "SELECT content_artifact_id FROM proofir_v3_extensions WHERE namespace=? ORDER BY content_artifact_id LIMIT ?",
}

V3_QUERY_ACCESS_PATHS = {
    "artifact.identity": "idx_v3_artifacts_kind",
    "dossier.subject": "idx_v3_subject_local_id",
    "dossier.claim": "idx_v3_claim_subject",
    "dossier.observation": "idx_v3_observation_subject",
    "derivation.conclusion": "idx_v3_conclusion_subject",
    "derivation.slice": "sqlite_autoindex_proofir_v3_step_premises_1",
    "derivation.recursive-seed": "idx_v3_scc_member_subject",
    "attachment.subject": "idx_v3_attachment_subject",
    "attachment.candidate-source": "idx_v3_candidate_source",
    "check.results": "sqlite_autoindex_proofir_v3_check_results_1",
    "dossier.coverage": "idx_v3_coverage_selector",
    "omissions.artifact": "idx_v3_omission_artifact",
    "omissions.triage": "idx_v3_omission_triage",
    "extensions.namespace": "idx_v3_extension_namespace",
}

_V3_QUERY_PARAMETERS = {
    "artifact.identity": ("proofir.claim", "3.0", 10),
    "dossier.subject": ("statement:goal", "statement", 10),
    "dossier.claim": ("sha256:" + "a" * 64, "statement", "statement:goal", 10),
    "dossier.observation": (
        "sha256:" + "a" * 64,
        "statement",
        "statement:goal",
        10,
    ),
    "derivation.conclusion": (
        "sha256:" + "a" * 64,
        "statement",
        "statement:goal",
        10,
    ),
    "derivation.slice": ("sha256:" + "a" * 64, "step:1", 10),
    "derivation.recursive-seed": (
        "sha256:" + "a" * 64,
        "statement",
        "statement:goal",
        10,
    ),
    "attachment.subject": (
        "sha256:" + "a" * 64,
        "statement",
        "statement:goal",
        10,
    ),
    "attachment.candidate-source": (
        "sha256:" + "a" * 64,
        "surface",
        "surface:1",
        10,
    ),
    "check.results": ("sha256:" + "a" * 64, "check:1", 10),
    "dossier.coverage": ('{"theorem":"statement:goal"}', 10),
    "omissions.artifact": ("sha256:" + "a" * 64, 10),
    "omissions.triage": (10,),
    "extensions.namespace": ("example.fixture/v1", 10),
}

_V3_QUERY_TABLES = {
    name: table
    for name, table in {
        "artifact.identity": "proofir_v3_artifacts",
        "dossier.subject": "proofir_v3_subjects",
        "dossier.claim": "proofir_v3_claims",
        "dossier.observation": "proofir_v3_observations",
        "derivation.conclusion": "proofir_v3_step_conclusions",
        "derivation.slice": "proofir_v3_step_premises",
        "derivation.recursive-seed": "proofir_v3_scc_members",
        "attachment.subject": "proofir_v3_attachments",
        "attachment.candidate-source": "proofir_v3_attachment_candidates",
        "check.results": "proofir_v3_check_results",
        "dossier.coverage": "proofir_v3_coverage",
        "omissions.artifact": "proofir_v3_omissions",
        "omissions.triage": "proofir_v3_omissions",
        "extensions.namespace": "proofir_v3_extensions",
    }.items()
}
_PLAN_SELECTION_MIN_ROWS = 32


_SCHEMA = r"""
CREATE TABLE IF NOT EXISTS proofir_v3_environments (
    environment_ref TEXT PRIMARY KEY CHECK(environment_ref GLOB 'sha256:*'),
    manifest_artifact_id TEXT,
    environment_json TEXT CHECK(environment_json IS NULL OR json_valid(environment_json)),
    resolution_state TEXT NOT NULL CHECK(resolution_state IN ('resolved','unresolved')),
    CHECK((resolution_state='resolved' AND manifest_artifact_id IS NOT NULL AND environment_json IS NOT NULL)
       OR (resolution_state='unresolved' AND manifest_artifact_id IS NULL AND environment_json IS NULL)),
    FOREIGN KEY(manifest_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id)
        ON DELETE SET NULL DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_artifacts (
    content_artifact_id TEXT PRIMARY KEY CHECK(content_artifact_id GLOB 'sha256:*'),
    artifact_kind TEXT NOT NULL CHECK(artifact_kind IN (
        'proofir.claim','proofir.derivation','proofir.plan','proofir.attempt-log',
        'proofir.environment','proofir.check-run','proofir.source-map',
        'proofir.attachment-set','proofir.governance-observation')),
    proofir_version TEXT NOT NULL CHECK(proofir_version='3.0'),
    environment_ref TEXT NOT NULL,
    canonical_json TEXT NOT NULL CHECK(json_valid(canonical_json)),
    source_pointer TEXT NOT NULL CHECK(source_pointer='/'),
    FOREIGN KEY(environment_ref) REFERENCES proofir_v3_environments(environment_ref)
        ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_subjects (
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL CHECK(length(subject_kind)>0),
    local_id TEXT NOT NULL CHECK(length(local_id)>0),
    fingerprint_scheme_name TEXT,
    fingerprint_scheme_version TEXT,
    fingerprint_digest TEXT,
    display TEXT,
    search_shape_json TEXT CHECK(search_shape_json IS NULL OR json_valid(search_shape_json)),
    opaque_payload_ref TEXT CHECK(opaque_payload_ref IS NULL OR opaque_payload_ref GLOB 'sha256:*'),
    CHECK((fingerprint_scheme_name IS NULL AND fingerprint_scheme_version IS NULL AND fingerprint_digest IS NULL)
       OR (fingerprint_scheme_name IS NOT NULL AND fingerprint_scheme_version IS NOT NULL
           AND fingerprint_digest GLOB 'sha256:*')),
    PRIMARY KEY(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(owner_content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_artifact_subjects (
    content_artifact_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,ordinal),
    UNIQUE(content_artifact_id,owner_content_artifact_id,subject_kind,subject_local_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_claims (
    content_artifact_id TEXT NOT NULL,
    claim_id TEXT NOT NULL CHECK(length(claim_id)>0),
    statement_owner_artifact_id TEXT NOT NULL,
    statement_kind TEXT NOT NULL,
    statement_local_id TEXT NOT NULL,
    assertion_state TEXT NOT NULL CHECK(assertion_state IN ('asserted','denied','unknown')),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,claim_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE,
    FOREIGN KEY(statement_owner_artifact_id,statement_kind,statement_local_id)
        REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_derivations (
    content_artifact_id TEXT PRIMARY KEY,
    derivation_id TEXT NOT NULL CHECK(length(derivation_id)>0),
    acyclic INTEGER NOT NULL CHECK(acyclic IN (0,1)),
    recursion_policy TEXT,
    source_pointer TEXT NOT NULL,
    CHECK((acyclic=1 AND recursion_policy IS NULL)
       OR (acyclic=0 AND recursion_policy='declared-strongly-connected-components')),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_derivation_sccs (
    content_artifact_id TEXT NOT NULL,
    component_id TEXT NOT NULL CHECK(length(component_id)>0),
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    semantics TEXT NOT NULL CHECK(semantics='declared-recursive-fixed-point'),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,component_id),
    UNIQUE(content_artifact_id,ordinal),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_derivations(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_scc_members (
    content_artifact_id TEXT NOT NULL,
    component_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL CHECK(subject_kind='statement'),
    subject_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,component_id,ordinal),
    UNIQUE(content_artifact_id,owner_content_artifact_id,subject_kind,subject_local_id),
    FOREIGN KEY(content_artifact_id,component_id) REFERENCES proofir_v3_derivation_sccs(content_artifact_id,component_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_derivation_steps (
    content_artifact_id TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    step_kind TEXT NOT NULL CHECK(step_kind='theorem-application'),
    rule_owner_artifact_id TEXT NOT NULL,
    rule_kind TEXT NOT NULL CHECK(rule_kind='declaration'),
    rule_local_id TEXT NOT NULL,
    context_owner_artifact_id TEXT NOT NULL,
    context_kind TEXT NOT NULL CHECK(context_kind='local-context'),
    context_local_id TEXT NOT NULL,
    check_owner_artifact_id TEXT NOT NULL,
    check_kind TEXT NOT NULL CHECK(check_kind='check-run'),
    check_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,step_local_id),
    UNIQUE(content_artifact_id,ordinal),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE,
    FOREIGN KEY(rule_owner_artifact_id,rule_kind,rule_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(context_owner_artifact_id,context_kind,context_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(check_owner_artifact_id,check_kind,check_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_step_premises (
    content_artifact_id TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL CHECK(subject_kind='statement'),
    subject_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,step_local_id,ordinal),
    FOREIGN KEY(content_artifact_id,step_local_id) REFERENCES proofir_v3_derivation_steps(content_artifact_id,step_local_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_step_conclusions (
    content_artifact_id TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL CHECK(subject_kind='statement'),
    subject_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,step_local_id),
    FOREIGN KEY(content_artifact_id,step_local_id) REFERENCES proofir_v3_derivation_steps(content_artifact_id,step_local_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_substitutions (
    content_artifact_id TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    variable TEXT NOT NULL CHECK(length(variable)>0),
    owner_content_artifact_id TEXT NOT NULL,
    term_kind TEXT NOT NULL CHECK(term_kind='term'),
    term_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,step_local_id,ordinal),
    FOREIGN KEY(content_artifact_id,step_local_id) REFERENCES proofir_v3_derivation_steps(content_artifact_id,step_local_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,term_kind,term_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_plans (
    content_artifact_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    policy_json TEXT NOT NULL CHECK(json_valid(policy_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,plan_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_plan_steps (
    content_artifact_id TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    step_kind TEXT NOT NULL,
    rule_owner_artifact_id TEXT NOT NULL,
    rule_kind TEXT NOT NULL,
    rule_local_id TEXT NOT NULL,
    conclusion_owner_artifact_id TEXT NOT NULL,
    conclusion_kind TEXT NOT NULL,
    conclusion_local_id TEXT NOT NULL,
    context_owner_artifact_id TEXT NOT NULL,
    context_kind TEXT NOT NULL,
    context_local_id TEXT NOT NULL,
    premises_json TEXT NOT NULL CHECK(json_valid(premises_json)),
    substitutions_json TEXT NOT NULL CHECK(json_valid(substitutions_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,plan_id,step_local_id),
    FOREIGN KEY(content_artifact_id,plan_id) REFERENCES proofir_v3_plans(content_artifact_id,plan_id) ON DELETE CASCADE,
    FOREIGN KEY(rule_owner_artifact_id,rule_kind,rule_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(context_owner_artifact_id,context_kind,context_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_attempt_logs (
    content_artifact_id TEXT NOT NULL,
    attempt_log_id TEXT NOT NULL,
    goal_owner_artifact_id TEXT NOT NULL,
    goal_kind TEXT NOT NULL,
    goal_local_id TEXT NOT NULL,
    summary_outcome TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,attempt_log_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE,
    FOREIGN KEY(goal_owner_artifact_id,goal_kind,goal_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_attempts (
    content_artifact_id TEXT NOT NULL,
    attempt_log_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    step_owner_artifact_id TEXT NOT NULL,
    step_kind TEXT NOT NULL,
    step_local_id TEXT NOT NULL,
    rule_owner_artifact_id TEXT NOT NULL,
    rule_kind TEXT NOT NULL,
    rule_local_id TEXT NOT NULL,
    conclusion_owner_artifact_id TEXT NOT NULL,
    conclusion_kind TEXT NOT NULL,
    conclusion_local_id TEXT NOT NULL,
    check_owner_artifact_id TEXT NOT NULL,
    check_kind TEXT NOT NULL,
    check_local_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('proposed','accepted','rejected','timeout','infrastructure-error')),
    premise_refs_json TEXT NOT NULL CHECK(json_valid(premise_refs_json)),
    substitutions_json TEXT NOT NULL CHECK(json_valid(substitutions_json)),
    diagnostics_json TEXT NOT NULL CHECK(json_valid(diagnostics_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,attempt_log_id,attempt_id),
    FOREIGN KEY(content_artifact_id,attempt_log_id) REFERENCES proofir_v3_attempt_logs(content_artifact_id,attempt_log_id) ON DELETE CASCADE,
    FOREIGN KEY(step_owner_artifact_id,step_kind,step_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(rule_owner_artifact_id,rule_kind,rule_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(check_owner_artifact_id,check_kind,check_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_attempt_residuals (
    content_artifact_id TEXT NOT NULL,
    attempt_log_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,attempt_log_id,ordinal),
    FOREIGN KEY(content_artifact_id,attempt_log_id) REFERENCES proofir_v3_attempt_logs(content_artifact_id,attempt_log_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_check_runs (
    content_artifact_id TEXT NOT NULL,
    check_run_id TEXT NOT NULL,
    checker_json TEXT NOT NULL CHECK(json_valid(checker_json)),
    operation TEXT NOT NULL,
    inputs_json TEXT NOT NULL CHECK(json_valid(inputs_json)),
    outputs_json TEXT NOT NULL CHECK(json_valid(outputs_json)),
    bounds_json TEXT NOT NULL CHECK(json_valid(bounds_json)),
    guarantee_scope TEXT NOT NULL,
    authority_basis TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,check_run_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_check_results (
    content_artifact_id TEXT NOT NULL,
    check_run_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('accepted','unchecked','rejected','unknown','error')),
    diagnostics_json TEXT NOT NULL CHECK(json_valid(diagnostics_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,check_run_id,ordinal),
    FOREIGN KEY(content_artifact_id,check_run_id) REFERENCES proofir_v3_check_runs(content_artifact_id,check_run_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_source_maps (
    content_artifact_id TEXT NOT NULL,
    source_map_id TEXT NOT NULL,
    policy_json TEXT NOT NULL CHECK(json_valid(policy_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,source_map_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_surfaces (
    content_artifact_id TEXT NOT NULL,
    source_map_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    source_path TEXT NOT NULL,
    module TEXT NOT NULL,
    declaration_name TEXT NOT NULL,
    start_json TEXT NOT NULL CHECK(json_valid(start_json)),
    end_json TEXT NOT NULL CHECK(json_valid(end_json)),
    content_digest TEXT NOT NULL,
    match_method TEXT NOT NULL,
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,source_map_id,ordinal),
    FOREIGN KEY(content_artifact_id,source_map_id) REFERENCES proofir_v3_source_maps(content_artifact_id,source_map_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_attachment_sets (
    content_artifact_id TEXT NOT NULL,
    attachment_set_id TEXT NOT NULL,
    resolver_json TEXT NOT NULL CHECK(json_valid(resolver_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,attachment_set_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_attachments (
    content_artifact_id TEXT NOT NULL,
    attachment_set_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    subject_owner_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    selection_decision TEXT NOT NULL CHECK(selection_decision IN ('selected','ambiguous','unresolved','none')),
    selected_candidate_id TEXT CHECK(selected_candidate_id IS NULL OR length(selected_candidate_id)>0),
    source_owner_artifact_id TEXT,
    source_kind TEXT,
    source_local_id TEXT,
    freshness TEXT NOT NULL CHECK(freshness IN ('fresh','stale','unknown')),
    decisive_evidence_json TEXT NOT NULL CHECK(json_valid(decisive_evidence_json) AND json_type(decisive_evidence_json)='array'),
    rejection_reasons_json TEXT NOT NULL CHECK(json_valid(rejection_reasons_json) AND json_type(rejection_reasons_json)='array'),
    semantic_acceptance INTEGER NOT NULL CHECK(semantic_acceptance=0),
    source_pointer TEXT NOT NULL,
    CHECK((selection_decision='selected' AND selected_candidate_id IS NOT NULL
           AND source_owner_artifact_id IS NOT NULL AND source_kind IS NOT NULL
           AND source_local_id IS NOT NULL)
       OR (selection_decision!='selected' AND selected_candidate_id IS NULL
           AND source_owner_artifact_id IS NULL AND source_kind IS NULL
           AND source_local_id IS NULL)),
    PRIMARY KEY(content_artifact_id,attachment_set_id,ordinal),
    FOREIGN KEY(content_artifact_id,attachment_set_id) REFERENCES proofir_v3_attachment_sets(content_artifact_id,attachment_set_id) ON DELETE CASCADE,
    FOREIGN KEY(subject_owner_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(source_owner_artifact_id,source_kind,source_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id),
    FOREIGN KEY(content_artifact_id,attachment_set_id,ordinal,selected_candidate_id)
        REFERENCES proofir_v3_attachment_candidates(content_artifact_id,attachment_set_id,attachment_ordinal,declaration_id)
        DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE IF NOT EXISTS proofir_v3_attachment_candidates (
    content_artifact_id TEXT NOT NULL,
    attachment_set_id TEXT NOT NULL,
    attachment_ordinal INTEGER NOT NULL CHECK(attachment_ordinal>=0),
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    source_owner_artifact_id TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    source_local_id TEXT NOT NULL,
    declaration_id TEXT NOT NULL CHECK(length(declaration_id)>0),
    method TEXT NOT NULL CHECK(method IN (
        'environment-fingerprint','producer-declaration','content-range',
        'content-name','path-range','module-name','name-only-diagnostic',
        'identity-conflict-diagnostic','unsafe-path-diagnostic','unmatched-diagnostic')),
    confidence TEXT NOT NULL CHECK(confidence IN ('exact','strong','bounded-fallback','none')),
    freshness TEXT NOT NULL CHECK(freshness IN ('fresh','stale','unknown')),
    rank INTEGER NOT NULL CHECK(rank>=0),
    policy_version TEXT NOT NULL CHECK(policy_version='proofir-attachment-policy-v1'),
    decisive_evidence_json TEXT NOT NULL CHECK(json_valid(decisive_evidence_json) AND json_type(decisive_evidence_json)='array'),
    rejection_reasons_json TEXT NOT NULL CHECK(json_valid(rejection_reasons_json) AND json_type(rejection_reasons_json)='array'),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,attachment_set_id,attachment_ordinal,ordinal),
    UNIQUE(content_artifact_id,attachment_set_id,attachment_ordinal,declaration_id),
    FOREIGN KEY(content_artifact_id,attachment_set_id,attachment_ordinal) REFERENCES proofir_v3_attachments(content_artifact_id,attachment_set_id,ordinal) ON DELETE CASCADE,
    FOREIGN KEY(source_owner_artifact_id,source_kind,source_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_observations (
    content_artifact_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    owner_content_artifact_id TEXT NOT NULL,
    subject_kind TEXT NOT NULL,
    subject_local_id TEXT NOT NULL,
    observation_kind TEXT NOT NULL,
    result TEXT NOT NULL,
    guarantee_scope TEXT NOT NULL,
    authority_basis TEXT NOT NULL,
    dimensions_json TEXT NOT NULL CHECK(json_valid(dimensions_json)),
    details_json TEXT NOT NULL CHECK(json_valid(details_json)),
    diagnostics_json TEXT NOT NULL CHECK(json_valid(diagnostics_json)),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,observation_id),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE,
    FOREIGN KEY(owner_content_artifact_id,subject_kind,subject_local_id) REFERENCES proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id)
);
CREATE TABLE IF NOT EXISTS proofir_v3_coverage (
    content_artifact_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    population_kind TEXT NOT NULL,
    selector_json TEXT NOT NULL CHECK(json_valid(selector_json)),
    universe_known INTEGER NOT NULL CHECK(universe_known IN (0,1)),
    expected INTEGER NOT NULL CHECK(expected>=0),
    discovered INTEGER NOT NULL CHECK(discovered>=0),
    decoded INTEGER NOT NULL CHECK(decoded>=0),
    valid INTEGER NOT NULL CHECK(valid>=0),
    projected INTEGER NOT NULL CHECK(projected>=0),
    query_matched INTEGER NOT NULL CHECK(query_matched>=0),
    bounds_json TEXT NOT NULL CHECK(json_valid(bounds_json)),
    source_pointer TEXT NOT NULL,
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_omissions (
    content_artifact_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal>=0),
    source_pointer TEXT NOT NULL,
    stage TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    details_json TEXT NOT NULL CHECK(json_valid(details_json)),
    PRIMARY KEY(content_artifact_id,ordinal),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS proofir_v3_extensions (
    content_artifact_id TEXT NOT NULL,
    namespace TEXT NOT NULL,
    payload_json TEXT NOT NULL CHECK(json_valid(payload_json)),
    payload_digest TEXT NOT NULL CHECK(payload_digest GLOB 'sha256:*'),
    storage_state TEXT NOT NULL CHECK(storage_state IN ('full','digest-sentinel')),
    original_bytes INTEGER NOT NULL CHECK(original_bytes>=0),
    source_pointer TEXT NOT NULL,
    PRIMARY KEY(content_artifact_id,namespace),
    FOREIGN KEY(content_artifact_id) REFERENCES proofir_v3_artifacts(content_artifact_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_v3_artifact_environment ON proofir_v3_artifacts(environment_ref,content_artifact_id);
CREATE INDEX IF NOT EXISTS idx_v3_artifacts_kind ON proofir_v3_artifacts(artifact_kind,proofir_version,content_artifact_id);
CREATE INDEX IF NOT EXISTS idx_v3_environment_manifest ON proofir_v3_environments(manifest_artifact_id) WHERE manifest_artifact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_v3_subject_local_id ON proofir_v3_subjects(local_id,owner_content_artifact_id,subject_kind);
CREATE INDEX IF NOT EXISTS idx_v3_artifact_subject_identity ON proofir_v3_artifact_subjects(owner_content_artifact_id,subject_kind,subject_local_id,content_artifact_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_v3_claim_subject ON proofir_v3_claims(statement_owner_artifact_id,statement_kind,statement_local_id,content_artifact_id,claim_id);
CREATE INDEX IF NOT EXISTS idx_v3_derivation_recursive ON proofir_v3_derivations(acyclic,content_artifact_id);
CREATE INDEX IF NOT EXISTS idx_v3_scc_member_subject ON proofir_v3_scc_members(owner_content_artifact_id,subject_kind,subject_local_id,content_artifact_id,component_id);
CREATE INDEX IF NOT EXISTS idx_v3_step_rule ON proofir_v3_derivation_steps(rule_owner_artifact_id,rule_kind,rule_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_step_context ON proofir_v3_derivation_steps(context_owner_artifact_id,context_kind,context_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_step_check ON proofir_v3_derivation_steps(check_owner_artifact_id,check_kind,check_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_premise_subject ON proofir_v3_step_premises(owner_content_artifact_id,subject_kind,subject_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_conclusion_subject ON proofir_v3_step_conclusions(owner_content_artifact_id,subject_kind,subject_local_id,content_artifact_id,step_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_substitution_subject ON proofir_v3_substitutions(owner_content_artifact_id,term_kind,term_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_plan_step_rule ON proofir_v3_plan_steps(rule_owner_artifact_id,rule_kind,rule_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_plan_step_conclusion ON proofir_v3_plan_steps(conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_plan_step_context ON proofir_v3_plan_steps(context_owner_artifact_id,context_kind,context_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attempt_goal ON proofir_v3_attempt_logs(goal_owner_artifact_id,goal_kind,goal_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attempt_step ON proofir_v3_attempts(step_owner_artifact_id,step_kind,step_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attempt_rule ON proofir_v3_attempts(rule_owner_artifact_id,rule_kind,rule_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attempt_conclusion ON proofir_v3_attempts(conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attempt_check ON proofir_v3_attempts(check_owner_artifact_id,check_kind,check_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_residual_subject ON proofir_v3_attempt_residuals(owner_content_artifact_id,subject_kind,subject_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_check_result_subject ON proofir_v3_check_results(owner_content_artifact_id,subject_kind,subject_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_surface_subject ON proofir_v3_surfaces(owner_content_artifact_id,subject_kind,subject_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attachment_subject ON proofir_v3_attachments(subject_owner_artifact_id,subject_kind,subject_local_id,content_artifact_id,attachment_set_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_v3_attachment_source ON proofir_v3_attachments(source_owner_artifact_id,source_kind,source_local_id);
CREATE INDEX IF NOT EXISTS idx_v3_attachment_selected_candidate ON proofir_v3_attachments(content_artifact_id,attachment_set_id,ordinal,selected_candidate_id);
CREATE INDEX IF NOT EXISTS idx_v3_candidate_source ON proofir_v3_attachment_candidates(source_owner_artifact_id,source_kind,source_local_id,content_artifact_id,attachment_set_id,attachment_ordinal,ordinal);
CREATE INDEX IF NOT EXISTS idx_v3_observation_subject ON proofir_v3_observations(owner_content_artifact_id,subject_kind,subject_local_id,content_artifact_id,observation_id);
CREATE INDEX IF NOT EXISTS idx_v3_coverage_selector ON proofir_v3_coverage(selector_json,content_artifact_id,population_kind);
CREATE INDEX IF NOT EXISTS idx_v3_omission_artifact ON proofir_v3_omissions(content_artifact_id,stage,reason_code,source_pointer,ordinal);
CREATE INDEX IF NOT EXISTS idx_v3_omission_triage ON proofir_v3_omissions(stage,reason_code,content_artifact_id,ordinal);
CREATE INDEX IF NOT EXISTS idx_v3_extension_namespace ON proofir_v3_extensions(namespace,content_artifact_id);
"""

# Every semantic row pointer is an RFC 6901 JSON Pointer.  SQLite cannot decode
# escape sequences, but it can reject missing roots, dangling ``~``, and every
# escape other than ``~0``/``~1`` before a row reaches the projection.
_SCHEMA = _SCHEMA.replace(
    "source_pointer TEXT NOT NULL",
    "source_pointer TEXT NOT NULL CHECK("
    "source_pointer='/' OR (substr(source_pointer,1,1)='/' "
    "AND source_pointer NOT GLOB '*~[^01]*' "
    "AND source_pointer NOT GLOB '*~'))",
)


_DELETE_ORDER = (
    "proofir_v3_attachment_candidates",
    "proofir_v3_attachments",
    "proofir_v3_attachment_sets",
    "proofir_v3_surfaces",
    "proofir_v3_source_maps",
    "proofir_v3_check_results",
    "proofir_v3_check_runs",
    "proofir_v3_attempt_residuals",
    "proofir_v3_attempts",
    "proofir_v3_attempt_logs",
    "proofir_v3_plan_steps",
    "proofir_v3_plans",
    "proofir_v3_substitutions",
    "proofir_v3_step_conclusions",
    "proofir_v3_step_premises",
    "proofir_v3_derivation_steps",
    "proofir_v3_scc_members",
    "proofir_v3_derivation_sccs",
    "proofir_v3_derivations",
    "proofir_v3_claims",
    "proofir_v3_observations",
    "proofir_v3_artifact_subjects",
    "proofir_v3_omissions",
    "proofir_v3_coverage",
    "proofir_v3_extensions",
    "proofir_v3_subjects",
    "proofir_v3_environments",
    "proofir_v3_artifacts",
)


def _json(value: Any) -> str:
    return canonical_bytes(value).decode("utf-8")


def _ref_values(ref: Mapping[str, Any], owner_artifact_id: str) -> tuple[str, str, str]:
    """Return the explicit descriptor owner and compact subject components."""

    return (
        str(ref.get("artifactRef", owner_artifact_id)),
        str(ref["kind"]),
        str(ref["localId"]),
    )


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def create_v3_schema(
    connection: sqlite3.Connection,
    *,
    manage_user_version: bool = True,
) -> None:
    """Create native-v3 tables, optionally owning database-wide version metadata."""

    connection.execute("PRAGMA foreign_keys = ON")
    existing = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='proofir_v3_subjects'"
    ).fetchone()
    if existing is not None and (
        "owner_content_artifact_id" not in str(existing[0])
        or "search_shape_json" not in str(existing[0])
    ):
        raise RuntimeError("obsolete ProofIR v3 schema requires a disposable rebuild")
    existing_observations = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' "
        "AND name='proofir_v3_observations'"
    ).fetchone()
    if existing_observations is not None and "dimensions_json" not in str(
        existing_observations[0]
    ):
        raise RuntimeError(
            "obsolete ProofIR v3 observation schema requires a disposable rebuild"
        )
    connection.executescript(_SCHEMA)
    # ``executescript`` commits a caller-open transaction; repeat the pragma because
    # SQLite ignores attempts to change foreign-key enforcement inside a transaction.
    connection.execute("PRAGMA foreign_keys = ON")
    if manage_user_version:
        connection.execute(f"PRAGMA user_version = {V3_SCHEMA_VERSION}")


def _checked_artifacts(artifacts: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    checked: dict[str, dict[str, Any]] = {}
    encodings: dict[str, bytes] = {}
    sources = list(artifacts)
    for checked_artifact in validate_envelope_batch(sources):
        artifact = checked_artifact.to_dict()
        artifact_id = str(artifact["artifactId"])
        encoded = canonical_bytes(artifact)
        prior = encodings.get(artifact_id)
        if prior is not None and prior != encoded:
            raise ValueError(
                f"conflicting canonical artifacts share identity {artifact_id}"
            )
        checked[artifact_id] = artifact
        encodings[artifact_id] = encoded
    return [checked[key] for key in sorted(checked)]


def _insert_environments(
    connection: sqlite3.Connection, artifacts: list[dict[str, Any]]
) -> None:
    manifests: dict[str, tuple[str, str]] = {}
    environment_refs = {str(artifact["environmentRef"]) for artifact in artifacts}
    for artifact in artifacts:
        if artifact["artifactKind"] != "proofir.environment":
            continue
        environment_ref = str(artifact["environmentRef"])
        candidate = (str(artifact["artifactId"]), _json(artifact["payload"]))
        prior = manifests.get(environment_ref)
        if prior is not None and prior != candidate:
            raise ValueError(f"multiple environment manifests claim {environment_ref}")
        manifests[environment_ref] = candidate
    for environment_ref in sorted(environment_refs):
        manifest = manifests.get(environment_ref)
        connection.execute(
            "INSERT INTO proofir_v3_environments(environment_ref,manifest_artifact_id,environment_json,resolution_state) VALUES(?,?,?,?)",
            (
                environment_ref,
                manifest[0] if manifest else None,
                manifest[1] if manifest else None,
                "resolved" if manifest else "unresolved",
            ),
        )


def _insert_artifact(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    artifact_id = str(artifact["artifactId"])
    connection.execute(
        "INSERT INTO proofir_v3_artifacts(content_artifact_id,artifact_kind,proofir_version,environment_ref,canonical_json,source_pointer) VALUES(?,?,?,?,?,?)",
        (
            artifact_id,
            artifact["artifactKind"],
            artifact["proofirVersion"],
            artifact["environmentRef"],
            _json(artifact),
            "/",
        ),
    )


def _insert_subjects(
    connection: sqlite3.Connection, artifacts: list[dict[str, Any]]
) -> None:
    for artifact in artifacts:
        owner = str(artifact["artifactId"])
        for ref in artifact["subjectRefs"]:
            fingerprint = ref.get("fingerprint", {})
            scheme = (
                fingerprint.get("scheme", {}) if isinstance(fingerprint, dict) else {}
            )
            connection.execute(
                "INSERT INTO proofir_v3_subjects(owner_content_artifact_id,subject_kind,local_id,fingerprint_scheme_name,fingerprint_scheme_version,fingerprint_digest,display,search_shape_json,opaque_payload_ref) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    owner,
                    ref["kind"],
                    ref["localId"],
                    scheme.get("name"),
                    scheme.get("version"),
                    fingerprint.get("digest")
                    if isinstance(fingerprint, dict)
                    else None,
                    ref.get("display"),
                    _json(ref["searchShape"]) if "searchShape" in ref else None,
                    ref.get("opaquePayloadRef"),
                ),
            )
    for artifact in artifacts:
        artifact_id = str(artifact["artifactId"])
        for ordinal, ref in enumerate(artifact["subjectRefs"]):
            owner, kind, local_id = _ref_values(ref, artifact_id)
            connection.execute(
                "INSERT INTO proofir_v3_artifact_subjects(content_artifact_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,source_pointer) VALUES(?,?,?,?,?,?)",
                (
                    artifact_id,
                    ordinal,
                    owner,
                    kind,
                    local_id,
                    f"/subjectRefs/{ordinal}",
                ),
            )


def _project_claim(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    payload = artifact["payload"]
    owner, kind, local_id = _ref_values(
        payload["statementRef"], str(artifact["artifactId"])
    )
    connection.execute(
        "INSERT INTO proofir_v3_claims(content_artifact_id,claim_id,statement_owner_artifact_id,statement_kind,statement_local_id,assertion_state,source_pointer) VALUES(?,?,?,?,?,?,?)",
        (
            artifact["artifactId"],
            payload["claimId"],
            owner,
            kind,
            local_id,
            payload["assertionState"],
            "/payload",
        ),
    )


def _project_derivation(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    recursion = payload.get("recursion")
    connection.execute(
        "INSERT INTO proofir_v3_derivations(content_artifact_id,derivation_id,acyclic,recursion_policy,source_pointer) VALUES(?,?,?,?,?)",
        (
            artifact_id,
            payload["derivationId"],
            int(payload["acyclic"]),
            recursion["policy"] if recursion else None,
            "/payload",
        ),
    )
    for component_ordinal, component in enumerate(
        recursion["components"] if recursion else ()
    ):
        component_pointer = f"/payload/recursion/components/{component_ordinal}"
        connection.execute(
            "INSERT INTO proofir_v3_derivation_sccs(content_artifact_id,component_id,ordinal,semantics,source_pointer) VALUES(?,?,?,?,?)",
            (
                artifact_id,
                component["componentId"],
                component_ordinal,
                component["semantics"],
                component_pointer,
            ),
        )
        for member_ordinal, member in enumerate(component["statementRefs"]):
            connection.execute(
                "INSERT INTO proofir_v3_scc_members(content_artifact_id,component_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,source_pointer) VALUES(?,?,?,?,?,?,?)",
                (
                    artifact_id,
                    component["componentId"],
                    member_ordinal,
                    *_ref_values(member, artifact_id),
                    f"{component_pointer}/statementRefs/{member_ordinal}",
                ),
            )
    for ordinal, step in enumerate(payload["steps"]):
        pointer = f"/payload/steps/{ordinal}"
        step_id = str(step["stepRef"]["localId"])
        rule = _ref_values(step["ruleRef"], artifact_id)
        context = _ref_values(step["localContextRef"], artifact_id)
        check = _ref_values(step["checkRunRef"], artifact_id)
        connection.execute(
            "INSERT INTO proofir_v3_derivation_steps(content_artifact_id,step_local_id,ordinal,step_kind,rule_owner_artifact_id,rule_kind,rule_local_id,context_owner_artifact_id,context_kind,context_local_id,check_owner_artifact_id,check_kind,check_local_id,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                step_id,
                ordinal,
                step["kind"],
                *rule,
                *context,
                *check,
                pointer,
            ),
        )
        for premise_ordinal, premise in enumerate(step["premiseRefs"]):
            connection.execute(
                "INSERT INTO proofir_v3_step_premises(content_artifact_id,step_local_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,source_pointer) VALUES(?,?,?,?,?,?,?)",
                (
                    artifact_id,
                    step_id,
                    premise_ordinal,
                    *_ref_values(premise, artifact_id),
                    f"{pointer}/premiseRefs/{premise_ordinal}",
                ),
            )
        connection.execute(
            "INSERT INTO proofir_v3_step_conclusions(content_artifact_id,step_local_id,owner_content_artifact_id,subject_kind,subject_local_id,source_pointer) VALUES(?,?,?,?,?,?)",
            (
                artifact_id,
                step_id,
                *_ref_values(step["conclusionRef"], artifact_id),
                f"{pointer}/conclusionRef",
            ),
        )
        for substitution_ordinal, substitution in enumerate(step["substitutions"]):
            connection.execute(
                "INSERT INTO proofir_v3_substitutions(content_artifact_id,step_local_id,ordinal,variable,owner_content_artifact_id,term_kind,term_local_id,source_pointer) VALUES(?,?,?,?,?,?,?,?)",
                (
                    artifact_id,
                    step_id,
                    substitution_ordinal,
                    substitution["variable"],
                    *_ref_values(substitution["termRef"], artifact_id),
                    f"{pointer}/substitutions/{substitution_ordinal}",
                ),
            )


def _project_plan(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    plan_id = str(payload["planId"])
    connection.execute(
        "INSERT INTO proofir_v3_plans(content_artifact_id,plan_id,policy_json,source_pointer) VALUES(?,?,?,?)",
        (artifact_id, plan_id, _json(payload["policy"]), "/payload"),
    )
    for ordinal, step in enumerate(payload["steps"]):
        connection.execute(
            "INSERT INTO proofir_v3_plan_steps(content_artifact_id,plan_id,step_local_id,ordinal,step_kind,rule_owner_artifact_id,rule_kind,rule_local_id,conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id,context_owner_artifact_id,context_kind,context_local_id,premises_json,substitutions_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                plan_id,
                step["stepRef"]["localId"],
                ordinal,
                step["kind"],
                *_ref_values(step["ruleRef"], artifact_id),
                *_ref_values(step["conclusionRef"], artifact_id),
                *_ref_values(step["localContextRef"], artifact_id),
                _json(step["premiseRefs"]),
                _json(step["substitutions"]),
                f"/payload/steps/{ordinal}",
            ),
        )


def _project_attempts(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    attempt_log_id = str(payload["attemptLogId"])
    connection.execute(
        "INSERT INTO proofir_v3_attempt_logs(content_artifact_id,attempt_log_id,goal_owner_artifact_id,goal_kind,goal_local_id,summary_outcome,source_pointer) VALUES(?,?,?,?,?,?,?)",
        (
            artifact_id,
            attempt_log_id,
            *_ref_values(payload["goalRef"], artifact_id),
            payload["summary"].get("outcome", "unknown"),
            "/payload",
        ),
    )
    for ordinal, attempt in enumerate(payload["attempts"]):
        connection.execute(
            "INSERT INTO proofir_v3_attempts(content_artifact_id,attempt_log_id,attempt_id,ordinal,step_owner_artifact_id,step_kind,step_local_id,rule_owner_artifact_id,rule_kind,rule_local_id,conclusion_owner_artifact_id,conclusion_kind,conclusion_local_id,check_owner_artifact_id,check_kind,check_local_id,outcome,premise_refs_json,substitutions_json,diagnostics_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                attempt_log_id,
                attempt["attemptId"],
                ordinal,
                *_ref_values(attempt["stepRef"], artifact_id),
                *_ref_values(attempt["ruleRef"], artifact_id),
                *_ref_values(attempt["conclusionRef"], artifact_id),
                *_ref_values(attempt["checkRunRef"], artifact_id),
                attempt["outcome"],
                _json(attempt["premiseRefs"]),
                _json(attempt["substitutions"]),
                _json(attempt["diagnostics"]),
                f"/payload/attempts/{ordinal}",
            ),
        )
    for ordinal, residual in enumerate(
        payload["summary"].get("residualPremiseRefs", [])
    ):
        connection.execute(
            "INSERT INTO proofir_v3_attempt_residuals(content_artifact_id,attempt_log_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,source_pointer) VALUES(?,?,?,?,?,?,?)",
            (
                artifact_id,
                attempt_log_id,
                ordinal,
                *_ref_values(residual, artifact_id),
                f"/payload/summary/residualPremiseRefs/{ordinal}",
            ),
        )


def _project_check_run(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    check_run_id = str(payload["checkRunId"])
    guarantee = payload["guarantee"]
    connection.execute(
        "INSERT INTO proofir_v3_check_runs(content_artifact_id,check_run_id,checker_json,operation,inputs_json,outputs_json,bounds_json,guarantee_scope,authority_basis,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (
            artifact_id,
            check_run_id,
            _json(payload["checker"]),
            payload["operation"],
            _json(payload["inputs"]),
            _json(payload["outputs"]),
            _json(payload["bounds"]),
            guarantee["scope"],
            guarantee["authorityBasis"],
            "/payload",
        ),
    )
    for ordinal, result in enumerate(payload["results"]):
        connection.execute(
            "INSERT INTO proofir_v3_check_results(content_artifact_id,check_run_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,result,diagnostics_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                check_run_id,
                ordinal,
                *_ref_values(result["subjectRef"], artifact_id),
                result["result"],
                _json(result["diagnostics"]),
                f"/payload/results/{ordinal}",
            ),
        )


def _project_source_map(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    source_map_id = str(payload["sourceMapId"])
    connection.execute(
        "INSERT INTO proofir_v3_source_maps(content_artifact_id,source_map_id,policy_json,source_pointer) VALUES(?,?,?,?)",
        (artifact_id, source_map_id, _json(payload["policy"]), "/payload"),
    )
    for ordinal, anchor in enumerate(payload["anchors"]):
        connection.execute(
            "INSERT INTO proofir_v3_surfaces(content_artifact_id,source_map_id,ordinal,owner_content_artifact_id,subject_kind,subject_local_id,source_path,module,declaration_name,start_json,end_json,content_digest,match_method,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                source_map_id,
                ordinal,
                *_ref_values(anchor["subjectRef"], artifact_id),
                anchor["sourcePath"],
                anchor["module"],
                anchor["declName"],
                _json(anchor["start"]),
                _json(anchor["end"]),
                anchor["contentDigest"],
                anchor["matchMethod"],
                f"/payload/anchors/{ordinal}",
            ),
        )


def _project_attachment_set(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    artifact_id = str(artifact["artifactId"])
    payload = artifact["payload"]
    attachment_set_id = str(payload["attachmentSetId"])
    connection.execute(
        "INSERT INTO proofir_v3_attachment_sets(content_artifact_id,attachment_set_id,resolver_json,source_pointer) VALUES(?,?,?,?)",
        (artifact_id, attachment_set_id, _json(payload["resolver"]), "/payload"),
    )
    for ordinal, attachment in enumerate(payload["attachments"]):
        pointer = f"/payload/attachments/{ordinal}"
        selected_ref = attachment["selectedSourceRef"]
        source_values = (
            _ref_values(selected_ref, artifact_id)
            if selected_ref is not None
            else (None, None, None)
        )
        connection.execute(
            "INSERT INTO proofir_v3_attachments(content_artifact_id,attachment_set_id,ordinal,subject_owner_artifact_id,subject_kind,subject_local_id,selection_decision,selected_candidate_id,source_owner_artifact_id,source_kind,source_local_id,freshness,decisive_evidence_json,rejection_reasons_json,semantic_acceptance,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                artifact_id,
                attachment_set_id,
                ordinal,
                *_ref_values(attachment["subjectRef"], artifact_id),
                attachment["selectionDecision"],
                attachment["selectedCandidateId"],
                *source_values,
                attachment["freshness"],
                _json(attachment["decisiveEvidence"]),
                _json(attachment["rejectionReasons"]),
                int(attachment["semanticAcceptance"]),
                pointer,
            ),
        )
        for candidate_ordinal, candidate in enumerate(attachment["candidates"]):
            connection.execute(
                "INSERT INTO proofir_v3_attachment_candidates(content_artifact_id,attachment_set_id,attachment_ordinal,ordinal,source_owner_artifact_id,source_kind,source_local_id,declaration_id,method,confidence,freshness,rank,policy_version,decisive_evidence_json,rejection_reasons_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    artifact_id,
                    attachment_set_id,
                    ordinal,
                    candidate_ordinal,
                    *_ref_values(candidate["sourceRef"], artifact_id),
                    candidate["declarationId"],
                    candidate["method"],
                    candidate["confidence"],
                    candidate["freshness"],
                    candidate["rank"],
                    candidate["policyVersion"],
                    _json(candidate["decisiveEvidence"]),
                    _json(candidate["rejectionReasons"]),
                    f"{pointer}/candidates/{candidate_ordinal}",
                ),
            )


def _project_observation(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    payload = artifact["payload"]
    connection.execute(
        "INSERT INTO proofir_v3_observations(content_artifact_id,observation_id,owner_content_artifact_id,subject_kind,subject_local_id,observation_kind,result,guarantee_scope,authority_basis,dimensions_json,details_json,diagnostics_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            artifact["artifactId"],
            payload["observationId"],
            *_ref_values(payload["subjectRef"], str(artifact["artifactId"])),
            payload["observationKind"],
            payload["result"],
            payload["guaranteeScope"],
            payload["authorityBasis"],
            _json(payload["dimensions"]),
            _json(payload["details"]),
            _json(payload["diagnostics"]),
            "/payload",
        ),
    )


_FAMILY_PROJECTORS = {
    "proofir.claim": _project_claim,
    "proofir.derivation": _project_derivation,
    "proofir.plan": _project_plan,
    "proofir.attempt-log": _project_attempts,
    "proofir.check-run": _project_check_run,
    "proofir.source-map": _project_source_map,
    "proofir.attachment-set": _project_attachment_set,
    "proofir.governance-observation": _project_observation,
}


def _project_common(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    artifact_id = str(artifact["artifactId"])
    coverage = artifact["coverage"]
    population = coverage["population"]
    connection.execute(
        "INSERT INTO proofir_v3_coverage(content_artifact_id,status,population_kind,selector_json,universe_known,expected,discovered,decoded,valid,projected,query_matched,bounds_json,source_pointer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            artifact_id,
            coverage["status"],
            population["kind"],
            _json(population["selector"]),
            int(coverage["universeKnown"]),
            coverage["expected"],
            coverage["discovered"],
            coverage["decoded"],
            coverage["valid"],
            coverage["projected"],
            coverage["queryMatched"],
            _json(coverage["bounds"]),
            "/coverage",
        ),
    )
    for ordinal, omission in enumerate(coverage["omitted"]):
        row = omission if isinstance(omission, dict) else {"value": omission}
        pointer = str(row.get("pointer", f"/coverage/omitted/{ordinal}"))
        stage = str(row.get("stage", "semantic-valid"))
        reason = str(row.get("reasonCode", row.get("reason", "unspecified")))
        connection.execute(
            "INSERT INTO proofir_v3_omissions(content_artifact_id,ordinal,source_pointer,stage,reason_code,details_json) VALUES(?,?,?,?,?,?)",
            (artifact_id, ordinal, pointer, stage, reason, _json(row)),
        )
    next_omission = len(coverage["omitted"])
    for namespace in sorted(artifact["extensions"]):
        payload = artifact["extensions"][namespace]
        encoded = canonical_bytes(payload)
        digest = "sha256:" + hashlib.sha256(encoded).hexdigest()
        oversized = len(encoded) > MAX_EXTENSION_BYTES
        stored = (
            {
                "truncated": True,
                "originalBytes": len(encoded),
                "sha256": digest,
            }
            if oversized
            else payload
        )
        connection.execute(
            "INSERT INTO proofir_v3_extensions(content_artifact_id,namespace,payload_json,payload_digest,storage_state,original_bytes,source_pointer) VALUES(?,?,?,?,?,?,?)",
            (
                artifact_id,
                namespace,
                _json(stored),
                digest,
                "digest-sentinel" if oversized else "full",
                len(encoded),
                f"/extensions/{_escape_pointer(namespace)}",
            ),
        )
        if oversized:
            connection.execute(
                "INSERT INTO proofir_v3_omissions(content_artifact_id,ordinal,source_pointer,stage,reason_code,details_json) VALUES(?,?,?,?,?,?)",
                (
                    artifact_id,
                    next_omission,
                    f"/extensions/{_escape_pointer(namespace)}",
                    "projected",
                    "extension-payload-byte-limit",
                    _json(stored),
                ),
            )
            next_omission += 1


def _project_validated(
    connection: sqlite3.Connection, artifacts: list[dict[str, Any]]
) -> None:
    _insert_environments(connection, artifacts)
    for artifact in artifacts:
        _insert_artifact(connection, artifact)
    _insert_subjects(connection, artifacts)
    for artifact in artifacts:
        projector = _FAMILY_PROJECTORS.get(str(artifact["artifactKind"]))
        if projector is not None:
            projector(connection, artifact)
        _project_common(connection, artifact)


def _clear_projection(connection: sqlite3.Connection) -> None:
    for table in _DELETE_ORDER:
        connection.execute(f"DELETE FROM {table}")


def project_envelopes(
    connection: sqlite3.Connection,
    artifacts: list[dict[str, Any]],
    *,
    exact_inventory: bool = True,
    manage_user_version: bool = True,
) -> dict[str, Any]:
    """Replace the complete projection atomically after validating every input.

    ``exact_inventory`` remains the standalone default.  Embedded callers can
    validate the native-v3 tables and access paths while sharing a connection
    that also owns another schema.
    """

    started = time.monotonic()
    checked = _checked_artifacts(artifacts)
    create_v3_schema(connection, manage_user_version=manage_user_version)
    with connection:
        connection.execute("PRAGMA defer_foreign_keys = ON")
        _clear_projection(connection)
        _project_validated(connection, checked)
        validate_v3_database(connection, exact_inventory=exact_inventory)
    counts: dict[str, Any] = projection_counts(connection)
    counts["elapsedSeconds"] = round(time.monotonic() - started, 6)
    return counts


def project_envelope(connection: sqlite3.Connection, artifact: dict[str, Any]) -> None:
    """Project one artifact into an otherwise caller-owned projection."""

    checked = validate_envelope(artifact).to_dict()
    create_v3_schema(connection)
    artifact_id = str(checked["artifactId"])
    existing = connection.execute(
        "SELECT canonical_json FROM proofir_v3_artifacts WHERE content_artifact_id=?",
        (artifact_id,),
    ).fetchone()
    if existing is not None:
        if str(existing[0]) != _json(checked):
            raise ValueError(f"conflicting projection for {artifact_id}")
        return
    _validate_incremental_external_references(connection, checked)
    with connection:
        connection.execute("PRAGMA defer_foreign_keys = ON")
        environment_ref = str(checked["environmentRef"])
        environment = connection.execute(
            "SELECT manifest_artifact_id,resolution_state "
            "FROM proofir_v3_environments WHERE environment_ref=?",
            (environment_ref,),
        ).fetchone()
        if environment is None:
            _insert_environments(connection, [checked])
        elif checked["artifactKind"] == "proofir.environment":
            if environment[1] == "resolved":
                raise ValueError(
                    f"environment {environment_ref} already has manifest "
                    f"{environment[0]}"
                )
            connection.execute(
                "UPDATE proofir_v3_environments SET manifest_artifact_id=?,environment_json=?,resolution_state='resolved' WHERE environment_ref=?",
                (artifact_id, _json(checked["payload"]), environment_ref),
            )
        _insert_artifact(connection, checked)
        _insert_subjects(connection, [checked])
        projector = _FAMILY_PROJECTORS.get(str(checked["artifactKind"]))
        if projector is not None:
            projector(connection, checked)
        _project_common(connection, checked)
        validate_v3_database(connection)


def _validate_incremental_external_references(
    connection: sqlite3.Connection, artifact: dict[str, Any]
) -> None:
    """Close external evidence against validated persisted artifacts.

    This is deliberately a read-before-write check. The single-artifact API is
    allowed to follow a check-run or support artifact already present in the
    project database, while premise/conclusion topology remains local to its
    owning derivation artifact.
    """

    rows = connection.execute(
        "SELECT content_artifact_id,canonical_json FROM proofir_v3_artifacts"
    )
    persisted = {
        str(row[0]): json.loads(str(row[1]))
        for row in rows
    }
    _validate_external_references(str(artifact["artifactId"]), artifact, persisted)


def projection_counts(connection: sqlite3.Connection) -> dict[str, int]:
    """Return deterministic logical row counts for every native family."""

    counts: dict[str, int] = {}
    for table in sorted(REQUIRED_TABLES):
        key = table.removeprefix("proofir_v3_")
        counts[key] = int(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        )
    return counts


def reconcile_projection(
    connection: sqlite3.Connection, artifacts: list[dict[str, Any]]
) -> dict[str, Any]:
    expected = {
        str(artifact["artifactId"]) for artifact in _checked_artifacts(artifacts)
    }
    observed = {
        str(row[0])
        for row in connection.execute(
            "SELECT content_artifact_id FROM proofir_v3_artifacts"
        )
    }
    return {
        "expected": len(expected),
        "observed": len(observed),
        "missing": sorted(expected - observed),
        "unexpected": sorted(observed - expected),
        "complete": expected == observed,
    }


def projection_metrics(connection: sqlite3.Connection) -> dict[str, Any]:
    page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
    started = time.monotonic()
    connection.execute("SELECT COUNT(*) FROM proofir_v3_artifacts").fetchone()
    try:
        object_bytes = {
            str(row[0]): int(row[1])
            for row in connection.execute(
                "SELECT name,sum(pgsize) FROM dbstat GROUP BY name ORDER BY name"
            )
        }
        dbstat_available = True
    except sqlite3.OperationalError:
        object_bytes = {}
        dbstat_available = False
    return {
        "databaseBytes": page_size * page_count,
        "objectBytes": object_bytes,
        "pageSize": page_size,
        "pageCount": page_count,
        "dbstatAvailable": dbstat_available,
        "warmQuerySeconds": round(time.monotonic() - started, 6),
        **projection_counts(connection),
    }


def query_plan_evidence(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    """Return deterministic optimizer evidence for every registered SQL family."""

    evidence: dict[str, dict[str, Any]] = {}
    for name in sorted(V3_QUERY_SHAPES):
        plan = connection.execute(
            "EXPLAIN QUERY PLAN " + V3_QUERY_SHAPES[name],
            _V3_QUERY_PARAMETERS[name],
        ).fetchall()
        rendered = [str(row[3]) for row in plan]
        expected = V3_QUERY_ACCESS_PATHS[name]
        table_rows = int(
            connection.execute(
                f"SELECT count(*) FROM {_V3_QUERY_TABLES[name]}"
            ).fetchone()[0]
        )
        selected = any(expected in row for row in rendered)
        evidence[name] = {
            "expectedAccessPath": expected,
            "selected": selected,
            "tableRows": table_rows,
            "selectionRequired": table_rows >= _PLAN_SELECTION_MIN_ROWS,
            "temporaryOrder": any("TEMP B-TREE" in row for row in rendered),
            "plan": rendered,
        }
    return evidence


def redundant_named_indexes(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    """Report named indexes that exactly duplicate another table access path."""

    findings: list[dict[str, Any]] = []
    for table in sorted(REQUIRED_TABLES):
        by_columns: dict[tuple[str, ...], list[str]] = {}
        for index in connection.execute(f"PRAGMA index_list({table})"):
            name = str(index[1])
            columns = tuple(
                str(row[2])
                for row in connection.execute(f"PRAGMA index_info({name})")
            )
            by_columns.setdefault(columns, []).append(name)
        for columns, names in by_columns.items():
            explicit = sorted(name for name in names if not name.startswith("sqlite_"))
            if explicit and len(names) > 1:
                findings.append(
                    {"table": table, "columns": list(columns), "indexes": sorted(names)}
                )
    return findings


def validate_v3_query_plans(connection: sqlite3.Connection) -> None:
    """Require registered access paths and index-compatible deterministic ordering."""

    failures = {
        name: row
        for name, row in query_plan_evidence(connection).items()
        if (row["selectionRequired"] and not row["selected"])
        or row["temporaryOrder"]
    }
    if failures:
        raise ValueError(
            "ProofIR v3 SQLite query-plan gates failed: "
            + ", ".join(sorted(failures))
        )


def _validate_schema_inventory(
    connection: sqlite3.Connection, *, exact_inventory: bool
) -> None:
    tables = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    indexes = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        )
    }
    if exact_inventory and tables != REQUIRED_TABLES:
        raise ValueError("ProofIR v3 SQLite schema does not match the native inventory")
    if not exact_inventory and not REQUIRED_TABLES <= tables:
        raise ValueError("ProofIR v3 SQLite schema is missing native tables")
    if not REQUIRED_INDEXES <= indexes:
        raise ValueError("ProofIR v3 SQLite access paths are incomplete")


def _validate_index_inventory(connection: sqlite3.Connection) -> None:
    if redundant_named_indexes(connection):
        raise ValueError("ProofIR v3 SQLite schema has redundant named indexes")


def _validate_storage_integrity(connection: sqlite3.Connection) -> None:
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("ProofIR v3 SQLite integrity check failed")
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        raise ValueError(
            f"ProofIR v3 SQLite foreign-key check failed: {len(violations)}"
        )


def validate_v3_database(
    connection: sqlite3.Connection, *, exact_inventory: bool = True
) -> None:
    """Validate native-v3 tables, optionally within an enclosing schema."""
    _validate_schema_inventory(connection, exact_inventory=exact_inventory)
    _validate_index_inventory(connection)
    _validate_storage_integrity(connection)


def publish_v3_database(
    destination: Path,
    artifacts: list[dict[str, Any]],
    *,
    max_database_bytes: int = DEFAULT_MAX_DATABASE_BYTES,
) -> dict[str, Any]:
    """Build a fresh database beside ``destination`` and atomically publish it."""

    if max_database_bytes < 1:
        raise ValueError("max_database_bytes must be positive")
    started = time.monotonic()
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = _acquire_v3_lock(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.{os.getpid()}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    sidecars = [
        Path(str(temporary) + suffix) for suffix in ("-journal", "-wal", "-shm")
    ]
    try:
        from ladon.proof_search_history_store import refuse_history_replacement

        refuse_history_replacement(destination.absolute())
        with sqlite3.connect(temporary) as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = DELETE")
            connection.execute("PRAGMA synchronous = FULL")
            page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
            max_pages = max(1, max_database_bytes // page_size)
            connection.execute(f"PRAGMA max_page_count = {max_pages}")
            try:
                create_v3_schema(connection)
            except sqlite3.OperationalError as error:
                if "full" in str(error).lower() or "max_page_count" in str(error).lower():
                    raise ValueError(
                        "ProofIR v3 database exceeds configured complete-database byte limit"
                    ) from error
                raise
            empty_metrics = projection_metrics(connection)
            project_envelopes(connection, artifacts)
            connection.execute("ANALYZE")
            validate_v3_database(connection)
            validate_v3_query_plans(connection)
            metrics = projection_metrics(connection)
            metrics["schemaBytes"] = empty_metrics["databaseBytes"]
            metrics["marginalProjectionBytes"] = max(
                0, metrics["databaseBytes"] - empty_metrics["databaseBytes"]
            )
            metrics["marginalObjectBytes"] = {
                name: max(
                    0,
                    allocated - empty_metrics["objectBytes"].get(name, 0),
                )
                for name, allocated in metrics["objectBytes"].items()
            }
            if metrics["databaseBytes"] > max_database_bytes:
                raise ValueError(
                    "ProofIR v3 database exceeds configured complete-database byte limit"
                )
            metrics.update(
                {
                    "accessPathGates": "passed",
                    "constructionPid": os.getpid(),
                    "integrity": "ok",
                    "foreignKeyViolations": 0,
                    "databaseByteLimit": max_database_bytes,
                    "reconciliation": reconcile_projection(connection, artifacts),
                    "queryPlans": query_plan_evidence(connection),
                    "statisticsRefreshed": True,
                }
            )
        _durable_v3_replace(temporary, destination)
        metrics["databaseBytes"] = destination.stat().st_size
        metrics["buildSeconds"] = round(time.monotonic() - started, 6)
        return metrics
    finally:
        temporary.unlink(missing_ok=True)
        for sidecar in sidecars:
            sidecar.unlink(missing_ok=True)
        _release_v3_lock(lock)


def normalized_rows(artifact: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return the language-neutral baseline rows retained by older parity gates."""

    artifact_id = str(artifact["artifactId"])
    environment_ref = str(artifact["environmentRef"])
    subjects = []
    for subject in artifact.get("subjectRefs", []):
        if (
            not isinstance(subject, dict)
            or not subject.get("kind")
            or not subject.get("localId")
        ):
            continue
        row = {
            "environmentRef": environment_ref,
            "kind": subject["kind"],
            "localId": subject["localId"],
            "fingerprint": subject.get("fingerprint"),
            "display": subject.get("display"),
        }
        if "searchShape" in subject:
            row["searchShape"] = subject["searchShape"]
        if "opaquePayloadRef" in subject:
            row["opaquePayloadRef"] = subject["opaquePayloadRef"]
        subjects.append(row)
    coverage = artifact.get("coverage", {})
    population = coverage.get("population", {}) if isinstance(coverage, dict) else {}
    return {
        "artifacts": [
            {
                "contentArtifactId": artifact_id,
                "artifactKind": artifact["artifactKind"],
                "proofirVersion": artifact["proofirVersion"],
                "environmentRef": environment_ref,
            }
        ],
        "subjects": subjects,
        "coverage": [
            {
                "contentArtifactId": artifact_id,
                "populationKind": population.get("kind", "unknown"),
                "selector": population.get("selector", {}),
                "queryMatched": int(coverage.get("queryMatched", 0))
                if isinstance(coverage, dict)
                else 0,
            }
        ],
        "extensions": [
            {
                "contentArtifactId": artifact_id,
                "namespace": str(namespace),
                "payload": payload,
            }
            for namespace, payload in artifact.get("extensions", {}).items()
        ],
    }


__all__ = [
    "DEFAULT_MAX_DATABASE_BYTES",
    "MAX_EXTENSION_BYTES",
    "REQUIRED_INDEXES",
    "REQUIRED_TABLES",
    "V3_QUERY_ACCESS_PATHS",
    "V3_QUERY_SHAPES",
    "V3_SCHEMA_VERSION",
    "create_v3_schema",
    "normalized_rows",
    "project_envelope",
    "project_envelopes",
    "projection_counts",
    "projection_metrics",
    "publish_v3_database",
    "query_plan_evidence",
    "reconcile_projection",
    "redundant_named_indexes",
    "validate_v3_database",
    "validate_v3_query_plans",
]
