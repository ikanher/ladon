from __future__ import annotations

import copy
import sqlite3

import pytest
from support.proofir_v3_native import native_artifacts

from ladon.proofir_sqlite_v3 import create_v3_schema, project_envelope, project_envelopes
from ladon.proofir_v3 import detached_content_id


def _check_and_derivation() -> tuple[dict, dict]:
    artifacts = native_artifacts()
    check = copy.deepcopy(artifacts["proofir.check-run"])
    derivation = copy.deepcopy(artifacts["proofir.derivation"])
    check["subjectRefs"].append({"kind": "check-run", "localId": "check:1"})
    check["artifactId"] = detached_content_id(check)
    derivation["payload"]["steps"][0]["checkRunRef"] = {
        "artifactRef": check["artifactId"],
        "kind": "check-run",
        "localId": "check:1",
    }
    derivation["artifactId"] = detached_content_id(derivation)
    return check, derivation


def test_incremental_external_check_reference_matches_batch_projection() -> None:
    check, derivation = _check_and_derivation()
    batch_connection = sqlite3.connect(":memory:")
    batch_counts = project_envelopes(batch_connection, [check, derivation])

    incremental_connection = sqlite3.connect(":memory:")
    create_v3_schema(incremental_connection)
    project_envelope(incremental_connection, check)
    project_envelope(incremental_connection, derivation)
    incremental_counts = {
        key: int(incremental_connection.execute(f"SELECT COUNT(*) FROM proofir_v3_{key}").fetchone()[0])
        for key in batch_counts
        if key != "elapsedSeconds"
    }
    assert incremental_counts == {key: value for key, value in batch_counts.items() if key != "elapsedSeconds"}


def test_incremental_dangling_external_reference_fails_before_rows_are_added() -> None:
    _check, derivation = _check_and_derivation()
    connection = sqlite3.connect(":memory:")
    create_v3_schema(connection)
    with pytest.raises(Exception, match="external reference"):
        project_envelope(connection, derivation)
    assert connection.execute("SELECT COUNT(*) FROM proofir_v3_artifacts").fetchone() == (0,)


def test_bare_check_input_artifact_reference_is_closed_in_batch() -> None:
    check, _derivation = _check_and_derivation()
    target = copy.deepcopy(native_artifacts()["proofir.claim"])
    target["environmentRef"] = check["environmentRef"]
    target["artifactId"] = detached_content_id(target)
    check["payload"]["inputs"]["artifactRefs"] = [target["artifactId"]]
    check["artifactId"] = detached_content_id(check)
    project_envelopes(sqlite3.connect(":memory:"), [check, target])


def test_bare_check_input_artifact_reference_rejects_missing_target() -> None:
    check, _target = _check_and_derivation()
    check["payload"]["inputs"]["artifactRefs"] = ["sha256:" + "9" * 64]
    check["artifactId"] = detached_content_id(check)
    with pytest.raises(Exception, match="artifact reference"):
        project_envelopes(sqlite3.connect(":memory:"), [check])


def test_external_reference_enforces_field_expected_kind() -> None:
    check, derivation = _check_and_derivation()
    derivation["payload"]["steps"][0]["checkRunRef"] = {
        "artifactRef": check["artifactId"],
        "kind": "statement",
        "localId": "statement:goal",
    }
    derivation["artifactId"] = detached_content_id(derivation)
    with pytest.raises(Exception, match="unexpected reference kind"):
        project_envelopes(sqlite3.connect(":memory:"), [check, derivation])
