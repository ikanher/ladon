"""Lean-authoritative theorem-lineage persistence for the local SQLite index."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ladon.proof_search_schema import PROOF_SEARCH_SCHEMA_GENERATION
from ladon.theorem_capsule_models import canonical_json_bytes, sha256_bytes


class TheoremLineageError(RuntimeError):
    """A theorem lineage plan cannot be safely normalized or stored."""


@dataclass(frozen=True)
class LineageIdentity:
    """Current repository/index identities used to validate one closure."""

    repository: str
    source_fingerprint: str
    configuration_fingerprint: str
    toolchain_identity: str
    base_generation_identity: str
    helper_identity: str
    schema_generation: str = PROOF_SEARCH_SCHEMA_GENERATION


@dataclass(frozen=True)
class LineageNode:
    """One declaration or explicit external frontier endpoint."""

    name: str
    owner_module: str
    kind: str
    project_owned: bool
    external_frontier: bool
    compiler_generated: bool
    declared_axiom: bool
    unsafe: bool
    source_path: str | None = None
    source_line: int | None = None
    source_column: int | None = None
    source_status: str = "unavailable"
    type_fingerprint: str | None = None
    value_fingerprint: str | None = None


@dataclass(frozen=True)
class LineageBundle:
    """Validated, normalized semantic graph ready for one transaction."""

    target_name: str
    target_module: str | None
    target_path: str | None
    plan_identity: str
    closure_fingerprint: str
    nodes: tuple[LineageNode, ...]
    edges: tuple[dict[str, str], ...]
    trust: tuple[dict[str, str], ...]
    scc_members: tuple[dict[str, Any], ...]
    omissions: tuple[dict[str, str], ...]
    unsupported_facets: tuple[str, ...]


def normalize_lineage_plan(plan: Mapping[str, Any]) -> LineageBundle:
    """Validate a complete theorem plan and normalize all graph endpoints."""

    graph = _mapping(plan.get("semanticGraph"), "semanticGraph")
    _validate_graph_header(graph)
    target = _mapping(plan.get("target"), "target")
    target_name = _required_string(target, "name")
    nodes, edges, trust, scc_members = _normalize_graph_components(plan, graph, target)
    closure_body = {
        "nodes": graph.get("nodes", []),
        "edges": graph.get("edges", []),
    }
    closure_fingerprint = _closure_fingerprint(graph, closure_body)
    plan_identity = str(plan.get("planIdentity") or _digest({"target": target, "graph": closure_body}))
    omissions = _unsupported_omissions(graph)
    return LineageBundle(
        target_name=target_name,
        target_module=str(target.get("module")) if target.get("module") else None,
        target_path=str(target.get("path")) if target.get("path") else None,
        plan_identity=plan_identity,
        closure_fingerprint=closure_fingerprint,
        nodes=tuple(nodes[name] for name in sorted(nodes)),
        edges=tuple(edges),
        trust=tuple(trust),
        scc_members=tuple(scc_members),
        omissions=omissions,
        unsupported_facets=tuple(str(value) for value in graph.get("unsupportedFacets", ()) if value),
    )


def _normalize_graph_components(
    plan: Mapping[str, Any],
    graph: Mapping[str, Any],
    target: Mapping[str, Any],
) -> tuple[dict[str, LineageNode], list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    local_rows = _local_rows(graph)
    modules = _project_modules(plan, target)
    nodes = _local_nodes(local_rows, modules)
    edges = _normalized_edges(graph)
    _validate_edge_count(graph, edges)
    _materialize_frontier_nodes(nodes, edges, modules)
    return (
        nodes,
        edges,
        _normalized_trust(graph.get("trustFrontier"), nodes),
        _normalized_scc(graph.get("stronglyConnectedComponents"), nodes),
    )


def _closure_fingerprint(graph: Mapping[str, Any], body: Mapping[str, Any]) -> str:
    computed = sha256_bytes(canonical_json_bytes(body))
    declared = str(graph.get("closureFingerprint") or "")
    if declared and declared != computed:
        raise TheoremLineageError("semantic closure fingerprint disagrees with graph")
    return declared or computed


def _unsupported_omissions(graph: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "facet": "semantic",
            "subject": str(value),
            "reason": "unsupported_facet",
            "details": str(value),
        }
        for value in graph.get("unsupportedFacets", ())
        if value
    )


def _validate_graph_header(graph: Mapping[str, Any]) -> None:
    if graph.get("status") != "complete":
        raise TheoremLineageError("semantic graph is not complete")
    if graph.get("authority") != "lean_environment":
        raise TheoremLineageError("semantic graph authority is not Lean environment")
    if not graph.get("helperChecksum"):
        raise TheoremLineageError("semantic graph helper checksum is missing")


def _local_rows(graph: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    local_rows = graph.get("nodes")
    if not isinstance(local_rows, list):
        raise TheoremLineageError("semantic graph nodes are malformed")
    expected = _optional_int(graph.get("nodeCount"))
    if expected is not None and expected != len(local_rows):
        raise TheoremLineageError("semantic graph node count disagrees with nodes")
    return [row for row in local_rows if isinstance(row, Mapping)]


def _project_modules(plan: Mapping[str, Any], target: Mapping[str, Any]) -> set[str]:
    build_graph = plan.get("buildGraph") or {}
    if not isinstance(build_graph, Mapping):
        raise TheoremLineageError("buildGraph is malformed")
    modules = {
        str(module.get("module"))
        for module in _rows(build_graph.get("modules"))
        if module.get("module")
    }
    if not modules and target.get("module"):
        modules.add(str(target["module"]))
    return modules


def _local_nodes(rows: list[Mapping[str, Any]], modules: set[str]) -> dict[str, LineageNode]:
    nodes: dict[str, LineageNode] = {}
    for row in rows:
        node = _node_from_row(row, project_owned=_owner_is_project(row, modules))
        _insert_node(nodes, node)
    return nodes


def _validate_edge_count(graph: Mapping[str, Any], edges: list[dict[str, str]]) -> None:
    expected = _optional_int(graph.get("edgeCount"))
    if expected is not None and expected != len(edges):
        raise TheoremLineageError("semantic graph edge count disagrees with edges")


def _materialize_frontier_nodes(
    nodes: dict[str, LineageNode],
    edges: list[dict[str, str]],
    modules: set[str],
) -> None:
    for edge in edges:
        if edge["source"] not in nodes:
            raise TheoremLineageError(f"lineage edge source is not a node: {edge['source']}")
        if edge["target"] not in nodes:
            nodes[edge["target"]] = LineageNode(
                name=edge["target"],
                owner_module=edge["targetOwnerModule"],
                kind=edge["targetKind"],
                project_owned=edge["targetOwnerModule"] in modules,
                external_frontier=True,
                compiler_generated=False,
                declared_axiom=False,
                unsafe=False,
            )
def ingest_theorem_lineage(
    connection: sqlite3.Connection,
    plan: Mapping[str, Any],
    identity: LineageIdentity,
    *,
    max_bytes: int | None = None,
) -> dict[str, Any]:
    """Validate and atomically replace one active theorem closure."""

    bundle = normalize_lineage_plan(plan)
    closure_id = _digest(
        {
            "theorem": bundle.target_name,
            "plan": bundle.plan_identity,
            "closure": bundle.closure_fingerprint,
            "base": identity.base_generation_identity,
        }
    )
    unsupported = json.dumps(list(bundle.unsupported_facets), sort_keys=True)
    started = time.monotonic()
    before_pages = _page_snapshot(connection)
    before_objects = _object_bytes(connection)
    preflight = {
        "estimatedRows": len(bundle.nodes) + len(bundle.edges) + len(bundle.trust) + len(bundle.scc_members) + len(bundle.omissions),
        "estimatedBytes": _estimate_bundle_bytes(bundle),
        "authority": "advisory",
    }
    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "UPDATE lineage_closures SET active = 0 WHERE theorem_name = ? AND active = 1",
            (bundle.target_name,),
        )
        connection.execute("DELETE FROM lineage_closures WHERE closure_id = ?", (closure_id,))
        connection.execute(
            """
            INSERT INTO lineage_closures(
                closure_id, theorem_name, theorem_module, theorem_path, plan_identity,
                semantic_closure_fingerprint, repository, source_fingerprint,
                configuration_fingerprint, toolchain_identity, helper_identity,
                base_generation_identity, schema_generation, authority, semantic_status,
                active, unsupported_facets_json, node_count, edge_count, created_identity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'lean_environment',
                      'complete', 1, ?, ?, ?, ?)
            """,
            (
                closure_id,
                bundle.target_name,
                bundle.target_module,
                bundle.target_path,
                bundle.plan_identity,
                bundle.closure_fingerprint,
                identity.repository,
                identity.source_fingerprint,
                identity.configuration_fingerprint,
                identity.toolchain_identity,
                identity.helper_identity,
                identity.base_generation_identity,
                identity.schema_generation,
                unsupported,
                len(bundle.nodes),
                len(bundle.edges),
                closure_id,
            ),
        )
        connection.executemany(
            """
            INSERT INTO lineage_nodes(
                closure_id, name, owner_module, kind, project_owned, external_frontier,
                compiler_generated, declared_axiom, unsafe, source_path, source_line,
                source_column, source_status, type_fingerprint, value_fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                (
                    closure_id, node.name, node.owner_module, node.kind,
                    int(node.project_owned), int(node.external_frontier),
                    int(node.compiler_generated), int(node.declared_axiom), int(node.unsafe),
                    node.source_path, node.source_line, node.source_column,
                    node.source_status, node.type_fingerprint, node.value_fingerprint,
                )
                for node in bundle.nodes
            ),
        )
        connection.executemany(
            "INSERT INTO lineage_edges(closure_id, source, target, kind, target_owner_module, target_kind) VALUES (?, ?, ?, ?, ?, ?)",
            (
                (
                    closure_id, edge["source"], edge["target"], edge["kind"],
                    edge["targetOwnerModule"], edge["targetKind"],
                )
                for edge in bundle.edges
            ),
        )
        connection.executemany(
            "INSERT INTO lineage_trust(closure_id, kind, scope, target) VALUES (?, ?, ?, ?)",
            ((closure_id, row["kind"], row["scope"], row["target"]) for row in bundle.trust),
        )
        connection.executemany(
            "INSERT INTO lineage_scc_members(closure_id, component_id, member, cyclic) VALUES (?, ?, ?, ?)",
            (
                (closure_id, row["componentId"], row["member"], int(row["cyclic"]))
                for row in bundle.scc_members
            ),
        )
        connection.executemany(
            "INSERT INTO lineage_omissions(closure_id, facet, subject, reason, details_json) VALUES (?, ?, ?, ?, ?)",
            (
                (closure_id, row["facet"], row["subject"], row["reason"], row["details"])
                for row in bundle.omissions
            ),
        )
        _refresh_lineage_statistics(connection)
        _validate_lineage_access_paths(connection)
        _enforce_lineage_budget(connection, max_bytes)
        _check_connection(connection)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    after_pages = _page_snapshot(connection)
    after_objects = _object_bytes(connection)
    return {
        "closureId": closure_id,
        "theorem": bundle.target_name,
        "nodeCount": len(bundle.nodes),
        "edgeCount": len(bundle.edges),
        "authority": "lean_environment",
        "status": "complete",
        "storage": {
            "before": before_pages,
            "after": after_pages,
            "marginalBytes": after_pages["allocatedBytes"] - before_pages["allocatedBytes"],
            "marginalObjects": {
                key: after_objects.get(key, 0) - before_objects.get(key, 0)
                for key in sorted(set(before_objects) | set(after_objects))
                if after_objects.get(key, 0) != before_objects.get(key, 0)
            },
        },
        "statistics": {"refreshed": True, "tables": ["lineage_edges", "lineage_nodes", "lineage_trust", "lineage_scc_members", "lineage_omissions"]},
        "preflight": preflight,
        "elapsedSeconds": round(time.monotonic() - started, 6),
    }


def _page_snapshot(connection: sqlite3.Connection) -> dict[str, int]:
    page_size = int(connection.execute("PRAGMA page_size").fetchone()[0])
    page_count = int(connection.execute("PRAGMA page_count").fetchone()[0])
    return {"pageSize": page_size, "pageCount": page_count, "allocatedBytes": page_size * page_count}


def _estimate_bundle_bytes(bundle: Any) -> int:
    """Conservative advisory estimate; allocated bytes remain authoritative."""
    return (len(bundle.nodes) * 256) + (len(bundle.edges) * 128) + ((len(bundle.trust) + len(bundle.scc_members) + len(bundle.omissions)) * 96)


def _object_bytes(connection: sqlite3.Connection) -> dict[str, int]:
    try:
        rows = connection.execute("SELECT name,SUM(pgsize) FROM dbstat GROUP BY name").fetchall()
    except sqlite3.Error:
        return {}
    return {str(name): int(size or 0) for name, size in rows}


def _refresh_lineage_statistics(connection: sqlite3.Connection) -> None:
    for table in ("lineage_closures", "lineage_nodes", "lineage_edges", "lineage_trust", "lineage_scc_members", "lineage_omissions"):
        connection.execute(f"ANALYZE {table}")


def _enforce_lineage_budget(connection: sqlite3.Connection, max_bytes: int | None) -> None:
    if max_bytes is None:
        return
    connection.execute(
        "INSERT OR REPLACE INTO metadata(key,value) VALUES ('completeDatabaseMaxBytes',?)",
        (str(max_bytes),),
    )
    connection.execute(
        "INSERT OR REPLACE INTO metadata(key,value) VALUES ('completeDatabaseBudgetPolicy','lineage-cli')"
    )
    if _page_snapshot(connection)["allocatedBytes"] > max_bytes:
        raise TheoremLineageError("lineage ingestion exceeds configured size limit")


def _validate_lineage_access_paths(connection: sqlite3.Connection) -> None:
    forward = connection.execute(
        "EXPLAIN QUERY PLAN SELECT target FROM lineage_edges WHERE closure_id=? AND source=?",
        ("<closure>", "<source>"),
    ).fetchall()
    reverse = connection.execute(
        "EXPLAIN QUERY PLAN SELECT source FROM lineage_edges WHERE closure_id=? AND target=?",
        ("<closure>", "<target>"),
    ).fetchall()
    forward_text = " ".join(str(tuple(row)) for row in forward)
    reverse_text = " ".join(str(tuple(row)) for row in reverse)
    if "lineage_edges" not in forward_text or "source=?" not in forward_text:
        raise TheoremLineageError("lineage forward access path is unavailable")
    if "lineage_edges" not in reverse_text or "target=?" not in reverse_text:
        raise TheoremLineageError("lineage reverse access path is unavailable")


def inspect_lineage_closure(
    connection: sqlite3.Connection,
    theorem: str,
    identity: LineageIdentity,
) -> dict[str, Any]:
    """Inspect one closure against current repository/index identities."""

    row = connection.execute(
        "SELECT * FROM lineage_closures WHERE theorem_name = ? AND active = 1",
        (theorem,),
    ).fetchone()
    if row is None:
        return {"status": "unavailable", "reason": "not_ingested", "theorem": theorem}
    description = connection.execute("SELECT * FROM lineage_closures LIMIT 0").description
    fields = {column[0]: row[index] for index, column in enumerate(description or ())}
    checks = (
        ("repository", identity.repository),
        ("source_fingerprint", identity.source_fingerprint),
        ("configuration_fingerprint", identity.configuration_fingerprint),
        ("toolchain_identity", identity.toolchain_identity),
        ("base_generation_identity", identity.base_generation_identity),
        ("helper_identity", identity.helper_identity),
        ("schema_generation", identity.schema_generation),
    )
    for field, expected in checks:
        if fields[field] != expected:
            reason = {
                "source_fingerprint": "stale-source",
                "configuration_fingerprint": "stale-configuration",
                "toolchain_identity": "stale-toolchain",
                "schema_generation": "incompatible-schema",
            }.get(field, "stale-identity")
            return {"status": reason, "theorem": theorem, "closureId": fields["closure_id"]}
    return {
        "status": "fresh",
        "theorem": theorem,
        "closureId": fields["closure_id"],
        "nodeCount": fields["node_count"],
        "edgeCount": fields["edge_count"],
        "authority": fields["authority"],
    }


def _normalized_edges(graph: Mapping[str, Any]) -> list[dict[str, str]]:
    raw_edges = graph.get("edges")
    if not isinstance(raw_edges, list):
        raw_edges = []
        for node in graph.get("nodes", []):
            for kind, key in (("type", "typeDependencies"), ("value", "valueDependencies")):
                for dependency in _rows(node.get(key)):
                    raw_edges.append(
                        {
                            "source": node.get("name"),
                            "target": dependency.get("name"),
                            "kind": kind,
                            "targetOwnerModule": dependency.get("ownerModule"),
                            "targetKind": dependency.get("kind"),
                        }
                    )
    edges: dict[tuple[str, str, str], dict[str, str]] = {}
    for raw in raw_edges:
        edge = {
            "source": _required_string(raw, "source"),
            "target": _required_string(raw, "target"),
            "kind": _required_string(raw, "kind"),
            "targetOwnerModule": _required_string(raw, "targetOwnerModule"),
            "targetKind": _required_string(raw, "targetKind"),
        }
        if edge["kind"] not in {"type", "value"}:
            raise TheoremLineageError(f"unsupported lineage edge kind: {edge['kind']}")
        key = (edge["source"], edge["target"], edge["kind"])
        previous = edges.get(key)
        if previous is not None and previous != edge:
            raise TheoremLineageError("conflicting duplicate lineage edge")
        edges[key] = edge
    return [edges[key] for key in sorted(edges)]


def _node_from_row(row: Mapping[str, Any], *, project_owned: bool) -> LineageNode:
    return LineageNode(
        name=_required_string(row, "name"),
        owner_module=_required_string(row, "ownerModule"),
        kind=_required_string(row, "kind"),
        project_owned=project_owned,
        external_frontier=False,
        compiler_generated=bool(row.get("compilerGenerated")),
        declared_axiom=bool(row.get("declaredAxiom")),
        unsafe=bool(row.get("unsafe")),
        type_fingerprint=_optional_string(row.get("typeFingerprint")),
        value_fingerprint=_optional_string(row.get("valueFingerprint")),
    )


def _insert_node(nodes: dict[str, LineageNode], node: LineageNode) -> None:
    previous = nodes.get(node.name)
    if previous is not None and previous != node:
        raise TheoremLineageError(f"conflicting duplicate lineage node: {node.name}")
    nodes[node.name] = node


def _normalized_trust(raw: Any, nodes: Mapping[str, LineageNode]) -> list[dict[str, str]]:
    rows = []
    for item in _rows(raw):
        target = _required_string(item, "target")
        if target not in nodes:
            raise TheoremLineageError(f"trust target is not a node: {target}")
        rows.append(
            {
                "kind": _required_string(item, "kind"),
                "scope": _required_string(item, "scope"),
                "target": target,
            }
        )
    return sorted(rows, key=lambda row: (row["kind"], row["scope"], row["target"]))


def _normalized_scc(raw: Any, nodes: Mapping[str, LineageNode]) -> list[dict[str, Any]]:
    result = []
    for component in _rows(raw):
        members = component.get("members")
        if not isinstance(members, list):
            raise TheoremLineageError("SCC members are malformed")
        component_id = _digest(sorted(str(member) for member in members))[:24]
        for member in sorted(str(member) for member in members):
            if member not in nodes:
                raise TheoremLineageError(f"SCC member is not a node: {member}")
            result.append(
                {"componentId": component_id, "member": member, "cyclic": bool(component.get("cyclic"))}
            )
    return sorted(result, key=lambda row: (row["componentId"], row["member"]))


def _owner_is_project(row: Mapping[str, Any], modules: set[str]) -> bool:
    return _required_string(row, "ownerModule") in modules


def _check_connection(connection: sqlite3.Connection) -> None:
    integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    if integrity != "ok":
        raise TheoremLineageError(f"SQLite integrity check failed: {integrity}")
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise TheoremLineageError("SQLite foreign-key check failed")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TheoremLineageError(f"{label} is malformed")
    return value


def _rows(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise TheoremLineageError("lineage rows are malformed")
    return value


def _required_string(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise TheoremLineageError(f"lineage field {key} is missing")
    return value


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _optional_int(value: Any) -> int | None:
    return value if isinstance(value, int) else None


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


__all__ = [
    "LineageBundle",
    "LineageIdentity",
    "LineageNode",
    "TheoremLineageError",
    "ingest_theorem_lineage",
    "inspect_lineage_closure",
    "normalize_lineage_plan",
]
