"""Project-local metric baselines for Ladon graph reports."""

from __future__ import annotations

from math import ceil
from typing import Any, Iterable


BASELINE_METHOD = "project_local_metric_distribution"


def summarize_quality_baseline(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize metric distributions from existing graph report data."""

    metrics = {
        "module_fan_in": distribution_summary(module_fan_in_values(module_dag)),
        "module_fan_out": distribution_summary(module_fan_out_values(module_dag)),
        "module_line_count": distribution_summary(module_line_count_values(module_dag)),
        "root_import_closure": distribution_summary(root_import_closure_values(module_dag)),
    }
    if declaration_graph:
        metrics.update(declaration_metric_summaries(declaration_graph))
    return {
        "method": BASELINE_METHOD,
        "metrics": {
            name: summary
            for name, summary in sorted(metrics.items())
            if summary["count"] > 0
        },
    }


def declaration_metric_summaries(declaration_graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return declaration-level metric distributions."""

    return {
        "declaration_fan_in": distribution_summary(declaration_fan_in_values(declaration_graph)),
        "declaration_fan_out": distribution_summary(declaration_fan_out_values(declaration_graph)),
        "declaration_family_size": distribution_summary(
            row_counts(declaration_graph.get("declaration_name_families", []))
        ),
        "unresolved_reference_class_count": distribution_summary(
            row_counts(declaration_graph.get("unresolved_reference_classes", []))
        ),
    }


def distribution_summary(raw_values: Iterable[int]) -> dict[str, Any]:
    """Return deterministic headline statistics for integer metric values."""

    values = sorted(int(value) for value in raw_values)
    if not values:
        return empty_distribution()
    return {
        "count": len(values),
        "min": values[0],
        "median": nearest_rank_percentile(values, 50),
        "p90": nearest_rank_percentile(values, 90),
        "p95": nearest_rank_percentile(values, 95),
        "p99": nearest_rank_percentile(values, 99),
        "max": values[-1],
        "values": values,
    }


def empty_distribution() -> dict[str, Any]:
    """Return the stable empty metric shape."""

    return {
        "count": 0,
        "min": 0,
        "median": 0,
        "p90": 0,
        "p95": 0,
        "p99": 0,
        "max": 0,
        "values": [],
    }


def nearest_rank_percentile(values: list[int], percentile: int) -> int:
    """Return a nearest-rank percentile from sorted values."""

    index = max(0, ceil((percentile / 100) * len(values)) - 1)
    return values[min(index, len(values) - 1)]


def calibrate_count(
    quality_baseline: dict[str, Any] | None,
    metric: str,
    count: int,
) -> dict[str, Any] | None:
    """Calibrate one count against a metric distribution if available."""

    if not quality_baseline:
        return None
    values = quality_baseline.get("metrics", {}).get(metric, {}).get("values", [])
    if not values:
        return None
    return {
        "metric": metric,
        "percentile": percentile_rank(values, count),
        "rank_desc": descending_rank(values, count),
        "population": len(values),
    }


def percentile_rank(values: list[int], count: int) -> float:
    """Return percentage of values less than or equal to count."""

    less_or_equal = sum(1 for value in values if value <= count)
    return round((less_or_equal / len(values)) * 100, 1)


def descending_rank(values: list[int], count: int) -> int:
    """Return one-based descending rank for count within metric values."""

    return 1 + sum(1 for value in values if value > count)


def module_fan_in_values(module_dag: dict[str, Any]) -> list[int]:
    """Compute module fan-in values from the full edge map."""

    edges = graph_edges(module_dag)
    modules = graph_nodes(edges)
    fan_in = {module: 0 for module in modules}
    for imports in edges.values():
        for imported in imports:
            fan_in[imported] = fan_in.get(imported, 0) + 1
    return list(fan_in.values())


def module_fan_out_values(module_dag: dict[str, Any]) -> list[int]:
    """Compute module fan-out values from the full edge map."""

    edges = graph_edges(module_dag)
    modules = graph_nodes(edges)
    return [len(edges.get(module, [])) for module in modules]


def module_line_count_values(module_dag: dict[str, Any]) -> list[int]:
    """Return source line-count values from module metadata."""

    metadata = module_dag.get("module_metadata", {})
    if not isinstance(metadata, dict):
        return []
    return [
        int(row.get("lineCount", 0))
        for row in metadata.values()
        if isinstance(row, dict) and int(row.get("lineCount", 0)) > 0
    ]


def declaration_fan_in_values(declaration_graph: dict[str, Any]) -> list[int]:
    """Compute declaration fan-in values from the full edge map."""

    edges = graph_edges(declaration_graph)
    declarations = graph_nodes(edges)
    fan_in = {declaration: 0 for declaration in declarations}
    for references in edges.values():
        for reference in references:
            fan_in[reference] = fan_in.get(reference, 0) + 1
    return list(fan_in.values())


def declaration_fan_out_values(declaration_graph: dict[str, Any]) -> list[int]:
    """Compute declaration fan-out values from the full edge map."""

    edges = graph_edges(declaration_graph)
    declarations = graph_nodes(edges)
    return [len(edges.get(declaration, [])) for declaration in declarations]


def graph_edges(summary: dict[str, Any]) -> dict[str, list[str]]:
    """Return normalized string-list graph edges from a summary."""

    return {
        str(source): [str(target) for target in targets]
        for source, targets in summary.get("edges", {}).items()
    }


def graph_nodes(edges: dict[str, list[str]]) -> list[str]:
    """Return all graph nodes appearing as sources or targets."""

    return sorted({*edges.keys(), *(target for targets in edges.values() for target in targets)})


def root_import_closure_values(module_dag: dict[str, Any]) -> list[int]:
    """Return direct root-import closure sizes."""

    return row_counts(module_dag.get("root_direct_import_closures", []), "reachable_module_count")


def row_counts(rows: list[dict[str, Any]], key: str = "count") -> list[int]:
    """Extract integer counts from report rows."""

    return [int(row.get(key, 0)) for row in rows]
