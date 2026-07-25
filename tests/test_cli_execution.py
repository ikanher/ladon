from __future__ import annotations

from argparse import Namespace
from io import StringIO
from pathlib import Path

import pytest

from ladon.cli_execution import (
    InvocationError,
    failure_policy,
    has_required_phase_failure,
    output_plan,
    parse_failure_selectors,
    write_output_plan,
)
from ladon.pipeline import RunContext, run_pipeline


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def cli_args(**overrides):
    values = {
        "legacy_json": None,
        "legacy_text": None,
        "output_format": None,
        "output": None,
        "report_version": "v2",
    }
    values.update(overrides)
    return Namespace(**values)


def test_default_output_is_one_text_representation_on_stdout() -> None:
    plan = output_plan(cli_args())

    assert [(target.format, target.destination) for target in plan.targets] == [
        ("text", "-")
    ]
    assert plan.uses_stdout is True


def test_canonical_json_stdout_is_unambiguous() -> None:
    plan = output_plan(cli_args(output_format="json", output="-"))

    assert [(target.format, target.destination) for target in plan.targets] == [
        ("json", "-")
    ]


def test_legacy_dual_output_requires_two_regular_file_paths() -> None:
    plan = output_plan(
        cli_args(legacy_json="report.json", legacy_text="report.txt")
    )

    assert plan.legacy is True
    assert len(plan.targets) == 2
    with pytest.raises(InvocationError, match="regular file"):
        output_plan(cli_args(legacy_json="-"))
    with pytest.raises(InvocationError, match="distinct"):
        output_plan(cli_args(legacy_json="report", legacy_text="report"))


def test_legacy_and_canonical_output_options_conflict() -> None:
    with pytest.raises(InvocationError, match="cannot be mixed"):
        output_plan(cli_args(legacy_json="report.json", output_format="json"))


def test_report_v1_is_limited_to_one_json_representation() -> None:
    plan = output_plan(
        cli_args(output_format="json", output="-", report_version="v1")
    )

    assert plan.report_version == "v1"
    with pytest.raises(InvocationError, match="sole JSON"):
        output_plan(cli_args(report_version="v1"))
    with pytest.raises(InvocationError, match="sole JSON"):
        output_plan(
            cli_args(
                legacy_json="report.json",
                legacy_text="report.txt",
                report_version="v1",
            )
        )


def test_output_writer_emits_only_the_selected_stdout_representation() -> None:
    stream = StringIO()
    plan = output_plan(cli_args())

    write_output_plan(
        plan,
        {"text": "TEXT\n", "json": '{"report": true}\n'},
        stdout=stream,
    )

    assert stream.getvalue() == "TEXT\n"


def test_output_writer_supports_legacy_dual_files_without_stdout(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "reports" / "report.json"
    text_path = tmp_path / "reports" / "report.txt"
    stream = StringIO()
    plan = output_plan(
        cli_args(legacy_json=str(json_path), legacy_text=str(text_path))
    )

    write_output_plan(
        plan,
        {"text": "TEXT\n", "json": '{"report": true}\n'},
        stdout=stream,
    )

    assert stream.getvalue() == ""
    assert json_path.read_text(encoding="utf-8") == '{"report": true}\n'
    assert text_path.read_text(encoding="utf-8") == "TEXT\n"


def test_failure_selector_grammar_is_exact_and_case_sensitive() -> None:
    selectors = parse_failure_selectors(
        [
            "kind:source_pattern.match",
            "severity:warning",
            "phase:proof_xray:skipped",
        ]
    )

    assert [selector.category for selector in selectors] == [
        "kind",
        "severity",
        "phase",
    ]
    for invalid in (
        "",
        "Severity:warning",
        "severity:Warning",
        "severity:fatal",
        "kind:",
        "phase:proof_xray:failed",
        "phase::partial",
    ):
        with pytest.raises(InvocationError, match="invalid --fail-on"):
            parse_failure_selectors([invalid])


def test_failure_policy_uses_selector_then_stable_row_order_and_or_semantics() -> None:
    payload = {
        "findings": [
            {
                "kind": "source_pattern.match",
                "severity": "warning",
                "subject": "B",
            },
            {
                "kind": "module_fan_in_hotspot",
                "severity": "error",
                "subject": "A",
            },
        ],
        "phases": [
            {"name": "proof_xray", "status": "skipped", "required": False}
        ],
    }
    selectors = parse_failure_selectors(
        [
            "severity:warning",
            "kind:source_pattern.match",
            "phase:proof_xray:skipped",
        ]
    )

    policy = failure_policy(payload, selectors)

    assert policy["selectors"] == [
        "severity:warning",
        "kind:source_pattern.match",
        "phase:proof_xray:skipped",
    ]
    assert [row["selector"] for row in policy["matches"]] == [
        "severity:warning",
        "severity:warning",
        "kind:source_pattern.match",
        "phase:proof_xray:skipped",
    ]


def test_v2_failure_policy_keys_do_not_leak_v3_dispositions() -> None:
    model = run_pipeline(
        RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")
    ).to_report_model()
    selectors = parse_failure_selectors(
        ["phase:lean_extraction:skipped"]
    )

    policy = failure_policy(model, selectors)

    assert policy["matches"]
    assert all(
        '"disposition"' not in match["stable_key"]
        for match in policy["matches"]
    )


def test_required_partial_or_failed_phase_is_operational() -> None:
    assert has_required_phase_failure(
        {"phases": [{"name": "build", "status": "partial", "required": True}]}
    )
    assert not has_required_phase_failure(
        {"phases": [{"name": "proof_xray", "status": "skipped", "required": False}]}
    )
