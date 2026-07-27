from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ladon.analysis.audit_registrations import (
    attach_audit_producer_registrations,
)
from ladon.finding_evidence import resolve_local_json_pointer
from ladon.inspection_query import inspect_dataset
from ladon.inspection_report_adapter import report_dataset
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_v3 import build_report_v3
from ladon.source_index import build_source_index


def test_pipeline_registers_audits_and_only_actionable_resources(
    tmp_path: Path,
) -> None:
    (tmp_path / "Pkg").mkdir()
    (tmp_path / "Pkg" / "Audit.lean").write_text(
        """\
#check Nat
set_option maxHeartbeats 0 in
set_option maxRecDepth 100 in
""",
        encoding="utf-8",
    )

    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Audit.lean",
            source_cache_enabled=False,
        )
    )
    dag = result.module_dag
    audit_rows = dag["auditProducerRegistrations"]["producers"]
    resource_rows = dag["resourceProducerRegistrations"]["producers"]

    assert len(audit_rows) == 1
    assert len(resource_rows) == 1
    assert next(iter(audit_rows.values()))["kind"] == ("audit_command_navigation")
    assert next(iter(audit_rows.values()))["evidenceRefs"][:2] == [
        "#/sections/module_dag/audit_surfaces/0/auditCommands/0",
        "#/sections/module_dag/module_metadata/Pkg.Audit",
    ]
    assert next(iter(resource_rows.values()))["kind"] == (
        "normalized_unlimited_resource_setting"
    )
    assert dag["audit_command_coverage"]["total"] == 1
    assert dag["resource_review_coverage"]["total"] == 1
    assert {region["kind"] for region in result.review_regions} >= {
        "audit_surface_region",
        "option_resource_region",
    }
    assert {
        "module_dag.audit_commands",
        "module_dag.resource_review_inputs",
    }.issubset(result.to_report_model().coverage.collections)


def test_registered_region_actions_use_ordinary_inspection_nouns(
    tmp_path: Path,
) -> None:
    (tmp_path / "Audit.lean").write_text(
        "#print axioms Nat\nset_option maxHeartbeats 0 in\n",
        encoding="utf-8",
    )

    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Audit.lean",
            source_cache_enabled=False,
        )
    )
    by_kind = {region["kind"]: region for region in result.review_regions}

    assert by_kind["audit_surface_region"]["inspectionAction"]["arguments"][:2] == [
        "inspect",
        "audits",
    ]
    assert by_kind["option_resource_region"]["inspectionAction"]["arguments"][:2] == [
        "inspect",
        "resources",
    ]


def test_lexical_candidate_audit_keeps_region_canonical_ref(
    tmp_path: Path,
) -> None:
    package = tmp_path / "Pkg"
    package.mkdir()
    (package / "Owner.lean").write_text(
        "namespace Pkg.Owner\n"
        "theorem target : True := by trivial\n"
        "end Pkg.Owner\n",
        encoding="utf-8",
    )
    (package / "Audit.lean").write_text(
        "import Pkg.Owner\n#print axioms Pkg.Owner.target\n",
        encoding="utf-8",
    )
    result = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Audit.lean",
            source_cache_enabled=False,
        )
    )
    command = result.module_dag["audit_surfaces"][0]["auditCommands"][0]
    candidate = command["candidateMatches"][0]
    canonical_ref = f"source-index:declaration:{candidate['id']}"
    registration = next(
        iter(result.module_dag["auditProducerRegistrations"]["producers"].values())
    )

    assert candidate["canonicalRef"] == canonical_ref
    assert canonical_ref in registration["evidenceRefs"]
    assert result.module_dag["audit_command_coverage"]["visible"] == 1
    assert any(
        region["kind"] == "audit_surface_region"
        for region in result.review_regions
    )

    for projection in ("full", "review"):
        _assert_candidate_audit_projection(
            result,
            projection=projection,
            canonical_ref=canonical_ref,
        )


def _assert_candidate_audit_projection(
    result,
    *,
    projection: str,
    canonical_ref: str,
) -> None:
    """Require one full/review report to preserve the exact candidate route."""

    payload = build_report_v3(
        result.to_report_model(),
        projection=projection,
        review_item_limit=1,
    ).to_dict()
    dag = payload["sections"]["module_dag"]
    emitted_candidate = dag["audit_surfaces"][0]["auditCommands"][0][
        "candidateMatches"
    ][0]
    region = next(
        row
        for row in payload["sections"]["review_regions"]
        if row["kind"] == "audit_surface_region"
    )
    signal = region["signals"][0]
    local_refs = [
        reference
        for reference in signal["evidenceRefs"]
        if reference.startswith("#/sections/")
    ]

    assert emitted_candidate["canonicalRef"] == canonical_ref
    assert canonical_ref in signal["evidenceRefs"]
    assert all(
        resolve_local_json_pointer(payload, reference) is not None
        for reference in local_refs
    )


def test_repository_policy_registers_only_matching_finite_resource(
    tmp_path: Path,
) -> None:
    result = _policy_resource_pipeline(tmp_path)
    policy_backed, unconfigured = _finite_resource_directives(result.module_dag)
    finite = _assert_finite_resource_registration(
        result.module_dag,
        policy_backed,
        unconfigured,
    )
    _assert_resource_policy_fingerprint(result)
    _assert_resource_policy_report(
        result,
        finite,
        policy_backed,
        unconfigured,
    )


def _policy_resource_pipeline(tmp_path: Path):
    policy_dir = tmp_path / ".ladon"
    policy_dir.mkdir()
    (policy_dir / "source-pattern-policy.json").write_text(
        """\
{
  "id": "resource-review",
  "patterns": [],
  "resourceThresholds": [
    {
      "id": "deep-recursion",
      "option": "maxRecDepth",
      "minimumValue": 100
    }
  ]
}
""",
        encoding="utf-8",
    )
    (tmp_path / "Audit.lean").write_text(
        """\
set_option maxHeartbeats 0 in
set_option maxRecDepth 100 in
set_option maxRecDepth 99 in
""",
        encoding="utf-8",
    )
    return run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Audit.lean",
            source_cache_enabled=False,
        )
    )


def _finite_resource_directives(
    dag: dict,
) -> tuple[dict, dict]:
    directives = dag["audit_surfaces"][0]["resourceDirectives"]
    by_value = {row["numericValue"]: row for row in directives}
    return by_value[100], by_value[99]


def _assert_finite_resource_registration(
    dag: dict,
    policy_backed: dict,
    unconfigured: dict,
) -> dict:
    directives = dag["audit_surfaces"][0]["resourceDirectives"]
    producers = dag["resourceProducerRegistrations"]["producers"]
    by_kind = {row["kind"]: row for row in producers.values()}
    finite = by_kind["policy_backed_finite_resource_setting"]

    assert len(producers) == 2
    assert policy_backed["pressure"] == "policy_backed"
    assert policy_backed["policyMatch"]["thresholdId"] == "deep-recursion"
    assert "pressure" not in unconfigured
    assert finite["evidenceRefs"] == [
        (
            "#/sections/module_dag/audit_surfaces/0/"
            f"resourceDirectives/{directives.index(policy_backed)}"
        ),
        (
            "#/sections/module_dag/resourceReviewPolicy/"
            "thresholds/deep-recursion"
        ),
    ]
    assert finite["authority"] == "lexical_text_and_repository_policy"
    assert dag["resource_review_coverage"]["total"] == 2
    assert dag["resource_review_coverage"]["authority"] == (
        "lexical_text_and_repository_policy"
    )
    return finite


def _assert_resource_policy_fingerprint(result) -> None:
    source_index = result.context.source_index
    assert source_index is not None
    assert source_index.options["policies"]["sourcePattern"][
        "resourceThresholds"
    ] == [
        {
            "id": "deep-recursion",
            "option": "maxRecDepth",
            "minimumValue": 100,
        }
    ]


def _assert_resource_policy_report(
    result,
    finite: dict,
    policy_backed: dict,
    unconfigured: dict,
) -> None:
    payload = build_report_v3(
        result.to_report_model(),
        projection="full",
    ).to_dict()
    for reference in finite["evidenceRefs"]:
        resolve_local_json_pointer(payload, reference)
    page = inspect_dataset(report_dataset(payload, "resources")).to_dict()
    inspected = {row["id"]: row for row in page["rows"]}
    assert inspected[policy_backed["id"]]["fields"]["pressure"] == "policy_backed"
    assert inspected[policy_backed["id"]]["enrichments"] == [
        policy_backed["policyMatch"]
    ]
    assert inspected[unconfigured["id"]]["fields"]["pressure"] == (
        "navigation_only"
    )
    option_region = next(
        row
        for row in payload["sections"]["review_regions"]
        if row["kind"] == "option_resource_region"
    )
    assert {row["kind"] for row in option_region["signals"]} == {
        "normalized_unlimited_resource_setting",
        "policy_backed_finite_resource_setting",
    }


def _canonical_audit_fixture(tmp_path: Path):
    """Return one command with canonical lexical and Lean declaration joins."""

    owner_path = tmp_path / "Pkg" / "Owner.lean"
    owner_path.parent.mkdir()
    owner_path.write_text(
        "namespace Pkg.Owner\ntheorem target : True := by trivial\nend Pkg.Owner\n",
        encoding="utf-8",
    )
    source_index = build_source_index(tmp_path, use_cache=False).index
    declaration = source_index.modules["Pkg.Owner"].declaration_evidence[0]
    command = {
        "id": "audit:canonical",
        "module": "Pkg.Audit",
        "containingOwner": "Pkg.Audit",
        "authority": "lexical_text",
        "candidateStatus": "lexical_candidate",
        "candidateMatchCount": 1,
        "candidateMatches": [
            {
                "id": declaration.identifier,
                "candidateDeclaration": "Pkg.Owner.target",
                "candidateReferencedOwner": "Pkg.Owner",
            }
        ],
        "candidateDeclarationId": declaration.identifier,
        "candidateReferencedDeclaration": "Pkg.Owner.target",
        "candidateReferencedOwner": "Pkg.Owner",
        "referencedDeclaration": "Pkg.Owner.target",
        "referencedOwner": "Pkg.Owner",
        "resultAuthority": "lean_environment",
        "nonclaim": "Lexical navigation evidence only.",
        "resultNonclaim": "Lean query evidence only.",
    }
    dag = {
        "module_metadata": {
            "Pkg.Audit": {"path": "Pkg/Audit.lean"},
            "Pkg.Owner": {"path": "Pkg/Owner.lean"},
        },
        "audit_surfaces": [
            {
                "module": "Pkg.Audit",
                "auditCommands": [command],
                "resourceDirectives": [],
            }
        ],
    }
    graph = {
        "declarations": [
            {
                "declaration": "Pkg.Owner.target",
                "module": "Pkg.Owner",
            }
        ]
    }
    return dag, source_index, graph, declaration.identifier


def test_audit_registration_cites_canonical_module_and_declarations(
    tmp_path: Path,
) -> None:
    dag, source_index, graph, declaration_id = _canonical_audit_fixture(tmp_path)

    attach_audit_producer_registrations(dag, source_index, graph)

    registration = next(iter(dag["auditProducerRegistrations"]["producers"].values()))
    assert registration["evidenceRefs"] == [
        "#/sections/module_dag/audit_surfaces/0/auditCommands/0",
        "#/sections/module_dag/module_metadata/Pkg.Audit",
        f"source-index:declaration:{declaration_id}",
        "#/sections/declaration_graph/declarations/0",
    ]
    assert registration["authority"] == ("lexical_text_and_lean_environment")
    assert dag["audit_command_coverage"]["completeness"] == "complete"


def test_audit_registration_suppresses_each_dangling_claim(
    tmp_path: Path,
) -> None:
    dag, source_index, graph, _ = _canonical_audit_fixture(tmp_path)
    dangling_rows = []

    missing_module = deepcopy(dag)
    del missing_module["module_metadata"]["Pkg.Audit"]
    dangling_rows.append((missing_module, graph))

    missing_lexical = deepcopy(dag)
    command = missing_lexical["audit_surfaces"][0]["auditCommands"][0]
    command["candidateMatches"][0]["id"] = "missing-declaration"
    dangling_rows.append((missing_lexical, graph))

    missing_lean = deepcopy(dag)
    dangling_rows.append((missing_lean, {"declarations": []}))

    for candidate, declaration_graph in dangling_rows:
        attach_audit_producer_registrations(
            candidate,
            source_index,
            declaration_graph,
        )
        assert candidate["auditProducerRegistrations"]["producers"] == {}
        command_coverage = candidate["audit_command_coverage"]
        assert {
            "visible": command_coverage["visible"],
            "total": command_coverage["total"],
            "omitted": command_coverage["omitted"],
            "completeness": command_coverage["completeness"],
        } == {
            "visible": 1,
            "total": 1,
            "omitted": 0,
            "completeness": "complete",
        }


def test_unresolved_lean_query_does_not_invent_or_require_declaration_ref(
    tmp_path: Path,
) -> None:
    dag, source_index, _, _ = _canonical_audit_fixture(tmp_path)
    command = dag["audit_surfaces"][0]["auditCommands"][0]
    command.update(
        {
            "candidateStatus": "unresolved",
            "candidateMatchCount": 0,
            "candidateMatches": [],
            "candidateDeclarationId": None,
            "candidateReferencedDeclaration": None,
            "candidateReferencedOwner": None,
            "referencedDeclaration": None,
            "referencedOwner": None,
        }
    )

    attach_audit_producer_registrations(
        dag,
        source_index,
        {"declarations": []},
    )

    registration = next(iter(dag["auditProducerRegistrations"]["producers"].values()))
    assert registration["evidenceRefs"] == [
        "#/sections/module_dag/audit_surfaces/0/auditCommands/0",
        "#/sections/module_dag/module_metadata/Pkg.Audit",
    ]
