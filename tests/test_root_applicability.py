from __future__ import annotations

from ladon.analysis.findings import root_import_closure_findings
from ladon.analysis.module_dag import summarize_module_dag
from ladon.analysis.quality_baseline import root_import_closure_values
from ladon.analysis.root_applicability import (
    root_applicability,
    root_views_applicable,
    root_views_auxiliary,
)
from ladon.ir import LeanModule
from ladon.render_module_dag import (
    root_applicability_lines,
    unreachable_module_lines,
)


def rootless_dag() -> dict:
    return {
        "root_reachability": root_applicability(
            (),
            population="inventory",
        ),
        "root_direct_import_closures": [
            {
                "root": "Invented",
                "direct_import": "Invented.Child",
                "reachable_module_count": 99,
            }
        ],
        "source_modules_not_reachable_from_chosen_roots_count": 8,
        "source_modules_not_reachable_from_chosen_roots": ["Fixture"],
    }


def test_rootless_envelope_suppresses_root_derived_claims() -> None:
    dag = rootless_dag()

    assert root_views_applicable(dag) is False
    assert root_import_closure_values(dag) == []
    assert root_import_closure_findings(dag) == []
    assert unreachable_module_lines(dag) == []
    assert root_applicability_lines(dag)[1].startswith(
        "- status: not_applicable"
    )


def test_explicit_inventory_root_is_an_auxiliary_view() -> None:
    dag = {
        "root_reachability": root_applicability(
            ("Fixture.Root",),
            population="inventory",
            auxiliary=True,
        )
    }

    assert root_views_applicable(dag) is True
    assert root_views_auxiliary(dag) is True
    assert root_applicability_lines(dag)[0] == "Auxiliary Root Reachability"


def test_legacy_reports_retain_historical_root_applicability() -> None:
    assert root_views_applicable({}) is True


def test_rootless_summary_does_not_invent_graph_roots() -> None:
    summary = summarize_module_dag(
        {
            "Fixture.Owner": LeanModule(
                name="Fixture.Owner",
                path="Fixture/Owner.lean",
                imports=("Fixture.Context",),
            ),
            "Fixture.Context": LeanModule(
                name="Fixture.Context",
                path="Fixture/Context.lean",
            ),
        }
    )

    assert summary["root_reachability"]["status"] == "not_applicable"
    assert summary["root_direct_import_closures"] == []
    assert "source_modules_not_reachable_from_chosen_roots_count" not in summary
