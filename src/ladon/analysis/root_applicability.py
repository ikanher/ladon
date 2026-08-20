"""Shared applicability contract for root-relative module-DAG views."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

ROOT_APPLICABILITY_KEY = "root_reachability"
ROOT_APPLICABILITY_STATUSES = frozenset(
    {"applicable", "auxiliary", "not_applicable"}
)


def root_applicability(
    roots: Sequence[str],
    *,
    population: str,
    auxiliary: bool = False,
    reason: str | None = None,
    coverage_ref: str = "module_dag.modules",
) -> dict[str, Any]:
    """Build one explicit root-relative applicability envelope."""

    selected = tuple(sorted(set(roots)))
    if selected:
        status = "auxiliary" if auxiliary else "applicable"
        resolved_reason = reason
    else:
        status = "not_applicable"
        resolved_reason = reason or "no explicit navigation root was resolved"
    return {
        "status": status,
        "reason": resolved_reason,
        "roots": list(selected),
        "population": population,
        "coverageRef": coverage_ref,
        "authority": "module_import_graph",
        "nonclaim": (
            "Root-relative reachability is a navigation view over the selected "
            "module graph, not mathematical relevance or Lean elaboration."
        ),
    }


def root_views_applicable(module_dag: Mapping[str, Any]) -> bool:
    """Return whether root-relative metrics may be interpreted.

    Reports predating the explicit envelope remain readable through their
    historical semantics. Newly produced rootless reports carry an explicit
    ``not_applicable`` state and fail closed.
    """

    raw = module_dag.get(ROOT_APPLICABILITY_KEY)
    if raw is None:
        return True
    return (
        isinstance(raw, Mapping)
        and raw.get("status") in {"applicable", "auxiliary"}
    )


def root_views_auxiliary(module_dag: Mapping[str, Any]) -> bool:
    """Return whether root-relative rows are auxiliary inventory views."""

    raw = module_dag.get(ROOT_APPLICABILITY_KEY)
    return isinstance(raw, Mapping) and raw.get("status") == "auxiliary"


__all__ = [
    "ROOT_APPLICABILITY_KEY",
    "ROOT_APPLICABILITY_STATUSES",
    "root_applicability",
    "root_views_applicable",
    "root_views_auxiliary",
]
