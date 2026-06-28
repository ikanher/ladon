"""Composite architecture-pressure findings from correlated graph signals."""

from __future__ import annotations

from typing import Any


HOTSPOT_THRESHOLD = 5
BROAD_INVENTORY_THRESHOLD = 20


def architecture_pressure_findings(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return composite findings that require multiple graph signals."""

    findings: list[dict[str, Any]] = []
    findings.extend(import_pressure_findings(module_dag))
    findings.extend(facade_fanout_findings(module_dag))
    findings.extend(root_scope_findings(module_dag))
    findings.extend(proof_family_import_findings(module_dag, declaration_graph))
    return findings


def import_pressure_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Correlate broad root import closure with high module fan-in."""

    closure = top_root_closure(module_dag)
    fan_in = top_metric_row(module_dag, "top_fan_in", "fan_in")
    if not both_hot(closure, fan_in):
        return []
    return [
        composite_finding(
            "composite_import_pressure",
            closure["subject"],
            (
                "Broad root import closure and high module fan-in co-occur; "
                "this is architecture pressure worth review."
            ),
            [closure, fan_in],
        )
    ]


def facade_fanout_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Correlate facade-heavy inventory with high module fan-out."""

    facade_count = int(module_dag.get("facade_module_count", 0))
    fan_out = (
        top_metric_row(module_dag, "top_facade_fan_out", "fan_out")
        or top_metric_row(module_dag, "top_fan_out", "fan_out")
    )
    if facade_count < HOTSPOT_THRESHOLD or not is_hot(fan_out):
        return []
    facade_signal = component_signal("facade_module_count", "module_inventory", facade_count)
    return [
        composite_finding(
            "facade_fanout_pressure",
            fan_out["subject"],
            (
                "Facade/barrel modules with high fan-out are public aggregation "
                "architecture pressure; read this as API-surface context, not "
                "ordinary implementation coupling."
            ),
            [facade_signal, fan_out],
        )
    ]


def root_scope_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag narrow chosen-root reachability inside a broad inventory."""

    module_count = int(module_dag.get("module_count", 0))
    unreachable = int(module_dag.get("source_modules_not_reachable_from_chosen_roots_count", 0))
    if module_count < BROAD_INVENTORY_THRESHOLD or unreachable < module_count // 2:
        return []
    root_scope = classify_root_scope(module_dag)
    finding = composite_finding(
        "root_scope_pressure",
        "chosen_roots",
        root_scope_message(root_scope),
        [
            component_signal("module_count", "inventory", module_count),
            component_signal("unreachable_modules", "chosen_roots", unreachable),
        ],
    )
    finding["root_scope"] = root_scope
    return [finding]


def classify_root_scope(module_dag: dict[str, Any]) -> dict[str, Any]:
    """Classify why chosen-root reachability is narrow."""

    root = first_chosen_root(module_dag)
    closure = top_root_closure(module_dag)
    classification = root_scope_classification(root, closure)
    return {
        "classification": classification,
        "chosen_root": root,
        "unreachable_ratio": unreachable_ratio(module_dag),
        "largest_direct_import_closure": int(closure["value"]) if closure else 0,
    }


def root_scope_classification(root: str | None, closure: dict[str, Any] | None) -> str:
    """Return the explanatory root-scope class."""

    if root and "." not in root:
        return "public_root_narrow_inventory"
    if closure and int(closure["value"]) >= BROAD_INVENTORY_THRESHOLD:
        return "narrow_owner_broad_import"
    if root and "." in root:
        return "narrow_owner"
    return "broad_inventory_scope_gap"


def first_chosen_root(module_dag: dict[str, Any]) -> str | None:
    """Return the selected root module when available."""

    roots = module_dag.get("chosen_roots", [])
    return str(roots[0]) if roots else None


def unreachable_ratio(module_dag: dict[str, Any]) -> float:
    """Return unreachable modules divided by total modules."""

    module_count = int(module_dag.get("module_count", 0))
    if module_count == 0:
        return 0.0
    unreachable = int(module_dag.get("source_modules_not_reachable_from_chosen_roots_count", 0))
    return round(unreachable / module_count, 3)


def root_scope_message(root_scope: dict[str, Any]) -> str:
    """Build a root-scope pressure message with classification context."""

    classification = root_scope["classification"]
    return (
        "The chosen root reaches a narrow slice of a broad inventory; "
        f"classification={classification}. Treat repo-wide inventory rows as "
        "review-scope pressure."
    )


def proof_family_import_findings(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Correlate repeated theorem-family names with broad import closure."""

    if declaration_graph is None:
        return []
    closure = top_root_closure(module_dag)
    family = top_metric_row(declaration_graph, "declaration_name_families", "count")
    if not both_hot(closure, family):
        return []
    return [
        composite_finding(
            "proof_family_import_pressure",
            family["subject"],
            (
                "Repeated declaration-family names occur under a broad root "
                "import closure; this is proof-architecture pressure."
            ),
            [closure, family],
        )
    ]


def top_root_closure(module_dag: dict[str, Any]) -> dict[str, Any] | None:
    """Return the largest direct root-import closure signal."""

    rows = module_dag.get("root_direct_import_closures", [])
    if not rows:
        return None
    row = max(rows, key=lambda item: int(item.get("reachable_module_count", 0)))
    subject = f"{row.get('root')} -> {row.get('direct_import')}"
    return component_signal("root_import_closure", subject, row.get("reachable_module_count", 0))


def top_metric_row(summary: dict[str, Any], row_key: str, metric: str) -> dict[str, Any] | None:
    """Return the largest metric row as a component signal."""

    rows = summary.get(row_key, [])
    if not rows:
        return None
    row = max(rows, key=lambda item: int(item.get(metric, 0)))
    return component_signal(metric_name(row_key, metric), row_subject(row), row.get(metric, 0))


def metric_name(row_key: str, metric: str) -> str:
    """Return a stable component metric name."""

    if row_key == "top_fan_in":
        return "module_fan_in"
    if row_key == "top_fan_out":
        return "module_fan_out"
    if row_key == "top_facade_fan_out":
        return "module_facade_fan_out"
    if row_key == "top_implementation_fan_out":
        return "module_implementation_fan_out"
    if row_key == "declaration_name_families":
        return "declaration_family_size"
    return metric


def row_subject(row: dict[str, Any]) -> str:
    """Return the best available row subject."""

    for key in ("module", "declaration", "suffix", "candidate"):
        if key in row:
            return str(row[key])
    return "unknown"


def both_hot(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    """Return true when two component signals are both above threshold."""

    return is_hot(left) and is_hot(right)


def is_hot(signal: dict[str, Any] | None) -> bool:
    """Return true when one component signal is above threshold."""

    return signal is not None and int(signal["value"]) >= HOTSPOT_THRESHOLD


def component_signal(metric: str, subject: str, value: Any) -> dict[str, Any]:
    """Build a stable component-signal payload."""

    return {"metric": metric, "subject": subject, "value": int(value)}


def composite_finding(
    kind: str,
    subject: str,
    message: str,
    component_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one composite architecture finding."""

    return {
        "kind": kind,
        "severity": "info",
        "subject": subject,
        "count": sum(int(signal["value"]) for signal in component_signals),
        "message": message,
        "component_signals": component_signals,
    }
