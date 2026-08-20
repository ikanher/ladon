#!/usr/bin/env python3
"""Run the non-skippable pinned-Lean declaration-surface acceptance gate."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from ladon.declaration_surface import (
    declarations_from_elaborated_payload,
    join_declaration_inventories,
)
from ladon.elaborated_extraction import run_elaborated_helper, source_hash
from ladon.lean_extraction import (
    declarations_from_helper_payload,
    module_from_helper_payload,
    run_helper,
)
from ladon.pipeline import RunContext, run_pipeline
from ladon.render import render_text
from ladon.report_v2 import (
    ReportV2,
    load_report_schema,
    serialize_report_bytes,
)
from ladon.report_v3 import (
    build_report_v3,
    load_report_v3_schema,
    serialize_report_v3_bytes,
)

EXPECTED_TOOLCHAIN = "4.32.1"


class GateFailure(RuntimeError):
    """Raised when required declaration evidence is absent."""


def build_parser() -> argparse.ArgumentParser:
    """Build the required/optional toolchain interface."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--required",
        action="store_true",
        help="Fail instead of skipping when the pinned Lake toolchain is unavailable.",
    )
    return parser


def project_root() -> Path:
    """Return the repository containing this gate."""

    return Path(__file__).resolve().parents[1]


def fixture_root() -> Path:
    """Return the tracked Lake declaration fixture."""

    return project_root() / "tests" / "fixtures" / "lean_declarations"


def require_toolchain(fixture: Path, required: bool) -> bool:
    """Build the fixture and verify its pinned reference toolchain."""

    lake = shutil.which("lake")
    if lake is None:
        if required:
            raise GateFailure("required executable is unavailable: lake")
        print("lean declaration gate: SKIP: lake is unavailable")
        return False
    version = run_checked([lake, "--version"], fixture).stdout
    if EXPECTED_TOOLCHAIN not in version:
        raise GateFailure(
            f"fixture selected Lean {version.strip()}; expected {EXPECTED_TOOLCHAIN}"
        )
    run_checked([lake, "build"], fixture)
    return True


def run_checked(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run one required command and retain concise failure output."""

    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        details = (result.stderr or result.stdout).strip()
        raise GateFailure(f"{' '.join(command)} failed: {details}")
    return result


def extract_fixture_rows(
    fixture: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run parser and elaborator helpers over the tracked root."""

    source = fixture / "LadonDeclarationFixture.lean"
    parser_payload = run_helper(
        fixture,
        source,
        project_root() / "src" / "ladon" / "lean" / "ladon_parser_helper.lean",
    )
    parser_module = module_from_helper_payload(fixture, source, parser_payload)
    parser_rows = declarations_from_helper_payload(
        parser_module,
        parser_payload,
        source_content_hash=source_hash(source),
    )
    elaborated_payload = run_elaborated_helper(
        fixture,
        source,
        "LadonDeclarationFixture",
    )
    rows = declarations_from_elaborated_payload(
        "LadonDeclarationFixture",
        "LadonDeclarationFixture.lean",
        elaborated_payload,
        parser_declarations=parser_rows,
        source_content_hash=source_hash(source),
        restrict_to_parser_inventory=True,
    )
    return elaborated_payload, rows


def assert_declaration_kinds(rows: Mapping[str, Any]) -> None:
    """Require every packet-declared declaration kind and unsafe flag."""

    expected = {
        "theoremKind": "theorem",
        "definitionKind": "def",
        "axiomKind": "axiom",
        "opaqueKind": "opaque",
        "unsafeKind": "def",
    }
    for suffix, kind in expected.items():
        row = required_row(rows, suffix)
        if row.kind != kind:
            raise GateFailure(f"{suffix} kind is {row.kind!r}, expected {kind!r}")
        if not row.source_range or not row.content_hash:
            raise GateFailure(f"{suffix} lacks source range/hash")
    if required_row(rows, "unsafeKind").surface.unsafe is not True:
        raise GateFailure("unsafeKind lacks Lean-observed unsafe status")


def assert_statement_surface(rows: Mapping[str, Any]) -> None:
    """Require binders, premises, conclusion, and printer provenance."""

    surface = required_row(rows, "structuredStatement").surface
    binder_infos = {row.binder_info for row in surface.binders.items}
    if not {"implicit", "instance_implicit", "explicit"} <= binder_infos:
        raise GateFailure("structuredStatement binder classes are incomplete")
    if surface.premises.items != ("True",) or surface.conclusion != "True":
        raise GateFailure("structuredStatement decomposition is incomplete")
    if not surface.rendered_type or not surface.printer_options:
        raise GateFailure("structuredStatement lacks rendered type provenance")
    notation = required_row(rows, "importedNotation").surface
    if not notation.rendered_type:
        raise GateFailure("imported notation did not retain an elaborated type")


def assert_dependency_split(rows: Mapping[str, Any]) -> None:
    """Require parser/elaborator disagreement and imported-target evidence."""

    row = required_row(rows, "parserElaboratorDisagreement")
    if "lexicalGhost" not in row.parser_candidates.items:
        raise GateFailure("parser disagreement fixture lacks lexicalGhost")
    if "lexicalGhost" in row.value_dependencies.items:
        raise GateFailure("lexicalGhost was incorrectly promoted to a Lean dependency")
    if not {"Nat.zero", "Nat.succ"} <= set(row.value_dependencies.items):
        raise GateFailure("elaborated macro constants are missing")
    imported = "LadonDeclarationFixture.importedDependency"
    root = required_row(rows, "rootUsesImportedDependency")
    if imported not in root.type_dependencies.items:
        raise GateFailure("root-only imported dependency is missing")
    if not rows[imported].is_imported_stub:
        raise GateFailure("root-only imported dependency is not a named stub")


def assert_inventory_join(
    fixture: Path,
    root_rows: Mapping[str, Any],
) -> None:
    """Require deterministic replacement of an imported stub by inventory."""

    source = fixture / "LadonDeclarationFixture" / "Imported.lean"
    payload = run_elaborated_helper(
        fixture,
        source,
        "LadonDeclarationFixture.Imported",
    )
    inventory = declarations_from_elaborated_payload(
        "LadonDeclarationFixture.Imported",
        "LadonDeclarationFixture/Imported.lean",
        payload,
        source_content_hash=source_hash(source),
    )
    joined = join_declaration_inventories(root_rows, inventory)
    imported = joined["LadonDeclarationFixture.importedDependency"]
    if imported.is_imported_stub or imported.kind != "def":
        raise GateFailure("inventory did not replace the imported declaration stub")


def assert_trust_and_bounds(rows: Mapping[str, Any]) -> None:
    """Require direct trust facts and finite large-body output."""

    sorry_facts = required_row(rows, "directSorry").surface.trust_facts
    if not any(row.kind == "direct_sorryAx" for row in sorry_facts):
        raise GateFailure("directSorry lacks direct sorryAx evidence")
    axiom_facts = required_row(rows, "directAxiomReference").surface.trust_facts
    if not any(row.kind == "direct_axiom_reference" for row in axiom_facts):
        raise GateFailure("directAxiomReference lacks direct axiom evidence")
    declared = required_row(rows, "axiomKind").surface.trust_facts
    if not any(row.kind == "declared_axiom" for row in declared):
        raise GateFailure("axiomKind lacks declared-axiom evidence")
    large = required_row(rows, "largeProofBody").surface
    if not large.body_truncated or not large.statement_excerpt.truncated:
        raise GateFailure("large proof body lacks explicit truncation evidence")


def assert_payload_bound_and_determinism(
    fixture: Path,
    first_payload: Mapping[str, Any],
) -> None:
    """Require stable normalized helper JSON and a conservative size ceiling."""

    second = run_elaborated_helper(
        fixture,
        fixture / "LadonDeclarationFixture.lean",
        "LadonDeclarationFixture",
    )
    first_bytes = canonical_payload_bytes(first_payload)
    second_bytes = canonical_payload_bytes(second)
    if first_bytes != second_bytes:
        raise GateFailure("elaborated helper payload is nondeterministic")
    if len(first_bytes) > 256_000:
        raise GateFailure(
            f"elaborated helper payload exceeds 256000 bytes: {len(first_bytes)}"
        )


def assert_default_pipeline_contract(fixture: Path) -> None:
    """Require the default Lean path to expose a bounded valid v3 projection."""

    model = default_pipeline_report(fixture)
    report = model.to_dict()
    extension = report["extensions"]["elaborated_declarations"]
    if extension["status"] != "complete":
        raise GateFailure("default Lean report lacks a complete elaborated extension")
    assert_default_source_inventory(report)
    rendered = render_text(model)
    if "LadonDeclarationFixture.axiomKind" not in rendered:
        raise GateFailure("default text report omitted a root declaration surface")
    if "LadonDeclarationFixture._aux_" in rendered:
        raise GateFailure(
            "default text report promoted a compiler-generated review root"
        )
    projected = build_report_v3(model, projection="review")
    try:
        Draft202012Validator(load_report_v3_schema()).validate(
            projected.to_dict()
        )
    except ValidationError as error:
        raise GateFailure(
            f"default Lean v3 report is schema-invalid: {error.message}"
        ) from error
    size = len(serialize_report_v3_bytes(projected).content)
    if size > 1_000_000:
        raise GateFailure(f"default Lean v3 report exceeds 1000000 bytes: {size}")


def default_pipeline_report(fixture: Path) -> ReportV2:
    """Build the real default model and check its explicit v2 projection."""

    report = run_pipeline(
        RunContext(
            repo_root=fixture,
            requested_root="LadonDeclarationFixture.lean",
            extraction_backend="lean",
        )
    ).to_report_model()
    compatibility = json.loads(
        serialize_report_bytes(report, version="v2").content
    )
    try:
        Draft202012Validator(load_report_schema()).validate(compatibility)
    except ValidationError as error:
        raise GateFailure(
            f"default Lean v2 report is schema-invalid: {error.message}"
        ) from error
    return report


def assert_default_source_inventory(report: Mapping[str, Any]) -> None:
    """Require raw compiler evidence without promoting it to owner review."""

    rows = source_inventory_rows(report)
    assert_default_owner_population(rows)
    compiler = required_compiler_population(rows)
    assert_compiler_population_evidence(compiler)
    assert_compiler_population_is_not_review_root(report, compiler)


def source_inventory_rows(
    report: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """Return declarations from the default elaborated extension."""

    extension = report["extensions"]["elaborated_declarations"]
    return extension["payload"]["declarations"]


def assert_default_owner_population(rows: list[Mapping[str, Any]]) -> None:
    """Require the expected owner inventory without generated helpers."""

    owner_names = {
        row["declaration"]
        for row in rows
        if not row["importedStub"] and row.get("population") == "target_owned"
    }
    if len(owner_names) != 13 or any("_aux_" in name for name in owner_names):
        raise GateFailure("default owner population retained generated helpers")
    if "LadonDeclarationFixture.termLexicalGhost" in owner_names:
        raise GateFailure("default Lean report retained a macro frontend constant")


def required_compiler_population(
    rows: list[Mapping[str, Any]],
) -> Mapping[str, Any]:
    """Return the sole raw compiler-generated declaration."""

    compiler_rows = [
        row
        for row in rows
        if not row["importedStub"]
        and row.get("population") == "compiler_generated"
    ]
    if len(compiler_rows) != 1:
        raise GateFailure("default Lean report lacks a separate compiler population")
    return compiler_rows[0]


def assert_compiler_population_evidence(compiler: Mapping[str, Any]) -> None:
    """Require Lean authority and toolchain evidence on generated output."""

    if (
        compiler.get("compilerGenerated") is not True
        or compiler.get("compilerAuthority") != "lean_environment"
        or not compiler.get("compilerToolchain")
    ):
        raise GateFailure("compiler population lacks Lean/toolchain evidence")


def assert_compiler_population_is_not_review_root(
    report: Mapping[str, Any],
    compiler: Mapping[str, Any],
) -> None:
    """Require compiler-generated output to remain outside owner review roots."""

    chosen = report["declaration_graph"]["chosen_roots"]
    if any(name == compiler["declaration"] for name in chosen):
        raise GateFailure("compiler-generated declaration became a review root")


def canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    """Return normalized JSON bytes for determinism checks."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def required_row(rows: Mapping[str, Any], suffix: str) -> Any:
    """Return one fixture declaration by unambiguous final name."""

    matches = [
        row
        for name, row in rows.items()
        if name == f"LadonDeclarationFixture.{suffix}"
    ]
    if len(matches) != 1:
        raise GateFailure(f"expected exactly one declaration ending in {suffix}")
    return matches[0]


def run_gate(required: bool) -> None:
    """Run every required real-Lean declaration-surface assertion."""

    fixture = fixture_root()
    if not require_toolchain(fixture, required):
        return
    payload, rows = extract_fixture_rows(fixture)
    assert_declaration_kinds(rows)
    assert_statement_surface(rows)
    assert_dependency_split(rows)
    assert_inventory_join(fixture, rows)
    assert_trust_and_bounds(rows)
    assert_payload_bound_and_determinism(fixture, payload)
    assert_default_pipeline_contract(fixture)
    print("lean declaration gate: PASS")


def main(argv: list[str] | None = None) -> int:
    """Run the gate and return a concise process status."""

    args = build_parser().parse_args(argv)
    try:
        run_gate(args.required)
    except (GateFailure, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"lean declaration gate: FAIL: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
