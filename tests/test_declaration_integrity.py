from __future__ import annotations

import hashlib
from collections.abc import Iterator, Mapping

from ladon.analysis.declaration_integrity import (
    BLOCK_DUPLICATE_COLLECTION_ID,
    CO_REACHABLE_COLLECTION_ID,
    COLLISION_COLLECTION_ID,
    FILE_DUPLICATE_COLLECTION_ID,
    SOURCE_SHAPE_COLLECTION_ID,
    _GraphEvidence,
    _shared_importer_witness,
    analyze_declaration_integrity,
)
from ladon.coverage import CollectionCoverage, CoverageCause
from ladon.ir import LeanModule, LeanTextDeclaration

SOURCE_FINGERPRINT = "sha256:declaration-integrity-source"
SCOPE_FINGERPRINT = "sha256:declaration-integrity-scope"
BLOCK_HASH = "b" * 64
FILE_HASH = hashlib.sha256(b"same source bytes").hexdigest()


def declaration(
    identifier: str,
    *,
    candidate_name: str | None,
    module_ordinal: int,
    privacy: str = "public",
    locality: str = "global",
    block_hash: str | None = None,
    block_version: str | None = None,
    shape_hash: str | None = None,
    shape_version: str | None = None,
    candidate_status: str | None = None,
) -> LeanTextDeclaration:
    written_name = (
        candidate_name.rsplit(".", 1)[-1]
        if candidate_name is not None
        else "unresolved"
    )
    return LeanTextDeclaration(
        name=written_name,
        kind="theorem",
        line=module_ordinal,
        column=9,
        start_offset=module_ordinal * 100,
        end_offset=module_ordinal * 100 + len(written_name),
        identifier=identifier,
        privacy=privacy,
        locality=locality,
        candidate_name=candidate_name,
        candidate_status=(
            candidate_status
            if candidate_status is not None
            else ("lexical_candidate" if candidate_name is not None else "unresolved")
        ),
        normalized_block_sha256=block_hash,
        block_normalization_version=block_version,
        normalized_source_shape_sha256=shape_hash,
        source_shape_normalization_version=shape_version,
    )


def module(
    name: str,
    *declarations: LeanTextDeclaration,
    imports: tuple[str, ...] = (),
    path: str | None = None,
) -> LeanModule:
    return LeanModule(
        name=name,
        path=path or f"{name.replace('.', '/')}.lean",
        imports=imports,
        declarations=tuple(row.name for row in declarations),
        declaration_evidence=tuple(declarations),
    )


def exact_graph_coverage(
    module_count: int,
    *,
    source_fingerprint: str = SOURCE_FINGERPRINT,
) -> CollectionCoverage:
    return CollectionCoverage.exact(
        identity="module_dag.modules",
        pointer="#/sections/module_dag/module_metadata",
        visible=module_count,
        total=module_count,
        population="selected_internal_modules",
        scope="explicit_selection",
        authority="module_import_graph",
        source_fingerprint=source_fingerprint,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )


def inventory_modules() -> dict[str, LeanModule]:
    return {
        "Pkg.A": module(
            "Pkg.A",
            declaration(
                "decl:a",
                candidate_name="Shared.value",
                module_ordinal=1,
                block_hash=BLOCK_HASH,
                block_version="normalized-block-v1",
            ),
        ),
        "Pkg.B": module(
            "Pkg.B",
            declaration(
                "decl:b",
                candidate_name="Shared.value",
                module_ordinal=2,
                block_hash=BLOCK_HASH,
                block_version="normalized-block-v1",
            ),
        ),
        "Pkg.Private": module(
            "Pkg.Private",
            declaration(
                "decl:private",
                candidate_name="Shared.value",
                module_ordinal=3,
                privacy="private",
            ),
        ),
        "Pkg.Local": module(
            "Pkg.Local",
            declaration(
                "decl:local",
                candidate_name="Shared.value",
                module_ordinal=4,
                locality="local",
            ),
        ),
        "Pkg.Other": module(
            "Pkg.Other",
            declaration(
                "decl:other",
                candidate_name="Other.value",
                module_ordinal=5,
            ),
        ),
        "Pkg.Unresolved": module(
            "Pkg.Unresolved",
            declaration(
                "decl:unresolved",
                candidate_name="Shared.value",
                candidate_status="unresolved",
                module_ordinal=6,
            ),
        ),
    }


def test_integrity_groups_keep_exact_evidence_kinds_and_bounded_members() -> None:
    modules = inventory_modules()
    content_hashes = {
        name: (
            FILE_HASH
            if name in {"Pkg.A", "Pkg.Other"}
            else hashlib.sha256(name.encode()).hexdigest()
        )
        for name in modules
    }

    result = analyze_declaration_integrity(
        modules,
        content_hashes=content_hashes,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        member_limit=1,
    )

    _assert_collision_group(result.collision_groups[0])
    _assert_duplicate_groups(result)
    _assert_integrity_coverage_ids(result)


def _assert_collision_group(collision) -> None:
    assert collision.key == "Shared.value"
    assert [member.module for member in collision.members] == [
        "Pkg.A",
        "Pkg.B",
    ]
    assert (
        collision.member_coverage.visible,
        collision.member_coverage.total,
        collision.member_coverage.omitted,
    ) == (1, 2, 1)
    assert collision.member_coverage.observed_lower_bound == 2
    assert collision.inspection_action.to_dict()["arguments"][:2] == [
        "inspect",
        "declarations",
    ]
    assert collision.inspection_action.filters == (
        ("integrity-group", collision.identifier),
    )
    assert collision.to_dict()["canonicalMemberRefs"] == [
        "source-index:declaration:decl:a",
        "source-index:declaration:decl:b",
    ]
    assert "Lean name-resolution error" in collision.nonclaims[1]


def _assert_duplicate_groups(result) -> None:
    block = result.exact_block_duplicate_groups[0]
    assert (block.key, block.key_version) == (
        BLOCK_HASH,
        "normalized-block-v1",
    )
    assert block.evidence_kind == ("exact_normalized_declaration_block_duplicate")

    source = result.exact_file_duplicate_groups[0]
    assert source.key == FILE_HASH
    assert [member.path for member in source.members] == [
        "Pkg/A.lean",
        "Pkg/Other.lean",
    ]
    assert source.evidence_kind == "exact_source_file_duplicate"
    assert source.inspection_action.filters == (("integrity-group", source.identifier),)


def _assert_integrity_coverage_ids(result) -> None:
    assert {row.identity for row in result.coverage_rows} == {
        COLLISION_COLLECTION_ID,
        BLOCK_DUPLICATE_COLLECTION_ID,
        FILE_DUPLICATE_COLLECTION_ID,
        SOURCE_SHAPE_COLLECTION_ID,
        CO_REACHABLE_COLLECTION_ID,
    }


def test_source_shape_similarity_is_distinct_bounded_evidence() -> None:
    shape_hash = "c" * 64
    modules = _shape_similarity_modules(shape_hash)

    result = analyze_declaration_integrity(
        modules,
        content_hashes=_module_hashes(modules),
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        member_limit=2,
    )

    assert result.exact_block_duplicate_groups == ()
    assert len(result.source_shape_similarity_groups) == 1
    _assert_source_shape_group(
        result.source_shape_similarity_groups[0],
        shape_hash,
    )
    assert result.source_shape_coverage.total == 1


def _assert_source_shape_group(group, shape_hash: str) -> None:
    """Check kind, bounded witnesses, authority, and lexical nonclaims."""

    assert group.evidence_kind == ("normalized_declaration_source_shape_similarity")
    assert (group.key, group.key_version) == (
        shape_hash,
        "source-shape-v1",
    )
    assert group.authority == "lexical_declaration_source_shape"
    assert [row.module for row in group.representatives] == [
        "Pkg.A",
        "Pkg.B",
    ]
    assert (
        group.member_coverage.visible,
        group.member_coverage.total,
        group.member_coverage.omitted,
    ) == (2, 3, 1)
    assert "not parsed Lean syntax" in group.nonclaims[1]


def _module_hashes(modules: dict[str, LeanModule]) -> dict[str, str]:
    """Return deterministic distinct source hashes for an in-memory fixture."""

    return {name: hashlib.sha256(name.encode()).hexdigest() for name in modules}


def _shape_similarity_modules(shape_hash: str) -> dict[str, LeanModule]:
    """Build three cross-module shape witnesses with distinct exact blocks."""

    modules: dict[str, LeanModule] = {}
    rows = (("Pkg.A", "a"), ("Pkg.B", "b"), ("Pkg.C", "d"))
    for index, (name, character) in enumerate(rows, start=1):
        modules[name] = module(
            name,
            declaration(
                f"decl:{index}",
                candidate_name=f"{name}.value",
                module_ordinal=index,
                block_hash=character * 64,
                block_version="normalized-block-v1",
                shape_hash=shape_hash,
                shape_version="source-shape-v1",
            ),
        )
    return modules


def test_source_shape_group_identity_is_order_independent() -> None:
    modules = _shape_similarity_modules("c" * 64)
    hashes = _module_hashes(modules)

    forward = analyze_declaration_integrity(
        modules,
        content_hashes=hashes,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )
    reverse = analyze_declaration_integrity(
        dict(reversed(tuple(modules.items()))),
        content_hashes=dict(reversed(tuple(hashes.items()))),
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    assert (
        forward.source_shape_similarity_groups[0].identifier
        == reverse.source_shape_similarity_groups[0].identifier
    )
    assert forward.to_dict() == reverse.to_dict()


def test_exact_block_clones_do_not_become_shape_only_similarity() -> None:
    modules = {
        name: module(
            name,
            declaration(
                f"decl:{name}",
                candidate_name=f"{name}.value",
                module_ordinal=index,
                block_hash=BLOCK_HASH,
                block_version="normalized-block-v1",
                shape_hash="c" * 64,
                shape_version="source-shape-v1",
            ),
        )
        for index, name in enumerate(("Pkg.A", "Pkg.B"), start=1)
    }

    result = analyze_declaration_integrity(
        modules,
        content_hashes=None,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    assert len(result.exact_block_duplicate_groups) == 1
    assert result.source_shape_similarity_groups == ()


def test_partial_source_shape_membership_keeps_total_unknown() -> None:
    modules = {
        name: module(
            name,
            declaration(
                f"decl:{name}",
                candidate_name=f"{name}.value",
                module_ordinal=index,
                block_hash=character * 64,
                block_version="normalized-block-v1",
                shape_hash="c" * 64,
                shape_version="source-shape-v1",
            ),
        )
        for index, (name, character) in enumerate(
            (("Pkg.A", "a"), ("Pkg.B", "b")),
            start=1,
        )
    }

    result = analyze_declaration_integrity(
        modules,
        content_hashes=None,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        inventory_complete=False,
    )

    group = result.source_shape_similarity_groups[0]
    assert group.member_coverage.total_known is False
    assert group.member_coverage.observed_lower_bound == 2
    assert result.source_shape_coverage.total_known is False
    assert result.source_shape_coverage.observed_lower_bound == 1


def test_integrity_group_ids_and_machine_rows_are_order_independent() -> None:
    modules = inventory_modules()
    hashes = {name: hashlib.sha256(name.encode()).hexdigest() for name in modules}
    forward = analyze_declaration_integrity(
        modules,
        content_hashes=hashes,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )
    reversed_result = analyze_declaration_integrity(
        dict(reversed(tuple(modules.items()))),
        content_hashes=dict(reversed(tuple(hashes.items()))),
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    assert forward.analysis_fingerprint == reversed_result.analysis_fingerprint
    assert forward.to_dict() == reversed_result.to_dict()


def test_block_hash_versions_and_distinct_paths_remain_separate() -> None:
    modules = {
        "Pkg.A": module(
            "Pkg.A",
            declaration(
                "decl:a",
                candidate_name="A.value",
                module_ordinal=1,
                block_hash=BLOCK_HASH,
                block_version="normalized-block-v1",
            ),
            path="Shared.lean",
        ),
        "Pkg.B": module(
            "Pkg.B",
            declaration(
                "decl:b",
                candidate_name="B.value",
                module_ordinal=2,
                block_hash=BLOCK_HASH,
                block_version="normalized-block-v2",
            ),
            path="Shared.lean",
        ),
    }
    result = analyze_declaration_integrity(
        modules,
        content_hashes={"Pkg.A": FILE_HASH, "Pkg.B": FILE_HASH},
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )

    assert result.exact_block_duplicate_groups == ()
    assert result.exact_file_duplicate_groups == ()


def co_reachable_modules() -> dict[str, LeanModule]:
    return {
        "Pkg.A": module(
            "Pkg.A",
            declaration(
                "decl:a",
                candidate_name="Shared.value",
                module_ordinal=1,
            ),
        ),
        "Pkg.B": module(
            "Pkg.B",
            declaration(
                "decl:b",
                candidate_name="Shared.value",
                module_ordinal=2,
            ),
        ),
        "Pkg.Facade": module(
            "Pkg.Facade",
            imports=("Pkg.A", "Pkg.B"),
        ),
    }


def test_shared_importer_registers_only_a_producer_with_exact_refs() -> None:
    modules = co_reachable_modules()
    edges = {
        "Pkg.A": (),
        "Pkg.B": (),
        "Pkg.Facade": ("Pkg.A", "Pkg.B"),
    }
    result = analyze_declaration_integrity(
        modules,
        content_hashes={
            name: hashlib.sha256(name.encode()).hexdigest() for name in modules
        },
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        selected_edges=edges,
        selected_graph_coverage=exact_graph_coverage(len(edges)),
    )

    collision = result.collision_groups[0]
    context = collision.selected_context
    assert context is not None
    _assert_shared_importer_context(context)
    _assert_collision_producer(result)
    assert result.co_reachable_coverage.completeness == "complete"


def test_shared_importer_prefers_widest_then_lexical_witness_independent_of_order(
) -> None:
    modules = {
        name: module(
            name,
            declaration(
                f"decl:{name}",
                candidate_name="Shared.value",
                module_ordinal=index,
            ),
        )
        for index, name in enumerate(("Pkg.A", "Pkg.B", "Pkg.C"), start=1)
    }
    modules.update(
        {
            "Pkg.Alpha": module("Pkg.Alpha", imports=("Pkg.A", "Pkg.B", "Pkg.C")),
            "Pkg.Beta": module("Pkg.Beta", imports=("Pkg.A", "Pkg.B", "Pkg.C")),
            "Pkg.Narrow": module("Pkg.Narrow", imports=("Pkg.A", "Pkg.B")),
        }
    )
    forward_edges = {
        "Pkg.A": (),
        "Pkg.B": (),
        "Pkg.C": (),
        "Pkg.Alpha": ("Pkg.C", "Pkg.A", "Pkg.B", "Pkg.A"),
        "Pkg.Beta": ("Pkg.B", "Pkg.C", "Pkg.A"),
        "Pkg.Narrow": ("Pkg.B", "Pkg.A", "Pkg.B"),
    }
    reversed_edges = {
        name: tuple(reversed(targets))
        for name, targets in reversed(tuple(forward_edges.items()))
    }

    results = tuple(
        analyze_declaration_integrity(
            modules,
            content_hashes={
                name: hashlib.sha256(name.encode()).hexdigest()
                for name in modules
            },
            source_fingerprint=SOURCE_FINGERPRINT,
            scope_fingerprint=SCOPE_FINGERPRINT,
            selected_edges=edges,
            selected_graph_coverage=exact_graph_coverage(len(edges)),
        )
        for edges in (forward_edges, reversed_edges)
    )
    assert results[0].to_dict() == results[1].to_dict()

    context = results[0].collision_groups[0].selected_context
    assert context is not None
    assert context.context_module == "Pkg.Alpha"
    assert context.member_modules == ("Pkg.A", "Pkg.B", "Pkg.C")
    assert context.evidence_refs == (
        "#/sections/module_dag/edges/Pkg.Alpha/0",
        "#/sections/module_dag/edges/Pkg.Alpha/1",
        "#/sections/module_dag/edges/Pkg.Alpha/2",
    )


def test_shared_importer_join_does_not_rescan_forward_graph() -> None:
    class NonIterableEdges(Mapping[str, tuple[str, ...]]):
        def __init__(self) -> None:
            self.lookups: list[str] = []

        def __getitem__(self, key: str) -> tuple[str, ...]:
            self.lookups.append(key)
            if key == "Pkg.Alpha":
                return ("Pkg.A", "Pkg.B", "Pkg.C")
            raise KeyError(key)

        def __iter__(self) -> Iterator[str]:
            raise AssertionError("collision joins must not scan every graph owner")

        def __len__(self) -> int:
            return 5_001

    class CountingImporters(dict[str, tuple[str, ...]]):
        def __init__(self) -> None:
            super().__init__(
                {
                    "Pkg.A": ("Pkg.Alpha",),
                    "Pkg.B": ("Pkg.Alpha",),
                    "Pkg.C": ("Pkg.Alpha",),
                }
            )
            self.lookups: list[str] = []

        def get(
            self,
            key: str,
            default: tuple[str, ...] = (),
        ) -> tuple[str, ...]:
            self.lookups.append(key)
            return super().get(key, default)

    edges = NonIterableEdges()
    importers = CountingImporters()
    graph = _GraphEvidence(
        edges=edges,
        importers_by_target=importers,
        roots=(),
        coverage=exact_graph_coverage(len(edges)),
    )

    context = _shared_importer_witness(
        graph,
        ("Pkg.C", "Pkg.A", "Pkg.B", "Pkg.A"),
    )

    assert context is not None
    assert context.context_module == "Pkg.Alpha"
    assert importers.lookups == ["Pkg.A", "Pkg.B", "Pkg.C"]
    assert edges.lookups == ["Pkg.Alpha", "Pkg.Alpha", "Pkg.Alpha"]


def _assert_shared_importer_context(context) -> None:
    assert (context.status, context.witness_kind) == (
        "co_reachable",
        "shared_importer",
    )
    assert context.member_modules == ("Pkg.A", "Pkg.B")
    assert context.evidence_refs == (
        "#/sections/module_dag/edges/Pkg.Facade/0",
        "#/sections/module_dag/edges/Pkg.Facade/1",
    )


def _assert_collision_producer(result) -> None:
    producer = next(iter(result.producer_registry.producers.values()))
    assert producer.kind == ("co_reachable_declaration_collision_candidate")
    assert producer.coverage_ref == CO_REACHABLE_COLLECTION_ID
    assert "source-index:declaration:decl:a" in producer.evidence_refs
    assert producer.action.to_dict()["arguments"][:2] == [
        "inspect",
        "declarations",
    ]


def test_explicit_root_closure_uses_deterministic_path_witnesses() -> None:
    modules = {
        **co_reachable_modules(),
        "Pkg.Left": module("Pkg.Left", imports=("Pkg.A",)),
        "Pkg.Right": module("Pkg.Right", imports=("Pkg.B",)),
        "Pkg.Root": module(
            "Pkg.Root",
            imports=("Pkg.Left", "Pkg.Right"),
        ),
    }
    modules["Pkg.Facade"] = module("Pkg.Facade")
    edges = {
        "Pkg.A": (),
        "Pkg.B": (),
        "Pkg.Facade": (),
        "Pkg.Left": ("Pkg.A",),
        "Pkg.Right": ("Pkg.B",),
        "Pkg.Root": ("Pkg.Left", "Pkg.Right"),
    }
    result = analyze_declaration_integrity(
        modules,
        content_hashes={
            name: hashlib.sha256(name.encode()).hexdigest() for name in modules
        },
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        selected_edges=edges,
        selected_roots=("Pkg.Root",),
        selected_graph_coverage=exact_graph_coverage(len(edges)),
    )

    context = result.collision_groups[0].selected_context
    assert context is not None
    assert (context.status, context.witness_kind) == (
        "co_reachable",
        "explicit_root_closure",
    )
    assert context.context_module == "Pkg.Root"
    assert context.witness is not None
    assert [row["path"] for row in context.witness["paths"]] == [
        ["Pkg.Root", "Pkg.Left", "Pkg.A"],
        ["Pkg.Root", "Pkg.Right", "Pkg.B"],
    ]


def test_disconnected_exact_graph_preserves_inventory_candidate_only() -> None:
    modules = co_reachable_modules()
    modules["Pkg.Facade"] = module("Pkg.Facade")
    edges = {name: () for name in modules}
    result = analyze_declaration_integrity(
        modules,
        content_hashes={
            name: hashlib.sha256(name.encode()).hexdigest() for name in modules
        },
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        selected_edges=edges,
        selected_graph_coverage=exact_graph_coverage(len(edges)),
    )

    context = result.collision_groups[0].selected_context
    assert context is not None
    assert context.status == "not_observed"
    assert result.producer_registry.producers == {}
    assert result.co_reachable_coverage.total == 0


def test_partial_mismatched_and_dangling_graphs_fail_closed() -> None:
    modules = co_reachable_modules()
    exact_edges = {
        "Pkg.A": (),
        "Pkg.B": (),
        "Pkg.Facade": ("Pkg.A", "Pkg.B"),
    }
    partial_coverage = CollectionCoverage.exact(
        identity="module_dag.modules",
        pointer="#/sections/module_dag/module_metadata",
        visible=2,
        total=3,
        population="selected_internal_modules",
        scope="explicit_selection",
        authority="module_import_graph",
        causes=(
            CoverageCause(
                kind="projection",
                identifier="test.partial",
                detail="one selected module was projected away",
            ),
        ),
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
    )
    cases = (
        (exact_edges, partial_coverage),
        (
            exact_edges,
            exact_graph_coverage(
                len(exact_edges),
                source_fingerprint="sha256:stale",
            ),
        ),
        (
            {
                "Pkg.A": ("Pkg.Missing",),
                "Pkg.B": (),
                "Pkg.Facade": ("Pkg.A", "Pkg.B"),
            },
            exact_graph_coverage(len(exact_edges)),
        ),
    )

    for edges, coverage in cases:
        result = analyze_declaration_integrity(
            modules,
            content_hashes={
                name: hashlib.sha256(name.encode()).hexdigest() for name in modules
            },
            source_fingerprint=SOURCE_FINGERPRINT,
            scope_fingerprint=SCOPE_FINGERPRINT,
            selected_edges=edges,
            selected_graph_coverage=coverage,
        )
        context = result.collision_groups[0].selected_context
        assert context is not None
        assert context.status == "unavailable"
        assert result.producer_registry.producers == {}
        assert result.co_reachable_coverage.total_known is False


def test_incomplete_inventory_never_invents_partition_totals() -> None:
    modules = inventory_modules()
    result = analyze_declaration_integrity(
        modules,
        content_hashes=None,
        source_fingerprint=SOURCE_FINGERPRINT,
        scope_fingerprint=SCOPE_FINGERPRINT,
        inventory_complete=False,
    )

    assert result.collision_coverage.total_known is False
    assert result.collision_groups[0].member_coverage.total_known is False
    assert result.file_duplicate_coverage.total_known is False
    assert result.file_duplicate_coverage.completeness == "partial"
    assert result.to_dict()["exactFileDuplicateCandidates"] == []
