"""Private SQLite schema for Ladon's persistent proof-search index.

The tables are an alpha implementation detail. Public callers consume the
versioned result dictionaries returned by :mod:`ladon.proof_search_index`.
"""

from __future__ import annotations

import sqlite3

PROOF_SEARCH_INDEX_SCHEMA = "ladon-proof-search-index-v6"
PROOF_SEARCH_INDEX_SCHEMA_VERSION = 6
PROOF_SEARCH_SCHEMA_GENERATION = "sqlite-v6-name2-fts2-lineage1-proofir1-history1"
LEGACY_INDEX_SCHEMA = "ladon-proof-search-index-v5"
LEGACY_SCHEMA_GENERATION = "sqlite-v5-name2-fts2-lineage1-proofir1"
PROOF_SEARCH_HELPER_IDENTITY = "lexical-navigation-v4;theorem-lineage-v2;proofir-catalog-v3"
PRIOR_LEXICAL_HELPER_IDENTITY = "lexical-navigation-v3;theorem-lineage-v2;proofir-catalog-v3"

REQUIRED_LOOKUP_INDEX_COLUMNS = {
    "idx_alias_target": ("target", "source", "kind"),
    "idx_declarations_candidate_name": ("candidate_name", "name"),
    "idx_declarations_name": ("name", "candidate_name", "module"),
    "idx_declarations_name_casefold": ("name_casefold", "name", "module"),
    "idx_declarations_head": ("head", "arity", "name"),
    "idx_declaration_shapes_head": ("symbol_head", "arity", "coarse_key", "declaration_id"),
    "idx_binders_head": ("head", "is_premise", "declaration_id", "ordinal"),
    "idx_structures_module_status": ("module", "authority", "declaration_id"),
    "idx_structure_fields_status": ("status", "name", "structure_id", "ordinal"),
    "idx_module_semantic_status": ("status", "reason", "module"),
    "idx_declarations_kind": ("kind", "candidate_name"),
    "idx_declarations_module": ("module", "candidate_name"),
    "idx_declarations_namespace": ("namespace", "candidate_name"),
    "idx_declarations_package": ("package", "module", "candidate_name"),
    "idx_declarations_path": ("path", "line", "column_number"),
    "idx_declarations_structure": ("structure_name", "candidate_name"),
    "idx_dependency_target": ("target", "source", "kind"),
    "idx_import_target": ("target", "source"),
    "idx_modules_package": ("package", "generated", "name"),
    "idx_omissions_reason": ("reason", "kind", "subject"),
    "idx_source_roots_library": ("library", "generated", "path"),
    "idx_structure_field_name": ("name", "structure_id"),
    "idx_lineage_closures_active_theorem": ("theorem_name", "active"),
    "idx_lineage_closures_generation": ("base_generation_identity", "theorem_name"),
    "idx_lineage_nodes_boundary": ("closure_id", "external_frontier", "project_owned", "name"),
    "idx_lineage_nodes_owner": ("closure_id", "owner_module", "kind", "name"),
    "idx_lineage_edges_reverse": ("closure_id", "target", "kind", "source"),
    "idx_lineage_trust_target": ("closure_id", "target", "scope", "kind"),
    "idx_lineage_scc_member": ("closure_id", "member", "component_id"),
    "idx_proofir_generation_active": ("active", "generation_id"),
    "idx_proofir_artifact_kind": ("artifact_kind", "schema_version", "path"),
    "idx_proofir_artifact_path_hash": ("path", "sha256", "artifact_kind"),
    "idx_proofir_artifact_generation_state": ("generation_id", "state", "path"),
    "idx_proofir_relation_source": ("source_artifact_id", "kind", "target_artifact_id"),
    "idx_proofir_relation_target": ("target_artifact_id", "kind", "source_artifact_id"),
    "idx_proofir_diagnostic_reason": ("reason", "kind", "subject"),
    "idx_proofir_diagnostic_artifact": ("artifact_id", "reason", "subject"),
    "idx_proofir_diagnostic_generation": ("generation_id", "artifact_id"),
}
REQUIRED_LOOKUP_INDEXES = frozenset(REQUIRED_LOOKUP_INDEX_COLUMNS)
REQUIRED_QUERY_SURFACES = frozenset({"declaration_search"})
EXPECTED_FOREIGN_KEYS = frozenset(
    {
        ("module_imports", "source", "modules", "name"),
        ("declarations", "module", "modules", "name"),
        ("symbols", "declaration_id", "declarations", "id"),
        ("declaration_dependencies", "source", "symbols", "name"),
        ("declaration_dependencies", "target", "symbols", "name"),
        ("declaration_shapes", "declaration_id", "declarations", "id"),
        ("declaration_shapes", "symbol_head", "symbols", "name"),
        ("module_semantic_state", "module", "modules", "name"),
        ("binders", "declaration_id", "declarations", "id"),
        ("structures", "declaration_id", "declarations", "id"),
        ("structures", "module", "modules", "name"),
        ("structure_fields", "structure_id", "structures", "declaration_id"),
        ("lineage_nodes", "closure_id", "lineage_closures", "closure_id"),
        ("lineage_edges", "closure_id", "lineage_nodes", "closure_id"),
        ("lineage_edges", "source", "lineage_nodes", "name"),
        ("lineage_edges", "target", "lineage_nodes", "name"),
        ("lineage_trust", "closure_id", "lineage_closures", "closure_id"),
        ("lineage_trust", "target", "lineage_nodes", "name"),
        ("lineage_scc_members", "closure_id", "lineage_closures", "closure_id"),
        ("lineage_scc_members", "member", "lineage_nodes", "name"),
        ("lineage_omissions", "closure_id", "lineage_closures", "closure_id"),
        ("proofir_artifacts", "generation_id", "proofir_generations", "generation_id"),
        ("proofir_relations", "generation_id", "proofir_generations", "generation_id"),
        ("proofir_relations", "source_artifact_id", "proofir_artifacts", "artifact_id"),
        ("proofir_relations", "target_artifact_id", "proofir_artifacts", "artifact_id"),
        ("proofir_diagnostics", "generation_id", "proofir_generations", "generation_id"),
        ("proofir_diagnostics", "artifact_id", "proofir_artifacts", "artifact_id"),
    }
)


def create_proof_search_schema(connection: sqlite3.Connection) -> None:
    """Create one empty v1 index with explicit graph access paths."""

    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE index_history (
            snapshot_id TEXT PRIMARY KEY,
            entry_json TEXT NOT NULL
        );

        CREATE TABLE source_roots (
            path TEXT NOT NULL,
            library TEXT NOT NULL,
            origin TEXT NOT NULL,
            generated INTEGER NOT NULL CHECK(generated IN (0, 1)),
            module_roots_json TEXT NOT NULL,
            PRIMARY KEY(path, library, generated)
        );

        CREATE TABLE modules (
            name TEXT PRIMARY KEY,
            path TEXT NOT NULL UNIQUE,
            package TEXT NOT NULL,
            generated INTEGER NOT NULL CHECK(generated IN (0, 1)),
            source_sha256 TEXT NOT NULL,
            source_bytes INTEGER NOT NULL CHECK(source_bytes >= 0),
            line_count INTEGER NOT NULL CHECK(line_count >= 0),
            evidence_status TEXT NOT NULL CHECK(
                evidence_status IN ('lean-confirmed', 'lexical-fallback', 'unavailable')
            )
        );

        CREATE TABLE module_imports (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            line INTEGER CHECK(line IS NULL OR line > 0),
            column_number INTEGER CHECK(column_number IS NULL OR column_number > 0),
            authority TEXT NOT NULL,
            PRIMARY KEY(source, target),
            FOREIGN KEY(source) REFERENCES modules(name) ON DELETE CASCADE
        );

        CREATE TABLE declarations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            candidate_name TEXT,
            name_casefold TEXT NOT NULL DEFAULT '',
            name_segments TEXT NOT NULL DEFAULT '',
            namespace TEXT NOT NULL,
            kind TEXT NOT NULL,
            module TEXT NOT NULL,
            package TEXT NOT NULL,
            path TEXT NOT NULL,
            line INTEGER NOT NULL CHECK(line > 0),
            column_number INTEGER NOT NULL CHECK(column_number > 0),
            start_offset INTEGER NOT NULL CHECK(start_offset >= 0),
            end_offset INTEGER NOT NULL CHECK(end_offset >= start_offset),
            block_sha256 TEXT,
            type_text TEXT,
            type_text_bytes INTEGER NOT NULL CHECK(type_text_bytes >= 0),
            type_text_truncated INTEGER NOT NULL CHECK(type_text_truncated IN (0, 1)),
            type_status TEXT NOT NULL CHECK(
                type_status IN ('lean-rendered', 'lexical-signature', 'unavailable')
            ),
            authority TEXT NOT NULL CHECK(authority IN ('lean_environment', 'lexical_text')),
            privacy TEXT NOT NULL,
            locality TEXT NOT NULL,
            structure_name TEXT,
            doc_text TEXT NOT NULL DEFAULT '',
            rendered_type TEXT NOT NULL DEFAULT '',
            conclusion_text TEXT NOT NULL DEFAULT '',
            fingerprint TEXT NOT NULL DEFAULT '',
            head TEXT NOT NULL DEFAULT '',
            arity INTEGER NOT NULL DEFAULT 0 CHECK(arity >= 0),
            is_proposition INTEGER NOT NULL DEFAULT 0 CHECK(is_proposition IN (0, 1)),
            semantic_status TEXT NOT NULL DEFAULT 'unavailable',
            helper_identity TEXT NOT NULL DEFAULT '',
            lean_identity TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(module) REFERENCES modules(name) ON DELETE CASCADE
        );

        CREATE TABLE binders (
            declaration_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
            name TEXT NOT NULL,
            binder_info TEXT NOT NULL,
            type_text TEXT NOT NULL,
            is_premise INTEGER NOT NULL CHECK(is_premise IN (0, 1)),
            authority TEXT NOT NULL,
            head TEXT NOT NULL DEFAULT '',
            PRIMARY KEY(declaration_id, ordinal),
            FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE CASCADE
        );

        CREATE TABLE declaration_dependencies (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            kind TEXT NOT NULL,
            authority TEXT NOT NULL,
            status TEXT NOT NULL,
            PRIMARY KEY(source, target, kind, authority),
            FOREIGN KEY(source) REFERENCES symbols(name) ON DELETE CASCADE,
            FOREIGN KEY(target) REFERENCES symbols(name) ON DELETE CASCADE
        ) WITHOUT ROWID;

        CREATE TABLE symbols (
            name TEXT PRIMARY KEY,
            declaration_id TEXT UNIQUE,
            kind TEXT NOT NULL,
            ownership TEXT NOT NULL,
            FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE SET NULL
        );

        CREATE TABLE declaration_shapes (
            declaration_id TEXT PRIMARY KEY,
            role TEXT NOT NULL,
            key_version TEXT NOT NULL,
            symbol_head TEXT,
            arity INTEGER NOT NULL CHECK(arity >= 0),
            shape_hash TEXT NOT NULL,
            coarse_key TEXT NOT NULL,
            authority TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
            FOREIGN KEY(symbol_head) REFERENCES symbols(name) ON DELETE SET NULL
        );

        CREATE TABLE module_semantic_state (
            module TEXT PRIMARY KEY,
            source_fingerprint TEXT NOT NULL,
            compiled_fingerprint TEXT NOT NULL,
            import_fingerprint TEXT NOT NULL,
            surface_fingerprint TEXT NOT NULL,
            helper_identity TEXT NOT NULL,
            lean_identity TEXT NOT NULL,
            status TEXT NOT NULL,
            reason TEXT NOT NULL,
            declaration_count INTEGER NOT NULL CHECK(declaration_count >= 0),
            dependency_count INTEGER NOT NULL CHECK(dependency_count >= 0),
            FOREIGN KEY(module) REFERENCES modules(name) ON DELETE CASCADE
        );

        CREATE TABLE structures (
            declaration_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            module TEXT NOT NULL,
            authority TEXT NOT NULL,
            FOREIGN KEY(declaration_id) REFERENCES declarations(id) ON DELETE CASCADE,
            FOREIGN KEY(module) REFERENCES modules(name) ON DELETE CASCADE
        );

        CREATE TABLE structure_fields (
            structure_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
            name TEXT NOT NULL,
            type_text TEXT,
            authority TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('complete', 'partial', 'unavailable')),
            PRIMARY KEY(structure_id, ordinal),
            FOREIGN KEY(structure_id) REFERENCES structures(declaration_id) ON DELETE CASCADE
        );

        CREATE TABLE aliases (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            kind TEXT NOT NULL,
            authority TEXT NOT NULL,
            PRIMARY KEY(source, target, kind)
        );

        CREATE TABLE lineage_closures (
            closure_id TEXT PRIMARY KEY,
            theorem_name TEXT NOT NULL,
            theorem_module TEXT,
            theorem_path TEXT,
            plan_identity TEXT NOT NULL,
            semantic_closure_fingerprint TEXT NOT NULL,
            repository TEXT NOT NULL,
            source_fingerprint TEXT NOT NULL,
            configuration_fingerprint TEXT NOT NULL,
            toolchain_identity TEXT NOT NULL,
            helper_identity TEXT NOT NULL,
            base_generation_identity TEXT NOT NULL,
            schema_generation TEXT NOT NULL,
            authority TEXT NOT NULL CHECK(authority = 'lean_environment'),
            semantic_status TEXT NOT NULL CHECK(semantic_status = 'complete'),
            active INTEGER NOT NULL CHECK(active IN (0, 1)),
            unsupported_facets_json TEXT NOT NULL,
            node_count INTEGER NOT NULL CHECK(node_count >= 0),
            edge_count INTEGER NOT NULL CHECK(edge_count >= 0),
            created_identity TEXT NOT NULL
        );

        CREATE TABLE lineage_nodes (
            closure_id TEXT NOT NULL,
            name TEXT NOT NULL,
            owner_module TEXT NOT NULL,
            kind TEXT NOT NULL,
            project_owned INTEGER NOT NULL CHECK(project_owned IN (0, 1)),
            external_frontier INTEGER NOT NULL CHECK(external_frontier IN (0, 1)),
            compiler_generated INTEGER NOT NULL CHECK(compiler_generated IN (0, 1)),
            declared_axiom INTEGER NOT NULL CHECK(declared_axiom IN (0, 1)),
            unsafe INTEGER NOT NULL CHECK(unsafe IN (0, 1)),
            source_path TEXT,
            source_line INTEGER CHECK(source_line IS NULL OR source_line > 0),
            source_column INTEGER CHECK(source_column IS NULL OR source_column > 0),
            source_status TEXT NOT NULL CHECK(source_status IN ('available', 'unavailable')),
            type_fingerprint TEXT,
            value_fingerprint TEXT,
            PRIMARY KEY(closure_id, name),
            FOREIGN KEY(closure_id) REFERENCES lineage_closures(closure_id) ON DELETE CASCADE
        );

        CREATE TABLE lineage_edges (
            closure_id TEXT NOT NULL,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('type', 'value')),
            target_owner_module TEXT NOT NULL,
            target_kind TEXT NOT NULL,
            PRIMARY KEY(closure_id, source, kind, target),
            FOREIGN KEY(closure_id, source)
                REFERENCES lineage_nodes(closure_id, name) ON DELETE CASCADE,
            FOREIGN KEY(closure_id, target)
                REFERENCES lineage_nodes(closure_id, name) ON DELETE CASCADE
        ) WITHOUT ROWID;

        CREATE TABLE lineage_trust (
            closure_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            scope TEXT NOT NULL CHECK(scope IN ('type', 'value', 'declaration')),
            target TEXT NOT NULL,
            PRIMARY KEY(closure_id, kind, scope, target),
            FOREIGN KEY(closure_id) REFERENCES lineage_closures(closure_id) ON DELETE CASCADE,
            FOREIGN KEY(closure_id, target)
                REFERENCES lineage_nodes(closure_id, name) ON DELETE CASCADE
        );

        CREATE TABLE lineage_scc_members (
            closure_id TEXT NOT NULL,
            component_id TEXT NOT NULL,
            member TEXT NOT NULL,
            cyclic INTEGER NOT NULL CHECK(cyclic IN (0, 1)),
            PRIMARY KEY(closure_id, component_id, member),
            FOREIGN KEY(closure_id) REFERENCES lineage_closures(closure_id) ON DELETE CASCADE,
            FOREIGN KEY(closure_id, member)
                REFERENCES lineage_nodes(closure_id, name) ON DELETE CASCADE
        );

        CREATE TABLE lineage_omissions (
            closure_id TEXT NOT NULL,
            facet TEXT NOT NULL,
            subject TEXT NOT NULL,
            reason TEXT NOT NULL,
            details_json TEXT NOT NULL,
            PRIMARY KEY(closure_id, facet, subject, reason),
            FOREIGN KEY(closure_id) REFERENCES lineage_closures(closure_id) ON DELETE CASCADE
        );

        CREATE TABLE proofir_generations (
            generation_id TEXT PRIMARY KEY,
            config_json TEXT NOT NULL,
            artifact_count INTEGER NOT NULL CHECK(artifact_count >= 0),
            total_bytes INTEGER NOT NULL CHECK(total_bytes >= 0),
            active INTEGER NOT NULL CHECK(active IN (0, 1)),
            status TEXT NOT NULL CHECK(status IN ('configured', 'not-configured'))
        );

        CREATE TABLE proofir_artifacts (
            artifact_id TEXT PRIMARY KEY,
            generation_id TEXT NOT NULL,
            path TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            byte_size INTEGER NOT NULL CHECK(byte_size >= 0),
            artifact_kind TEXT NOT NULL,
            schema_version TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('cataloged', 'unsupported', 'malformed')),
            metadata_json TEXT NOT NULL,
            diagnostic TEXT,
            UNIQUE(generation_id, path, sha256),
            FOREIGN KEY(generation_id) REFERENCES proofir_generations(generation_id) ON DELETE CASCADE
        );

        CREATE TABLE proofir_relations (
            relation_id TEXT PRIMARY KEY,
            generation_id TEXT NOT NULL,
            source_artifact_id TEXT NOT NULL,
            target_artifact_id TEXT NOT NULL,
            kind TEXT NOT NULL,
            details_json TEXT NOT NULL,
            UNIQUE(generation_id, source_artifact_id, target_artifact_id, kind),
            FOREIGN KEY(generation_id) REFERENCES proofir_generations(generation_id) ON DELETE CASCADE,
            FOREIGN KEY(source_artifact_id) REFERENCES proofir_artifacts(artifact_id) ON DELETE CASCADE,
            FOREIGN KEY(target_artifact_id) REFERENCES proofir_artifacts(artifact_id) ON DELETE CASCADE
        );

        CREATE TABLE proofir_diagnostics (
            diagnostic_id TEXT PRIMARY KEY,
            generation_id TEXT NOT NULL,
            artifact_id TEXT,
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            reason TEXT NOT NULL,
            details_json TEXT NOT NULL,
            FOREIGN KEY(generation_id) REFERENCES proofir_generations(generation_id) ON DELETE CASCADE,
            FOREIGN KEY(artifact_id) REFERENCES proofir_artifacts(artifact_id) ON DELETE CASCADE
        );

        CREATE VIRTUAL TABLE declaration_search USING fts5(
            candidate_name,
            name_segments,
            namespace,
            module,
            package,
            doc_text,
            rendered_type,
            conclusion_text,
            type_text,
            content='declarations',
            content_rowid='rowid',
            tokenize='unicode61'
        );

        CREATE TABLE evidence_coverage (
            collection TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            authority TEXT NOT NULL,
            reason TEXT,
            observed INTEGER NOT NULL CHECK(observed >= 0),
            total_known INTEGER NOT NULL CHECK(total_known IN (0, 1))
        );

        CREATE TABLE omissions (
            kind TEXT NOT NULL,
            subject TEXT NOT NULL,
            reason TEXT NOT NULL,
            details_json TEXT NOT NULL,
            PRIMARY KEY(kind, subject, reason)
        );

        CREATE INDEX idx_declarations_candidate_name
            ON declarations(candidate_name, name);
        CREATE INDEX idx_declarations_name
            ON declarations(name, candidate_name, module);
        CREATE INDEX idx_declarations_name_casefold
            ON declarations(name_casefold, name, module);
        CREATE INDEX idx_declarations_head
            ON declarations(head, arity, name) WHERE head <> '';
        CREATE INDEX idx_declaration_shapes_head
            ON declaration_shapes(symbol_head, arity, coarse_key, declaration_id);
        CREATE INDEX idx_binders_head
            ON binders(head, is_premise, declaration_id, ordinal)
            WHERE head <> '';
        CREATE INDEX idx_structures_module_status
            ON structures(module, authority, declaration_id);
        CREATE INDEX idx_structure_fields_status
            ON structure_fields(status, name, structure_id, ordinal);
        CREATE INDEX idx_module_semantic_status
            ON module_semantic_state(status, reason, module);
        CREATE INDEX idx_declarations_kind
            ON declarations(kind, candidate_name);
        CREATE INDEX idx_declarations_module
            ON declarations(module, candidate_name);
        CREATE INDEX idx_declarations_namespace
            ON declarations(namespace, candidate_name);
        CREATE INDEX idx_declarations_package
            ON declarations(package, module, candidate_name);
        CREATE INDEX idx_declarations_path
            ON declarations(path, line, column_number);
        CREATE INDEX idx_declarations_structure
            ON declarations(structure_name, candidate_name)
            WHERE structure_name IS NOT NULL;
        CREATE INDEX idx_import_target
            ON module_imports(target, source);
        CREATE INDEX idx_dependency_target
            ON declaration_dependencies(target, source, kind);
        CREATE INDEX idx_alias_target
            ON aliases(target, source, kind);
        CREATE INDEX idx_modules_package
            ON modules(package, generated, name);
        CREATE INDEX idx_source_roots_library
            ON source_roots(library, generated, path);
        CREATE INDEX idx_structure_field_name
            ON structure_fields(name, structure_id);
        CREATE INDEX idx_omissions_reason
            ON omissions(reason, kind, subject);
        CREATE UNIQUE INDEX idx_lineage_closures_active_theorem
            ON lineage_closures(theorem_name, active) WHERE active = 1;
        CREATE INDEX idx_lineage_closures_generation
            ON lineage_closures(base_generation_identity, theorem_name);
        CREATE INDEX idx_lineage_nodes_boundary
            ON lineage_nodes(closure_id, external_frontier, project_owned, name);
        CREATE INDEX idx_lineage_nodes_owner
            ON lineage_nodes(closure_id, owner_module, kind, name);
        CREATE INDEX idx_lineage_edges_reverse
            ON lineage_edges(closure_id, target, kind, source);
        CREATE INDEX idx_lineage_trust_target
            ON lineage_trust(closure_id, target, scope, kind);
        CREATE INDEX idx_lineage_scc_member
            ON lineage_scc_members(closure_id, member, component_id);
        CREATE INDEX idx_proofir_generation_active
            ON proofir_generations(active, generation_id);
        CREATE UNIQUE INDEX idx_proofir_generation_active_unique
            ON proofir_generations(active) WHERE active = 1;
        CREATE INDEX idx_proofir_artifact_kind
            ON proofir_artifacts(artifact_kind, schema_version, path);
        CREATE INDEX idx_proofir_artifact_path_hash
            ON proofir_artifacts(path, sha256, artifact_kind);
        CREATE INDEX idx_proofir_artifact_generation_state
            ON proofir_artifacts(generation_id, state, path);
        CREATE INDEX idx_proofir_relation_source
            ON proofir_relations(source_artifact_id, kind, target_artifact_id);
        CREATE INDEX idx_proofir_relation_target
            ON proofir_relations(target_artifact_id, kind, source_artifact_id);
        CREATE INDEX idx_proofir_diagnostic_reason
            ON proofir_diagnostics(reason, kind, subject);
        CREATE INDEX idx_proofir_diagnostic_artifact
            ON proofir_diagnostics(artifact_id, reason, subject);
        CREATE INDEX idx_proofir_diagnostic_generation
            ON proofir_diagnostics(generation_id, artifact_id);
        """
    )


def schema_lookup_indexes(connection: sqlite3.Connection) -> frozenset[str]:
    """Return the named non-auto indexes installed in one database."""

    rows = connection.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'index' AND sql IS NOT NULL"
    )
    return frozenset(str(row[0]) for row in rows)


def schema_query_surfaces(connection: sqlite3.Connection) -> frozenset[str]:
    """Return private virtual-table query surfaces installed in a database."""

    rows = connection.execute(
        "SELECT name FROM sqlite_schema WHERE type = 'table' AND sql LIKE 'CREATE VIRTUAL TABLE%'"
    )
    return frozenset(str(row[0]) for row in rows)


def schema_index_columns(
    connection: sqlite3.Connection,
) -> dict[str, tuple[str, ...]]:
    """Return ordered indexed columns for every required lookup index."""

    return {
        name: tuple(
            str(row[2])
            for row in connection.execute(f"PRAGMA index_info({name})")
        )
        for name in REQUIRED_LOOKUP_INDEXES
    }


def schema_foreign_keys(
    connection: sqlite3.Connection,
) -> frozenset[tuple[str, str, str, str]]:
    """Return declared table/column foreign-key relationships."""

    tables = (
        "source_roots",
        "modules",
        "module_imports",
        "declarations",
        "binders",
        "declaration_dependencies",
        "symbols",
        "declaration_shapes",
        "module_semantic_state",
        "structures",
        "structure_fields",
        "aliases",
        "evidence_coverage",
        "omissions",
        "lineage_closures",
        "lineage_nodes",
        "lineage_edges",
        "lineage_trust",
        "lineage_scc_members",
        "lineage_omissions",
        "proofir_generations",
        "proofir_artifacts",
        "proofir_relations",
        "proofir_diagnostics",
    )
    rows = []
    for table in tables:
        rows.extend(
            (table, str(row[3]), str(row[2]), str(row[4]))
            for row in connection.execute(f"PRAGMA foreign_key_list({table})")
        )
    return frozenset(rows)


def schema_foreign_key_index_gaps(connection: sqlite3.Connection) -> list[dict[str, object]]:
    """Report child foreign-key prefixes lacking a primary/explicit index."""
    gaps: list[dict[str, object]] = []
    tables = [str(row[0]) for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    for table in tables:
        gaps.extend(_foreign_key_gaps_for_table(connection, table))
    return gaps


def _foreign_key_gaps_for_table(connection: sqlite3.Connection, table: str) -> list[dict[str, object]]:
    grouped: dict[int, list[tuple[int, str]]] = {}
    for row in connection.execute(f"PRAGMA foreign_key_list({table})"):
        grouped.setdefault(int(row[0]), []).append((int(row[1]), str(row[3])))
    indexes = [tuple(str(item[2]) for item in connection.execute(f"PRAGMA index_info({row[1]})")) for row in connection.execute(f"PRAGMA index_list({table})")]
    return [{"table": table, "columns": list(child), "reason": "missing-child-key-prefix"} for columns in grouped.values() if (child := tuple(column for _, column in sorted(columns))) and not any(index[: len(child)] == child for index in indexes)]


__all__ = [
    "EXPECTED_FOREIGN_KEYS",
    "PROOF_SEARCH_HELPER_IDENTITY",
    "PROOF_SEARCH_INDEX_SCHEMA",
    "PROOF_SEARCH_INDEX_SCHEMA_VERSION",
    "PROOF_SEARCH_SCHEMA_GENERATION",
    "REQUIRED_LOOKUP_INDEXES",
    "REQUIRED_LOOKUP_INDEX_COLUMNS",
    "REQUIRED_QUERY_SURFACES",
    "create_proof_search_schema",
    "schema_foreign_key_index_gaps",
    "schema_foreign_keys",
    "schema_index_columns",
    "schema_lookup_indexes",
    "schema_query_surfaces",
]
