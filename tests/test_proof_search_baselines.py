from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ladon.proof_search_baselines import (
    BASELINE_SCHEMA,
    SqlTraceCounter,
    assert_public_contract,
    baseline_metadata,
    database_bytes,
    load_contract_fixture,
    measure_command,
    measure_command_phases,
    measure_named_commands,
    normalize_sql_statement,
    repository_fingerprint,
    write_baseline,
)
from ladon.proof_search_index import build_proof_search_index, query_proof_search_index


FIXTURE = Path(__file__).parent / "fixtures/proof_search_baselines/public-contracts-v1.json"


def test_public_contract_fixture_has_stable_semantic_predicates() -> None:
    payload = load_contract_fixture(FIXTURE)
    assert payload["schema"] == "ladon-proof-search-contract-fixtures-v1"
    assert payload["contracts"]["name"]["results"][0]["matchMode"] == "exact-name"


def test_public_contract_fixture_is_deterministic_when_loaded_twice() -> None:
    assert load_contract_fixture(FIXTURE) == load_contract_fixture(FIXTURE)


def test_mixed_case_exact_name_lookup_is_now_a_passing_contract(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text(
        "theorem fixedIndexPathExpression : True := True.intro\n",
        encoding="utf-8",
    )
    build_proof_search_index(tmp_path)
    result = query_proof_search_index(tmp_path, text="fixedIndexPathExpression")
    assert result["rows"]


def test_sql_trace_counter_normalizes_literals_and_counts_classes() -> None:
    assert normalize_sql_statement(" select * from t where id = 12 ") == (
        "SELECT * FROM T WHERE ID = ?"
    )
    connection = sqlite3.connect(":memory:")
    connection.execute("create table values_table (id integer)")
    counter = SqlTraceCounter().attach(connection)
    connection.execute("insert into values_table values (?)", (1,))
    connection.execute("select * from values_table where id = ?", (1,)).fetchall()
    counter.detach()
    assert counter.count == 3
    assert counter.classes() == {"BEGIN": 1, "INSERT": 1, "SELECT": 1}


def test_baseline_metadata_is_identity_bearing_and_deterministic(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("theorem t : True := True.intro\n", encoding="utf-8")
    first = baseline_metadata(tmp_path, command=["probe"])
    second = baseline_metadata(tmp_path, command=["probe"])
    assert first["schema"] == BASELINE_SCHEMA
    assert first["repositoryFingerprint"] == second["repositoryFingerprint"]
    assert first["environment"]["python"]


def test_baseline_writer_refuses_accidental_overwrite(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    write_baseline(path, {"schema": BASELINE_SCHEMA})
    with pytest.raises(FileExistsError):
        write_baseline(path, {"schema": BASELINE_SCHEMA})
    write_baseline(path, {"schema": BASELINE_SCHEMA, "updated": True}, overwrite=True)
    assert json.loads(path.read_text(encoding="utf-8"))["updated"] is True


def test_measure_command_uses_argv_without_shell(tmp_path: Path) -> None:
    measurement = measure_command([sys.executable, "-c", "print('ok')"])
    assert measurement.return_code == 0
    assert measurement.stdout_bytes > 0
    assert measurement.argv[0] == sys.executable


def test_measure_command_phases_separates_cold_and_warm() -> None:
    phases = measure_command_phases(
        [sys.executable, "-c", "print('ok')"], warm_runs=2
    )
    assert phases["cold"]["returnCode"] == 0
    assert len(phases["warm"]) == 2


def test_named_measurements_and_database_bytes_are_deterministic(tmp_path: Path) -> None:
    database = tmp_path / "proof-search.sqlite"
    database.write_bytes(b"sqlite")
    named = measure_named_commands(
        {"name-query": [sys.executable, "-c", "print('ok')"]}, warm_runs=0
    )
    assert named["name-query"]["phases"]["cold"]["returnCode"] == 0
    assert database_bytes([database]) == {str(database): 6}


def test_baseline_script_generates_non_destructive_json(tmp_path: Path) -> None:
    output = tmp_path / "baseline.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/proof_search_baseline.py",
            "--repo-root",
            str(tmp_path),
            "--output",
            str(output),
            "--probe",
            sys.executable,
            "-c",
            "print('probe')",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == BASELINE_SCHEMA
    assert payload["phaseMeasurements"][0]["phases"]["cold"]["returnCode"] == 0


def test_contract_predicate_rejects_missing_public_fields() -> None:
    with pytest.raises(AssertionError, match="missing fields"):
        assert_public_contract({"schema": "x"})


def test_repository_fingerprint_ignores_generated_state(tmp_path: Path) -> None:
    (tmp_path / "Main.lean").write_text("def x := 1\n", encoding="utf-8")
    first = repository_fingerprint(tmp_path)
    (tmp_path / ".ladon").mkdir()
    (tmp_path / ".ladon" / "index.sqlite").write_bytes(b"generated")
    assert repository_fingerprint(tmp_path) == first
