from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from ladon.benchmark_process import MeasuredProcess
from ladon.large_inventory_gate import (
    ScaleCeilings,
    analysis_command,
    normalized_report_bytes,
    progress_cache_evidence,
    progress_phase_evidence,
    run_large_inventory_measurements,
)


class FakeInstalledCli:
    """Produce deterministic reports while preserving cache/run distinctions."""

    def __init__(
        self,
        *,
        warm_cache_evidence: bool = True,
        warm_semantic_drift: bool = False,
        warm_timeout: bool = False,
    ) -> None:
        self.commands: list[list[str]] = []
        self.warm_cache_evidence = warm_cache_evidence
        self.warm_semantic_drift = warm_semantic_drift
        self.warm_timeout = warm_timeout

    def __call__(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
        timeout_seconds: float,
    ) -> MeasuredProcess:
        del cwd, environment, timeout_seconds
        copied = list(command)
        self.commands.append(copied)
        cache = Path(option(copied, "--cache-dir"))
        warm = cache.joinpath("populated").is_file()
        cache.mkdir(parents=True, exist_ok=True)
        cache.joinpath("populated").write_text("cache-v1\n", encoding="utf-8")
        representation = option(copied, "--format")
        output = Path(option(copied, "--output"))
        output.parent.mkdir(parents=True, exist_ok=True)
        if representation == "json":
            output.write_text(
                json.dumps(
                    report_payload(
                        warm=warm,
                        semantic_drift=warm and self.warm_semantic_drift,
                    ),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        else:
            output.write_text("Ladon compact report\n", encoding="utf-8")
        cache_key = (
            "source_index_cache_hits"
            if warm
            else "source_index_cache_misses"
        )
        cache_payload = (
            {cache_key: 12}
            if not warm or self.warm_cache_evidence
            else {}
        )
        stderr = json.dumps(
            {
                "schemaVersion": 1,
                "phase": "discover",
                "event": "finish",
                "cache": cache_payload,
            },
            sort_keys=True,
        )
        return MeasuredProcess(
            returncode=-15 if warm and self.warm_timeout else 0,
            stdout="",
            stderr=stderr,
            wall_seconds=0.4 if warm else 1.2,
            peak_rss_mib=42.0,
            descendant_count=0,
            timed_out=warm and self.warm_timeout,
        )


def report_payload(*, warm: bool, semantic_drift: bool = False) -> dict:
    """Return a minimal v3-shaped payload with registered volatile fields."""

    return {
        "metadata": {
            "report_version": "ladon-report-v3",
            "generated_at_utc": "2026-07-25T12:00:00Z",
        },
        "projection": {
            "name": "review",
            "analysis_fingerprint": "sha256:stable-analysis",
        },
        "phases": {
            "discover": {
                "elapsed_seconds": 0.4 if warm else 1.2,
                "counters": {
                    "source_cache_hits": 12 if warm else 0,
                    "source_cache_rebuilt": 0 if warm else 12,
                },
            }
        },
        "pipeline": {
            "timings": {
                "discover": {
                    "elapsed_seconds": 0.4 if warm else 1.2,
                    "counters": {
                        "source_cache_hits": 12 if warm else 0,
                        "source_cache_rebuilt": 0 if warm else 12,
                    },
                }
            }
        },
        "sections": {
            "module_dag": {
                "module_count": 13 if semantic_drift else 12,
            }
        },
    }


def gate_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    analyzer = tmp_path / "installed" / "bin" / "ladon"
    analyzer.parent.mkdir(parents=True)
    analyzer.write_text("#!/bin/sh\n", encoding="utf-8")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    return analyzer, fixture, runtime


def fixture_identity() -> dict:
    return {
        "id": "sha256:fixture",
        "moduleCount": 12,
        "sourceLineCount": 240,
        "declarationCount": 60,
    }


def candidate_identity() -> dict:
    return {
        "id": "sha256:candidate",
        "supportedPythonMinors": ["3.11", "3.12"],
    }


def test_six_samples_measure_both_public_representations(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)
    runner = FakeInstalledCli()

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={"CI": "1"},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        runner=runner,
        require_large_fixture=False,
    )

    assert_sample_protocol(result, runner, analyzer)
    assert_sample_evidence(result)


def assert_sample_protocol(
    result: dict,
    runner: FakeInstalledCli,
    analyzer: Path,
) -> None:
    assert result["passed"]
    assert result["protocol"]["sampleCount"] == 3
    assert len(result["samples"]["cold"]) == 3
    assert len(result["samples"]["warm"]) == 3
    assert len(runner.commands) == 12
    template = result["protocol"]["commandTemplate"]
    assert template[0] == "ladon" and "benchmark" not in template
    assert all(
        "--cache-dir" in command and command[0] == str(analyzer)
        for command in runner.commands
    )


def assert_sample_evidence(result: dict) -> None:
    assert result["cacheReuse"]["validated"]
    assert result["determinism"]["validated"]
    assert len(result["checks"]) == 36
    first = result["samples"]["cold"][0]["representations"]["json"]
    assert first["phaseProgress"][0]["phase"] == "discover"
    assert first["outsideProgressWallSeconds"] > 0


def test_each_exceeded_ceiling_retains_exact_identity_and_values(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        ceilings=ScaleCeilings(
            cold_wall_seconds=1.0,
            warm_wall_seconds=0.2,
            peak_rss_mib=40.0,
            canonical_json_bytes=100,
            compact_text_bytes=10,
        ),
        runner=FakeInstalledCli(),
        require_large_fixture=False,
    )

    assert not result["passed"]
    exceeded = [
        row
        for row in result["failures"]
        if row.get("metric") in {
            "wall_seconds",
            "peak_rss_mib",
            "json_bytes",
            "text_bytes",
        }
    ]
    assert exceeded
    assert all(row["observed"] > row["ceiling"] for row in exceeded)
    assert all(row["candidateId"] == "sha256:candidate" for row in exceeded)
    assert all(row["fixtureId"] == "sha256:fixture" for row in exceeded)


def test_exact_wall_and_rss_boundaries_pass_without_noise_allowance(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        ceilings=ScaleCeilings(
            cold_wall_seconds=1.2,
            warm_wall_seconds=0.4,
            peak_rss_mib=42.0,
            canonical_json_bytes=10_000,
            compact_text_bytes=1_000,
        ),
        runner=FakeInstalledCli(),
        require_large_fixture=False,
    )

    assert result["passed"]
    boundary_checks = [
        row
        for row in result["checks"]
        if row["metric"] in {"wall_seconds", "peak_rss_mib"}
    ]
    assert boundary_checks
    assert all(row["passed"] for row in boundary_checks)
    assert any(row["observed"] == row["ceiling"] for row in boundary_checks)


def test_warm_speed_without_an_observed_hit_fails_cache_contract(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        runner=FakeInstalledCli(warm_cache_evidence=False),
        require_large_fixture=False,
    )

    assert not result["cacheReuse"]["validated"]
    assert {
        row["temperature"] for row in result["failures"]
        if row["id"].endswith("cache_outcome")
    } == {"warm"}


def test_normalized_content_detects_semantic_warm_drift(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        runner=FakeInstalledCli(warm_semantic_drift=True),
        require_large_fixture=False,
    )

    assert not result["determinism"]["validated"]
    assert any(
        row["id"] == "determinism.normalized_report_bytes"
        for row in result["failures"]
    )


def test_timeouts_remain_sample_evidence_and_do_not_abort_protocol(
    tmp_path: Path,
) -> None:
    analyzer, fixture, runtime = gate_fixture(tmp_path)
    runner = FakeInstalledCli(warm_timeout=True)

    result = run_large_inventory_measurements(
        analyzer=analyzer,
        fixture_root=fixture,
        runtime_root=runtime,
        environment={},
        candidate_identity=candidate_identity(),
        fixture_identity=fixture_identity(),
        runner=runner,
        require_large_fixture=False,
    )

    assert len(runner.commands) == 12
    assert not result["passed"]
    assert not result["execution"]["validated"]
    assert result["determinism"]["normalizedJsonRuns"] == 3
    assert {
        row["temperature"]
        for row in result["failures"]
        if row["id"].endswith("process_success")
    } == {"warm"}


def test_normalization_changes_only_registered_runtime_and_cache_fields() -> None:
    cold = report_payload(warm=False)
    warm = report_payload(warm=True)

    cold_bytes, cold_fields = normalized_report_bytes(cold)
    warm_bytes, warm_fields = normalized_report_bytes(warm)

    assert cold_bytes == warm_bytes
    assert cold_fields == warm_fields
    assert "/metadata/generated_at_utc" in cold_fields
    assert any("cache" in field for field in cold_fields)


def test_normalization_preserves_user_fields_with_cache_like_names() -> None:
    first = report_payload(warm=False)
    second = report_payload(warm=False)
    first["sections"]["module_dag"]["cachePolicyName"] = "first"
    second["sections"]["module_dag"]["cachePolicyName"] = "second"
    first["sections"]["module_dag"]["module_metadata"] = {
        "Pkg.Cache": {"path": "one.lean"}
    }
    second["sections"]["module_dag"]["module_metadata"] = {
        "Pkg.Cache": {"path": "two.lean"}
    }

    first_bytes, first_fields = normalized_report_bytes(first)
    second_bytes, second_fields = normalized_report_bytes(second)

    assert first_bytes != second_bytes
    assert first_fields == second_fields
    assert not any("cachePolicyName" in field for field in first_fields)
    assert not any("Pkg.Cache" in field for field in first_fields)


def test_progress_cache_evidence_ignores_non_json_diagnostics() -> None:
    stderr = "\n".join(
        [
            "ladon: compatibility warning",
            json.dumps(
                {
                    "cache": {
                        "source_index_cache_hits": 10,
                        "source_index_cache_rebuilt": 2,
                    }
                }
            ),
        ]
    )

    evidence = progress_cache_evidence(stderr)

    assert evidence.hit_count == 10
    assert evidence.rebuilt_count == 2
    assert evidence.observed


def test_phase_evidence_retains_latest_incomplete_heartbeat() -> None:
    rows = [
        {
            "phase": "discover",
            "event": "finish",
            "status": "complete",
            "elapsedSeconds": 0.5,
            "completed": 2600,
            "total": None,
        },
        {
            "phase": "module_dag",
            "event": "start",
            "status": "running",
            "elapsedSeconds": 0.0,
            "completed": None,
            "total": None,
        },
        {
            "phase": "module_dag",
            "event": "update",
            "status": "running",
            "elapsedSeconds": 5.0,
            "completed": None,
            "total": None,
        },
    ]

    evidence = progress_phase_evidence(
        "\n".join(json.dumps(row) for row in rows)
    )

    assert evidence[0]["phase"] == "discover"
    assert evidence[0]["elapsedSeconds"] == 0.5
    assert evidence[1]["phase"] == "module_dag"
    assert evidence[1]["event"] == "update"
    assert evidence[1]["elapsedSeconds"] == 5.0


def test_analysis_command_has_no_benchmark_only_product_route(
    tmp_path: Path,
) -> None:
    command = analysis_command(
        tmp_path / "ladon",
        fixture_root=tmp_path / "fixture",
        cache=tmp_path / "cache",
        output=tmp_path / "report.json",
        representation="json",
    )

    assert command[0] == str(tmp_path / "ladon")
    assert command[1:3] == ["--repo-root", str(tmp_path / "fixture")]
    assert command[command.index("--scope") + 1] == "inventory"
    assert "--cache-dir" in command
    assert "--projection" in command
    assert "benchmark" not in command


def option(command: Sequence[str], name: str) -> str:
    index = command.index(name)
    return command[index + 1]
