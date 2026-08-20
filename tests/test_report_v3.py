from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from ladon.inspection_report_adapter import report_dataset
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_contract import (
    ExtensionEnvelope,
    PhaseEnvelope,
    ReportModelError,
)
from ladon.report_model import ReportV2
from ladon.report_v2 import (
    REPORT_VERSION,
    load_report_schema,
    serialize_report_bytes,
)
from ladon.report_v3 import (
    REPORT_V3_VERSION,
    ReportV3SizeLimitError,
    build_report_v3,
    load_report_v3_schema,
    serialize_report_v3_bytes,
    write_report_v3_file,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"


def canonical_model() -> ReportV2:
    """Return an analyzed v2 model that v3 can project without rerunning."""

    return run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
        )
    ).to_report_model()


def model_with_large_payload() -> ReportV2:
    """Return a model with enough evidence to distinguish all projections."""

    model = canonical_model()
    module_payload = {
        "payload_marker": "module-payload-owned-once",
        "module_count": 500,
        "rows": [
            {
                "module": f"Fixture.Module{index:04d}",
                "imports": [f"Fixture.Shared{index % 17:02d}"],
                "source_bytes": 4096 + index,
            }
            for index in range(500)
        ],
    }
    proof_payload = {
        "payload_marker": "extension-payload-owned-once",
        "rows": [{"subject": f"Fixture.proof{index:04d}"} for index in range(200)],
    }
    phases = dict(model.phases)
    phases["module_dag"] = PhaseEnvelope.complete(
        "module_dag",
        required=True,
        data=module_payload,
        counters={"modules": 500},
    )
    phases["proof_xray"] = PhaseEnvelope.complete(
        "proof_xray",
        data=proof_payload,
        counters={"rows": 200},
    )
    extensions = dict(model.extensions)
    extensions["proof_xray"] = ExtensionEnvelope(
        namespace="proof_xray",
        version="1",
        status="complete",
        authority="capability-owner",
        payload=proof_payload,
    )
    return replace(model, phases=phases, extensions=extensions)


def model_with_declarations() -> ReportV2:
    """Return declaration rows carrying deliberately repeated evidence."""

    model = canonical_model()
    common_surface = {
        "authority": "lean_environment",
        "confidence": "direct",
        "nonclaim": "Navigation evidence only; not theorem truth.",
        "trustFacts": [
            {
                "kind": "direct_reference",
                "authority": "lean_environment",
                "nonclaim": "Direct only; not transitive closure.",
            }
        ],
    }
    declarations = [
        {
            "declaration": f"Fixture.theorem{index}",
            "module": "Fixture",
            "authority": "lean_environment",
            "confidence": "direct",
            "nonclaim": "Navigation evidence only; not theorem truth.",
            "surface": common_surface,
        }
        for index in range(3)
    ]
    graph = {
        "declaration_count": len(declarations),
        "declarations": declarations,
        "edges": [],
        "elaborated_edges": [],
        "elaborated_surface": {"status": "complete", "row_count": 3},
    }
    phases = dict(model.phases)
    phases["declaration_graph"] = PhaseEnvelope.complete(
        "declaration_graph",
        data=graph,
    )
    extensions = dict(model.extensions)
    extensions["elaborated_declarations"] = ExtensionEnvelope(
        namespace="elaborated_declarations",
        version="1",
        status="complete",
        authority="lean-environment-direct",
        payload={
            "summary": graph["elaborated_surface"],
            "declarations": declarations,
            "edges": graph["elaborated_edges"],
            "caps": {"statementBytes": 1024},
        },
    )
    return replace(model, phases=phases, extensions=extensions)


def v3_validator() -> Draft202012Validator:
    """Return the checked packaged v3 validator."""

    schema = load_report_v3_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def pre_integrity_v3_payload(projection: str) -> dict[str, Any]:
    """Return the original v3 shape before additive integrity envelopes."""

    payload = build_report_v3(
        canonical_model(),
        projection=projection,
    ).to_dict()
    payload.pop("coverage")
    payload.pop("snapshot")
    for omission in payload["projection"]["omissions"]:
        omission.pop("coverageRef", None)
    return payload


@pytest.mark.parametrize("projection", ["summary", "review", "full"])
def test_packaged_schema_validates_every_projection(projection: str) -> None:
    report = build_report_v3(
        model_with_large_payload(),
        projection=projection,
        summary_item_limit=5,
        review_item_limit=30,
    )

    v3_validator().validate(report.to_dict())

    assert report.payload["metadata"]["report_version"] == REPORT_V3_VERSION
    assert report.payload["metadata"]["source_report_version"] == REPORT_VERSION
    assert report.payload["projection"]["name"] == projection


@pytest.mark.parametrize("projection", ["summary", "review", "full"])
def test_schema_accepts_pre_integrity_v3_payload(projection: str) -> None:
    payload = pre_integrity_v3_payload(projection)

    v3_validator().validate(payload)

    assert "coverage" not in payload
    assert "snapshot" not in payload
    assert all(
        "coverageRef" not in omission
        for omission in payload["projection"]["omissions"]
    )


def test_pre_integrity_v3_reader_keeps_missing_coverage_unknown() -> None:
    dataset = report_dataset(pre_integrity_v3_payload("full"), "modules")

    assert dataset.rows
    assert dataset.coverage["totalKnown"] is False
    assert dataset.coverage["total"] is None
    assert dataset.coverage["omitted"] is None
    assert dataset.coverage["completeness"] == "partial"
    assert dataset.artifact.source_fingerprint is None


def test_payloads_have_one_owner_and_envelopes_only_reference_them() -> None:
    report = build_report_v3(model_with_large_payload(), projection="full")
    payload = report.to_dict()
    content = serialize_report_v3_bytes(report).content

    assert content.count(b"module-payload-owned-once") == 1
    assert content.count(b"extension-payload-owned-once") == 1
    assert payload["phases"]["module_dag"]["payloadRef"] == ("#/sections/module_dag")
    assert payload["pipeline"]["timings"]["module_dag"]["payloadRef"] == (
        "#/sections/module_dag"
    )
    assert payload["extensions"]["proof_xray"]["payloadRef"] == (
        "#/sections/proof_xray"
    )
    assert "data" not in payload["phases"]["module_dag"]
    assert "data" not in payload["pipeline"]["timings"]["module_dag"]
    assert "payload" not in payload["extensions"]["proof_xray"]


@pytest.mark.parametrize("projection", ["summary", "review", "full"])
def test_every_payload_reference_resolves_in_each_projection(
    projection: str,
) -> None:
    payload = build_report_v3(
        model_with_declarations(),
        projection=projection,
    ).to_dict()
    references = payload_references(payload)

    assert references
    assert all(
        resolve_json_pointer(payload, reference) is not None for reference in references
    )
    elaborated = payload["extensions"]["elaborated_declarations"]
    assert elaborated["payloadRef"] == "#/sections/declaration_graph"
    assert elaborated["payloadView"]["capsRef"] == (
        "#/sections/elaborated_declaration_caps"
    )
    assert "extension.elaborated_declarations" not in payload["sections"]


def test_projection_sizes_order_and_share_analysis_fingerprint() -> None:
    model = model_with_large_payload()
    reports = {
        projection: build_report_v3(
            model,
            projection=projection,
            summary_item_limit=5,
            review_item_limit=30,
        )
        for projection in ("summary", "review", "full")
    }
    sizes = {
        name: len(serialize_report_v3_bytes(report).content)
        for name, report in reports.items()
    }

    assert sizes["summary"] < sizes["review"] < sizes["full"]
    assert {report.analysis_fingerprint for report in reports.values()} == {
        reports["full"].analysis_fingerprint
    }
    assert reports["summary"].payload["projection"]["omissions"]
    assert reports["review"].payload["projection"]["omissions"]
    assert reports["full"].payload["projection"]["omissions"] == []


def test_declaration_rows_reference_deduplicated_evidence() -> None:
    payload = build_report_v3(
        model_with_declarations(),
        projection="full",
    ).to_dict()
    graph = payload["sections"]["declaration_graph"]
    rows = graph["declarations"]
    evidence = graph["_declarationEvidence"]

    assert len(evidence) == 1
    assert len({row["evidenceRef"] for row in rows}) == 1
    assert all(not repeated_evidence_keys(row) for row in rows)
    assert {
        value
        for entry in evidence.values()
        for value in entry["fields"].values()
        if isinstance(value, str)
    } >= {
        "lean_environment",
        "direct",
        "Navigation evidence only; not theorem truth.",
    }

    review_payload = build_report_v3(
        model_with_declarations(),
        projection="review",
        summary_item_limit=2,
        review_item_limit=2,
    ).to_dict()
    review = review_payload["sections"]["declaration_graph"]
    assert len(review["declarations"]) == 2
    assert all(
        resolve_json_pointer(review_payload, row["evidenceRef"])
        for row in review["declarations"]
    )


def test_analysis_fingerprint_normalizes_registered_runtime_fields() -> None:
    first = model_with_large_payload()
    second_phases = dict(first.phases)
    source = first.phases["module_dag"]
    second_data = dict(source.data)
    second_data["helperElapsedSeconds"] = 42.0
    first_data = dict(source.data)
    first_data["helperElapsedSeconds"] = 1.0
    first_phases = dict(first.phases)
    first_phases["module_dag"] = replace(
        source,
        elapsed_seconds=1.0,
        data=first_data,
    )
    second_phases["module_dag"] = replace(
        source,
        elapsed_seconds=99.0,
        data=second_data,
    )

    first_report = build_report_v3(
        replace(first, phases=first_phases),
        projection="full",
    )
    second_report = build_report_v3(
        replace(first, phases=second_phases),
        projection="full",
    )

    assert first_report.analysis_fingerprint == second_report.analysis_fingerprint
    assert serialize_report_v3_bytes(first_report).content != (
        serialize_report_v3_bytes(second_report).content
    )


def test_analysis_fingerprint_does_not_normalize_user_cache_names() -> None:
    model = canonical_model()
    source = model.phases["module_dag"]
    first_data = {
        **dict(source.data or {}),
        "module_metadata": {"Pkg.Cache": {"path": "one.lean", "lineCount": 1}},
    }
    second_data = {
        **dict(source.data or {}),
        "module_metadata": {"Pkg.Cache": {"path": "two.lean", "lineCount": 999}},
    }
    first_phases = {
        **model.phases,
        "module_dag": replace(source, data=first_data),
    }
    second_phases = {
        **model.phases,
        "module_dag": replace(source, data=second_data),
    }

    first = build_report_v3(replace(model, phases=first_phases))
    second = build_report_v3(replace(model, phases=second_phases))

    assert first.analysis_fingerprint != second.analysis_fingerprint


def test_bounded_bytes_and_atomic_file_leave_destination_intact(
    tmp_path: Path,
) -> None:
    report = build_report_v3(model_with_large_payload(), projection="review")
    unbounded = serialize_report_v3_bytes(report)
    destination = tmp_path / "report.json"
    destination.write_bytes(b"prior-report\n")

    with pytest.raises(ReportV3SizeLimitError, match="configured limit"):
        serialize_report_v3_bytes(report, max_bytes=len(unbounded.content) - 1)
    with pytest.raises(ReportV3SizeLimitError, match="configured limit"):
        write_report_v3_file(
            report,
            destination,
            max_bytes=len(unbounded.content) - 1,
        )

    assert destination.read_bytes() == b"prior-report\n"

    result = write_report_v3_file(
        report,
        destination,
        max_bytes=len(unbounded.content),
    )

    assert result.byte_count == len(unbounded.content)
    assert destination.read_bytes() == unbounded.content
    assert json.loads(destination.read_bytes())["projection"]["name"] == "review"


def test_v2_schema_reader_and_serializer_remain_available() -> None:
    model = canonical_model()
    serialized = serialize_report_bytes(model)
    payload = json.loads(serialized.content)
    validator = Draft202012Validator(load_report_schema())

    validator.validate(payload)

    assert payload["metadata"]["report_version"] == REPORT_VERSION
    assert serialized.warnings
    assert all("disposition" not in phase for phase in payload["phases"].values())
    assert "data" in payload["phases"]["module_dag"]
    assert (
        payload["pipeline"]["timings"]["module_dag"]["data"]
        == (payload["phases"]["module_dag"]["data"])
    )


def test_v3_rejects_frozen_v2_mapping_without_exact_dispositions() -> None:
    with pytest.raises(
        ReportModelError,
        match="cannot preserve terminal phase dispositions",
    ):
        build_report_v3(canonical_model().to_dict())


def repeated_evidence_keys(value: Any) -> set[str]:
    """Find evidence keys that must live outside compact declaration rows."""

    if isinstance(value, list):
        return set().union(*(repeated_evidence_keys(item) for item in value))
    if not isinstance(value, Mapping):
        return set()
    found = set(value) & {"authority", "confidence", "nonclaim", "nonclaims"}
    return found | set().union(
        *(repeated_evidence_keys(item) for item in value.values())
    )


def resolve_json_pointer(payload: Mapping[str, Any], pointer: str) -> Any:
    """Resolve one local RFC 6901 pointer used by the v3 contract."""

    value: Any = payload
    for token in pointer.removeprefix("#/").split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def payload_references(payload: Mapping[str, Any]) -> list[str]:
    """Return non-null payload references from every envelope view."""

    groups = (
        payload["phases"].values(),
        payload["pipeline"]["timings"].values(),
        payload["extensions"].values(),
    )
    return [
        reference
        for rows in groups
        for row in rows
        for reference in [row["payloadRef"]]
        if reference is not None
    ]
