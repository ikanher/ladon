from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from support.proofir_v3_native import derivation_artifact

from ladon.proofir_catalog import PROOFIR_CONFIG_RELATIVE_PATH


def _run_json(arguments: list[str], *, environment: dict[str, str]) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def _fixture_repository(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "Main.lean").write_text("theorem goal : True := by trivial\n")
    artifact = derivation_artifact()
    (repository / "derivation.json").write_text(json.dumps(artifact), encoding="utf-8")
    config = repository / PROOFIR_CONFIG_RELATIVE_PATH
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"artifacts": ["derivation.json"]}), encoding="utf-8")
    return repository, artifact


def test_installed_cli_queries_stored_derivation_without_lean(tmp_path: Path) -> None:
    repository, artifact = _fixture_repository(tmp_path)
    index = tmp_path / "proof-search.sqlite3"
    environment = dict(os.environ)
    environment["LEAN"] = str(tmp_path / "must-not-run-lean")
    _run_json(
        [
            "proof-search",
            "index",
            "build",
            "--repo-root",
            str(repository),
            "--index",
            str(index),
            "--format",
            "json",
        ],
        environment=environment,
    )
    common = [
        "--repo-root",
        str(repository),
        "--index",
        str(index),
        "--end",
        "statement:goal",
        "--limit",
        "20",
        "--format",
        "json",
    ]
    route = _run_json(
        [
            "proof-search",
            "evidence",
            "route",
            str(artifact["artifactId"]),
            "--start",
            "statement:a",
            *common,
        ],
        environment=environment,
    )
    complete_slice = _run_json(
        [
            "proof-search",
            "evidence",
            "slice",
            str(artifact["artifactId"]),
            *common,
        ],
        environment=environment,
    )
    alternatives = _run_json(
        [
            "proof-search",
            "evidence",
            "alternatives",
            str(artifact["artifactId"]),
            *common,
        ],
        environment=environment,
    )

    assert route["queryKind"] == "navigation-path"
    assert route["status"] == "found"
    assert complete_slice["queryKind"] == "complete-derivation-slice"
    assert complete_slice["status"] == "complete"
    assert alternatives["queryKind"] == "alternative-analysis"
    assert alternatives["status"] == "complete"
    assert {route["checkerAcceptance"], complete_slice["checkerAcceptance"], alternatives["checkerAcceptance"]} == {"not-evaluated"}
    assert all(result["boundsApplied"]["maxAlternatives"] == 20 for result in (route, complete_slice, alternatives))
