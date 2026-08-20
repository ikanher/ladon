"""Declaration population calibration and target-owned graph rankings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def attach_declaration_populations(
    dag: dict[str, Any],
    declaration_graph: dict[str, Any],
    declarations: list[dict[str, Any]],
) -> None:
    """Classify declaration rows from module and Lean generation evidence."""

    module_rows = dag.get("population_calibration", {}).get("rows", [])
    module_populations = {
        str(row.get("module")): str(row.get("population", "unclassified"))
        for row in module_rows
        if isinstance(row, dict)
    }
    counts, by_declaration = _calibrate_declaration_rows(
        declarations,
        module_populations,
    )
    declaration_graph["population_calibration"] = (
        _declaration_population_summary(declarations, counts)
    )
    edges = declaration_graph.get("edges", {})
    declaration_graph["top_target_owned_fan_in"] = (
        calibrated_declaration_ranking(edges, by_declaration, "fan_in")
    )
    declaration_graph["top_target_owned_fan_out"] = (
        calibrated_declaration_ranking(edges, by_declaration, "fan_out")
    )


def _calibrate_declaration_rows(
    declarations: list[dict[str, Any]],
    module_populations: Mapping[str, str],
) -> tuple[dict[str, int], dict[str, str]]:
    counts: dict[str, int] = {}
    by_declaration: dict[str, str] = {}
    for row in declarations:
        population, authority = declaration_population(
            row,
            module_populations,
        )
        row["population"] = population
        row["populationAuthority"] = authority
        counts[population] = counts.get(population, 0) + 1
        by_declaration[str(row.get("declaration", ""))] = population
    return counts, by_declaration


def _declaration_population_summary(
    declarations: list[dict[str, Any]],
    counts: Mapping[str, int],
) -> dict[str, Any]:
    return {
        "selectedPopulation": "target_owned",
        "rawCount": len(declarations),
        "counts": dict(sorted(counts.items())),
        "exclusions": {
            population: count
            for population, count in sorted(counts.items())
            if population != "target_owned"
        },
        "nonclaim": (
            "Declaration populations preserve extraction authority and do not "
            "state proof correctness or theorem truth."
        ),
    }


def calibrated_declaration_ranking(
    raw_edges: Any,
    populations: Mapping[str, str],
    metric: str,
) -> list[dict[str, Any]]:
    """Rank an independently recomputed target-owned declaration subgraph."""

    edges = normalized_declaration_edges(raw_edges)
    relationships = _relationships_for_metric(edges, metric)
    rows = [
        calibrated_declaration_row(
            declaration,
            targets,
            populations,
            metric,
        )
        for declaration, targets in relationships.items()
        if populations.get(declaration) == "target_owned"
    ]
    return sorted(
        rows,
        key=lambda row: (
            -int(row[metric]),
            str(row["declaration"]),
        ),
    )[:15]


def _relationships_for_metric(
    edges: dict[str, tuple[str, ...]],
    metric: str,
) -> Mapping[str, Sequence[str]]:
    if metric == "fan_in":
        return reverse_declaration_relationships(edges)
    if metric == "fan_out":
        return edges
    raise ValueError(f"unsupported declaration metric: {metric}")


def normalized_declaration_edges(raw: Any) -> dict[str, tuple[str, ...]]:
    """Return only string-to-string declaration relationships."""

    if not isinstance(raw, Mapping):
        return {}
    return {
        str(source): tuple(
            sorted(
                str(target)
                for target in targets
                if isinstance(target, str)
            )
        )
        for source, targets in raw.items()
        if isinstance(source, str) and isinstance(targets, Sequence)
    }


def reverse_declaration_relationships(
    edges: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    """Reverse declaration relationships while retaining zero-degree rows."""

    reverse: dict[str, list[str]] = {
        declaration: [] for declaration in edges
    }
    for source, targets in edges.items():
        for target in targets:
            reverse.setdefault(target, []).append(source)
    return {
        declaration: tuple(sorted(sources))
        for declaration, sources in reverse.items()
    }


def calibrated_declaration_row(
    declaration: str,
    relationships: Sequence[str],
    populations: Mapping[str, str],
    metric: str,
) -> dict[str, Any]:
    """Expose selected and raw populations without carrying raw inflation."""

    selected = [
        target
        for target in relationships
        if populations.get(target) == "target_owned"
    ]
    denominator = len(relationships)
    return {
        "declaration": declaration,
        metric: len(selected),
        "rawMetric": denominator,
        "population": "target_owned_to_target_owned",
        "numerator": len(selected),
        "denominator": denominator,
        "exclusions": {
            "nonTargetOwnedEndpoints": denominator - len(selected)
        },
        "authority": "parser_candidate_graph_and_population_policy",
    }


def declaration_population(
    row: Mapping[str, Any],
    module_populations: Mapping[str, str],
) -> tuple[str, str]:
    """Apply imported/compiler evidence before containing-module ownership."""

    if bool(row.get("importedStub")):
        return "imported", "lean_imported_stub"
    if bool(row.get("compilerGenerated")):
        authority = str(row.get("compilerAuthority") or "unclassified")
        if authority == "lean_environment" and row.get("compilerToolchain"):
            return "compiler_generated", authority
        return "unclassified", "incomplete_compiler_generation_evidence"
    module = str(row.get("module", ""))
    population = module_populations.get(module, "unclassified")
    return population, "containing_module_population"


__all__ = [
    "attach_declaration_populations",
    "calibrated_declaration_ranking",
    "calibrated_declaration_row",
    "declaration_population",
    "normalized_declaration_edges",
    "reverse_declaration_relationships",
]
