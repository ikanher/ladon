from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelopes
from ladon.proofir_v3 import (
    ProofIRV3Error,
    canonical_bytes,
    validate_envelope_batch,
)

ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests/fixtures/proofir_v3_parity/conformance-corpus-v1.json"
RELEASE_EVIDENCE = ROOT / "docs/proofir-v3-release-evidence.json"
RELEASE_SCHEMA = ROOT / "docs/proofir-v3-release-evidence.schema.json"
UMBRELLA = ROOT / "openspec/changes/ladon-proofir-evidence-semantics-v3-umbrella"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_valid_corpus_case(row: dict[str, Any]) -> None:
    checked = validate_envelope_batch(row["artifacts"])
    assert [artifact.content_id for artifact in checked] == row["artifactIds"]
    assert [
        canonical_bytes(artifact.to_dict()).decode("utf-8") for artifact in checked
    ] == row["canonicalJson"]


def _assert_invalid_corpus_case(row: dict[str, Any]) -> None:
    with pytest.raises(ProofIRV3Error) as captured:
        validate_envelope_batch(row["artifacts"])
    diagnostic = captured.value.diagnostic.to_dict()
    actual = {
        key: diagnostic[key] for key in ("stage", "code", "pointer", "message")
    }
    assert actual == row["diagnostic"]


def test_shared_conformance_corpus_is_self_contained_and_executable() -> None:
    corpus = _load(CORPUS)
    assert corpus["format"] == "proofir-v3-conformance-corpus-v1"
    assert corpus["canonicalProfile"] == "proofir-json-integer-v1"
    case_ids = [row["id"] for family in ("valid", "invalid") for row in corpus[family]]
    assert len(case_ids) == len(set(case_ids))
    assert corpus["valid"] and corpus["invalid"]

    for row in corpus["valid"]:
        _assert_valid_corpus_case(row)
    for row in corpus["invalid"]:
        _assert_invalid_corpus_case(row)


def test_release_evidence_has_a_versioned_machine_validated_format() -> None:
    schema = _load(RELEASE_SCHEMA)
    evidence = _load(RELEASE_EVIDENCE)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(evidence)

    ledger = _load(UMBRELLA / "children/dependency-ledger.json")
    expected = {
        row["change"]: row["exitClass"] for row in ledger["children"]
    }
    observed = {
        row["change"]: row["exitClass"] for row in evidence["childExitClasses"]
    }
    assert observed == expected


def test_dependency_ledger_names_existing_changes_with_identical_specs() -> None:
    ledger = _load(UMBRELLA / "children/dependency-ledger.json")
    rows = ledger["children"]
    change_ids = [row["change"] for row in rows]
    assert len(change_ids) == len(set(change_ids))

    for row in rows:
        change_id = row["change"]
        change = ROOT / "openspec/changes" / change_id
        if not change.is_dir():
            archived = sorted((ROOT / "openspec/changes/archive").glob(f"*-{change_id}"))
            if archived:
                change = archived[-1]
        umbrella_spec = UMBRELLA / "specs" / change_id / "spec.md"
        child_spec = change / "specs" / change_id / "spec.md"
        assert change.is_dir(), f"dependency-ledger child is absent: {change_id}"
        assert (change / "proposal.md").is_file(), change_id
        assert (change / "design.md").is_file(), change_id
        assert (change / "tasks.md").is_file(), change_id
        assert child_spec.read_bytes() == umbrella_spec.read_bytes(), change_id


def test_legacy_artifacts_fail_before_projection_and_leave_zero_rows() -> None:
    corpus = _load(CORPUS)
    legacy = next(row for row in corpus["invalid"] if row["id"] == "legacy-kind")
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    with pytest.raises(ProofIRV3Error) as captured:
        project_envelopes(connection, legacy["artifacts"])
    assert captured.value.diagnostic.code == "legacy-artifact-kind"
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_artifacts"
    ).fetchone() == (0,)
    assert connection.execute(
        "SELECT COUNT(*) FROM proofir_v3_subjects"
    ).fetchone() == (0,)
