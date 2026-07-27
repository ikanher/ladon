"""Conservative declaration-collision and exact-duplicate analysis.

This pass consumes canonical source-index rows and an optional selected module
graph.  It never reparses Lean text and never promotes lexical equality or hash
equality into a Lean environment, compilation, theorem, or proof claim.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.analysis.declaration_integrity_models import (
    BLOCK_DUPLICATE_COLLECTION_ID,
    BLOCK_DUPLICATE_NONCLAIMS,
    CO_REACHABLE_COLLECTION_ID,
    CO_REACHABLE_NONCLAIMS,
    COLLISION_COLLECTION_ID,
    COLLISION_NONCLAIMS,
    DECLARATION_INTEGRITY_ANALYSIS_VERSION,
    DECLARATION_INTEGRITY_SCHEMA,
    DEFAULT_GROUP_LIMIT,
    DEFAULT_MEMBER_LIMIT,
    FILE_DUPLICATE_COLLECTION_ID,
    INTEGRITY_POINTER,
    SOURCE_SHAPE_COLLECTION_ID,
    SOURCE_SHAPE_NONCLAIMS,
    DeclarationIntegrityGroup,
    DeclarationIntegrityMember,
    DeclarationIntegrityResult,
    SelectedContextAssessment,
    SourceFileIntegrityMember,
    co_reachable_coverage,
    declaration_group,
    file_group,
    group_collection_coverage,
)
from ladon.analysis.structural_joins import (
    deterministic_graph_path,
    graph_path_witness,
    normalized_edges,
)
from ladon.coverage import (
    CollectionCoverage,
    InspectionAction,
    ProducerRegistration,
    ProducerRegistry,
)
from ladon.finding_evidence import json_pointer_token
from ladon.ir import LeanModule, LeanTextDeclaration


_SHA256_RE = re.compile(r"[0-9a-f]{64}")

__all__ = (
    "BLOCK_DUPLICATE_COLLECTION_ID",
    "CO_REACHABLE_COLLECTION_ID",
    "COLLISION_COLLECTION_ID",
    "DECLARATION_INTEGRITY_SCHEMA",
    "FILE_DUPLICATE_COLLECTION_ID",
    "SOURCE_SHAPE_COLLECTION_ID",
    "DeclarationIntegrityResult",
    "analyze_declaration_integrity",
    "declaration_integrity_fingerprint",
)


@dataclass(frozen=True)
class _GraphEvidence:
    """Validated exact selected graph used only for coexistence witnesses."""

    edges: Mapping[str, tuple[str, ...]]
    importers_by_target: Mapping[str, tuple[str, ...]]
    roots: tuple[str, ...]
    coverage: CollectionCoverage


def analyze_declaration_integrity(
    modules: Mapping[str, LeanModule],
    *,
    content_hashes: Mapping[str, str] | None,
    source_fingerprint: str,
    scope_fingerprint: str | None = None,
    inventory_complete: bool = True,
    selected_edges: Mapping[str, Sequence[str]] | None = None,
    selected_roots: Sequence[str] = (),
    selected_graph_coverage: CollectionCoverage | None = None,
    group_limit: int = DEFAULT_GROUP_LIMIT,
    member_limit: int = DEFAULT_MEMBER_LIMIT,
) -> DeclarationIntegrityResult:
    """Partition lexical integrity evidence and register exact graph joins.

    ``modules`` is the source-index inventory over which collision and duplicate
    groups are measured. ``selected_edges`` is a possibly narrower selected
    module graph and is usable only with exact fingerprint-matched coverage.
    """

    _validate_inputs(
        modules,
        content_hashes=content_hashes,
        source_fingerprint=source_fingerprint,
        group_limit=group_limit,
        member_limit=member_limit,
    )
    fingerprint = declaration_integrity_fingerprint(
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        group_limit=group_limit,
        member_limit=member_limit,
    )
    declarations = _declaration_members(modules, source_fingerprint)
    graph, graph_reason = _validated_graph_evidence(
        modules,
        selected_edges=selected_edges,
        selected_roots=selected_roots,
        coverage=selected_graph_coverage,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )
    collisions = _collision_groups(
        declarations,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        inventory_complete=inventory_complete,
        member_limit=member_limit,
        graph=graph,
        graph_unavailable_reason=graph_reason,
    )
    blocks = _block_duplicate_groups(
        declarations,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        inventory_complete=inventory_complete,
        member_limit=member_limit,
    )
    files, file_complete = _file_duplicate_groups(
        modules,
        content_hashes=content_hashes,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        inventory_complete=inventory_complete,
        member_limit=member_limit,
    )
    shapes = _source_shape_similarity_groups(
        declarations,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        inventory_complete=inventory_complete,
        member_limit=member_limit,
    )
    collision_coverage = group_collection_coverage(
        COLLISION_COLLECTION_ID,
        "collisionCandidates",
        len(collisions),
        group_limit=group_limit,
        complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        population="public_global_lexical_candidate_name_partitions",
        authority="lexical_text",
    )
    block_coverage = group_collection_coverage(
        BLOCK_DUPLICATE_COLLECTION_ID,
        "exactBlockDuplicateCandidates",
        len(blocks),
        group_limit=group_limit,
        complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        population="normalized_lexical_declaration_block_partitions",
        authority="lexical_declaration_block_hash",
    )
    file_coverage = group_collection_coverage(
        FILE_DUPLICATE_COLLECTION_ID,
        "exactFileDuplicateCandidates",
        len(files),
        group_limit=group_limit,
        complete=file_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        population="source_index_content_hash_partitions",
        authority="source_index_content_hash",
    )
    shape_coverage = group_collection_coverage(
        SOURCE_SHAPE_COLLECTION_ID,
        "sourceShapeSimilarityCandidates",
        len(shapes),
        group_limit=group_limit,
        complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
        population="lexical_declaration_source_shape_partitions",
        authority="lexical_declaration_source_shape",
    )
    producers, co_reachable_coverage = _co_reachable_producers(
        collisions,
        collision_visible=collision_coverage.visible,
        graph=graph,
        graph_unavailable_reason=graph_reason,
        inventory_complete=inventory_complete,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=fingerprint,
    )
    return DeclarationIntegrityResult(
        analysis_fingerprint=fingerprint,
        collision_groups=collisions,
        exact_block_duplicate_groups=blocks,
        exact_file_duplicate_groups=files,
        source_shape_similarity_groups=shapes,
        collision_coverage=collision_coverage,
        block_duplicate_coverage=block_coverage,
        file_duplicate_coverage=file_coverage,
        source_shape_coverage=shape_coverage,
        co_reachable_coverage=co_reachable_coverage,
        producer_registry=producers,
    )


def declaration_integrity_fingerprint(
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    group_limit: int,
    member_limit: int,
) -> str:
    """Return the deterministic analysis/configuration fingerprint."""

    payload = {
        "version": DECLARATION_INTEGRITY_ANALYSIS_VERSION,
        "sourceFingerprint": source_fingerprint,
        "scopeFingerprint": scope_fingerprint,
        "groupLimit": group_limit,
        "memberLimit": member_limit,
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _validate_inputs(
    modules: Mapping[str, LeanModule],
    *,
    content_hashes: Mapping[str, str] | None,
    source_fingerprint: str,
    group_limit: int,
    member_limit: int,
) -> None:
    if not source_fingerprint:
        raise ValueError("source fingerprint must be non-empty")
    if group_limit < 1 or member_limit < 1:
        raise ValueError("integrity projection limits must be positive")
    _validate_module_mapping(modules)
    _validate_content_hashes(modules, content_hashes)


def _validate_module_mapping(modules: Mapping[str, LeanModule]) -> None:
    """Require stable module and declaration identities from the source index."""

    for name, module in modules.items():
        if name != module.name or not module.path:
            raise ValueError("module mapping must use canonical module names")
    declaration_ids = [
        row.identifier
        for module in modules.values()
        for row in module.declaration_evidence
        if row.identifier
    ]
    if len(declaration_ids) != len(set(declaration_ids)):
        raise ValueError("lexical declaration identities must be unique")


def _validate_content_hashes(
    modules: Mapping[str, LeanModule],
    content_hashes: Mapping[str, str] | None,
) -> None:
    """Reject hashes that cannot have come from canonical source-index rows."""

    if content_hashes is None:
        return
    unexpected = set(content_hashes) - set(modules)
    if unexpected:
        raise ValueError("content hashes contain modules outside the source inventory")
    if any(
        not isinstance(digest, str) or _SHA256_RE.fullmatch(digest) is None
        for digest in content_hashes.values()
    ):
        raise ValueError("content hashes must be lowercase SHA-256 hex values")


def _declaration_members(
    modules: Mapping[str, LeanModule],
    source_fingerprint: str,
) -> tuple[DeclarationIntegrityMember, ...]:
    rows = (
        _declaration_member(module, declaration, source_fingerprint)
        for _, module in sorted(modules.items())
        for declaration in module.declaration_evidence
        if declaration.identifier
    )
    return tuple(sorted(rows, key=_declaration_member_sort_key))


def _declaration_member(
    module: LeanModule,
    declaration: LeanTextDeclaration,
    source_fingerprint: str,
) -> DeclarationIntegrityMember:
    return DeclarationIntegrityMember(
        module=module.name,
        path=module.path,
        declaration_id=declaration.identifier,
        written_name=declaration.name,
        candidate_name=declaration.candidate_name,
        candidate_status=declaration.candidate_status,
        kind=declaration.kind,
        line=declaration.line,
        column=declaration.column,
        privacy=declaration.privacy,
        locality=declaration.locality,
        normalized_block_sha256=declaration.normalized_block_sha256,
        block_normalization_version=declaration.block_normalization_version,
        normalized_source_shape_sha256=(declaration.normalized_source_shape_sha256),
        source_shape_normalization_version=(
            declaration.source_shape_normalization_version
        ),
        source_fingerprint=source_fingerprint,
    )


def _declaration_member_sort_key(
    member: DeclarationIntegrityMember,
) -> tuple[str, str, int, int, str]:
    return (
        member.module,
        member.path,
        member.line,
        member.column,
        member.declaration_id,
    )


def _collision_groups(
    declarations: Sequence[DeclarationIntegrityMember],
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
    graph: _GraphEvidence | None,
    graph_unavailable_reason: str | None,
) -> tuple[DeclarationIntegrityGroup, ...]:
    partitions: dict[str, list[DeclarationIntegrityMember]] = defaultdict(list)
    for member in declarations:
        if (
            member.candidate_name is not None
            and member.candidate_status == "lexical_candidate"
            and member.privacy == "public"
            and member.locality == "global"
        ):
            partitions[member.candidate_name].append(member)
    raw_groups = (
        (name, tuple(sorted(members, key=_declaration_member_sort_key)))
        for name, members in partitions.items()
        if len({member.module for member in members}) >= 2
    )
    return tuple(
        declaration_group(
            evidence_kind="lexical_candidate_name_collision",
            key=name,
            key_version="lexical-fully-qualified-candidate-v1",
            authority="lexical_text",
            members=members,
            index=index,
            collection_key="collisionCandidates",
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            inventory_complete=inventory_complete,
            member_limit=member_limit,
            nonclaims=COLLISION_NONCLAIMS,
            selected_context=_selected_context_assessment(
                members,
                graph=graph,
                unavailable_reason=graph_unavailable_reason,
                source_fingerprint=source_fingerprint,
                scope_fingerprint=scope_fingerprint,
            ),
        )
        for index, (name, members) in enumerate(sorted(raw_groups))
    )


def _block_duplicate_groups(
    declarations: Sequence[DeclarationIntegrityMember],
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
) -> tuple[DeclarationIntegrityGroup, ...]:
    partitions: dict[
        tuple[str, str],
        list[DeclarationIntegrityMember],
    ] = defaultdict(list)
    for member in declarations:
        if (
            member.block_normalization_version is not None
            and member.normalized_block_sha256 is not None
        ):
            partitions[
                (
                    member.block_normalization_version,
                    member.normalized_block_sha256,
                )
            ].append(member)
    raw_groups = (
        (key, tuple(sorted(members, key=_declaration_member_sort_key)))
        for key, members in partitions.items()
        if len({member.module for member in members}) >= 2
    )
    return tuple(
        declaration_group(
            evidence_kind="exact_normalized_declaration_block_duplicate",
            key=digest,
            key_version=version,
            authority="lexical_declaration_block_hash",
            members=members,
            index=index,
            collection_key="exactBlockDuplicateCandidates",
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            inventory_complete=inventory_complete,
            member_limit=member_limit,
            nonclaims=BLOCK_DUPLICATE_NONCLAIMS,
        )
        for index, ((version, digest), members) in enumerate(sorted(raw_groups))
    )


def _file_duplicate_groups(
    modules: Mapping[str, LeanModule],
    *,
    content_hashes: Mapping[str, str] | None,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
) -> tuple[tuple[DeclarationIntegrityGroup, ...], bool]:
    if content_hashes is None:
        return (), False
    complete = inventory_complete and set(content_hashes) == set(modules)
    partitions: dict[str, list[SourceFileIntegrityMember]] = defaultdict(list)
    for name, digest in sorted(content_hashes.items()):
        module = modules[name]
        partitions[digest].append(
            SourceFileIntegrityMember(
                module=name,
                path=module.path,
                content_sha256=digest,
                source_fingerprint=source_fingerprint,
            )
        )
    raw_groups = (
        (
            digest,
            tuple(sorted(members, key=lambda row: (row.path, row.module))),
        )
        for digest, members in partitions.items()
        if len({member.path for member in members}) >= 2
    )
    groups = tuple(
        file_group(
            digest=digest,
            members=members,
            index=index,
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            inventory_complete=complete,
            member_limit=member_limit,
        )
        for index, (digest, members) in enumerate(sorted(raw_groups))
    )
    return groups, complete


def _source_shape_similarity_groups(
    declarations: Sequence[DeclarationIntegrityMember],
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
    inventory_complete: bool,
    member_limit: int,
) -> tuple[DeclarationIntegrityGroup, ...]:
    """Partition cross-module shape matches that are not exact block clones."""

    partitions: dict[
        tuple[str, str],
        list[DeclarationIntegrityMember],
    ] = defaultdict(list)
    for member in declarations:
        key = _source_shape_partition_key(member)
        if key is not None:
            partitions[key].append(member)
    raw_groups = (
        (key, tuple(sorted(members, key=_declaration_member_sort_key)))
        for key, members in partitions.items()
        if _is_source_shape_similarity(members)
    )
    return tuple(
        declaration_group(
            evidence_kind="normalized_declaration_source_shape_similarity",
            key=digest,
            key_version=version,
            authority="lexical_declaration_source_shape",
            members=members,
            index=index,
            collection_key="sourceShapeSimilarityCandidates",
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
            analysis_fingerprint=analysis_fingerprint,
            inventory_complete=inventory_complete,
            member_limit=member_limit,
            nonclaims=SOURCE_SHAPE_NONCLAIMS,
        )
        for index, ((version, digest), members) in enumerate(sorted(raw_groups))
    )


def _source_shape_partition_key(
    member: DeclarationIntegrityMember,
) -> tuple[str, str] | None:
    """Return a shape key only when exact-block comparison is also available."""

    if (
        member.source_shape_normalization_version is None
        or member.normalized_source_shape_sha256 is None
        or member.block_normalization_version is None
        or member.normalized_block_sha256 is None
    ):
        return None
    return (
        member.source_shape_normalization_version,
        member.normalized_source_shape_sha256,
    )


def _is_source_shape_similarity(
    members: Sequence[DeclarationIntegrityMember],
) -> bool:
    """Require cross-module membership and at least two exact block values."""

    modules = {member.module for member in members}
    exact_blocks = {
        (
            member.block_normalization_version,
            member.normalized_block_sha256,
        )
        for member in members
    }
    return len(modules) >= 2 and len(exact_blocks) >= 2


def _validated_graph_evidence(
    modules: Mapping[str, LeanModule],
    *,
    selected_edges: Mapping[str, Sequence[str]] | None,
    selected_roots: Sequence[str],
    coverage: CollectionCoverage | None,
    source_fingerprint: str,
    scope_fingerprint: str | None,
) -> tuple[_GraphEvidence | None, str | None]:
    if selected_edges is None or coverage is None:
        return None, "selected module-graph evidence was not supplied"
    reason = _graph_coverage_unavailable_reason(
        coverage,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )
    if reason is not None:
        return None, reason
    edges = normalized_edges(selected_edges)
    if edges is None:
        return None, "selected module graph is dangling or malformed"
    if not set(edges).issubset(modules):
        return None, "selected module graph contains an unknown source module"
    if coverage.visible != len(edges) or coverage.total != len(edges):
        return None, "selected graph coverage does not count every graph module"
    roots = tuple(sorted(set(selected_roots)))
    if any(root not in edges for root in roots):
        return None, "an explicit selected root is absent from the graph"
    return (
        _GraphEvidence(
            edges=edges,
            importers_by_target=_importers_by_target(edges),
            roots=roots,
            coverage=coverage,
        ),
        None,
    )


def _importers_by_target(
    edges: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    """Invert one validated graph for bounded collision-witness joins."""

    importers: dict[str, list[str]] = {target: [] for target in edges}
    for source in sorted(edges):
        for target in edges[source]:
            importers[target].append(source)
    return {
        target: tuple(rows)
        for target, rows in sorted(importers.items())
    }


def _graph_coverage_unavailable_reason(
    coverage: CollectionCoverage,
    *,
    source_fingerprint: str,
    scope_fingerprint: str | None,
) -> str | None:
    if (
        coverage.completeness != "complete"
        or not coverage.total_known
        or coverage.omitted != 0
    ):
        return "selected module-graph coverage is partial or projected"
    if coverage.source_fingerprint != source_fingerprint:
        return "selected graph and source-index fingerprints do not match"
    if coverage.scope_fingerprint != scope_fingerprint:
        return "selected graph and analysis-scope fingerprints do not match"
    return None


def _selected_context_assessment(
    members: Sequence[DeclarationIntegrityMember],
    *,
    graph: _GraphEvidence | None,
    unavailable_reason: str | None,
    source_fingerprint: str,
    scope_fingerprint: str | None,
) -> SelectedContextAssessment:
    if graph is None:
        return SelectedContextAssessment(
            status="unavailable",
            reason=unavailable_reason or "selected graph evidence is unavailable",
            source_fingerprint=source_fingerprint,
            scope_fingerprint=scope_fingerprint,
        )
    member_modules = tuple(sorted({member.module for member in members}))
    direct = _shared_importer_witness(graph, member_modules)
    if direct is not None:
        return direct
    closure = _root_closure_witness(graph, member_modules)
    if closure is not None:
        return closure
    return SelectedContextAssessment(
        status="not_observed",
        reason=(
            "No exact shared-importer or explicit-root closure witness reaches "
            "two observed collision-member modules."
        ),
        coverage_ref=graph.coverage.identity,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
    )


def _shared_importer_witness(
    graph: _GraphEvidence,
    member_modules: Sequence[str],
) -> SelectedContextAssessment | None:
    witnessed_by_importer: dict[str, list[str]] = defaultdict(list)
    for target in sorted(set(member_modules)):
        for importer in graph.importers_by_target.get(target, ()):
            witnessed_by_importer[importer].append(target)
    candidates = [
        (source, tuple(witnessed))
        for source, witnessed in witnessed_by_importer.items()
        if len(witnessed) >= 2
    ]
    if not candidates:
        return None
    importer, witnessed = min(
        candidates,
        key=lambda row: (-len(row[1]), row[0], row[1]),
    )
    edge_refs = tuple(
        _edge_pointer(importer, target, graph.edges[importer]) for target in witnessed
    )
    witness = {
        "type": "shared-importer",
        "importer": importer,
        "memberModules": list(witnessed),
        "edgeRefs": list(edge_refs),
        "authority": "module_import_graph",
    }
    return SelectedContextAssessment(
        status="co_reachable",
        reason=(
            "One selected module directly imports at least two collision-member "
            "modules."
        ),
        witness_kind="shared_importer",
        context_module=importer,
        member_modules=witnessed,
        witness=witness,
        evidence_refs=edge_refs,
        coverage_ref=graph.coverage.identity,
        source_fingerprint=graph.coverage.source_fingerprint,
        scope_fingerprint=graph.coverage.scope_fingerprint,
    )


def _root_closure_witness(
    graph: _GraphEvidence,
    member_modules: Sequence[str],
) -> SelectedContextAssessment | None:
    candidate = _best_root_candidate(graph, member_modules)
    if candidate is None:
        return None
    root, witnessed, paths = candidate
    path_witnesses = _complete_path_witnesses(graph, paths)
    if path_witnesses is None:
        return None
    evidence_refs = _path_evidence_refs(path_witnesses)
    witness = {
        "type": "explicit-root-closure",
        "root": root,
        "memberModules": list(witnessed),
        "paths": [dict(row) for row in path_witnesses],
        "authority": "module_import_graph",
    }
    return SelectedContextAssessment(
        status="co_reachable",
        reason=(
            "One explicit selected root has deterministic graph paths to at "
            "least two collision-member modules."
        ),
        witness_kind="explicit_root_closure",
        context_module=root,
        member_modules=witnessed,
        witness=witness,
        evidence_refs=evidence_refs,
        coverage_ref=graph.coverage.identity,
        source_fingerprint=graph.coverage.source_fingerprint,
        scope_fingerprint=graph.coverage.scope_fingerprint,
    )


def _best_root_candidate(
    graph: _GraphEvidence,
    member_modules: Sequence[str],
) -> tuple[str, tuple[str, ...], tuple[tuple[str, ...], ...]] | None:
    """Return the widest, then lexicographically first, exact root closure."""

    candidates = tuple(
        candidate
        for root in graph.roots
        for candidate in (_root_candidate(graph, root, member_modules),)
        if candidate is not None
    )
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (-len(row[1]), row[0], row[1], row[2]),
    )[0]


def _complete_path_witnesses(
    graph: _GraphEvidence,
    paths: Sequence[Sequence[str]],
) -> tuple[Mapping[str, Any], ...] | None:
    """Resolve every selected path or fail the relationship closed."""

    witnesses = tuple(graph_path_witness(graph.edges, path) for path in paths)
    if any(witness is None for witness in witnesses):
        return None
    return tuple(witness for witness in witnesses if witness is not None)


def _path_evidence_refs(
    witnesses: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    """Flatten canonical edge references from exact path witnesses."""

    return tuple(
        str(edge["pointer"]) for witness in witnesses for edge in witness["edgeRefs"]
    )


def _root_candidate(
    graph: _GraphEvidence,
    root: str,
    member_modules: Sequence[str],
) -> tuple[str, tuple[str, ...], tuple[tuple[str, ...], ...]] | None:
    rows = tuple(
        (member, deterministic_graph_path(graph.edges, root, member))
        for member in member_modules
    )
    reachable = tuple((member, path) for member, path in rows if path is not None)
    if len(reachable) < 2:
        return None
    return (
        root,
        tuple(member for member, _ in reachable),
        tuple(path for _, path in reachable if path is not None),
    )


def _edge_pointer(
    source: str,
    target: str,
    targets: Sequence[str],
) -> str:
    return (
        "#/sections/module_dag/edges/"
        f"{json_pointer_token(source)}/{targets.index(target)}"
    )


def _co_reachable_producers(
    collisions: Sequence[DeclarationIntegrityGroup],
    *,
    collision_visible: int,
    graph: _GraphEvidence | None,
    graph_unavailable_reason: str | None,
    inventory_complete: bool,
    source_fingerprint: str,
    scope_fingerprint: str | None,
    analysis_fingerprint: str,
) -> tuple[ProducerRegistry, CollectionCoverage]:
    co_reachable = tuple(
        group
        for group in collisions
        if (
            group.selected_context is not None
            and group.selected_context.status == "co_reachable"
        )
    )
    visible_collision_ids = {
        group.identifier for group in collisions[:collision_visible]
    }
    visible = tuple(
        group for group in co_reachable if group.identifier in visible_collision_ids
    )
    complete = graph is not None and inventory_complete
    coverage = co_reachable_coverage(
        visible=len(visible),
        observed=len(co_reachable),
        complete=complete,
        unavailable_reason=graph_unavailable_reason,
        source_fingerprint=source_fingerprint,
        scope_fingerprint=scope_fingerprint,
        analysis_fingerprint=analysis_fingerprint,
    )
    registry = ProducerRegistry()
    for group in visible:
        registry = registry.register_producer(
            _producer_registration(group, coverage.identity)
        )
    return registry, coverage


def _producer_registration(
    group: DeclarationIntegrityGroup,
    coverage_ref: str,
) -> ProducerRegistration:
    context = group.selected_context
    if context is None or context.status != "co_reachable":
        raise ValueError("producer registration requires co-reachable context")
    group_index_ref = (
        f"{INTEGRITY_POINTER}/collisionCandidates/{_collision_group_index(group)}"
    )
    declaration_refs = tuple(
        member.canonical_ref
        for member in group.members
        if (
            isinstance(member, DeclarationIntegrityMember)
            and member.module in context.member_modules
        )
    )
    return ProducerRegistration(
        identity=f"{group.identifier}.co_reachable",
        kind="co_reachable_declaration_collision_candidate",
        evidence_refs=(
            group_index_ref,
            *declaration_refs,
            *context.evidence_refs,
        ),
        coverage_ref=coverage_ref,
        authority="lexical_text_and_module_import_graph",
        nonclaims=CO_REACHABLE_NONCLAIMS,
        action=InspectionAction(
            noun="declarations",
            filters=(("integrity-group", group.identifier),),
        ),
    )


def _collision_group_index(group: DeclarationIntegrityGroup) -> int:
    prefix = f"{INTEGRITY_POINTER}/collisionCandidates/"
    pointer = group.member_coverage.pointer
    if not pointer.startswith(prefix):
        raise ValueError("collision group has a noncanonical member pointer")
    index_text = pointer[len(prefix) :].split("/", 1)[0]
    if not index_text.isdecimal():
        raise ValueError("collision group pointer has an invalid index")
    return int(index_text)
