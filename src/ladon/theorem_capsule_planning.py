"""Lean-authoritative, read-only planning for theorem capsules."""

from __future__ import annotations

import json
import tempfile
import threading
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from ladon.ir import LeanTextDeclaration
from ladon.process_supervisor import ProcessCancelled, run_bounded_target_process
from ladon.target_build import (
    TargetPreflightError,
    validate_compiled_state,
    validate_lake_preflight,
    validate_target_repository,
)
from ladon.theorem_capsule_configuration import (
    configuration_files,
    locked_package_rows,
    unsupported_facets,
    verify_configuration_files,
)
from ladon.theorem_capsule_graph import (
    normalize_helper_nodes,
    semantic_components,
    semantic_edges,
    semantic_external_frontier,
    trust_frontier,
)
from ladon.theorem_capsule_inventory import (
    CapsuleLayout,
    CapsuleSource,
    discover_capsule_layout,
    locate_exact_theorem,
    repository_module_closure,
    source_inventory_fingerprint,
    verify_selected_sources,
)
from ladon.theorem_capsule_models import (
    GUARANTEE_LEVEL,
    NONCLAIMS,
    PLAN_PROTOCOL,
    CapsuleInvocationError,
    CapsuleOperationalError,
    TheoremPlan,
    canonical_json_bytes,
    sha256_bytes,
)

DEFAULT_CAPSULE_HELPER = Path(
    str(
        resources.files("ladon").joinpath(
            "lean",
            "ladon_theorem_capsule_helper.lean",
        )
    )
)
HELPER_VERSION = "ladon-theorem-capsule-helper-v1"
PLAN_VERSION = "ladon-theorem-capsule-planner-v1"
HELPER_OUTPUT_LIMIT_BYTES = 64 * 1024 * 1024


def plan_theorem_capsule(
    repo_root: Path,
    theorem_name: str,
    *,
    helper_path: Path = DEFAULT_CAPSULE_HELPER,
    timeout_seconds: float = 120.0,
    max_rss_bytes: int | None = None,
    cancel_event: threading.Event | None = None,
) -> TheoremPlan:
    """Plan one exact theorem capsule without writing in the target repository."""

    if max_rss_bytes is not None and max_rss_bytes <= 0:
        raise CapsuleInvocationError("theorem helper RSS limit must be positive")
    root = _planning_preflight(repo_root, theorem_name, timeout_seconds)
    layout = discover_capsule_layout(root)
    located = locate_exact_theorem(layout, theorem_name)
    entry = located.source
    declaration = located.declaration
    helper = _run_exact_helper(
        root,
        entry,
        theorem_name,
        layout,
        helper_path=helper_path,
        timeout_seconds=timeout_seconds,
        max_rss_bytes=max_rss_bytes,
        cancel_event=cancel_event,
    )
    _validate_helper_result(helper, theorem_name, entry, declaration)
    sources = repository_module_closure(layout, entry)
    configuration = configuration_files(root)
    unsupported = unsupported_facets(root, configuration, sources.values())
    payload = _plan_payload(
        root,
        layout,
        entry,
        declaration,
        helper,
        sources,
        configuration,
        unsupported,
    )
    verify_selected_sources(layout, sources)
    verify_configuration_files(root, configuration)
    return TheoremPlan.create(payload)


def _planning_preflight(
    repo_root: Path,
    theorem_name: str,
    timeout_seconds: float,
) -> Path:
    if not _valid_fully_qualified_name(theorem_name):
        raise CapsuleInvocationError(
            "theorem name must be a fully qualified Lean declaration name"
        )
    if timeout_seconds <= 0:
        raise CapsuleInvocationError("theorem helper timeout must be positive")
    try:
        root, _ = validate_lake_preflight(validate_target_repository(repo_root))
        validate_compiled_state(root, build_requested=False)
    except TargetPreflightError as exc:
        raise CapsuleOperationalError(str(exc)) from exc
    if not (root / "lean-toolchain").is_file():
        raise CapsuleOperationalError(
            f"theorem planning requires a pinned lean-toolchain: {root}"
        )
    return root


def _valid_fully_qualified_name(value: str) -> bool:
    parts = value.split(".")
    return len(parts) >= 2 and all(part and not part.isspace() for part in parts)


def _run_exact_helper(
    repo_root: Path,
    entry: CapsuleSource,
    theorem_name: str,
    layout: CapsuleLayout,
    *,
    helper_path: Path,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    cancel_event: threading.Event | None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ladon-theorem-plan-") as temporary:
        module_file = Path(temporary) / "repository-modules.txt"
        module_file.write_text(
            "\n".join(layout.modules) + "\n",
            encoding="utf-8",
        )
        process = run_bounded_target_process(
            [
                "lake",
                "env",
                "lean",
                "--run",
                str(helper_path),
                entry.module,
                entry.path,
                theorem_name,
                str(module_file),
            ],
            cwd=repo_root,
            timeout_seconds=timeout_seconds,
            max_output_bytes=HELPER_OUTPUT_LIMIT_BYTES,
            max_rss_bytes=max_rss_bytes,
            cancel_event=cancel_event,
        )
    if process.output_limited:
        raise CapsuleOperationalError(
            "Lean theorem dependency stream exceeded the finite output limit"
        )
    if process.memory_limited:
        raise CapsuleOperationalError(
            "Lean theorem helper exceeded the finite process-tree RSS limit"
        )
    if not process.succeeded:
        outcome = "timed out" if process.timed_out else "failed"
        detail = (process.stderr or process.stdout).strip()[:2000]
        raise CapsuleOperationalError(
            f"Lean theorem helper {outcome} for {entry.path}: {detail}"
        )
    return parse_helper_payload(process.stdout)


def parse_helper_payload(stdout: str) -> dict[str, Any]:
    start = stdout.find('{"version"')
    if start < 0:
        raise CapsuleOperationalError("Lean theorem helper emitted no JSON payload")
    try:
        payload = json.loads(stdout[start:])
    except json.JSONDecodeError as exc:
        raise CapsuleOperationalError(
            "Lean theorem helper emitted malformed JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise CapsuleOperationalError("Lean theorem helper payload must be an object")
    return payload


def _validate_helper_result(
    payload: Mapping[str, Any],
    theorem_name: str,
    entry: CapsuleSource,
    declaration: LeanTextDeclaration,
) -> None:
    _validate_helper_header(payload)
    _validate_helper_completion(payload, theorem_name)
    nodes = _validate_helper_stream(payload)
    _validate_helper_target(payload, nodes, theorem_name, entry)
    _validate_source_agreement(payload, declaration)


def _validate_helper_header(payload: Mapping[str, Any]) -> None:
    if payload.get("helperVersion") != HELPER_VERSION:
        raise CapsuleOperationalError("Lean theorem helper version is incompatible")
    if payload.get("protocolVersion") != PLAN_PROTOCOL:
        raise CapsuleOperationalError("Lean theorem helper protocol is incompatible")


def _validate_helper_completion(
    payload: Mapping[str, Any],
    theorem_name: str,
) -> None:
    if payload.get("status") != "complete" or payload.get("complete") is not True:
        reason = str(payload.get("reason") or payload.get("status") or "unavailable")
        raise CapsuleInvocationError(
            f"Lean did not confirm {theorem_name} as an extractable theorem: {reason}"
        )


def _validate_helper_stream(
    payload: Mapping[str, Any],
) -> list[Any]:
    nodes = payload.get("nodes")
    end = payload.get("endRecord")
    if not isinstance(nodes, list) or not isinstance(end, Mapping):
        raise CapsuleOperationalError("Lean theorem dependency stream is malformed")
    if end.get("kind") != "end" or end.get("nodeCount") != len(nodes):
        raise CapsuleOperationalError(
            "Lean theorem dependency stream has no valid completion record"
        )
    if not isinstance(end.get("checksum"), str) or not end["checksum"]:
        raise CapsuleOperationalError(
            "Lean theorem dependency stream checksum is unavailable"
        )
    if end["checksum"] != helper_closure_checksum(nodes):
        raise CapsuleOperationalError(
            "Lean theorem dependency stream checksum disagrees with its nodes"
        )
    return nodes


def helper_closure_checksum(nodes: Iterable[Any]) -> str:
    """Recompute the helper's portable ordered-name stream checksum."""

    names = []
    for row in nodes:
        if not isinstance(row, Mapping) or not isinstance(row.get("name"), str):
            raise CapsuleOperationalError("Lean theorem dependency node is malformed")
        names.append(str(row["name"]))
    state = 2166136261
    for byte in "\n".join(sorted(names)).encode("utf-8"):
        state = (state * 16777619 + byte + 1) % 4294967291
    return str(state)


def _validate_helper_target(
    payload: Mapping[str, Any],
    nodes: list[Any],
    theorem_name: str,
    entry: CapsuleSource,
) -> None:
    if payload.get("target") != theorem_name or payload.get("module") != entry.module:
        raise CapsuleOperationalError("Lean theorem helper target identity disagrees")
    target = next(
        (row for row in nodes if isinstance(row, Mapping) and row.get("name") == theorem_name),
        None,
    )
    if target is None or target.get("kind") != "theorem":
        raise CapsuleOperationalError("Lean theorem node is absent or has the wrong kind")
    if target.get("ownerModule") != entry.module:
        raise CapsuleOperationalError("Lean theorem owner disagrees with source ownership")


def _validate_source_agreement(
    payload: Mapping[str, Any],
    declaration: LeanTextDeclaration,
) -> None:
    target_range = payload.get("targetRange")
    start = target_range.get("start") if isinstance(target_range, Mapping) else None
    finish = (
        target_range.get("finish")
        if isinstance(target_range, Mapping)
        else None
    )
    start_line = start.get("line") if isinstance(start, Mapping) else None
    finish_line = finish.get("line") if isinstance(finish, Mapping) else None
    if (
        not isinstance(start_line, int)
        or not isinstance(finish_line, int)
        or not start_line <= declaration.line <= finish_line
    ):
        raise CapsuleOperationalError(
            "Lean theorem range disagrees with the lexical source command"
        )


def _plan_payload(
    repo_root: Path,
    layout: CapsuleLayout,
    entry: CapsuleSource,
    declaration: LeanTextDeclaration,
    helper: Mapping[str, Any],
    sources: Mapping[str, CapsuleSource],
    configuration: tuple[dict[str, Any], ...],
    unsupported: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    prefix_end = _prefix_end_bytes(entry, declaration)
    files = tuple(
        _planned_file(
            source,
            target=source.module == entry.module,
            prefix_end=(
                prefix_end
                if source.module == entry.module
                else None
            ),
        )
        for source in sources.values()
    )
    nodes = normalize_helper_nodes(helper)
    edges = semantic_edges(nodes)
    components = semantic_components(nodes, edges)
    semantic_frontier = semantic_external_frontier(nodes, edges)
    build_modules, build_edges, external_imports = _build_graph(
        layout,
        sources,
        target_module=entry.module,
    )
    locked_packages = locked_package_rows(repo_root)
    trust_rows = trust_frontier(nodes)
    closure_fingerprint = sha256_bytes(
        canonical_json_bytes({"nodes": nodes, "edges": edges})
    )
    return {
        "plannerVersion": PLAN_VERSION,
        "guaranteeLevel": GUARANTEE_LEVEL,
        "eligible": not unsupported,
        "repository": {
            "root": str(repo_root),
            "sourceInventoryFingerprint": source_inventory_fingerprint(
                layout,
                sources,
                configuration,
            ),
            "layoutFingerprint": layout.fingerprint,
            "layoutStatus": layout.source_map.status,
            "sourceRoots": [
                source_root.to_dict(repo_root)
                for source_root in layout.source_map.roots
            ],
            "configurationFingerprint": sha256_bytes(
                canonical_json_bytes({"files": list(configuration)})
            ),
        },
        "toolchain": {
            "leanVersion": helper.get("leanVersion"),
            "helperVersion": helper.get("helperVersion"),
            "protocolVersion": helper.get("protocolVersion"),
        },
        "target": {
            "name": helper["target"],
            "kind": "theorem",
            "module": entry.module,
            "path": entry.path,
            "prefixEndOffset": prefix_end,
            "sourceLine": declaration.line,
            "sourceColumn": declaration.column,
            "sourceRange": helper.get("targetRange"),
            "typeFingerprint": _target_node(nodes, str(helper["target"]))[
                "typeFingerprint"
            ],
            "valueFingerprint": _target_node(nodes, str(helper["target"])).get(
                "valueFingerprint"
            ),
        },
        "semanticGraph": {
            "status": "complete",
            "authority": "lean_environment",
            "nodes": list(nodes),
            "edges": list(edges),
            "nodeCount": len(nodes),
            "edgeCount": len(edges),
            "stronglyConnectedComponents": list(components),
            "externalFrontier": list(semantic_frontier),
            "helperChecksum": _mapping(helper["endRecord"])["checksum"],
            "closureFingerprint": closure_fingerprint,
            "trustFrontier": list(trust_rows),
        },
        "buildGraph": {
            "status": "complete",
            "authority": "selected_source_import_graph",
            "modules": list(build_modules),
            "edges": list(build_edges),
            "externalImports": list(external_imports),
            "lockedPackages": list(locked_packages),
            "moduleDagFingerprint": sha256_bytes(
                canonical_json_bytes(
                    {
                        "modules": list(build_modules),
                        "edges": list(build_edges),
                        "externalImports": list(external_imports),
                        "lockedPackages": list(locked_packages),
                    }
                )
            ),
        },
        "files": list(files),
        "configurationFiles": list(configuration),
        "unsupportedFacets": list(unsupported),
        "nonclaims": list(NONCLAIMS),
    }


def _prefix_end_bytes(
    source: CapsuleSource,
    declaration: LeanTextDeclaration,
) -> int:
    """Translate the lexical character boundary into an exact UTF-8 byte end."""

    character_end = declaration.block_end_offset
    if character_end is None:
        raise CapsuleOperationalError("target source command boundary is unavailable")
    try:
        text = source.content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CapsuleOperationalError(
            f"target Lean source is not UTF-8: {source.path}"
        ) from exc
    if character_end > len(text):
        raise CapsuleOperationalError("target source command boundary is outside source")
    return len(text[:character_end].encode("utf-8"))


def _planned_file(
    source: CapsuleSource,
    *,
    target: bool,
    prefix_end: int | None,
) -> dict[str, Any]:
    content = source.content
    row: dict[str, Any] = {
        "path": source.path,
        "module": source.module,
        "role": "target_prefix" if target else "module_import",
        "inclusionReason": (
            "owner_prefix_through_theorem"
            if target
            else "repository_import_closure"
        ),
        "sourceSha256": sha256_bytes(content),
        "sourceBytes": len(content),
    }
    if prefix_end is not None:
        prefix = content[:prefix_end]
        row["prefixEndOffset"] = prefix_end
        row["materializedSha256"] = sha256_bytes(prefix)
        row["materializedBytes"] = len(prefix)
    else:
        row["materializedSha256"] = row["sourceSha256"]
        row["materializedBytes"] = row["sourceBytes"]
    return row


def _build_graph(
    layout: CapsuleLayout,
    sources: Mapping[str, CapsuleSource],
    *,
    target_module: str,
) -> tuple[
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
    tuple[dict[str, Any], ...],
]:
    selected = set(sources)
    module_rows = tuple(
        {
            "module": name,
            "path": sources[name].path,
            "inclusionReason": (
                "target_owner" if name == target_module else "import_closure"
            ),
        }
        for name in sorted(selected)
    )
    edges = []
    external = set()
    for source in sorted(selected):
        for target in sorted(set(sources[source].imports)):
            if target in selected:
                edges.append({"source": source, "target": target, "kind": "import"})
            elif target not in layout.paths:
                external.add((source, target))
    external_rows = tuple(
        {
            "source": source,
            "module": target,
            "kind": (
                "toolchain_import"
                if _is_toolchain_module(target)
                else "locked_external_import"
            ),
            "lockEvidence": (
                None
                if _is_toolchain_module(target)
                else "lake-manifest.json"
            ),
        }
        for source, target in sorted(external)
    )
    return module_rows, tuple(edges), external_rows


def _is_toolchain_module(module: str) -> bool:
    return any(
        module == prefix or module.startswith(f"{prefix}.")
        for prefix in ("Init", "Lean", "Std")
    )


def _target_node(
    nodes: Iterable[Mapping[str, Any]],
    name: str,
) -> Mapping[str, Any]:
    target = next((row for row in nodes if row.get("name") == name), None)
    if target is None:
        raise CapsuleOperationalError("Lean theorem target node is missing")
    return target


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CapsuleOperationalError("Lean theorem helper mapping is malformed")
    return value


__all__ = [
    "DEFAULT_CAPSULE_HELPER",
    "HELPER_VERSION",
    "PLAN_VERSION",
    "ProcessCancelled",
    "helper_closure_checksum",
    "normalize_helper_nodes",
    "parse_helper_payload",
    "plan_theorem_capsule",
    "semantic_components",
    "semantic_edges",
    "semantic_external_frontier",
    "trust_frontier",
]
