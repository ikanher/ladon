from __future__ import annotations

import json
from argparse import Namespace
from dataclasses import replace
from pathlib import Path

from ladon import cli
from ladon.cli import emit_report, main
from ladon.cli_execution import output_plan
from ladon.coverage import CoverageRegistry
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_contract import Finding


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def test_multi_render_reuses_one_projection_with_exact_semantics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    model = _large_finding_model()
    builds = 0
    original = cli.build_report_v3

    def counted_build(*args, **kwargs):
        nonlocal builds
        builds += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(cli, "build_report_v3", counted_build)
    for projection, expected in (("summary", 60), ("review", 130)):
        json_path = tmp_path / f"{projection}.json"
        text_path = tmp_path / f"{projection}.txt"
        plan = output_plan(
            _emit_args(json_path, text_path, projection=projection)
        )

        emit_report(model, plan)

        _assert_projected_parity(
            json_path,
            text_path,
            projection=projection,
            expected=expected,
        )
    assert builds == 2


def test_emit_preflight_rejects_physical_alias_before_analysis(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    physical = tmp_path / "physical"
    physical.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(physical, target_is_directory=True)
    monkeypatch.setattr(
        "ladon.cli.run_pipeline",
        lambda _context: (_ for _ in ()).throw(
            AssertionError("analysis must not start")
        ),
    )

    status = main(
        [
            "--repo-root",
            str(FIXTURE_ROOT),
            "--emit",
            f"json={physical / 'report'}",
            "--emit",
            f"text={alias / 'report'}",
        ]
    )

    assert status == 2
    assert "--emit destinations must be unique" in capsys.readouterr().err
    assert not (physical / "report").exists()


def _large_finding_model():
    model = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    findings = tuple(_fixture_finding(index) for index in range(130))
    coverage = dict(model.coverage.collections)
    coverage["report.findings"] = replace(
        coverage["report.findings"],
        visible=len(findings),
        observed_lower_bound=len(findings),
        total=len(findings),
        omitted=0,
        completeness="complete",
    )
    return replace(
        model,
        findings=findings,
        coverage=CoverageRegistry(coverage),
    )


def _fixture_finding(index: int) -> Finding:
    return Finding.from_mapping(
        {
            "id": f"finding:{index}",
            "kind": f"fixture.{index % 3}",
            "severity": ("error", "warning", "info")[index % 3],
            "subject": f"Fixture.subject{index}",
            "message": "review",
            "authority": "fixture",
            "evidence_count": 1,
        }
    )


def _emit_args(
    json_path: Path,
    text_path: Path,
    *,
    projection: str,
) -> Namespace:
    return Namespace(
        legacy_json=None,
        legacy_text=None,
        emit=[f"json={json_path}", f"text={text_path}"],
        output_format=None,
        output=None,
        report_version=None,
        projection=projection,
    )


def _assert_projected_parity(
    json_path: Path,
    text_path: Path,
    *,
    projection: str,
    expected: int,
) -> None:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    text = text_path.read_text(encoding="utf-8")
    fingerprint = payload["projection"]["analysis_fingerprint"]
    coverage = payload["coverage"]["collections"]["report.findings"]
    assert len(payload["sections"]["findings"]) == expected
    assert f"Analysis fingerprint: {fingerprint}" in text
    assert f"Projection: {projection}" in text
    assert f"- selected: {expected}" in text
    assert (
        "report.findings: "
        f"visible={coverage['visible']} "
        f"total={coverage['total']} "
        f"omitted={coverage['omitted']} "
        f"completeness={coverage['completeness']} "
        f"authority={coverage['authority']} "
        f"population={coverage['population']} "
        f"scope={coverage['scope']}"
    ) in text
