from __future__ import annotations

from types import SimpleNamespace

import pytest

from ladon.evidence_receipt_readers import stored_query_receipt
from ladon.theorem_cli import build_theorem_parser
from ladon.theorem_lineage_cli import _reject_inapplicable_closure_options, _write_result
from ladon.theorem_lineage_projection import TheoremLineageProjectionError


def test_lineage_parser_exposes_bounded_views_and_refresh_policy() -> None:
    parser = build_theorem_parser()
    args = parser.parse_args(
        [
            "lineage",
            "Demo.target",
            "--view",
            "bottlenecks",
            "--from",
            "trust",
            "--edge-kind",
            "value",
            "--refresh",
            "never",
            "--max-depth",
            "3",
        ]
    )
    assert args.theorem_command == "lineage"
    assert args.view == "bottlenecks"
    assert args.boundary == "trust"
    assert args.refresh == "never"
    assert args.max_depth == 3


def test_lineage_parser_accepts_repeated_roots_and_custom_index() -> None:
    parser = build_theorem_parser()
    args = parser.parse_args(
        [
            "lineage",
            "Demo.target",
            "--root",
            "Demo",
            "--root",
            "Init",
            "--index",
            "/tmp/demo.sqlite",
        ]
    )
    assert args.roots == ["Demo", "Init"]
    assert args.index == "/tmp/demo.sqlite"


def test_lineage_defaults_to_summary_for_first_pass() -> None:
    args = build_theorem_parser().parse_args(["lineage", "Demo.target"])
    assert args.view == "summary"
    assert args.max_dominators == 100


def test_lineage_parser_exposes_complete_database_budget_and_summary() -> None:
    parser = build_theorem_parser()
    args = parser.parse_args(
        [
            "lineage",
            "Demo.target",
            "--view",
            "summary",
            "--max-database-mib",
            "1024",
        ]
    )
    assert args.view == "summary"
    assert args.max_database_mib == 1024


def test_closure_view_tracks_explicit_route_only_options() -> None:
    parser = build_theorem_parser()
    defaults = parser.parse_args(["lineage", "Demo.target", "--view", "closure"])
    assert defaults.max_traversal_edges == 100000
    assert defaults.max_output_bytes == 33554432
    assert getattr(defaults, "_lineage_explicit_options", set()) == set()

    explicit = parser.parse_args(
        ["lineage", "Demo.target", "--view", "closure", "--max-routes", "20"]
    )
    with pytest.raises(TheoremLineageProjectionError, match="--max-routes"):
        _reject_inapplicable_closure_options(explicit)


@pytest.mark.parametrize(
    "options,diagnostic",
    [
        (["--from", "trust"], "--from"),
        (["--root", "Demo.root"], "--root"),
        (["--direction", "ancestry"], "--direction"),
        (["--max-depth", "32"], "--max-depth"),
        (["--max-traversal-edges", "100000"], "--max-traversal-edges"),
        (["--max-dominators", "100"], "--max-dominators"),
    ],
)
def test_closure_view_rejects_explicit_route_selectors_and_budgets(options, diagnostic):
    args = build_theorem_parser().parse_args(
        ["lineage", "Demo.target", "--view", "closure", *options]
    )
    with pytest.raises(TheoremLineageProjectionError, match=diagnostic):
        _reject_inapplicable_closure_options(args)


def test_byte_limit_failure_preserves_existing_output_file(tmp_path):
    destination = tmp_path / "lineage.json"
    destination.write_text("previous report\n", encoding="utf-8")
    receipt = stored_query_receipt(
        "theorem-lineage", "Demo.target", observed=True,
        source_ref="lineage:fixture", source_freshness="fresh",
        projection_kind="sqlite-row",
    )
    args = SimpleNamespace(
        format="json", output=str(destination), max_output_bytes=1,
    )

    with pytest.raises(RuntimeError, match="output byte cap"):
        _write_result({"status": "available", "evidenceReceipt": receipt}, args)

    assert destination.read_text(encoding="utf-8") == "previous report\n"
