from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from test_theorem_lineage_query import lineage_database

from ladon.proof_search_index import build_proof_search_index
from ladon.theorem_cli import theorem_main
from ladon.theorem_lineage_projection import ProjectionQuery, project_lineage
from ladon.theorem_lineage_query import LineageQuery

FIXTURE = Path(__file__).parent / "fixtures" / "theorem_capsule"


@pytest.fixture
def compiled_repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    shutil.copytree(FIXTURE, root, ignore=shutil.ignore_patterns(".lake", ".ladon"))
    completed = subprocess.run(
        ["lake", "build"], cwd=root, text=True, capture_output=True, check=False, timeout=120
    )
    if completed.returncode != 0:
        pytest.fail(completed.stderr or completed.stdout)
    return root


def test_store_query_projection_preserves_authority_and_contiguous_edges() -> None:
    connection, identity = lineage_database()
    result = project_lineage(
        connection,
        identity,
        ProjectionQuery(
            lineage=LineageQuery(theorem="Demo.target", boundary="trust"),
            view="graph",
        ),
    )
    assert result["authority"] == "lean_environment"
    assert result["closureId"]
    for route in result["routes"]:
        assert route["nodes"][0] == route["root"]
        assert route["nodes"][-1] == "Demo.target"
        assert len(route["edges"]) == len(route["nodes"]) - 1
        assert all(
            {"source": source, "target": target} in result["edges"]
            for source, target in zip(route["nodes"], route["nodes"][1:])
        )
    assert "alternative proofs" in result["nonclaim"]


def test_installed_cli_refreshes_then_serves_a_warm_source_linked_route(
    compiled_repository: Path, tmp_path: Path
) -> None:
    build_proof_search_index(compiled_repository)
    first_payload = _run_lineage(compiled_repository, tmp_path / "first.json", "missing")
    warm_payload = _run_lineage(compiled_repository, tmp_path / "warm.json", "never")
    route_payload = _run_lineage(
        compiled_repository,
        tmp_path / "base-route.json",
        "never",
        boundary="declaration",
        roots=("CapsuleFixture.base",),
    )
    _assert_refresh_and_source_anchor(first_payload, warm_payload, route_payload)


def _run_lineage(
    repository: Path,
    output: Path,
    refresh: str,
    *,
    boundary: str = "project",
    roots: tuple[str, ...] = (),
) -> dict[str, object]:
    command = [
        "lineage", "CapsuleFixture.chosen", "--repo-root", str(repository),
        "--view", "routes", "--from", boundary, "--format", "json",
        "--refresh", refresh, "--output", str(output),
    ]
    for root in roots:
        command.extend(("--root", root))
    assert theorem_main(command) == 0
    return json.loads(output.read_text(encoding="utf-8"))


def _assert_refresh_and_source_anchor(
    first_payload: dict[str, object], warm_payload: dict[str, object], route_payload: dict[str, object]
) -> None:
    chosen = next(row for row in warm_payload["nodes"] if row["name"] == "CapsuleFixture.chosen")
    assert first_payload["refresh"] == {"policy": "missing", "performed": True}
    assert warm_payload["refresh"] == {"policy": "never", "performed": False}
    assert warm_payload["authority"] == "lean_environment"
    assert chosen["sourcePath"] == "CapsuleFixture.lean"
    assert chosen["sourceLine"] == 11
    assert any(route["target"] == "CapsuleFixture.chosen" for route in warm_payload["routes"])
    assert route_payload["routes"][0]["nodes"] == ["CapsuleFixture.base", "CapsuleFixture.chosen"]
