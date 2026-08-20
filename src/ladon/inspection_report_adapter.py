"""Canonical report-row inspection adapters."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any

from ladon.analysis.audit_registrations import (
    AUDIT_COMMAND_COVERAGE,
    RESOURCE_DIRECTIVE_COVERAGE,
    RESOURCE_REVIEW_COVERAGE,
)
from ladon.analysis.import_boundaries import IMPORT_BOUNDARY_COVERAGE
from ladon.coverage import CoverageRegistry
from ladon.inspection_adapter_common import (
    additive_row,
    candidate_family,
    declaration_row,
    filter_link,
    id_link,
    line_anchor,
    make_row,
    mapping_rows,
    noun_authority,
    noun_population,
    optional_int,
    optional_mapping,
    optional_mapping_or_none,
    optional_text,
    ordered_int,
    pointer_token,
    population,
    source_anchor,
    source_order,
    stable_id,
    string_list,
    text,
    unknown_coverage,
    with_enrichment,
)
from ladon.inspection_declaration_authority import (
    declaration_candidate_relationship,
    graph_declaration_authority,
    graph_declaration_status,
)
from ladon.inspection_models import (
    INSPECTION_NOUNS,
    ArtifactIdentity,
    InspectionCompatibilityError,
    InspectionDataset,
    InspectionRow,
)
from ladon.inspection_report_proof import merge_quoted_proof_rows
from ladon.inspection_report_reader import inspection_report_view
from ladon.pipeline_inspection_navigation import (
    INSPECTION_OPTIONS_COVERAGE,
    INSPECTION_PROOF_MECHANISMS_COVERAGE,
    TEXT_DECLARATIONS_COVERAGE,
)
from ladon.report_coverage import (
    DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
    MODULE_DAG_MODULES_COVERAGE,
    PROOF_XRAY_ROWS_COVERAGE,
)

REPORT_COLLECTION_KEYS: Mapping[str, tuple[str, ...]] = {
    "options": ("optionRows", "optionCommands", "genericOptions"),
    "proof-mechanisms": (
        "proofMechanisms",
        "proofMechanismOccurrences",
        "tacticOccurrences",
        "attributeOccurrences",
    ),
}
DECLARATION_INTEGRITY_COLLECTIONS = (
    "collisionCandidates",
    "exactBlockDuplicateCandidates",
    "sourceShapeSimilarityCandidates",
)
FILE_INTEGRITY_COLLECTION = "exactFileDuplicateCandidates"
DECLARATION_MEMBER_REF_PREFIX = "source-index:declaration:"
MODULE_MEMBER_REF_PREFIX = "source-index:module:"
REPORT_CANONICAL_COVERAGE_IDS: Mapping[str, tuple[str, ...]] = {
    "modules": (MODULE_DAG_MODULES_COVERAGE,),
    "declarations": (
        TEXT_DECLARATIONS_COVERAGE,
        DECLARATION_GRAPH_DECLARATIONS_COVERAGE,
    ),
    "imports": (IMPORT_BOUNDARY_COVERAGE,),
    "audits": (AUDIT_COMMAND_COVERAGE,),
    "options": (INSPECTION_OPTIONS_COVERAGE,),
    "resources": (RESOURCE_DIRECTIVE_COVERAGE,),
    "proof-mechanisms": (
        INSPECTION_PROOF_MECHANISMS_COVERAGE,
        PROOF_XRAY_ROWS_COVERAGE,
    ),
}

if frozenset(REPORT_CANONICAL_COVERAGE_IDS) != frozenset(INSPECTION_NOUNS):
    raise AssertionError("report coverage map must classify every inspection noun")


def report_dataset(
    payload: Mapping[str, Any],
    noun: str,
) -> InspectionDataset:
    """Adapt one compatible report without reading its source checkout."""

    sections, coverage, artifact = inspection_report_view(payload)
    rows, available = _selected_rows(sections, noun, artifact)
    return InspectionDataset(
        noun=noun,
        artifact=artifact,
        coverage=_selected_coverage(
            coverage,
            noun=noun,
            rows=rows,
            artifact=artifact,
            available=available,
        ),
        rows=tuple(sorted(rows, key=lambda row: row.order_key)),
        unavailable_reason=(
            None
            if available
            else f"{noun} evidence is unavailable in the selected report"
        ),
    )


def _selected_rows(
    sections: Mapping[str, Any],
    noun: str,
    artifact: ArtifactIdentity,
) -> tuple[list[InspectionRow], bool]:
    dag = optional_mapping(sections.get("module_dag"))
    builders: Mapping[
        str,
        Callable[
            [Mapping[str, Any], ArtifactIdentity, str],
            tuple[list[InspectionRow], bool],
        ],
    ] = {
        "modules": _module_rows,
        "imports": _import_rows,
        "audits": _audit_rows,
        "resources": _resource_rows,
        "options": _additive_module_rows,
    }
    if noun == "declarations":
        return _declaration_rows(sections, dag, artifact)
    if noun == "proof-mechanisms":
        return _proof_mechanism_rows(sections, dag, artifact)
    return builders[noun](dag, artifact, noun)


def _module_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> tuple[list[InspectionRow], bool]:
    del noun
    metadata = optional_mapping(dag.get("module_metadata"))
    rows = [
        _module_row(artifact, str(name), raw, dag)
        for name, raw in sorted(metadata.items())
        if isinstance(raw, Mapping)
    ]
    memberships = _integrity_memberships(dag, noun="modules")
    return (
        [
            _with_integrity_memberships(
                row,
                memberships.get(text(row.fields.get("module")), ()),
            )
            for row in rows
        ],
        "module_metadata" in dag,
    )


def _module_row(
    artifact: ArtifactIdentity,
    name: str,
    raw: Mapping[str, Any],
    dag: Mapping[str, Any],
) -> InspectionRow:
    path = text(raw.get("path"))
    identifier = (
        optional_text(optional_mapping(raw.get("populationEvidence")).get("id"))
        or f"module:{name}"
    )
    return make_row(
        artifact,
        noun="modules",
        identifier=identifier,
        canonical_ref=("#/sections/module_dag/module_metadata/" + pointer_token(name)),
        population_name=population(raw, "analyzed_modules"),
        scope=_report_scope(dag),
        authority="module_import_graph",
        anchor=source_anchor(path, None),
        coverage_ref="module_dag.modules",
        fields={
            "module": name,
            "path": path,
            "tag": string_list(raw.get("tags")),
            "role": string_list(raw.get("roles")),
            "status": "analyzed",
        },
        order_key=(name, identifier),
        related=(
            filter_link("imports", "module", name, "outgoing imports"),
            filter_link(
                "declarations",
                "module",
                name,
                "contained declarations",
            ),
        ),
    )


def _declaration_rows(
    sections: Mapping[str, Any],
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
) -> tuple[list[InspectionRow], bool]:
    graph = optional_mapping(sections.get("declaration_graph"))
    graph_rows = [
        _graph_declaration(artifact, row, index, dag)
        for index, row in enumerate(mapping_rows(graph.get("declarations")))
    ]
    lexical_rows, lexical_available = _lexical_declarations(dag, artifact)
    linked_lexical = _link_lean_enrichments(lexical_rows, graph_rows)
    memberships = _integrity_memberships(dag, noun="declarations")
    rows = [
        _with_integrity_memberships(
            row,
            memberships.get(row.identifier, ()),
        )
        for row in (*graph_rows, *linked_lexical)
    ]
    available = "declarations" in graph or bool(graph_rows) or lexical_available
    return rows, available


def _integrity_memberships(
    dag: Mapping[str, Any],
    *,
    noun: str,
) -> dict[str, tuple[str, ...]]:
    """Index complete canonical integrity membership for report inspection."""

    integrity = optional_mapping(dag.get("declaration_integrity"))
    collections = (
        DECLARATION_INTEGRITY_COLLECTIONS
        if noun == "declarations"
        else (FILE_INTEGRITY_COLLECTION,)
    )
    expected_prefix = (
        DECLARATION_MEMBER_REF_PREFIX
        if noun == "declarations"
        else MODULE_MEMBER_REF_PREFIX
    )
    memberships: dict[str, set[str]] = {}
    for collection in collections:
        for group in mapping_rows(integrity.get(collection)):
            identifier = optional_text(group.get("id"))
            if identifier is None:
                raise InspectionCompatibilityError(
                    "declaration-integrity group identity is missing"
                )
            references = _integrity_member_references(
                group,
                expected_prefix=expected_prefix,
            )
            for reference in references:
                member = reference.removeprefix(expected_prefix)
                memberships.setdefault(member, set()).add(identifier)
    return {
        member: tuple(sorted(groups)) for member, groups in sorted(memberships.items())
    }


def _integrity_member_references(
    group: Mapping[str, Any],
    *,
    expected_prefix: str,
) -> tuple[str, ...]:
    """Read complete refs, with bounded representatives as compatibility input."""

    supplied = group.get("canonicalMemberRefs")
    if supplied is None:
        supplied = [
            member.get("canonicalRef")
            for member in mapping_rows(group.get("representativeMembers"))
        ]
    if (
        not isinstance(supplied, Sequence)
        or isinstance(supplied, (str, bytes))
        or any(
            not isinstance(reference, str)
            or not reference.startswith(expected_prefix)
            or not reference.removeprefix(expected_prefix)
            for reference in supplied
        )
    ):
        raise InspectionCompatibilityError(
            "declaration-integrity canonical member references are malformed"
        )
    return tuple(dict.fromkeys(supplied))


def _with_integrity_memberships(
    row: InspectionRow,
    memberships: Sequence[str],
) -> InspectionRow:
    """Attach exact group identities without changing the canonical row owner."""

    if not memberships:
        return row
    return replace(
        row,
        fields={
            **row.fields,
            "integrity-group": tuple(memberships),
        },
    )


def _lexical_declarations(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
) -> tuple[list[InspectionRow], bool]:
    metadata = optional_mapping(dag.get("module_metadata"))
    rows: list[InspectionRow] = []
    available = False
    for module_name, raw_module in sorted(metadata.items()):
        if not isinstance(raw_module, Mapping):
            continue
        if "textDeclarations" in raw_module:
            available = True
        rows.extend(
            _module_lexical_declarations(
                artifact,
                str(module_name),
                raw_module,
                dag,
            )
        )
    return rows, available


def _module_lexical_declarations(
    artifact: ArtifactIdentity,
    module_name: str,
    raw_module: Mapping[str, Any],
    dag: Mapping[str, Any],
) -> list[InspectionRow]:
    module = {
        "name": module_name,
        "path": text(raw_module.get("path")),
        "population": raw_module.get("population"),
        "populationEvidence": raw_module.get("populationEvidence"),
    }
    return [
        declaration_row(
            artifact,
            raw,
            module,
            canonical_ref=(
                "#/sections/module_dag/module_metadata/"
                f"{pointer_token(module_name)}/textDeclarations/{row_index}"
            ),
            coverage_ref="module_dag.text_declarations",
            scope=_report_scope(dag),
        )
        for row_index, raw in enumerate(
            mapping_rows(raw_module.get("textDeclarations"))
        )
    ]


def _link_lean_enrichments(
    lexical_rows: Sequence[InspectionRow],
    graph_rows: Sequence[InspectionRow],
) -> list[InspectionRow]:
    graph_ids = {
        (
            text(row.fields.get("module")),
            text(row.fields.get("name")),
        ): row
        for row in graph_rows
    }
    return [_linked_lexical_row(row, graph_ids) for row in lexical_rows]


def _linked_lexical_row(
    row: InspectionRow,
    graph_rows: Mapping[tuple[str, str], InspectionRow],
) -> InspectionRow:
    key = (
        text(row.fields.get("module")),
        text(row.fields.get("candidate-name") or row.fields.get("name")),
    )
    matched = graph_rows.get(key)
    if matched is None:
        return row
    candidate_status = text(matched.fields.get("candidate-status"))
    return with_enrichment(
        row,
        {
            "noun": "declarations",
            "id": matched.identifier,
            "relationship": declaration_candidate_relationship(candidate_status),
            "authority": matched.authority,
        },
    )


def _graph_declaration(
    artifact: ArtifactIdentity,
    raw: Mapping[str, Any],
    index: int,
    dag: Mapping[str, Any],
) -> InspectionRow:
    name = text(raw.get("name") or raw.get("declaration"))
    module = text(raw.get("module"))
    identifier = optional_text(raw.get("id")) or stable_id(
        "lean-declaration",
        module,
        name,
    )
    path = optional_text(raw.get("sourcePath") or raw.get("path"))
    source_range = optional_mapping_or_none(
        raw.get("sourceRange") or raw.get("selectionRange")
    )
    surface = optional_mapping(raw.get("surface"))
    authority = graph_declaration_authority(raw, surface)
    candidate_status = graph_declaration_status(raw, surface)
    return make_row(
        artifact,
        noun="declarations",
        identifier=identifier,
        canonical_ref=f"#/sections/declaration_graph/declarations/{index}",
        population_name=population(raw, "analyzed_declarations"),
        scope=_report_scope(dag),
        authority=authority,
        anchor=source_anchor(path, source_range),
        coverage_ref="declaration_graph.declarations",
        fields=_graph_declaration_fields(
            raw,
            module,
            name,
            candidate_status=candidate_status,
        ),
        order_key=(
            module,
            path or "",
            source_order(source_range, "line"),
            source_order(source_range, "column"),
            name,
            identifier,
        ),
        related=(id_link("modules", f"module:{module}", "declaring module"),),
        enrichments=(_surface_enrichment(surface, authority),),
        nonclaims=_surface_nonclaims(surface),
    )


def _graph_declaration_fields(
    raw: Mapping[str, Any],
    module: str,
    name: str,
    *,
    candidate_status: str,
) -> dict[str, Any]:
    return {
        "module": module,
        "name": name,
        "kind": optional_text(raw.get("kind")),
        "candidate-status": candidate_status,
        "privacy": optional_text(raw.get("privacy")),
        "locality": optional_text(raw.get("locality")),
        "candidate-family": candidate_family(raw),
    }


def _surface_enrichment(
    surface: Mapping[str, Any],
    authority: str,
) -> Mapping[str, Any]:
    return {
        "status": optional_text(surface.get("status")) or "unavailable",
        "authority": authority,
        "backend": optional_text(surface.get("backend")) or "unavailable",
        "toolchain": optional_text(surface.get("leanVersion")),
        "nonclaim": optional_text(surface.get("nonclaim")),
    }


def _surface_nonclaims(
    surface: Mapping[str, Any],
) -> tuple[str, ...]:
    value = optional_text(surface.get("nonclaim"))
    return (value,) if value else ()


def _import_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> tuple[list[InspectionRow], bool]:
    del noun
    boundaries = mapping_rows(dag.get("import_boundaries"))
    if boundaries:
        return (
            [
                _boundary_row(artifact, row, index, dag)
                for index, row in enumerate(boundaries)
            ],
            True,
        )
    return _legacy_import_rows(dag, artifact), "import_sites" in dag


def _boundary_row(
    artifact: ArtifactIdentity,
    raw: Mapping[str, Any],
    index: int,
    dag: Mapping[str, Any],
) -> InspectionRow:
    importer = text(raw.get("sourceModule"))
    target = text(raw.get("targetModule"))
    path = text(raw.get("sourcePath"))
    line = optional_int(raw.get("line"))
    identifier = optional_text(raw.get("id")) or stable_id(
        "report-boundary",
        importer,
        target,
        path,
        str(line),
    )
    return _import_inspection_row(
        artifact,
        identifier=identifier,
        canonical_ref=f"#/sections/module_dag/import_boundaries/{index}",
        importer=importer,
        target=target,
        path=path,
        line=line,
        boundary=optional_text(raw.get("classification")),
        coverage_ref=optional_text(raw.get("coverageRef"))
        or "module_dag.import_boundaries",
        authority=optional_text(raw.get("authority")) or "lexical_text",
        scope=_report_scope(dag),
        nonclaim=optional_text(raw.get("nonclaim")),
    )


def _legacy_import_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
) -> list[InspectionRow]:
    sites = optional_mapping(dag.get("import_sites"))
    rows: list[InspectionRow] = []
    for importer, raw_targets in sorted(sites.items()):
        rows.extend(
            _importer_rows(
                artifact,
                str(importer),
                optional_mapping(raw_targets),
                dag,
            )
        )
    return rows


def _importer_rows(
    artifact: ArtifactIdentity,
    importer: str,
    targets: Mapping[str, Any],
    dag: Mapping[str, Any],
) -> list[InspectionRow]:
    return [
        _legacy_import_row(artifact, importer, str(target), raw, dag)
        for target, raw in sorted(targets.items())
    ]


def _legacy_import_row(
    artifact: ArtifactIdentity,
    importer: str,
    target: str,
    raw: Any,
    dag: Mapping[str, Any],
) -> InspectionRow:
    site = raw if isinstance(raw, Mapping) else {}
    path = text(site.get("sourcePath"))
    line = optional_int(site.get("line"))
    identifier = stable_id(
        "report-import",
        importer,
        target,
        path,
        str(line),
    )
    return _import_inspection_row(
        artifact,
        identifier=identifier,
        canonical_ref=(
            "#/sections/module_dag/import_sites/"
            f"{pointer_token(importer)}/{pointer_token(target)}"
        ),
        importer=importer,
        target=target,
        path=path,
        line=line,
        boundary="unclassified",
        coverage_ref="module_dag.import_sites",
        authority="lexical_text",
        scope=_report_scope(dag),
        nonclaim=None,
    )


def _import_inspection_row(
    artifact: ArtifactIdentity,
    *,
    identifier: str,
    canonical_ref: str,
    importer: str,
    target: str,
    path: str,
    line: int | None,
    boundary: str | None,
    coverage_ref: str,
    authority: str,
    scope: str,
    nonclaim: str | None,
) -> InspectionRow:
    return make_row(
        artifact,
        noun="imports",
        identifier=identifier,
        canonical_ref=canonical_ref,
        population_name="selected_lexical_import_occurrences",
        scope=scope,
        authority=authority,
        anchor=line_anchor(path, line),
        coverage_ref=coverage_ref,
        fields={
            "module": importer,
            "target": target,
            "path": path,
            "boundary": boundary,
        },
        order_key=(
            importer,
            path,
            ordered_int(line),
            target,
            identifier,
        ),
        related=(id_link("modules", f"module:{importer}", "source module"),),
        nonclaims=(nonclaim,) if nonclaim else (),
    )


def _audit_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> tuple[list[InspectionRow], bool]:
    del noun
    return _registered_surface_rows(
        dag,
        artifact,
        noun="audits",
        collection_key="auditCommands",
        registration_key="auditProducerRegistrations",
        row_coverage_ref=AUDIT_COMMAND_COVERAGE,
        registration_coverage_ref=AUDIT_COMMAND_COVERAGE,
        registered_only=False,
    )


def _resource_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> tuple[list[InspectionRow], bool]:
    del noun
    return _registered_surface_rows(
        dag,
        artifact,
        noun="resources",
        collection_key="resourceDirectives",
        registration_key="resourceProducerRegistrations",
        row_coverage_ref=RESOURCE_DIRECTIVE_COVERAGE,
        registration_coverage_ref=RESOURCE_REVIEW_COVERAGE,
        registered_only=False,
    )


def _registered_surface_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    *,
    noun: str,
    collection_key: str,
    registration_key: str,
    row_coverage_ref: str,
    registration_coverage_ref: str,
    registered_only: bool,
) -> tuple[list[InspectionRow], bool]:
    rows, surface_available = _surface_rows(
        dag,
        artifact,
        noun=noun,
        collection_key=collection_key,
        coverage_ref=row_coverage_ref,
    )
    registrations = dag.get(registration_key)
    if not isinstance(registrations, Mapping):
        return rows, surface_available
    producers = registrations.get("producers")
    if not isinstance(producers, Mapping):
        return [], False
    identifiers = _registered_inspection_ids(
        producers,
        noun=noun,
        coverage_ref=registration_coverage_ref,
    )
    by_identifier = {row.identifier: row for row in rows}
    unresolved = identifiers - by_identifier.keys()
    if unresolved:
        raise InspectionCompatibilityError(
            "report-owned inspection actions do not resolve canonical "
            f"{noun} rows: {', '.join(sorted(unresolved))}"
        )
    selected = (
        [row for row in rows if row.identifier in identifiers]
        if registered_only
        else rows
    )
    return selected, True


def _registered_inspection_ids(
    producers: Mapping[str, Any],
    *,
    noun: str,
    coverage_ref: str,
) -> set[str]:
    identifiers: set[str] = set()
    for producer in producers.values():
        if not isinstance(producer, Mapping):
            raise InspectionCompatibilityError(
                f"{noun} producer registration is malformed"
            )
        if producer.get("coverageRef") != coverage_ref:
            raise InspectionCompatibilityError(
                f"{noun} producer registration has incompatible coverage"
            )
        identifiers.add(_inspection_action_id(producer, noun))
    return identifiers


def _inspection_action_id(
    producer: Mapping[str, Any],
    noun: str,
) -> str:
    action = producer.get("inspectionAction")
    if not isinstance(action, Mapping) or action.get("command") != "ladon":
        raise InspectionCompatibilityError(
            f"{noun} producer inspection action is malformed"
        )
    arguments = action.get("arguments")
    if (
        not isinstance(arguments, list)
        or len(arguments) != 4
        or arguments[:3] != ["inspect", noun, "--id"]
        or not isinstance(arguments[3], str)
        or not arguments[3]
    ):
        raise InspectionCompatibilityError(
            f"{noun} producer inspection action must use one exact row ID"
        )
    return arguments[3]


def _surface_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    *,
    noun: str,
    collection_key: str,
    coverage_ref: str,
) -> tuple[list[InspectionRow], bool]:
    surfaces = dag.get("audit_surfaces")
    rows: list[InspectionRow] = []
    for surface_index, surface in enumerate(mapping_rows(surfaces)):
        rows.extend(
            _one_surface_rows(
                artifact,
                surface,
                surface_index,
                noun=noun,
                collection_key=collection_key,
                coverage_ref=coverage_ref,
                scope=_report_scope(dag),
            )
        )
    return rows, isinstance(surfaces, list)


def _one_surface_rows(
    artifact: ArtifactIdentity,
    surface: Mapping[str, Any],
    surface_index: int,
    *,
    noun: str,
    collection_key: str,
    coverage_ref: str,
    scope: str,
) -> list[InspectionRow]:
    module = {
        "name": text(surface.get("module")),
        "path": text(surface.get("path")),
    }
    return [
        additive_row(
            artifact,
            noun,
            raw,
            module,
            canonical_ref=(
                "#/sections/module_dag/audit_surfaces/"
                f"{surface_index}/{collection_key}/{row_index}"
            ),
            coverage_ref=coverage_ref,
            scope=scope,
        )
        for row_index, raw in enumerate(mapping_rows(surface.get(collection_key)))
    ]


def _additive_module_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> tuple[list[InspectionRow], bool]:
    navigation_rows = _inspection_navigation_rows(dag, artifact, noun)
    if navigation_rows is not None:
        return navigation_rows, True
    keys = REPORT_COLLECTION_KEYS[noun]
    metadata = optional_mapping(dag.get("module_metadata"))
    available = _module_collection_is_present(metadata, keys)
    rows: list[InspectionRow] = []
    for module_name, raw_module in sorted(metadata.items()):
        if isinstance(raw_module, Mapping):
            rows.extend(
                _one_module_additive_rows(
                    artifact,
                    noun,
                    str(module_name),
                    raw_module,
                    keys,
                    dag,
                )
            )
    return rows, available


def _inspection_navigation_rows(
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
    noun: str,
) -> list[InspectionRow] | None:
    """Prefer the bounded canonical report owner over compatibility fields."""

    navigation = optional_mapping(dag.get("inspection_navigation"))
    collection_key = {
        "options": "options",
        "proof-mechanisms": "proofMechanisms",
    }[noun]
    if collection_key not in navigation:
        return None
    coverage_ref = REPORT_CANONICAL_COVERAGE_IDS[noun][0]
    return [
        additive_row(
            artifact,
            noun,
            raw,
            {},
            canonical_ref=(
                f"#/sections/module_dag/inspection_navigation/{collection_key}/{index}"
            ),
            coverage_ref=coverage_ref,
            scope=_report_scope(dag),
        )
        for index, raw in enumerate(mapping_rows(navigation.get(collection_key)))
    ]


def _proof_mechanism_rows(
    sections: Mapping[str, Any],
    dag: Mapping[str, Any],
    artifact: ArtifactIdentity,
) -> tuple[list[InspectionRow], bool]:
    lexical, lexical_available = _additive_module_rows(
        dag,
        artifact,
        noun="proof-mechanisms",
    )
    return merge_quoted_proof_rows(
        sections,
        artifact,
        lexical,
        lexical_available=lexical_available,
        scope=_report_scope(dag),
    )


def _one_module_additive_rows(
    artifact: ArtifactIdentity,
    noun: str,
    module_name: str,
    raw_module: Mapping[str, Any],
    keys: Sequence[str],
    dag: Mapping[str, Any],
) -> list[InspectionRow]:
    module = {
        "name": module_name,
        "path": text(raw_module.get("path")),
        "population": raw_module.get("population"),
    }
    rows: list[InspectionRow] = []
    for key in keys:
        rows.extend(
            additive_row(
                artifact,
                noun,
                raw,
                module,
                canonical_ref=(
                    "#/sections/module_dag/module_metadata/"
                    f"{pointer_token(module_name)}/{key}/{row_index}"
                ),
                coverage_ref=f"module_dag.{noun.replace('-', '_')}",
                scope=_report_scope(dag),
            )
            for row_index, raw in enumerate(mapping_rows(raw_module.get(key)))
        )
    return rows


def _module_collection_is_present(
    metadata: Mapping[str, Any],
    keys: Sequence[str],
) -> bool:
    return any(
        isinstance(raw, Mapping) and any(key in raw for key in keys)
        for raw in metadata.values()
    )


def _selected_coverage(
    registry: CoverageRegistry,
    *,
    noun: str,
    rows: Sequence[InspectionRow],
    artifact: ArtifactIdentity,
    available: bool,
) -> dict[str, Any]:
    visible = len(rows)
    canonical_id = _canonical_coverage_id(noun, registry, rows)
    if canonical_id is not None:
        row = registry.require(canonical_id)
        if row.visible != visible:
            raise InspectionCompatibilityError(
                f"{canonical_id} coverage exposes {row.visible} rows but "
                f"inspection found {visible}"
            )
        return row.to_dict()
    reason = (
        "selected report lacks collection coverage for this adapted surface"
        if available
        else f"{noun} collection is absent from the selected report"
    )
    return unknown_coverage(
        identity=f"inspection.report.{noun.replace('-', '_')}",
        pointer=f"#/inspection/{noun}",
        visible=visible,
        population_name=_adapted_population(noun, rows),
        scope=artifact.scope_fingerprint or "selected_report_scope",
        authority=_adapted_authority(noun, rows),
        source_fingerprint=artifact.source_fingerprint,
        reason=reason,
        completeness="partial" if available else "unavailable",
        scope_fingerprint=artifact.scope_fingerprint,
        analysis_fingerprint=artifact.analysis_fingerprint,
    )


def _adapted_population(
    noun: str,
    rows: Sequence[InspectionRow],
) -> str:
    """Describe a compatibility union without relabeling its row populations."""

    populations = {row.population for row in rows}
    if len(populations) == 1:
        return next(iter(populations))
    if populations:
        return f"combined_{noun.replace('-', '_')}_inspection_rows"
    return noun_population(noun)


def _adapted_authority(
    noun: str,
    rows: Sequence[InspectionRow],
) -> str:
    """Describe mixed report authority without promoting one component."""

    authorities = {row.authority for row in rows}
    if len(authorities) == 1:
        return next(iter(authorities))
    if authorities:
        return "multiple_registered_authorities"
    return noun_authority(noun)


def _canonical_coverage_id(
    noun: str,
    registry: CoverageRegistry,
    rows: Sequence[InspectionRow],
) -> str | None:
    return next(
        (
            candidate
            for candidate in REPORT_CANONICAL_COVERAGE_IDS[noun]
            if candidate in registry.collections
            and all(row.coverage_ref == candidate for row in rows)
        ),
        None,
    )


def _report_scope(dag: Mapping[str, Any]) -> str:
    scope = optional_mapping(dag.get("analysis_scope"))
    return (
        optional_text(scope.get("effectiveScope"))
        or optional_text(scope.get("requestedScope"))
        or "selected_report_scope"
    )


__all__ = ["report_dataset"]
