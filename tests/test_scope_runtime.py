from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import pytest

from ladon.cli import main
from ladon.pipeline import RunContext, run_pipeline
from ladon.pipeline_extraction import analysis_module_roots
from ladon.report_v3 import build_report_v3
from ladon.reportset_cli import positive_number_argument
from ladon.scope import ScopePlanningError
from ladon.scope_runtime import resolve_analysis_scope


def write_project(root: Path) -> None:
    (root / "Pkg").mkdir()
    (root / "Pkg.lean").write_text(
        "import Pkg.Owner\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Owner.lean").write_text(
        "import Pkg.Core\ntheorem owner : True := by trivial\n",
        encoding="utf-8",
    )
    (root / "Pkg" / "Core.lean").write_text(
        "def core : Nat := 1\n",
        encoding="utf-8",
    )


def write_generated_family_policy(path: Path) -> None:
    """Write a valid generated-family policy for preview fingerprinting."""

    path.write_text(
        json.dumps(
            {
                "schema": "ladon-generated-family-policy-v2",
                "families": [
                    {
                        "id": "fixture.generated",
                        "pathPatterns": ["Pkg/Generated/*.lean"],
                        "reviewThreshold": {
                            "metric": "memberCount",
                            "atLeast": 2,
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def assert_selected_generated_policy(generated: dict) -> None:
    """Check preview evidence for the discovered generated-family policy."""

    assert generated["status"] == "selected"
    assert generated["path"] == ".ladon/generated-family-policy.json"
    assert generated["sha256"].startswith("sha256:")


def assert_requested_preview_resources(resources: dict) -> None:
    """Check requested limits are planned without observed runtime state."""

    assert resources["requested"]["wallSeconds"] == 30.0
    assert resources["requested"]["rssBytes"] == 256 * 1024 * 1024
    assert resources["requested"]["reportBytes"] == 4096
    assert resources["leanHelperTimeoutSeconds"] == 17.0
    assert resources["observed"] is None
    assert resources["crossed"] is None
    assert resources["previewOnly"] is True


@pytest.mark.parametrize("value", ["nan", "inf", "-inf", "0", "-1"])
def test_preview_deadlines_reject_nonfinite_or_nonpositive_values(
    value: str,
) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_number_argument(value)


def test_resolved_scope_reuses_index_and_selects_primary_plus_context(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"

    cold = resolve_analysis_scope(
        repo,
        scope_kind="owner",
        roots=("Pkg.Owner",),
        cache_dir=cache,
    )
    warm = resolve_analysis_scope(
        repo,
        scope_kind="owner",
        roots=("Pkg.Owner",),
        cache_dir=cache,
    )

    assert cold.source_index.cache.status == "miss"
    assert warm.source_index.cache.status == "hit"
    assert set(warm.discovery.modules) == {"Pkg.Owner", "Pkg.Core"}
    assert warm.discovery.analysis_root_module == "Pkg.Owner"
    assert warm.scope_plan.primary_modules == ("Pkg.Owner",)
    assert warm.scope_plan.context_modules == ("Pkg.Core",)


def test_preview_is_explicit_and_nonexecuting(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    resolved = resolve_analysis_scope(
        repo,
        scope_kind="inventory",
        roots=("Pkg",),
        use_cache=False,
    )
    payload = resolved.preview_payload(
        cache_dir=None,
        extraction_backend="lean",
    )

    assert payload["schema"] == "ladon-analysis-preview-v1"
    assert payload["scope"]["primaryPopulation"]["selectedCount"] == 3
    assert payload["execution"]["willRunLean"] is False
    assert payload["execution"]["willRunLake"] is False
    assert payload["execution"]["willRunVersionControl"] is False


def test_inventory_scope_needs_no_unique_top_level_root(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A.lean").write_text("def a : Nat := 1\n", encoding="utf-8")
    (repo / "B.lean").write_text("def b : Nat := 2\n", encoding="utf-8")

    resolved = resolve_analysis_scope(
        repo,
        scope_kind="inventory",
        use_cache=False,
    )

    assert resolved.scope_plan.primary_modules == ("A", "B")
    assert resolved.discovery.analysis_root_module == "A"
    assert set(resolved.discovery.modules) == {"A", "B"}
    assert resolved.scope_plan.report_anchor == "A"
    assert resolved.scope_plan.resolved_navigation_roots == ()
    assert (
        resolved.scope_plan.to_payload()["navigationRoots"]["status"]
        == "not_requested"
    )
    context = RunContext(repo_root=repo)
    context.scope_plan = resolved.scope_plan
    assert analysis_module_roots(context, resolved.discovery) == ()


def test_explicit_inventory_navigation_root_is_auxiliary(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A.lean").write_text("def a : Nat := 1\n", encoding="utf-8")
    (repo / "B.lean").write_text("def b : Nat := 2\n", encoding="utf-8")

    resolved = resolve_analysis_scope(
        repo,
        scope_kind="inventory",
        navigation_roots=("B",),
        use_cache=False,
    )
    context = RunContext(repo_root=repo)
    context.scope_plan = resolved.scope_plan

    assert resolved.scope_plan.primary_modules == ("A", "B")
    assert resolved.scope_plan.requested_selection_roots == ()
    assert resolved.scope_plan.resolved_selection_roots == ()
    assert resolved.scope_plan.requested_navigation_roots == ("B",)
    assert resolved.scope_plan.resolved_navigation_roots == ("B",)
    assert resolved.discovery.analysis_root_module == "A"
    assert analysis_module_roots(context, resolved.discovery) == ("B",)


def test_unresolved_inventory_navigation_root_is_not_replaced(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A.lean").write_text("def a : Nat := 1\n", encoding="utf-8")

    with pytest.raises(
        ScopePlanningError,
        match="does not resolve through the source index",
    ):
        resolve_analysis_scope(
            repo,
            scope_kind="inventory",
            navigation_roots=("Missing",),
            use_cache=False,
        )


def test_pipeline_uses_every_explicit_multi_root_for_dag_reachability(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A").mkdir()
    (repo / "B").mkdir()
    (repo / "A.lean").write_text("import A.Core\n", encoding="utf-8")
    (repo / "A" / "Core.lean").write_text(
        "def a : Nat := 1\n",
        encoding="utf-8",
    )
    (repo / "B.lean").write_text("import B.Core\n", encoding="utf-8")
    (repo / "B" / "Core.lean").write_text(
        "def b : Nat := 2\n",
        encoding="utf-8",
    )

    payload = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_roots=("A", "B"),
            analysis_scope="multi-root",
            source_cache_enabled=False,
        )
    ).to_report_payload()

    assert payload["module_dag"]["analysis_scope"]["resolvedRoots"] == ["A", "B"]
    assert payload["module_dag"]["chosen_roots"] == ["A", "B"]
    assert (
        payload["module_dag"][
            "source_modules_not_reachable_from_chosen_roots_count"
        ]
        == 0
    )


def assert_partial_discovery_phase(payload: dict) -> None:
    """Check retained source-index diagnostics for one unreadable module."""

    discover = payload["phases"]["discover"]
    assert discover["status"] == "partial"
    assert discover["required"] is True
    assert discover["counters"]["inventory_modules"] == 3
    assert discover["counters"]["indexed_modules"] == 2
    assert discover["counters"]["source_cache_failed"] == 1
    source_failure = next(
        row
        for row in discover["diagnostics"]
        if row["id"] == "source_index.source_failed"
    )
    assert source_failure["subject"] == "Broken"


def assert_partial_module_dag(payload: dict) -> None:
    """Check downstream metrics are labeled with their retained population."""

    dag_phase = payload["phases"]["module_dag"]
    assert dag_phase["status"] == "partial"
    assert dag_phase["required"] is True
    assert payload["module_dag"]["module_count"] == 2
    assert payload["module_dag"]["source_index"]["inventoryModuleCount"] == 3
    assert payload["module_dag"]["source_index"]["indexedModuleCount"] == 2
    assert payload["module_dag"]["completeness"]["metricsPopulation"] == (
        "retained_readable_modules"
    )


def test_pipeline_retains_readable_inventory_after_one_source_failure(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "A.lean").write_text("def a : Nat := 1\n", encoding="utf-8")
    (repo / "B.lean").write_text("def b : Nat := 2\n", encoding="utf-8")
    (repo / "Broken.lean").write_bytes(b"\xff")

    payload = run_pipeline(
        RunContext(
            repo_root=repo,
            analysis_scope="inventory",
            source_cache_enabled=False,
        )
    ).to_report_payload()

    assert_partial_discovery_phase(payload)
    assert_partial_module_dag(payload)


def test_invalid_scope_fails_before_analysis(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    with pytest.raises(ScopePlanningError, match="does not resolve"):
        resolve_analysis_scope(
            repo,
            scope_kind="owner",
            roots=("Pkg.Absent",),
            use_cache=False,
        )


def test_installed_preview_json_starts_no_external_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("preview started an external process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    status = main(
        [
            "preview",
            "--repo-root",
            str(repo),
            "--root",
            "Pkg.Owner",
            "--scope",
            "owner",
            "--extraction-backend",
            "lean",
            "--no-cache",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert status == 0
    assert payload["execution"]["willRunLean"] is False
    assert payload["scope"]["resolvedRoots"] == ["Pkg.Owner"]
    assert captured.err == ""


def test_installed_preview_fingerprints_policies_and_requested_limits(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    policy_dir = repo / ".ladon"
    policy_dir.mkdir()
    policy = policy_dir / "generated-family-policy.json"
    write_generated_family_policy(policy)

    status = main(
        [
            "preview",
            "--repo-root",
            str(repo),
            "--root",
            "Pkg.Owner",
            "--overall-timeout",
            "30",
            "--max-rss-mib",
            "256",
            "--max-report-bytes",
            "4096",
            "--lean-timeout",
            "17",
            "--no-cache",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    generated = payload["policies"]["generatedFamily"]
    resources = payload["resources"]
    assert status == 0
    assert_selected_generated_policy(generated)
    assert_requested_preview_resources(resources)
    assert captured.err == ""


def test_cold_and_warm_cache_evidence_do_not_change_analysis_fingerprint(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"

    cold = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            analysis_scope="inventory",
            source_cache_dir=cache,
        )
    )
    warm = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            analysis_scope="inventory",
            source_cache_dir=cache,
        )
    )

    cold_v3 = build_report_v3(cold.to_report_model())
    warm_v3 = build_report_v3(warm.to_report_model())
    assert cold.context.source_index_cache["status"] == "miss"
    assert warm.context.source_index_cache["status"] == "hit"
    assert cold_v3.analysis_fingerprint == warm_v3.analysis_fingerprint


def test_policy_change_invalidates_index_and_scope_fingerprint(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_project(repo)
    cache = tmp_path / "cache"
    policy = repo / "ladon-source-pattern-policy.json"
    policy.write_text(
        '{"patterns":[{"id":"first","pattern":"owner"}]}',
        encoding="utf-8",
    )

    first = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            analysis_scope="inventory",
            source_cache_dir=cache,
        )
    )
    policy.write_text(
        '{"patterns":[{"id":"second","pattern":"core"}]}',
        encoding="utf-8",
    )
    second = run_pipeline(
        RunContext(
            repo_root=repo,
            requested_root="Pkg",
            analysis_scope="inventory",
            source_cache_dir=cache,
        )
    )

    assert first.context.source_index_cache["status"] == "miss"
    assert second.context.source_index_cache["status"] == "invalidation"
    assert first.context.scope_plan is not None
    assert second.context.scope_plan is not None
    assert first.context.scope_plan.fingerprint != second.context.scope_plan.fingerprint
    assert (
        first.context.policy_inputs["sourcePattern"]["sha256"]
        != second.context.policy_inputs["sourcePattern"]["sha256"]
    )
