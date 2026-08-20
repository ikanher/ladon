from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from ladon.cli import main
from ladon.configuration import (
    policy_fingerprint_options,
    resolve_policy_configuration,
)
from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_models import (
    INSPECTION_NOUNS,
    InspectionCompatibilityError,
    InspectionInvocationError,
    InspectionNotFoundError,
)
from ladon.inspection_query import inspect_dataset
from ladon.pipeline import RunContext, run_pipeline
from ladon.report_v3 import build_report_v3
from ladon.source_index import build_source_index

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "tiny_lean"
INSPECTION_FIXTURE_ROOT = (
    Path(__file__).parent / "fixtures" / "inspection_lean"
)


def inspection_index_payload() -> dict:
    payload = build_source_index(
        INSPECTION_FIXTURE_ROOT,
        use_cache=False,
    ).index.to_payload()
    module = payload["entries"][0]["module"]
    module["optionRows"] = [
        {
            "id": "option:tiny:pp-universes",
            "module": "Tiny",
            "path": "Tiny.lean",
            "sourceRange": source_range(1, 1),
            "option": "pp.universes",
            "optionClass": "generic",
            "lexicalScope": "module",
            "status": "parsed",
            "authority": "lexical_text",
            "nonclaim": "Configured option only.",
        }
    ]
    module["resourceSettings"] = [
        {
            "id": "resource:tiny:finite",
            "module": "Tiny",
            "path": "Tiny.lean",
            "sourceRange": source_range(1, 1),
            "option": "maxRecDepth",
            "numericValue": 1000000,
            "normalizedMeaning": "finite",
            "lexicalScope": "module",
            "status": "parsed",
            "authority": "lexical_text",
        },
        {
            "id": "resource:tiny:unlimited",
            "module": "Tiny",
            "path": "Tiny.lean",
            "sourceRange": source_range(2, 1),
            "option": "maxHeartbeats",
            "numericValue": 0,
            "normalizedMeaning": "unlimited",
            "lexicalScope": "declaration",
            "status": "parsed",
            "authority": "lexical_text",
        },
    ]
    module["proofMechanisms"] = [proof_mechanism(index) for index in range(3)]
    module["proofMechanisms"].append(
        {
            "id": "mechanism:aggregate:simp",
            "module": "Tiny",
            "mechanism": "simp",
            "kind": "aggregate",
            "aggregate": True,
            "memberIds": ["mechanism:tiny:0", "mechanism:tiny:1"],
            "status": "complete",
            "authority": "lexical_text",
        }
    )
    return payload


def proof_mechanism(index: int) -> dict:
    return {
        "id": f"mechanism:tiny:{index}",
        "module": "Tiny",
        "path": "Tiny.lean",
        "sourceRange": source_range(index + 1, 3),
        "declaration": "Tiny.example",
        "mechanism": "simp",
        "kind": "tactic-token",
        "status": "observed",
        "authority": "lexical_text",
    }


def source_range(line: int, column: int) -> dict:
    return {
        "start": {"line": line, "column": column, "offset": line - 1},
        "end": {"line": line, "column": column + 1, "offset": line},
    }


def write_index(path: Path, payload: dict | None = None) -> dict:
    selected = payload or inspection_index_payload()
    path.write_text(
        json.dumps(selected, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return selected


@pytest.mark.parametrize("noun", INSPECTION_NOUNS)
def test_every_noun_adapts_stable_canonical_rows(
    tmp_path: Path,
    noun: str,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)

    dataset = load_inspection_dataset(
        index,
        noun,
        artifact_kind="source-index",
    )
    first = inspect_dataset(dataset, limit=20).to_dict()
    repeated = inspect_dataset(dataset, limit=20).to_dict()

    assert first == repeated
    assert first["schema"] == "ladon-inspection-page-v1"
    assert first["rows"]
    assert first["coverage"]["collection"]["sourceFingerprint"]
    assert all(canonical_source_row(row) for row in first["rows"])


def test_real_audit_artifact_is_inspectable_after_source_is_removed(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    source = repository / "Audit.lean"
    source.write_text("#check Nat\n", encoding="utf-8")
    payload = build_source_index(repository, use_cache=False).index.to_payload()
    index = tmp_path / "source-index.json"
    index.write_text(json.dumps(payload), encoding="utf-8")
    source.unlink()

    page = inspect_dataset(
        load_inspection_dataset(
            index,
            "audits",
            artifact_kind="source-index",
        )
    ).to_dict()

    assert page["coverage"]["collection"]["id"] == "source_index.audits"
    assert page["coverage"]["collection"]["completeness"] == "complete"
    assert [row["fields"]["subject"] for row in page["rows"]] == ["Nat"]
    assert page["rows"][0]["id"].startswith("ladon.audit.")


def canonical_source_row(row: dict) -> bool:
    """Return whether one source-index projection retains its owner fields."""

    return bool(
        row["id"]
        and row["canonicalRef"].startswith("#/entries/")
        and row["authority"]
        and row["population"]
        and row["coverageRef"]
    )


def test_filters_normalize_order_and_pages_are_disjoint_exhaustive(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    dataset = load_inspection_dataset(
        index,
        "proof-mechanisms",
        artifact_kind="source-index",
    )
    filters = (("kind", "tactic-token"), ("module", "Tiny"))
    first = inspect_dataset(dataset, filters=filters, limit=1)
    equivalent = inspect_dataset(
        dataset,
        filters=tuple(reversed(filters)),
        limit=1,
    )

    assert first.query.fingerprint == equivalent.query.fingerprint
    assert first.next_cursor == equivalent.next_cursor
    pages = [first]
    while pages[-1].next_cursor is not None:
        pages.append(
            inspect_dataset(
                dataset,
                filters=tuple(reversed(filters)),
                cursor=pages[-1].next_cursor,
                limit=1,
            )
        )
    identifiers = [row.identifier for page in pages for row in page.rows]
    assert identifiers == [
        "mechanism:tiny:0",
        "mechanism:tiny:1",
        "mechanism:tiny:2",
    ]
    assert len(identifiers) == len(set(identifiers))
    assert all(page.matching_total == 3 for page in pages)


def test_late_declaration_and_exact_id_remain_reachable(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    dataset = load_inspection_dataset(
        index,
        "declarations",
        artifact_kind="source-index",
    )
    first = inspect_dataset(dataset, limit=2)
    assert first.next_cursor is not None
    late = inspect_dataset(
        dataset,
        cursor=first.next_cursor,
        limit=2,
    )
    assert len(late.rows) == 1

    selected = inspect_dataset(
        dataset,
        identifier=late.rows[0].identifier,
    )
    assert selected.rows == late.rows
    with pytest.raises(InspectionNotFoundError, match="not found"):
        inspect_dataset(dataset, identifier="ladon.absent")


def test_cursor_rejects_artifact_query_and_limit_drift(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    payload = write_index(first_path)
    first_dataset = load_inspection_dataset(
        first_path,
        "proof-mechanisms",
        artifact_kind="source-index",
    )
    first = inspect_dataset(first_dataset, limit=1)
    assert first.next_cursor is not None

    payload["entries"][0]["module"]["tags"].append("changed-artifact")
    write_index(second_path, payload)
    changed_dataset = load_inspection_dataset(
        second_path,
        "proof-mechanisms",
        artifact_kind="source-index",
    )
    with pytest.raises(
        InspectionCompatibilityError,
        match="artifactFingerprint",
    ):
        inspect_dataset(
            changed_dataset,
            cursor=first.next_cursor,
            limit=1,
        )
    with pytest.raises(
        InspectionCompatibilityError,
        match="queryFingerprint",
    ):
        inspect_dataset(
            first_dataset,
            filters=(("kind", "aggregate"),),
            cursor=first.next_cursor,
            limit=1,
        )
    with pytest.raises(InspectionCompatibilityError, match="limit"):
        inspect_dataset(first_dataset, cursor=first.next_cursor, limit=2)


def test_artifact_identity_layers_reject_internal_fingerprint_mismatch(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    payload = inspection_index_payload()
    payload["fingerprint"] = "0" * 64
    write_index(index, payload)
    with pytest.raises(
        InspectionCompatibilityError,
        match="does not match its manifest",
    ):
        load_inspection_dataset(
            index,
            "modules",
            artifact_kind="source-index",
        )

    model = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    report_payload = build_report_v3(model, projection="full").to_dict()
    collection = next(iter(report_payload["coverage"]["collections"].values()))
    collection["analysisFingerprint"] = "sha256:incompatible"
    report = tmp_path / "report.json"
    report.write_text(json.dumps(report_payload), encoding="utf-8")
    with pytest.raises(
        InspectionCompatibilityError,
        match="analysis fingerprints",
    ):
        load_inspection_dataset(
            report,
            "modules",
            artifact_kind="report",
        )


def test_invalid_filters_and_lookup_combinations_fail_closed(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    dataset = load_inspection_dataset(
        index,
        "declarations",
        artifact_kind="source-index",
    )

    with pytest.raises(InspectionInvocationError, match="supported filters"):
        inspect_dataset(dataset, filters=(("mystery", "value"),))
    with pytest.raises(InspectionInvocationError, match="cannot be combined"):
        inspect_dataset(
            dataset,
            identifier=dataset.rows[0].identifier,
            filters=(("kind", "def"),),
        )


def test_resource_pressure_has_no_implicit_finite_threshold(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    dataset = load_inspection_dataset(
        index,
        "resources",
        artifact_kind="source-index",
    )
    rows = {row.identifier: row.to_dict() for row in dataset.rows}

    assert rows["resource:tiny:finite"]["fields"]["pressure"] == ("navigation_only")
    assert rows["resource:tiny:unlimited"]["fields"]["pressure"] == "unlimited"
    assert all("measured runtime" in row["nonclaims"][0] for row in rows.values())


def test_real_source_index_audit_row_remains_lexical_without_enrichment(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    payload = inspection_index_payload()
    write_index(index, payload)

    row = inspect_dataset(
        load_inspection_dataset(
            index,
            "audits",
            artifact_kind="source-index",
        )
    ).to_dict()["rows"][0]

    assert row["authority"] == "lexical_text"
    assert row["fields"]["subject"] == "Tiny.Core.coreTruth"
    assert row["enrichments"] == []


def test_aggregate_has_no_fabricated_anchor_and_links_bounded_members(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    dataset = load_inspection_dataset(
        index,
        "proof-mechanisms",
        artifact_kind="source-index",
    )
    aggregate = inspect_dataset(
        dataset,
        identifier="mechanism:aggregate:simp",
    ).to_dict()["rows"][0]

    assert aggregate["sourceAnchor"]["status"] == "unavailable"
    assert "no single" in aggregate["sourceAnchor"]["reason"]
    assert [row["id"] for row in aggregate["related"][1:]] == [
        "mechanism:tiny:0",
        "mechanism:tiny:1",
    ]


def test_supported_empty_additive_collection_is_exactly_empty(
    tmp_path: Path,
) -> None:
    index = tmp_path / "index.json"
    payload = build_source_index(
        INSPECTION_FIXTURE_ROOT,
        use_cache=False,
    ).index.to_payload()
    write_index(index, payload)

    page = inspect_dataset(
        load_inspection_dataset(
            index,
            "options",
            artifact_kind="source-index",
        )
    ).to_dict()

    assert page["rows"] == []
    assert page["coverage"]["collection"]["totalKnown"] is True
    assert page["coverage"]["collection"]["total"] == 0
    assert page["coverage"]["collection"]["completeness"] == "complete"
    assert page["diagnostics"] == []
    dataset = load_inspection_dataset(
        index,
        "options",
        artifact_kind="source-index",
    )
    with pytest.raises(
        InspectionNotFoundError,
        match="not found",
    ):
        inspect_dataset(dataset, identifier="option:absent")


def test_live_binding_accepts_exact_snapshot_then_rejects_source_drift(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE_ROOT, repository)
    payload = build_source_index(repository, use_cache=False).index.to_payload()
    index = tmp_path / "index.json"
    write_index(index, payload)

    selected = load_inspection_dataset(
        index,
        "modules",
        artifact_kind="source-index",
        repo_root=repository,
    )
    assert selected.artifact.live_fingerprint == payload["fingerprint"]

    (repository / "Tiny.lean").write_text(
        "import Tiny.Core\nimport Tiny.Helper\n\ndef changed := true\n",
        encoding="utf-8",
    )
    with pytest.raises(InspectionCompatibilityError, match="stale"):
        load_inspection_dataset(
            index,
            "modules",
            artifact_kind="source-index",
            repo_root=repository,
        )


def test_live_binding_re_resolves_explicit_policy_configuration(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    shutil.copytree(FIXTURE_ROOT, repository)
    policy = repository / "policy.json"
    policy.write_text(
        json.dumps({"id": "initial", "patterns": []}),
        encoding="utf-8",
    )
    policies = resolve_policy_configuration(
        repository,
        source_pattern_policy=policy,
    )
    payload = build_source_index(
        repository,
        options=policy_fingerprint_options(policies),
        use_cache=False,
    ).index.to_payload()
    index = tmp_path / "index.json"
    write_index(index, payload)

    selected = load_inspection_dataset(
        index,
        "modules",
        artifact_kind="source-index",
        repo_root=repository,
    )
    assert selected.artifact.live_fingerprint == payload["fingerprint"]

    policy.write_text(
        json.dumps({"id": "changed", "patterns": []}),
        encoding="utf-8",
    )
    with pytest.raises(
        InspectionCompatibilityError,
        match="live configuration fingerprint",
    ):
        load_inspection_dataset(
            index,
            "modules",
            artifact_kind="source-index",
            repo_root=repository,
        )


def test_artifact_only_cli_is_checkout_independent_and_starts_no_process(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = tmp_path / "index.json"
    write_index(index)

    def forbidden_process(*_args, **_kwargs):
        raise AssertionError("artifact-only inspection started a process")

    monkeypatch.setattr(subprocess, "run", forbidden_process)
    monkeypatch.setattr(subprocess, "Popen", forbidden_process)
    monkeypatch.chdir(tmp_path)
    status = main(
        [
            "inspect",
            "modules",
            "--source-index",
            str(index),
            "--format",
            "json",
        ]
    )

    captured = capsys.readouterr()
    assert status == 0
    assert json.loads(captured.out)["artifact"]["kind"] == "source-index"
    assert captured.err == ""


def test_cli_text_and_json_render_the_same_page(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = tmp_path / "index.json"
    write_index(index)
    arguments = [
        "inspect",
        "proof-mechanisms",
        "--source-index",
        str(index),
        "--filter",
        "kind=tactic-token",
        "--limit",
        "2",
    ]

    assert main([*arguments, "--format", "json"]) == 0
    machine_capture = capsys.readouterr()
    payload = json.loads(machine_capture.out)
    assert main([*arguments, "--format", "text"]) == 0
    text_capture = capsys.readouterr()

    assert machine_capture.err == text_capture.err == ""
    assert f"Rows: {len(payload['rows'])} visible" in text_capture.out
    assert payload["query"]["fingerprint"] in text_capture.out
    assert payload["coverage"]["collection"]["id"] in text_capture.out
    assert all(row["id"] in text_capture.out for row in payload["rows"])
    assert payload["nextCursor"] in text_capture.out


def test_cli_error_classes_keep_stdout_clean(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    index = tmp_path / "index.json"
    write_index(index)

    status = main(
        [
            "inspect",
            "modules",
            "--source-index",
            str(index),
            "--id",
            "module:absent",
        ]
    )
    missing = capsys.readouterr()
    assert status == 1
    assert missing.out == ""
    assert "inspection.id_not_found" in missing.err

    status = main(
        [
            "inspect",
            "modules",
            "--source-index",
            str(index),
            "--filter",
            "kind=theorem",
        ]
    )
    invalid = capsys.readouterr()
    assert status == 2
    assert invalid.out == ""
    assert "supported filters" in invalid.err


def test_report_adapters_preserve_report_coverage_and_source_identity(
    tmp_path: Path,
) -> None:
    model = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    payload = build_report_v3(model, projection="full").to_dict()
    report = tmp_path / "report.json"
    report.write_text(json.dumps(payload), encoding="utf-8")

    for noun in ("modules", "declarations", "imports"):
        page = inspect_dataset(
            load_inspection_dataset(
                report,
                noun,
                artifact_kind="report",
            )
        ).to_dict()
        assert page["rows"]
        assert (
            page["artifact"]["sourceFingerprint"]
            == payload["snapshot"]["sourceIndexFingerprint"]
        )
        assert all(
            row["canonicalRef"].startswith("#/sections/") for row in page["rows"]
        )
    modules = inspect_dataset(
        load_inspection_dataset(
            report,
            "modules",
            artifact_kind="report",
        )
    ).to_dict()
    assert modules["coverage"]["collection"]["id"] == "module_dag.modules"
    assert modules["coverage"]["collection"]["completeness"] == "complete"


def test_report_live_binding_is_rejected_as_an_invocation_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    model = run_pipeline(
        RunContext(
            repo_root=FIXTURE_ROOT,
            requested_root="Tiny.lean",
            source_cache_enabled=False,
        )
    ).to_report_model()
    report = tmp_path / "report.json"
    report.write_text(
        json.dumps(build_report_v3(model).to_dict()),
        encoding="utf-8",
    )

    status = main(
        [
            "inspect",
            "modules",
            "--report",
            str(report),
            "--repo-root",
            str(FIXTURE_ROOT),
        ]
    )
    captured = capsys.readouterr()
    assert status == 2
    assert captured.out == ""
    assert "supported only with --source-index" in captured.err


def test_inspect_help_is_caller_neutral_and_documents_integrity(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["inspect", "--help"])
    captured = capsys.readouterr()

    assert exit_info.value.code == 0
    assert "modules,declarations,imports,audits,options,resources" in captured.out
    assert "--report REPORT | --source-index SOURCE_INDEX" in captured.out
    assert "Cursors are opaque" in captured.out
    assert "LLM" not in captured.out
