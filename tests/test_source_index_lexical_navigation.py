from __future__ import annotations

import json
from pathlib import Path

from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_query import inspect_dataset
from ladon.source_index import SOURCE_INDEX_ALGORITHM_VERSION, build_source_index
from ladon.source_index_models import (
    SOURCE_INDEX_AUDITS_COVERAGE,
    SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE,
    SOURCE_INDEX_FINGERPRINT_VERSION,
    SOURCE_INDEX_OPTIONS_COVERAGE,
    SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE,
    SOURCE_INDEX_RESOURCES_COVERAGE,
    SOURCE_INDEX_SCHEMA,
    SourceIndex,
    source_index_collection_mapping,
    source_index_declaration_mapping,
)

NAVIGATION_SOURCE = """\
namespace Demo
section Work
variable (α : Type)
open scoped BigOperators
local notation "unit" => Unit
local instance localInhabited : Inhabited α := ⟨Classical.choice inferInstance⟩
export List (map)
set_option pp.universes true
set_option maxRecDepth 4096
@[simp] theorem first : True := by
  simp
omit α in
set_option maxHeartbeats 0 in
theorem second : True := by
  exact True.intro
#check Demo.first
end Work
end Demo
"""


def write_navigation_repo(root: Path, source: str = NAVIGATION_SOURCE) -> None:
    (root / "Demo.lean").write_text(source, encoding="utf-8")


def module_for(root: Path, source: str = NAVIGATION_SOURCE):
    write_navigation_repo(root, source)
    return build_source_index(root, use_cache=False).index.entries[0].module


def assert_navigation_contexts(module) -> None:
    declarations = {row.candidate_name: row for row in module.declaration_evidence}
    contexts = {row.identifier: row for row in module.scope_contexts}
    first = contexts[declarations["Demo.first"].scope_context_id or ""]
    second = contexts[declarations["Demo.second"].scope_context_id or ""]

    assert {
        "namespace": first.namespace_stack,
        "section": first.section_stack,
        "variables": first.variables,
        "notations": first.local_notations,
        "instances": first.local_instances,
        "scopes": first.opened_scopes,
        "exports": first.exports,
        "secondOmissions": second.omissions,
        "status": (first.status, second.status),
    } == {
        "namespace": ("Demo",),
        "section": ("Work",),
        "variables": ("(α : Type)",),
        "notations": ('"unit" => Unit',),
        "instances": (
            "localInhabited : Inhabited α := ⟨Classical.choice inferInstance⟩",
        ),
        "scopes": ("BigOperators",),
        "exports": ("List (map)",),
        "secondOmissions": ("α",),
        "status": ("complete", "complete"),
    }
    assert all(row.source_refs for row in (first, second))
    assert all("instance selection" in row.nonclaim for row in (first, second))


def assert_navigation_options(module) -> None:
    assert [
        (
            row.option,
            row.option_class,
            row.raw_value,
            row.lexical_scope,
            row.declaration_candidate,
        )
        for row in module.option_rows
    ] == [
        ("pp.universes", "pretty_printer", "true", "module", None),
        ("maxRecDepth", "resource", "4096", "module", None),
        (
            "maxHeartbeats",
            "resource",
            "0",
            "command_local",
            "Demo.second",
        ),
    ]


def assert_navigation_resources(module) -> None:
    assert [
        (
            row.option,
            row.numeric_value,
            row.normalized_meaning,
            row.status,
        )
        for row in module.resource_settings
    ] == [
        ("maxRecDepth", 4096, "finite", "parsed"),
        ("maxHeartbeats", 0, "unlimited", "parsed"),
    ]


def assert_navigation_mechanisms(module) -> None:
    assert [
        (row.kind, row.mechanism, row.declaration_candidate)
        for row in module.proof_mechanisms
    ] == [
        ("attribute", "simp", "Demo.first"),
        ("tactic-token", "simp", "Demo.first"),
        ("tactic-token", "exact", "Demo.second"),
    ]
    assert all(
        "not an elaborated tactic invocation" in row.nonclaim
        for row in module.proof_mechanisms
    )


def test_canonical_pass_records_scope_options_resources_and_mechanisms(
    tmp_path: Path,
) -> None:
    module = module_for(tmp_path)
    assert_navigation_contexts(module)
    assert_navigation_options(module)
    assert_navigation_resources(module)
    assert_navigation_mechanisms(module)
    assert [row.subject for row in module.audit_commands] == ["Demo.first"]
    assert len(module.command_skeletons) == 1
    assert module.command_skeletons[0].normalization_version == ("command-skeleton-v1")


def test_command_skeleton_normalizes_trivia_strings_and_numeric_serials(
    tmp_path: Path,
) -> None:
    first = module_for(
        tmp_path,
        """\
#check Nat
#eval row42 + 17 + 0x2a
#check "first payload"
""",
    ).command_skeletons[0]
    second = module_for(
        tmp_path,
        """\
-- unrelated comment
#check Nat
#eval row0007 + 999 + 0xFF
#check "different payload"
""",
    ).command_skeletons[0]
    changed = module_for(
        tmp_path,
        """\
#check Nat
#eval column0007 + 999 + 0xFF
#check "different payload"
""",
    ).command_skeletons[0]

    assert first.value == second.value
    assert first.token_count == second.token_count
    assert changed.value != first.value
    assert first.authority == "lexical_text"
    assert "not parsed Lean syntax" in first.nonclaim


def test_command_skeleton_retains_string_presence_without_string_content(
    tmp_path: Path,
) -> None:
    with_string = module_for(
        tmp_path,
        '#check "payload"\n',
    ).command_skeletons[0]
    changed_content = module_for(
        tmp_path,
        '#check "other payload"\n',
    ).command_skeletons[0]
    bare = module_for(
        tmp_path,
        "#check\n",
    ).command_skeletons[0]

    assert with_string.value == changed_content.value
    assert with_string.value != bare.value
    assert with_string.token_count > bare.token_count


def test_comment_and_string_text_emit_no_executable_navigation_rows(
    tmp_path: Path,
) -> None:
    module = module_for(
        tmp_path,
        """\
-- set_option maxHeartbeats 0
/- set_option maxRecDepth 999999 -/
def quoted : String :=
  "set_option pp.universes true; by simp; @[simp]"
theorem real : True := by
  trivial
""",
    )

    assert module.option_rows == ()
    assert module.resource_settings == ()
    assert [
        (row.kind, row.mechanism, row.declaration_candidate)
        for row in module.proof_mechanisms
    ] == [("tactic-token", "trivial", "real")]


def test_generic_expression_is_retained_but_resource_normalization_fails_closed(
    tmp_path: Path,
) -> None:
    module = module_for(
        tmp_path,
        """\
set_option custom.limit budget * 2
set_option maxHeartbeats budget * 2
theorem kept : True := by rfl
""",
    )

    generic, resource_option = module.option_rows
    assert (
        generic.option,
        generic.option_class,
        generic.raw_value,
        generic.status,
    ) == ("custom.limit", "generic", "budget * 2", "parsed")
    assert resource_option.raw_value == "budget * 2"
    resource = module.resource_settings[0]
    assert resource.numeric_value is None
    assert resource.normalized_meaning is None
    assert resource.status == "unresolved"
    assert "not one literal" in (resource.reason or "")


def test_unbalanced_scope_marks_declaration_context_unresolved(
    tmp_path: Path,
) -> None:
    module = module_for(
        tmp_path,
        """\
namespace Demo
section Work
variable (α : Type)
theorem unresolved : True := by trivial
""",
    )
    declaration = module.declaration_evidence[0]
    contexts = {row.identifier: row for row in module.scope_contexts}
    context = contexts[declaration.scope_context_id or ""]

    assert declaration.candidate_status == "unresolved"
    assert declaration.scope_context_status == "unresolved"
    assert context.status == "unresolved"
    assert context.reason == "lexical scope remains unclosed at end of source"


def test_active_context_is_bounded_with_explicit_omission_count(
    tmp_path: Path,
) -> None:
    variables = "\n".join(f"variable (x{index} : Nat)" for index in range(40))
    module = module_for(
        tmp_path,
        f"{variables}\ntheorem bounded : True := by trivial\n",
    )
    declaration = module.declaration_evidence[0]
    contexts = {row.identifier: row for row in module.scope_contexts}
    context = contexts[declaration.scope_context_id or ""]

    assert len(context.variables) == 32
    assert context.omitted_count == 8
    assert context.variables[0] == "(x0 : Nat)"
    assert context.variables[-1] == "(x31 : Nat)"


def test_long_context_value_discloses_truncation(
    tmp_path: Path,
) -> None:
    exported = "X" * 300
    module = module_for(
        tmp_path,
        f"export {exported}\ntheorem bounded : True := by trivial\n",
    )
    command = next(row for row in module.scope_context_commands if row.kind == "export")
    declaration = module.declaration_evidence[0]
    contexts = {row.identifier: row for row in module.scope_contexts}
    context = contexts[declaration.scope_context_id or ""]

    assert len(command.value) == 256
    assert command.value_total_characters == 300
    assert command.value_truncated is True
    assert context.omitted_count == 1


def test_v3_compact_codec_round_trips_and_registers_exact_coverage(
    tmp_path: Path,
) -> None:
    write_navigation_repo(tmp_path)
    built = build_source_index(tmp_path, use_cache=False).index
    payload = built.to_payload()
    module_payload = payload["entries"][0]["module"]

    assert_v3_payload_shape(payload, module_payload)
    decoded = SourceIndex.from_payload(
        tmp_path,
        payload,
        expected_fingerprint=built.fingerprint,
    )
    assert decoded.to_payload() == payload
    assert_v3_coverage(decoded)
    assert_v3_public_mappings(module_payload)


def assert_v3_payload_shape(payload, module_payload) -> None:
    assert SOURCE_INDEX_SCHEMA.endswith("-v3")
    assert SOURCE_INDEX_FINGERPRINT_VERSION.endswith("-v4")
    assert SOURCE_INDEX_ALGORITHM_VERSION == 5
    assert payload["fingerprintManifest"]["algorithmVersion"] == 5
    assert module_payload["auditCommandsComplete"] is True
    assert module_payload["commandSkeletonsComplete"] is True
    assert all(
        isinstance(row, list) and len(row) == 25
        for row in module_payload["declarationEvidence"]
    )
    assert all(
        isinstance(row, list)
        for key in (
            "scopeContextCommands",
            "scopeContextRows",
            "optionRows",
            "resourceSettings",
            "proofMechanisms",
            "auditCommands",
            "commandSkeletons",
        )
        for row in module_payload[key]
    )


def assert_v3_coverage(decoded: SourceIndex) -> None:
    coverage = decoded.coverage_registry()
    assert coverage.require(SOURCE_INDEX_AUDITS_COVERAGE).total == 1
    assert coverage.require(SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE).total == 1
    assert coverage.require(SOURCE_INDEX_OPTIONS_COVERAGE).total == 3
    assert coverage.require(SOURCE_INDEX_RESOURCES_COVERAGE).total == 2
    assert coverage.require(SOURCE_INDEX_PROOF_MECHANISMS_COVERAGE).total == 3


def assert_v3_public_mappings(module_payload) -> None:
    declaration = source_index_declaration_mapping(
        module_payload["declarationEvidence"][1]
    )
    option = source_index_collection_mapping(
        "optionRows",
        module_payload["optionRows"][0],
        module="Demo",
        path="Demo.lean",
    )
    skeleton = source_index_collection_mapping(
        "commandSkeletons",
        module_payload["commandSkeletons"][0],
        module="Demo",
        path="Demo.lean",
    )
    audit = source_index_collection_mapping(
        "auditCommands",
        module_payload["auditCommands"][0],
        module="Demo",
        path="Demo.lean",
    )
    assert_public_declaration_mapping(declaration)
    assert_public_navigation_mappings(option, skeleton, audit)


def assert_public_declaration_mapping(declaration) -> None:
    assert declaration["scopeContextStatus"] == "complete"
    assert declaration["scopeContextId"]
    assert declaration["normalizedSourceShapeSha256"]
    assert (
        declaration["sourceShapeNormalizationVersion"]
        == "ladon-lexical-declaration-source-shape-v2"
    )


def assert_public_navigation_mappings(option, skeleton, audit) -> None:
    assert option["option"] == "pp.universes"
    assert option["sourceRange"]["start"]["line"] == 8
    assert skeleton["normalizationVersion"] == "command-skeleton-v1"
    assert skeleton["tokenCount"] > 0
    assert skeleton["value"].startswith("sha256:")
    assert audit["subject"] == "Demo.first"
    assert audit["authority"] == "lexical_text"
    assert audit["sourceRange"]["start"]["line"] == 16


def legacy_navigation_payload(index: SourceIndex) -> dict:
    payload = index.to_payload()
    module_payload = payload["entries"][0]["module"]
    module_payload["declarationEvidence"] = [
        [*row[:18], *row[20:23]] for row in module_payload["declarationEvidence"]
    ]
    for key in (
        "scopeContextCommands",
        "scopeContextRows",
        "optionRows",
        "resourceSettings",
        "proofMechanisms",
        "auditCommands",
        "commandSkeletons",
    ):
        module_payload.pop(key)
    module_payload.pop("auditCommandsComplete")
    module_payload.pop("commandSkeletonsComplete")
    return payload


def assert_legacy_navigation_unavailable(decoded: SourceIndex) -> None:
    module = decoded.entries[0].module
    assert all(
        row.scope_context_id is None and row.scope_context_status == "unavailable"
        for row in module.declaration_evidence
    )
    assert all(
        row.normalized_source_shape_sha256 is None
        and row.source_shape_normalization_version is None
        and row.authority == "lexical_text"
        for row in module.declaration_evidence
    )
    assert_legacy_navigation_collections(module)
    audit_coverage = decoded.coverage_registry().require(
        SOURCE_INDEX_AUDITS_COVERAGE
    )
    assert audit_coverage.total_known is False
    assert audit_coverage.completeness == "partial"
    assert_legacy_skeleton_coverage(decoded)


def assert_legacy_navigation_collections(module) -> None:
    assert module.scope_contexts == ()
    assert module.option_rows == ()
    assert module.resource_settings == ()
    assert module.proof_mechanisms == ()
    assert module.audit_commands == ()
    assert module.audit_commands_complete is False
    assert module.command_skeletons == ()
    assert module.command_skeletons_complete is False


def assert_legacy_skeleton_coverage(decoded: SourceIndex) -> None:
    skeleton_coverage = decoded.coverage_registry().require(
        SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE
    )
    assert skeleton_coverage.total_known is False
    assert skeleton_coverage.completeness == "partial"
    assert {cause.identifier for cause in skeleton_coverage.causes} == {
        "source_index.command_skeletons_unavailable"
    }


def test_v3_legacy_declaration_prefix_decodes_context_as_unavailable(
    tmp_path: Path,
) -> None:
    write_navigation_repo(tmp_path)
    built = build_source_index(tmp_path, use_cache=False).index

    decoded = SourceIndex.from_payload(
        tmp_path,
        legacy_navigation_payload(built),
        expected_fingerprint=built.fingerprint,
    )

    assert_legacy_navigation_unavailable(decoded)


def test_unusable_v3_command_skeleton_row_has_partial_coverage(
    tmp_path: Path,
) -> None:
    write_navigation_repo(tmp_path)
    built = build_source_index(tmp_path, use_cache=False).index
    payload = built.to_payload()
    payload["entries"][0]["module"]["commandSkeletons"][0][4] = "unavailable"

    decoded = SourceIndex.from_payload(
        tmp_path,
        payload,
        expected_fingerprint=built.fingerprint,
    )
    coverage = decoded.coverage_registry().require(
        SOURCE_INDEX_COMMAND_SKELETONS_COVERAGE
    )

    assert coverage.total_known is False
    assert coverage.completeness == "partial"
    assert {cause.identifier for cause in coverage.causes} == {
        "source_index.command_skeletons_unavailable"
    }


def test_actual_compact_artifact_inspection_resolves_scope_context(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_navigation_repo(repo)
    payload = build_source_index(repo, use_cache=False).index.to_payload()
    artifact = tmp_path / "source-index.json"
    artifact.write_text(
        json.dumps(payload, sort_keys=True),
        encoding="utf-8",
    )

    declarations = inspect_dataset(
        load_inspection_dataset(
            artifact,
            "declarations",
            artifact_kind="source-index",
        ),
        filters=(("candidate-name", "Demo.second"),),
    )
    options = inspect_dataset(
        load_inspection_dataset(
            artifact,
            "options",
            artifact_kind="source-index",
        ),
        filters=(("option", "maxHeartbeats"),),
    )
    resources = inspect_dataset(
        load_inspection_dataset(
            artifact,
            "resources",
            artifact_kind="source-index",
        ),
        filters=(("meaning", "unlimited"),),
    )
    mechanisms = inspect_dataset(
        load_inspection_dataset(
            artifact,
            "proof-mechanisms",
            artifact_kind="source-index",
        ),
        filters=(("declaration", "Demo.first"),),
    )

    declaration_context = declarations.rows[0].fields["scope-context"]
    option_context = options.rows[0].fields["scope-context"]
    assert declaration_context["omissions"] == ["α"]
    assert declaration_context["namespaceStack"] == ["Demo"]
    assert option_context["sectionStack"] == ["Work"]
    assert resources.rows[0].fields["pressure"] == "unlimited"
    assert {row.fields["mechanism"] for row in mechanisms.rows} == {"simp"}
    assert all(
        row.source_anchor.status == "exact"
        for page in (declarations, options, resources, mechanisms)
        for row in page.rows
    )
