from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from ladon.artifact_versions import UnsupportedArtifactVersionError
from ladon.atlas import build_report_atlas
from ladon.atlas_diff import diff_atlases
from ladon.atlas_sqlite import write_atlas_sqlite
from ladon.atlas_workflow import build_atlas_workflow
from ladon.ir import (
    BoundedStrings,
    BoundedText,
    ExtractionBundle,
    LeanDeclaration,
    LeanDeclarationSurface,
    LeanModule,
    LeanTrustFact,
)
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text
from ladon.report_v2 import (
    REPORT_VERSION,
    Diagnostic,
    PhaseEnvelope,
    ReportModelError,
    UnsupportedReportVersionError,
    canonical_json_bytes,
    coerce_report_v2,
    load_report_schema,
    mark_report_phase_required,
    replace_report_phase,
    serialize_report_bytes,
    serialize_v1_json,
    supported_report_view,
    update_report_metadata,
)
from ladon.report_v3 import build_report_v3

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
V1_FIXTURES = Path(__file__).parent / "fixtures" / "report_v1"


def canonical_payload(*, timestamp: str | None = None) -> dict:
    return run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            generated_at_utc=timestamp,
        )
    ).to_report_payload()


def elaborated_payload() -> dict:
    """Return a report with one complete bounded Lean declaration surface."""

    def fake_lean(_context: RunContext, discovery) -> ExtractionBundle:
        target = LeanDeclaration(
            name="Imported.assumption",
            module="Imported",
            kind="axiom",
            is_imported_stub=True,
            resolution="resolved_imported_constant",
        )
        root = complete_surface_declaration()
        return ExtractionBundle(
            modules={
                **discovery.modules,
                "Tiny": LeanModule("Tiny", "Tiny.lean"),
            },
            declarations={root.name: root, target.name: target},
        )

    return run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_lean,
        )
    ).to_report_payload()


def complete_surface_declaration() -> LeanDeclaration:
    """Build one finite declaration IR row for report contract assertions."""

    parser = BoundedStrings(
        items=("lexicalGhost",),
        total=1,
        status="complete",
        reason=None,
        authority="lean_parser",
    )
    dependencies = BoundedStrings(
        items=("Imported.assumption",),
        total=1,
        status="complete",
        reason=None,
        authority="lean_environment",
    )
    surface = LeanDeclarationSurface(
        status="complete",
        reason=None,
        rendered_type="True → True",
        rendered_type_bytes=13,
        printer_options={"prettyPrinter": "Lean.Meta.ppExpr"},
        premises=BoundedStrings(
            items=("True",),
            total=1,
            status="complete",
            reason=None,
        ),
        conclusion="True",
        statement_excerpt=BoundedText(
            text="theorem root : True → True",
            total_bytes=26,
            status="complete",
            reason=None,
        ),
        has_value=True,
        proof_form="environment_value",
        trust_facts=(
            LeanTrustFact(
                kind="direct_axiom_reference",
                scope="value",
                target="Imported.assumption",
            ),
        ),
        helper_version="ladon-elaborated-helper-v1",
        lean_version="4.32.1",
    )
    return LeanDeclaration(
        name="Tiny.root",
        module="Tiny",
        kind="theorem",
        references=("lexicalGhost",),
        source_path="Tiny.lean",
        source_range={"startLine": 1, "endLine": 3},
        content_hash="sha256:fixture",
        extraction_backend="lean_elaborated_helper",
        parser_candidates=parser,
        type_dependencies=BoundedStrings(
            items=(),
            total=0,
            status="complete",
            reason=None,
        ),
        value_dependencies=dependencies,
        surface=surface,
    )


def validator() -> Draft202012Validator:
    schema = load_report_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def emitted_v2_payload(payload: dict) -> dict:
    """Return the explicit compatibility serialization under test."""

    return json.loads(serialize_report_bytes(payload, version="v2").content)


def validate_emitted_v2(payload: dict) -> dict:
    """Validate and return one explicit v2 compatibility payload."""

    emitted = emitted_v2_payload(payload)
    validator().validate(emitted)
    return emitted


def test_packaged_schema_validates_explicit_v2_pipeline_report() -> None:
    payload = canonical_payload()
    emitted = validate_emitted_v2(payload)
    validator().validate(payload)

    assert payload == emitted
    assert emitted["metadata"]["report_version"] == REPORT_VERSION
    assert emitted["metadata"]["generated_at_utc"] is None
    assert emitted["phases"]["build"]["status"] == "skipped"
    assert emitted["phases"]["build"]["required"] is False
    assert "disposition" not in emitted["phases"]["build"]


def test_all_v1_matrix_fixtures_adapt_to_schema_valid_v2() -> None:
    schema_validator = validator()

    for path in sorted(V1_FIXTURES.glob("*.json")):
        source = json.loads(path.read_text(encoding="utf-8"))
        payload = coerce_report_v2(source).to_dict()
        schema_validator.validate(emitted_v2_payload(payload))


def test_emitted_report_matrix_is_schema_valid_and_normalized_deterministic(
    tmp_path: Path,
) -> None:
    def fake_lean(_context: RunContext, discovery) -> ExtractionBundle:
        return ExtractionBundle(modules=discovery.modules, declarations={})

    def contexts() -> list[RunContext]:
        return [
            RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean"),
            RunContext(
                repo_root=FIXTURE_ROOT,
                requested_root="Tiny.lean",
                extraction_backend="lean",
                lean_extractor=fake_lean,
            ),
            RunContext(
                repo_root=FIXTURE_ROOT,
                requested_root="Tiny.lean",
                proof_xray={
                    "artifactKind": "ladon_proof_xray",
                    "schemaVersion": 1,
                    "rows": [],
                },
            ),
            RunContext(
                repo_root=FIXTURE_ROOT,
                requested_root="Tiny.lean",
                packet_dirs=(tmp_path / "missing-packet",),
            ),
        ]

    first = [run_pipeline(context).to_report_payload() for context in contexts()]
    second = [run_pipeline(context).to_report_payload() for context in contexts()]

    for left, right in zip(first, second, strict=True):
        validate_emitted_v2(left)
        validate_emitted_v2(right)
        assert canonical_json_bytes(
            left,
            normalize_timings=True,
        ) == canonical_json_bytes(right, normalize_timings=True)


def test_default_and_explicit_timestamps_follow_volatility_policy() -> None:
    assert canonical_payload()["metadata"]["generated_at_utc"] is None
    assert (
        canonical_payload(timestamp="2026-05-10T00:00:00+00:00")["metadata"][
            "generated_at_utc"
        ]
        == "2026-05-10T00:00:00+00:00"
    )


def test_skipped_phase_preserves_text_reason_not_character_count() -> None:
    payload = canonical_payload()
    phase = payload["phases"]["lean_extraction"]

    assert phase["status"] == "skipped"
    assert phase["reason"] == "text backend selected"
    assert "reason" not in phase["counters"]


def test_invalid_phase_adapter_fails_structurally() -> None:
    result = run_pipeline(
        RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")
    )
    invalid = replace(result, module_dag=[])  # type: ignore[arg-type]

    payload = invalid.to_report_payload()

    assert payload["module_dag"] == {}
    assert payload["phases"]["module_dag"]["status"] == "failed"
    assert (
        payload["phases"]["module_dag"]["diagnostics"][0]["id"]
        == "report.invalid_phase_payload"
    )
    validate_emitted_v2(payload)


def test_registered_extensions_have_explicit_absent_state() -> None:
    extensions = canonical_payload()["extensions"]

    assert set(extensions) == {
        "atlas",
        "elaborated_declarations",
        "packet_evidence",
        "proof_xray",
    }
    assert extensions["atlas"]["status"] == "skipped"
    assert extensions["proof_xray"]["authority"] == "capability-owner"


def test_elaborated_extension_is_schema_valid_bounded_and_text_equivalent() -> None:
    first = elaborated_payload()
    second = elaborated_payload()

    validate_emitted_v2(first)
    normalized = canonical_json_bytes(first, normalize_timings=True)
    assert normalized == canonical_json_bytes(second, normalize_timings=True)
    assert len(normalized) < 256_000
    extension = first["extensions"]["elaborated_declarations"]
    assert extension["status"] == "complete"
    root = next(
        row
        for row in extension["payload"]["declarations"]
        if row["declaration"] == "Tiny.root"
    )
    assert root["surface"]["renderedType"] in render_text(first)
    assert {
        (row["kind"], row["authority"]) for row in extension["payload"]["edges"]
    } == {("value_dependency", "lean_environment")}


def test_v2_omits_additive_v3_rows_while_v3_retains_them() -> None:
    result = run_pipeline(
        RunContext(repo_root=FIXTURE_ROOT, requested_root="Tiny.lean")
    )
    model = result.to_report_model()
    v2 = model.to_dict()
    v3 = build_report_v3(model, projection="full").to_dict()

    for dag in (
        v2["module_dag"],
        v2["phases"]["module_dag"]["data"],
        v2["pipeline"]["timings"]["module_dag"]["data"],
    ):
        assert_v2_additive_fields_omitted(dag)
    assert_v3_additive_fields_retained(v3["sections"]["module_dag"])


def test_v2_omits_v3_audit_candidate_payloads(tmp_path: Path) -> None:
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
    model = run_pipeline(
        RunContext(
            repo_root=tmp_path,
            requested_root="Pkg/Audit.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    v2 = model.to_dict()
    v3_dag = build_report_v3(model, projection="full").to_dict()["sections"][
        "module_dag"
    ]
    forbidden_dag_fields = {
        "auditProducerRegistrations",
        "resourceProducerRegistrations",
        "audit_command_coverage",
        "resource_review_coverage",
    }
    forbidden_command_fields = {
        "candidateMatches",
        "candidateCoverage",
        "candidateDeclarationId",
        "candidateReferencedDeclaration",
        "candidateReferencedOwner",
        "candidateAuthority",
        "candidateSourceIndexFingerprint",
        "candidateNonclaim",
    }

    for dag in (
        v2["module_dag"],
        v2["phases"]["module_dag"]["data"],
        v2["pipeline"]["timings"]["module_dag"]["data"],
    ):
        command = dag["audit_surfaces"][0]["auditCommands"][0]
        assert forbidden_dag_fields.isdisjoint(dag)
        assert forbidden_command_fields.isdisjoint(command)
        assert command["candidateStatus"] == "lexical_candidate"
        assert command["candidateMatchCount"] == 1

    candidate = v3_dag["audit_surfaces"][0]["auditCommands"][0][
        "candidateMatches"
    ][0]
    assert candidate["canonicalRef"].startswith("source-index:declaration:")
    assert "auditProducerRegistrations" in v3_dag


def assert_v2_additive_fields_omitted(dag: Mapping[str, Any]) -> None:
    """Protect the frozen v2 module-DAG wire."""

    assert "declaration_source_shape_coverage" not in dag
    integrity = dag["declaration_integrity"]
    assert "sourceShapeSimilarityCandidates" not in integrity
    assert (
        "declaration_integrity.source_shape_similarities" not in integrity["coverage"]
    )
    assert "inspection_navigation" not in dag
    assert "inspection_option_coverage" not in dag
    assert "inspection_proof_mechanism_coverage" not in dag
    assert "resource_directive_coverage" not in dag
    assert "text_declaration_coverage" not in dag


def assert_v3_additive_fields_retained(v3_dag: Mapping[str, Any]) -> None:
    """Require current v3 reports to retain additive inspection evidence."""

    assert "declaration_source_shape_coverage" in v3_dag
    assert "sourceShapeSimilarityCandidates" in v3_dag["declaration_integrity"]
    assert "inspection_navigation" in v3_dag
    assert "inspection_option_coverage" in v3_dag
    assert "inspection_proof_mechanism_coverage" in v3_dag
    assert "resource_directive_coverage" in v3_dag
    assert "text_declaration_coverage" in v3_dag


def test_unavailable_elaboration_emits_schema_valid_skipped_extension() -> None:
    def fake_lean(_context: RunContext, discovery) -> ExtractionBundle:
        declaration = LeanDeclaration(name="Tiny.root", module="Tiny")
        return ExtractionBundle(
            modules=discovery.modules,
            declarations={declaration.name: declaration},
        )

    payload = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            extraction_backend="lean",
            lean_extractor=fake_lean,
        )
    ).to_report_payload()
    extension = payload["extensions"]["elaborated_declarations"]

    validate_emitted_v2(payload)
    assert extension["status"] == "skipped"
    assert "unavailable" in extension["reason"]


def test_phase_requiredness_and_cli_metadata_round_trip() -> None:
    payload = mark_report_phase_required(
        canonical_payload(),
        "lean_extraction",
    )
    payload = update_report_metadata(
        payload,
        failure_policy={"selectors": ["build"], "matches": []},
    )
    build = PhaseEnvelope.failed(
        "build",
        "lake build failed",
        required=True,
        diagnostics=(
            Diagnostic(
                identifier="build.command_failed",
                severity="error",
                message="lake build exited with status 1",
                phase="build",
            ),
        ),
        data={"command": ["lake", "build"]},
    )

    payload = replace_report_phase(payload, build)

    assert payload["phases"]["lean_extraction"]["required"] is True
    assert payload["phases"]["build"]["required"] is True
    assert payload["phases"]["build"]["status"] == "failed"
    assert payload["metadata"]["failure_policy"]["selectors"] == ["build"]
    validator().validate(payload)
    validate_emitted_v2(payload)


def test_phase_replacement_preserves_valid_data_and_rejects_changed_data() -> None:
    phase = PhaseEnvelope.complete("module_dag", data={"rows": [1, 2]})

    replaced = replace(phase, required=True)

    assert replaced.data is phase.data
    with pytest.raises(ReportModelError, match="JSON-serializable"):
        replace(phase, data={"bad": object()})


def test_phase_constructor_rejects_spoofed_validation_identity() -> None:
    invalid_data = {"bad": object()}

    with pytest.raises(TypeError, match="_validated_data_identity"):
        PhaseEnvelope(  # type: ignore[call-arg]
            name="module_dag",
            status="complete",
            data=invalid_data,
            _validated_data_identity=id(invalid_data),
        )


def test_phase_replacement_revalidates_mutated_shared_data() -> None:
    shared_data = {"rows": [1, 2]}
    phase = PhaseEnvelope.complete("module_dag", data=shared_data)
    shared_data["bad"] = object()

    with pytest.raises(ReportModelError, match="JSON-serializable"):
        replace(phase, required=True)


def test_all_public_v2_mapping_adapters_preserve_frozen_schema() -> None:
    payload = canonical_payload()
    view = supported_report_view(payload, consumer="test")
    required = mark_report_phase_required(payload, "lean_extraction")
    updated = update_report_metadata(
        payload,
        failure_policy={"selectors": [], "matches": []},
    )
    replaced = replace_report_phase(
        payload,
        PhaseEnvelope.skipped("build", "not requested"),
    )

    for candidate in (view, required, updated, replaced):
        assert isinstance(candidate, dict)
        validator().validate(candidate)
        assert all("disposition" not in phase for phase in candidate["phases"].values())
        assert all(
            "disposition" not in phase
            for phase in candidate["pipeline"]["timings"].values()
        )


def test_frozen_v2_schema_rejects_enriched_phase_rows() -> None:
    payload = canonical_payload()
    enriched = coerce_report_v2(payload).phases["build"].to_dict()
    payload["phases"]["build"] = enriched
    payload["pipeline"]["timings"]["build"] = enriched

    errors = list(validator().iter_errors(payload))

    assert len(errors) == 2
    assert all("disposition" in error.message for error in errors)


def test_frozen_v2_round_trip_restores_only_default_typed_dispositions() -> None:
    payload = canonical_payload()
    model = coerce_report_v2(payload)

    assert model.phases["build"].disposition == "skipped"
    assert model.phases["module_dag"].disposition == "complete"
    assert json.loads(serialize_report_bytes(model).content) == payload


def test_normalized_bytes_ignore_registered_phase_and_helper_timings() -> None:
    first = canonical_payload()
    second = canonical_payload()
    first["phases"]["lean_extraction"]["data"] = {
        "helperElapsedSeconds": 1.0,
    }
    second["phases"]["lean_extraction"]["data"] = {
        "helperElapsedSeconds": 2.0,
    }

    assert canonical_json_bytes(first, normalize_timings=True) == canonical_json_bytes(
        second,
        normalize_timings=True,
    )


def test_normalized_resource_wall_time_preserves_limits_and_outcomes() -> None:
    first = canonical_payload()
    second = canonical_payload()
    for payload, wall_time in ((first, 1.0), (second, 2.0)):
        payload["phases"]["module_dag"]["data"]["run_resources"] = {
            "observed": {"observedWallSeconds": wall_time, "moduleCount": 3},
            "limits": {"wallSeconds": 10.0},
            "status": "accepted",
        }
    original = json.loads(json.dumps(second))
    assert canonical_json_bytes(first, normalize_timings=True) == canonical_json_bytes(
        second, normalize_timings=True,
    )
    assert second == original
    second["phases"]["module_dag"]["data"]["run_resources"]["limits"]["wallSeconds"] = 20.0
    assert canonical_json_bytes(first, normalize_timings=True) != canonical_json_bytes(
        second, normalize_timings=True,
    )


def test_text_uses_typed_findings_and_reports_omitted_rows() -> None:
    source = {
        "metadata": {
            "analysis_root_module": "Tiny",
            "repo_root": "/repo",
            "report_version": "clean-core-1",
        },
        "module_dag": {
            "module_count": 1,
            "edge_count": 0,
            "acyclic": True,
            "topological_layer_count": 1,
            "facade_module_count": 0,
        },
        "findings": [
            {
                "kind": "generic.review",
                "severity": "warning",
                "subject": "Tiny",
                "message": "review Tiny",
                "count": 2,
            },
            {
                "kind": "source_pattern.match",
                "severity": "info",
                "subject": "Tiny.lean:1",
                "message": "detail remains in its owner section",
            },
        ],
    }

    text = render_text(source)

    assert "- selected: 2" in text
    assert "- displayed: 1" in text
    assert "- rendered in named sections: 1" in text
    assert "- omitted with inspection route: 0" in text
    assert "inspection route:" in text
    assert "id=finding:generic.review:" in text
    assert "evidence=2 authority=ladon-analysis" in text
    assert "build: skipped" in text


def test_v1_serializer_is_bounded_and_warns_about_information_loss() -> None:
    result = serialize_v1_json(canonical_payload())

    assert result.payload["metadata"]["report_version"] == "clean-core-1"
    assert "phases" not in result.payload
    assert "extensions" not in result.payload
    assert result.warnings
    assert (
        "information" not in result.warnings[0].lower() or "loses" in result.warnings[0]
    )


def test_deterministic_bytes_serialize_existing_payload_without_analysis() -> None:
    payload = canonical_payload(timestamp="2026-05-10T00:00:00+00:00")

    first = serialize_report_bytes(payload)
    second = serialize_report_bytes(payload)

    assert first.content == second.content
    assert json.loads(first.content)["metadata"]["report_version"] == REPORT_VERSION
    assert "phase dispositions" in first.warnings[0]


def test_reader_dispatch_rejects_unknown_major_actionably() -> None:
    payload = canonical_payload()
    payload["metadata"]["report_version"] = "ladon-report-v9"

    with pytest.raises(
        UnsupportedReportVersionError,
        match="atlas cannot read Ladon report version.*supported versions",
    ):
        supported_report_view(payload, consumer="atlas")


def test_atlas_reads_schema_valid_v2(tmp_path: Path) -> None:
    payload = canonical_payload()
    report_path = tmp_path / "reports" / "tiny.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_bytes(serialize_report_bytes(payload, version="v2").content)

    atlas = build_report_atlas(report_path.parent)
    assert atlas["summary"]["reports"] == 1


def test_atlas_reader_rejects_unknown_report_major(tmp_path: Path) -> None:
    payload = canonical_payload()
    payload["metadata"]["report_version"] = "ladon-report-v7"
    report_path = tmp_path / "tiny.json"
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        UnsupportedReportVersionError,
        match="atlas report reader.*ladon-report-v7",
    ):
        build_report_atlas(tmp_path)


def test_derived_readers_reject_unknown_atlas_major(tmp_path: Path) -> None:
    invalid = {"schema": "ladon-report-atlas-v9", "nodes": [], "edges": []}
    valid = {"schema": "ladon-report-atlas-v1", "nodes": [], "edges": []}

    with pytest.raises(UnsupportedArtifactVersionError, match="atlas diff"):
        diff_atlases(invalid, valid)
    with pytest.raises(UnsupportedArtifactVersionError, match="atlas SQLite"):
        write_atlas_sqlite(invalid, tmp_path / "atlas.sqlite")
    with pytest.raises(UnsupportedArtifactVersionError, match="atlas workflow"):
        build_atlas_workflow(invalid)
