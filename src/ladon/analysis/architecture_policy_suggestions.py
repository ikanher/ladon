"""Heuristic draft-policy suggestions for architecture boundary checks."""

from __future__ import annotations

from collections import defaultdict
import re
from typing import Any

MIN_DRAFT_GROUP_SIZE = 3


def draft_policy_suggestions(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Suggest a draft policy from repeated module-name prefixes."""

    edges = normalized_edges(module_dag.get("edges", {}))
    prefix_by_module = inferred_prefix_membership(edges)
    cross_edges = cross_prefix_edges(edges, prefix_by_module)
    if len(set(prefix_by_module.values())) < 2 or not cross_edges:
        return []
    groups = draft_groups(cross_edges, prefix_by_module)
    return [draft_policy(groups, cross_edges)]


def normalized_edges(raw_edges: Any) -> dict[str, tuple[str, ...]]:
    """Return importer -> imported module edges from a DAG report."""

    if not isinstance(raw_edges, dict):
        return {}
    return {
        str(source): tuple(str(target) for target in targets if str(target))
        for source, targets in raw_edges.items()
        if isinstance(targets, list)
    }


def cross_prefix_edges(
    edges: dict[str, tuple[str, ...]],
    prefix_by_module: dict[str, str],
) -> list[tuple[str, str]]:
    """Return imports between different inferred prefixes."""

    return [
        (source, target)
        for source, targets in edges.items()
        for target in targets
        if prefix_by_module.get(source)
        and prefix_by_module.get(target)
        and prefix_by_module[source] != prefix_by_module[target]
    ]


def draft_groups(
    cross_edges: list[tuple[str, str]],
    prefix_by_module: dict[str, str],
) -> dict[str, list[str]]:
    """Return draft policy group patterns used by cross-prefix edges."""

    prefixes = sorted({prefix_by_module[module] for edge in cross_edges for module in edge})
    return {
        group_id(prefix): sorted(prefix_patterns(prefix, prefix_by_module))[:3]
        for prefix in prefixes
    }


def draft_policy(
    groups: dict[str, list[str]],
    cross_edges: list[tuple[str, str]],
) -> dict[str, Any]:
    """Return one draft peer-prefix policy suggestion."""

    return {
        "kind": "draft_peer_prefix_policy",
        "reason": "repeated module-name prefixes with cross-prefix imports",
        "groups": groups,
        "rules": [
            {
                "id": "draft-peer-prefix-boundary",
                "kind": "forbid_imports",
                "from": sorted(groups),
                "to": sorted(groups),
                "includeTransitive": True,
                "suggestCommonDependencies": True,
            }
        ],
        "sampleCrossImports": [
            {"sourceModule": source, "targetModule": target}
            for source, target in sorted(cross_edges)[:12]
        ],
    }


def inferred_prefix_membership(edges: dict[str, tuple[str, ...]]) -> dict[str, str]:
    """Return modules assigned to repeated leading-name prefixes."""

    prefix_by_module = {
        module: prefix
        for module in graph_modules(edges)
        for prefix in [inferred_module_prefix(module)]
        if prefix
    }
    counts = prefix_counts(prefix_by_module)
    return {
        module: prefix
        for module, prefix in prefix_by_module.items()
        if counts[prefix] >= MIN_DRAFT_GROUP_SIZE
    }


def graph_modules(edges: dict[str, tuple[str, ...]]) -> list[str]:
    """Return all modules mentioned in an edge map."""

    return sorted(set(edges) | {target for targets in edges.values() for target in targets})


def prefix_counts(prefix_by_module: dict[str, str]) -> dict[str, int]:
    """Count modules per inferred prefix."""

    counts: dict[str, int] = defaultdict(int)
    for prefix in prefix_by_module.values():
        counts[prefix] += 1
    return counts


def inferred_module_prefix(module: str) -> str:
    """Infer a repeated-family prefix from one module basename."""

    basename = module.rsplit(".", 1)[-1]
    tokens = camel_tokens(basename)
    if not tokens:
        return ""
    if len(tokens[0]) >= 2 and tokens[0].isupper():
        return "".join(tokens[: min(3, len(tokens))])
    return leading_prefix(tokens)


def leading_prefix(tokens: list[str]) -> str:
    """Return a coarse leading CamelCase prefix."""

    chosen: list[str] = []
    for token in tokens:
        chosen.append(token)
        if len("".join(chosen)) >= 6 or len(chosen) >= 3:
            break
    return "".join(chosen)


def camel_tokens(value: str) -> list[str]:
    """Split a Lean module basename into coarse CamelCase tokens."""

    return re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+", value)


def group_id(prefix: str) -> str:
    """Return a readable policy group id from a module-name prefix."""

    parts = camel_tokens(prefix)
    return "-".join(part.lower() for part in parts) or prefix.lower()


def prefix_patterns(prefix: str, membership: dict[str, str]) -> list[str]:
    """Return glob patterns covering modules assigned to one inferred prefix."""

    parents = {
        module.rsplit(".", 1)[0]
        for module, module_prefix in membership.items()
        if module_prefix == prefix and "." in module
    }
    return [f"{parent}.{prefix}*" for parent in sorted(parents)]
