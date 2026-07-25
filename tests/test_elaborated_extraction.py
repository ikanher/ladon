from __future__ import annotations

import json
import threading
from pathlib import Path

from ladon.declaration_surface import (
    MAX_DEPENDENCIES,
    declarations_from_elaborated_payload,
    join_declaration_inventories,
)
from ladon.elaborated_extraction import (
    augment_with_elaborated_surfaces,
    parse_helper_json_suffix,
)
from ladon.extraction import ModuleDiscovery
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.process_supervisor import ProcessCancelled


def helper_payload() -> dict:
    return {
        "version": "2",
        "helperVersion": "ladon-elaborated-helper-v1",
        "leanVersion": "4.32.1",
        "declarations": [
            {
                "fullyQualifiedName": "Root.theorem",
                "kind": "theorem",
                "sourceRange": {
                    "start": {"line": 3, "column": 1},
                    "finish": {"line": 7, "column": 4},
                },
                "status": "complete",
                "renderedType": "∀ {α : Type} [Inhabited α], True → True",
                "renderedTypeBytes": 48,
                "renderedTypeTruncated": False,
                "printerOptions": {
                    "prettyPrinter": "Lean.Meta.ppExpr",
                    "ppAll": False,
                },
                "binders": {
                    "items": [
                        {
                            "name": "α",
                            "binderInfo": "implicit",
                            "typeText": "Type",
                            "isPremise": False,
                        },
                        {
                            "name": "premise",
                            "binderInfo": "explicit",
                            "typeText": "True",
                            "isPremise": True,
                        },
                    ],
                    "total": 2,
                    "truncated": False,
                    "status": "complete",
                },
                "premises": {
                    "items": ["True"],
                    "total": 1,
                    "truncated": False,
                    "status": "complete",
                },
                "conclusion": "True",
                "typeConstants": {
                    "items": ["True", "Inhabited"],
                    "total": 2,
                    "truncated": False,
                    "status": "complete",
                },
                "valueConstants": {
                    "items": [
                        "Root.axiom",
                        "Imported.helper",
                        "sorryAx",
                    ],
                    "total": 3,
                    "truncated": False,
                    "status": "complete",
                },
                "statementExcerpt": {
                    "text": "theorem theorem : True",
                    "totalBytes": 2048,
                    "truncated": True,
                    "status": "complete",
                },
                "statementRange": {
                    "startLine": 3,
                    "startColumn": 1,
                    "endLine": 7,
                    "endColumn": 4,
                },
                "proofRange": {
                    "startLine": 5,
                    "startColumn": 10,
                    "endLine": 7,
                    "endColumn": 4,
                },
                "hasValue": True,
                "proofForm": "environment_value",
                "bodyTotalBytes": 2048,
                "bodyTruncated": True,
                "declaredAxiom": False,
                "unsafe": False,
                "trustFacts": [
                    {
                        "kind": "direct_sorryAx",
                        "scope": "value",
                        "target": "sorryAx",
                    },
                    {
                        "kind": "direct_axiom_reference",
                        "scope": "value",
                        "target": "Root.axiom",
                    },
                ],
                "dependencyModules": [
                    {"name": "Imported.helper", "module": "Imported"},
                    {"name": "sorryAx", "module": "Init.Prelude"},
                ],
            },
            {
                "fullyQualifiedName": "Root.axiom",
                "kind": "axiom",
                "status": "complete",
                "renderedType": "True",
                "binders": {
                    "items": [],
                    "total": 0,
                    "truncated": False,
                    "status": "complete",
                },
                "premises": {
                    "items": [],
                    "total": 0,
                    "truncated": False,
                    "status": "complete",
                },
                "typeConstants": {
                    "items": ["True"],
                    "total": 1,
                    "truncated": False,
                    "status": "complete",
                },
                "valueConstants": {
                    "items": [],
                    "total": 0,
                    "truncated": False,
                    "status": "complete",
                },
                "statementExcerpt": {
                    "text": "axiom axiom : True",
                    "totalBytes": 18,
                    "truncated": False,
                    "status": "complete",
                },
                "hasValue": False,
                "declaredAxiom": True,
                "unsafe": False,
                "trustFacts": [
                    {"kind": "declared_axiom", "scope": "declaration"}
                ],
            },
        ],
    }


def test_normalization_keeps_parser_and_elaborated_authorities_separate() -> None:
    parser = {
        "Root.theorem": LeanDeclaration(
            name="Root.theorem",
            module="Root",
            references=("lexicalGhost",),
        )
    }

    rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        helper_payload(),
        parser_declarations=parser,
        source_content_hash="sha256:source",
    )
    theorem = rows["Root.theorem"]

    assert_separate_authorities(theorem)
    assert_statement_surface(theorem)


def assert_separate_authorities(theorem: LeanDeclaration) -> None:
    """Check parser, type, and value facts remain independent."""

    assert theorem.references == ("lexicalGhost",)
    assert theorem.parser_candidates.items == ("lexicalGhost",)
    assert theorem.parser_candidates.authority == "lean_parser"
    assert theorem.type_dependencies.items == ("Inhabited", "True")
    assert theorem.value_dependencies.items == (
        "Imported.helper",
        "Root.axiom",
        "sorryAx",
    )
    assert "lexicalGhost" not in theorem.value_dependencies.items


def assert_statement_surface(theorem: LeanDeclaration) -> None:
    """Check the bounded theorem statement decomposition."""

    assert theorem.surface.binders.items[0].binder_info == "implicit"
    assert theorem.surface.premises.items == ("True",)
    assert theorem.surface.conclusion == "True"
    assert theorem.surface.body_truncated is True


def test_normalization_adds_named_imported_stubs_and_direct_trust_rows() -> None:
    rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        helper_payload(),
    )

    assert rows["Imported.helper"].is_imported_stub is True
    assert rows["Imported.helper"].module == "Imported"
    assert rows["Imported.helper"].resolution == "resolved_imported_constant"
    facts = rows["Root.theorem"].surface.trust_facts
    assert [(row.kind, row.scope, row.target) for row in facts] == [
        ("direct_axiom_reference", "value", "Root.axiom"),
        ("direct_sorryAx", "value", "sorryAx"),
    ]
    assert "transitive axiom closure" in facts[0].nonclaim


def test_normalization_retains_lean_compiler_generation_evidence() -> None:
    payload = helper_payload()
    payload["declarations"].append(
        {
            "fullyQualifiedName": "Root._aux_match_1",
            "kind": "def",
            "compilerGenerated": True,
            "sourceRange": {
                "start": {"line": 8, "column": 1},
                "finish": {"line": 8, "column": 12},
            },
        }
    )
    parser = {
        "Root.theorem": LeanDeclaration(
            name="Root.theorem",
            module="Root",
        )
    }

    rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        payload,
        parser_declarations=parser,
        restrict_to_parser_inventory=True,
    )

    generated = rows["Root._aux_match_1"]
    assert generated.compiler_generated is True
    assert generated.compiler_authority == "lean_environment"
    assert generated.compiler_toolchain == "4.32.1"


def test_inventory_join_replaces_stub_by_fully_qualified_name() -> None:
    root_rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        helper_payload(),
    )
    inventory_row = LeanDeclaration(
        name="Imported.helper",
        module="Imported",
        kind="def",
        extraction_backend="lean_elaborated_helper",
        confidence="lean_environment",
    )

    joined = join_declaration_inventories(
        root_rows,
        {"Imported.helper": inventory_row},
    )

    assert joined["Imported.helper"].is_imported_stub is False
    assert joined["Imported.helper"].kind == "def"


def test_older_payload_normalizes_to_explicit_unavailable_surfaces() -> None:
    rows = declarations_from_elaborated_payload(
        "Old",
        "Old.lean",
        {
            "version": "1",
            "declarations": [
                {"fullyQualifiedName": "Old.value", "kind": "def"}
            ],
        },
    )
    row = rows["Old.value"]

    assert row.surface.status == "unavailable"
    assert row.surface.reason
    assert row.type_dependencies.status == "unavailable"
    assert row.value_dependencies.status == "unavailable"
    assert row.parser_candidates.status == "unavailable"


def test_dependency_collections_are_sorted_deduplicated_and_capped() -> None:
    payload = helper_payload()
    values = [f"Dep.{index:03d}" for index in reversed(range(80))]
    values.extend(["Dep.010", "Dep.011"])
    payload["declarations"][0]["valueConstants"] = {
        "items": values,
        "total": 82,
        "truncated": False,
        "status": "complete",
    }

    rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        payload,
    )
    dependencies = rows["Root.theorem"].value_dependencies

    assert len(dependencies.items) == MAX_DEPENDENCIES
    assert dependencies.items == tuple(sorted(dependencies.items))
    assert dependencies.total == 82
    assert dependencies.truncated is True


def test_parser_inventory_filters_frontend_generated_auxiliary_constants() -> None:
    payload = helper_payload()
    payload["declarations"].append(
        {
            "fullyQualifiedName": "Root._aux_generated",
            "kind": "def",
            "status": "complete",
        }
    )
    parser = {
        name: LeanDeclaration(name=name, module="Root")
        for name in ("Root.theorem", "Root.axiom")
    }

    rows = declarations_from_elaborated_payload(
        "Root",
        "Root.lean",
        payload,
        parser_declarations=parser,
        restrict_to_parser_inventory=True,
    )

    assert "Root.theorem" in rows
    assert "Root.axiom" in rows
    assert "Root._aux_generated" not in rows


def test_helper_json_parser_accepts_lean_warning_prefix() -> None:
    payload = helper_payload()
    stdout = "Fixture.lean:1:0: warning: fixture warning\n" + json.dumps(payload)

    assert parse_helper_json_suffix(stdout) == payload


def test_helper_failure_preserves_runtime_and_marks_surface_unavailable(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Root.lean"
    source.write_text(
        "theorem root : True := True.intro\n#check Root.root\n",
        encoding="utf-8",
    )
    discovery = ModuleDiscovery(
        repo_root=tmp_path,
        analysis_root_file=source,
        analysis_root_module="Root",
        inventory_root="Root",
        modules={"Root": LeanModule("Root", "Root.lean")},
    )
    declaration = LeanDeclaration(name="Root.root", module="Root")
    bundle = ExtractionBundle(
        modules=discovery.modules,
        declarations={declaration.name: declaration},
        counters={"requested": 1},
        diagnostics=(
            {
                "id": "existing",
                "severity": "warning",
                "message": "existing diagnostic",
                "subject": "Root",
            },
        ),
        runtime={"protocolVersion": "ladon-lean-batch-v1"},
    )

    def fail_helper(*_args, **_kwargs):
        raise RuntimeError("fixture elaboration failed")

    monkeypatch.setattr(
        "ladon.elaborated_extraction.run_elaborated_helper",
        fail_helper,
    )
    result = augment_with_elaborated_surfaces(discovery, bundle)

    assert result.runtime == bundle.runtime
    assert result.counters["requested"] == 1
    assert result.counters["elaborated_failed"] == 1
    assert len(result.diagnostics) == 2
    surface = result.declarations["Root.root"].surface
    assert surface.status == "unavailable"
    assert surface.reason == "fixture elaboration failed"
    query = next(iter(result.audit_queries.values()))
    assert query.status == "unavailable"
    assert query.reason == "fixture elaboration failed"
    assert query.subject == "Root.root"


def test_elaborated_cancellation_preserves_rows_and_stops_remaining_work(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / "Root.lean"
    source.write_text("theorem root : True := True.intro\n", encoding="utf-8")
    discovery = ModuleDiscovery(
        repo_root=tmp_path,
        analysis_root_file=source,
        analysis_root_module="Root",
        inventory_root="Root",
        modules={"Root": LeanModule("Root", "Root.lean")},
    )
    cancel = threading.Event()
    observed: list[threading.Event | None] = []

    def cancelled_helper(*_args, **kwargs):
        observed.append(kwargs.get("cancel_event"))
        raise ProcessCancelled("watchdog cancellation")

    monkeypatch.setattr(
        "ladon.elaborated_extraction.run_elaborated_helper",
        cancelled_helper,
    )

    result = augment_with_elaborated_surfaces(
        discovery,
        ExtractionBundle(modules=discovery.modules),
        cancel_event=cancel,
    )

    assert observed == [cancel]
    assert result.counters["elaborated_failed"] == 1
    assert result.diagnostics[-1]["id"] == "lean.elaborated_surface_cancelled"
