from __future__ import annotations

from pathlib import Path

from ladon.proofir_calibration import run_calibration


def test_calibration_records_fingerprints_and_predicates_without_database_mutation(tmp_path: Path) -> None:
    result = run_calibration(tmp_path, ("python", "-c", "print('surface exact')"), predicates=("surface exact", "missing"))
    assert result["schema"] == "ladon-proofir-calibration-v1"
    assert result["databaseMutated"] is False
    assert result["predicates"] == {"surface exact": True, "missing": False}
    assert result["before"] == result["after"]

