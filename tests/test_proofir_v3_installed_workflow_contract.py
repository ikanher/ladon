from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from support.proofir_v3_native import claim_artifact

from ladon.proofir_catalog import PROOFIR_CONFIG_RELATIVE_PATH
from ladon.proofir_v3 import detached_content_id


def _run(*arguments: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "ladon.entrypoint", *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    return json.loads(completed.stdout)


def _legacy_artifact() -> dict[str, object]:
    artifact = claim_artifact()
    artifact["artifactKind"] = "proofir_bridge_index"
    artifact["artifactId"] = None
    artifact["artifactId"] = detached_content_id(artifact)
    return artifact


@pytest.fixture
def installed_workflow(
    tmp_path: Path,
) -> tuple[tuple[str, ...], dict[str, object], dict[str, object]]:
    repository = tmp_path / "repo"
    repository.mkdir()
    (repository / "Main.lean").write_text("theorem goal : True := by trivial\n", encoding="utf-8")
    native = claim_artifact()
    legacy = _legacy_artifact()
    (repository / "claim.json").write_text(json.dumps(native), encoding="utf-8")
    (repository / "legacy.json").write_text(json.dumps(legacy), encoding="utf-8")
    config = repository / PROOFIR_CONFIG_RELATIVE_PATH
    config.parent.mkdir(parents=True)
    config.write_text(json.dumps({"artifacts": ["claim.json", "legacy.json"]}), encoding="utf-8")
    index = tmp_path / "proof-search.sqlite3"
    common = ("--repo-root", str(repository), "--index", str(index), "--format", "json")
    built = _run("proof-search", "index", "build", *common)
    return common, legacy, built


def test_installed_discovery_and_indexing(
    installed_workflow: tuple[tuple[str, ...], dict[str, object], dict[str, object]],
) -> None:
    common, _, built = installed_workflow
    assert built["counts"]["proofirV3Artifacts"] == 1
    assert built["counts"]["proofirDiagnostics"] == 1
    status = _run("proof-search", "index", "status", *common)
    assert status["freshness"] == "fresh"


def test_installed_dossier_reports_coverage_and_limitations(
    installed_workflow: tuple[tuple[str, ...], dict[str, object], dict[str, object]],
) -> None:
    common, _, _ = installed_workflow
    dossier = _run("proof-search", "evidence", "theorem", "statement:goal", *common)
    assert dossier["schema"] == "ladon-proofir-v3-theorem-evidence-v1"
    assert dossier["claims"]["returned"] == 1
    assert dossier["coverage"]["applicability"] == "unavailable"
    assert {row["id"] for row in dossier["limitations"]["rows"]} == {
        "evidence-not-theorem-truth",
        "navigation-not-complete-proof-slice",
    }
    assert dossier["nonclaims"]


def test_installed_legacy_and_type_diagnostics_are_bounded(
    installed_workflow: tuple[tuple[str, ...], dict[str, object], dict[str, object]],
) -> None:
    common, legacy, _ = installed_workflow
    rejected = _run("proof-search", "evidence", "artifact", str(legacy["artifactId"]), *common)
    assert rejected["rows"] == []
    diagnostics = _run(
        "proof-search",
        "search",
        "type-text",
        "--pattern",
        "True",
        "--limit",
        "1",
        "--diagnostic-limit",
        "1",
        *common,
    )
    assert diagnostics["schema"] == "ladon-proof-search-type-text-result-v2"
    assert diagnostics["coverage"]["authority"] == "sqlite_lexical_shortlist"
    assert diagnostics["nonclaims"]
