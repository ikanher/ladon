"""Composite architecture-pressure findings from structural graph joins."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ladon.analysis.architecture_join_candidates import (
    strongest_facade_fanout_candidate,
    strongest_import_pressure_candidate,
    strongest_proof_family_candidate,
)
from ladon.analysis.architecture_measures import (
    DECLARATION_COVERAGE_REF,
    MODULE_COVERAGE_REF,
    component_refs,
    component_signal,
    known_denominator,
    metric_row_signal,
    nonnegative_integer_value,
    root_closure_signal,
    row_string,
    top_metric_row,
    top_root_closure,
    valid_string_sequence,
)
from ladon.analysis.root_applicability import root_views_applicable
from ladon.analysis.structural_joins import (
    JOIN_NONCLAIM,
    build_structural_join,
    graph_path_witness,
)
from ladon.finding_evidence import (
    aggregate_value_evidence,
    json_pointer_token,
)


HOTSPOT_THRESHOLD = 5
BROAD_INVENTORY_THRESHOLD = 20
COMPOSITE_AUTHORITY = "ladon_derived_structural_join"


def architecture_pressure_findings(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Return composite findings backed by explicit structural joins."""

    findings: list[dict[str, Any]] = []
    findings.extend(import_pressure_findings(module_dag))
    findings.extend(facade_fanout_findings(module_dag))
    findings.extend(root_scope_findings(module_dag))
    findings.extend(proof_family_import_findings(module_dag, declaration_graph))
    return findings


def import_pressure_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Join a hot fan-in subject to a broad root-import closure."""

    if not root_views_applicable(module_dag):
        return []
    candidate = strongest_import_pressure_candidate(module_dag)
    if candidate is None:
        return []
    closure = root_closure_signal(
        module_dag,
        candidate.closure_index,
        candidate.closure,
    )
    fan_in = metric_row_signal(
        module_dag,
        "top_fan_in",
        candidate.fan_index,
        candidate.fan_in,
        "fan_in",
    )
    witness = graph_path_witness(
        module_dag.get("edges"),
        candidate.path,
    )
    if witness is None:
        return []
    join = build_structural_join(
        "composite_import_pressure",
        canonical_sections={"module_dag": module_dag},
        component_metrics=("root_import_closure", "module_fan_in"),
        component_refs=component_refs((closure, fan_in)),
        witness_refs=(root_applicability_witness(module_dag), witness),
        population="selected_module_import_graph",
        scope=str(closure["measure"]["scope"]),
        authority="module_import_graph",
        coverage_refs=(MODULE_COVERAGE_REF,),
    )
    if join is None:
        return []
    return [
        composite_finding(
            "composite_import_pressure",
            closure["subject"],
            (
                "A high-fan-in module is witnessed inside a broad direct-root "
                "import closure; this is architecture pressure worth review."
            ),
            [closure, fan_in],
            join=join,
        )
    ]


def facade_fanout_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Join facade-inventory pressure to a witnessed facade fan-out row."""

    facade_count = nonnegative_integer_value(
        module_dag.get("facade_module_count")
    )
    if facade_count is None or facade_count < HOTSPOT_THRESHOLD:
        return []
    candidate = strongest_facade_fanout_candidate(module_dag)
    if candidate is None:
        return []
    subject = row_string(candidate.row, "module")
    facade_signal = facade_count_signal(module_dag, facade_count)
    fan_out = metric_row_signal(
        module_dag,
        candidate.row_key,
        candidate.index,
        candidate.row,
        "fan_out",
        metric_override="module_facade_fan_out",
        population_override="facade_modules",
    )
    join = build_structural_join(
        "facade_fanout_pressure",
        canonical_sections={"module_dag": module_dag},
        component_metrics=(
            "facade_module_count",
            "module_facade_fan_out",
        ),
        component_refs=component_refs((facade_signal, fan_out)),
        witness_refs=(facade_membership_witness(subject),),
        population="facade_modules",
        scope="selected_module_inventory",
        authority="module_import_graph_and_inventory_role",
        coverage_refs=(MODULE_COVERAGE_REF,),
    )
    if join is None:
        return []
    return [
        composite_finding(
            "facade_fanout_pressure",
            subject,
            (
                "A facade-population member has high fan-out; read this as "
                "API-surface context, not ordinary implementation coupling."
            ),
            [facade_signal, fan_out],
            join=join,
        )
    ]


def facade_count_signal(
    module_dag: Mapping[str, Any],
    facade_count: int,
) -> dict[str, Any]:
    """Build the exact facade-inventory component measure."""

    return component_signal(
        "facade_module_count",
        "module_inventory",
        facade_count,
        unit="module",
        population="facade_modules",
        scope="selected_module_inventory",
        denominator=known_denominator(
            module_dag.get("module_count"),
            unit="module",
            population="selected_module_inventory",
        ),
        aggregation="distinct_modules",
        authority="module_import_graph_and_inventory_role",
        coverage_ref=MODULE_COVERAGE_REF,
        evidence_ref=aggregate_value_evidence(
            "module_dag",
            "facade_module_count",
            authority="module_import_graph_and_inventory_role",
        ),
    )


def facade_membership_witness(subject: str) -> dict[str, Any]:
    """Point to the canonical facade role used by the join."""

    return {
        "type": "population-membership",
        "pointer": (
            "#/sections/module_dag/module_metadata/"
            f"{json_pointer_token(subject)}"
        ),
        "subject": subject,
        "role": "facade",
        "authority": "module_import_graph_and_inventory_role",
    }


def root_scope_findings(module_dag: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag narrow explicit-root reachability inside a broad inventory."""

    if not root_views_applicable(module_dag):
        return []
    roots = valid_string_sequence(module_dag.get("chosen_roots"))
    module_count = nonnegative_integer_value(module_dag.get("module_count"))
    unreachable = nonnegative_integer_value(
        module_dag.get(
            "source_modules_not_reachable_from_chosen_roots_count"
        )
    )
    if not root_scope_is_hot(roots, module_count, unreachable):
        return []
    if module_count is None or unreachable is None:
        return []
    total_signal, unreachable_signal = root_scope_signals(
        module_count,
        unreachable,
    )
    join = build_structural_join(
        "root_scope_pressure",
        canonical_sections={"module_dag": module_dag},
        component_metrics=("module_count", "unreachable_modules"),
        component_refs=component_refs((total_signal, unreachable_signal)),
        witness_refs=(
            root_subset_witness(roots),
            root_applicability_witness(module_dag),
        ),
        population="selected_module_inventory",
        scope="explicit_root_reachability",
        authority="module_import_graph",
        coverage_refs=(MODULE_COVERAGE_REF,),
    )
    if join is None:
        return []
    root_scope = classify_root_scope(module_dag)
    headline = unreachable_headline(module_count, unreachable)
    finding = composite_finding(
        "root_scope_pressure",
        "chosen_roots",
        root_scope_message(root_scope),
        [total_signal, unreachable_signal],
        join=join,
        headline_measure=headline,
    )
    finding["root_scope"] = root_scope
    return [finding]


def root_scope_is_hot(
    roots: Sequence[str],
    module_count: int | None,
    unreachable: int | None,
) -> bool:
    """Validate an explicit homogeneous root-reachability population."""

    return bool(
        roots
        and module_count is not None
        and unreachable is not None
        and unreachable <= module_count
        and module_count >= BROAD_INVENTORY_THRESHOLD
        and unreachable >= module_count // 2
    )


def root_scope_signals(
    module_count: int,
    unreachable: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the inventory and unreachable-subset component measures."""

    denominator = known_denominator(
        module_count,
        unit="module",
        population="selected_module_inventory",
    )
    total = component_signal(
        "module_count",
        "inventory",
        module_count,
        unit="module",
        population="selected_module_inventory",
        scope="selected_module_inventory",
        denominator=denominator,
        aggregation="distinct_modules",
        authority="module_import_graph",
        coverage_ref=MODULE_COVERAGE_REF,
        evidence_ref=aggregate_value_evidence(
            "module_dag",
            "module_count",
            authority="module_import_graph",
        ),
    )
    unreachable_signal = component_signal(
        "unreachable_modules",
        "chosen_roots",
        unreachable,
        unit="module",
        population="selected_module_inventory",
        scope="explicit_root_reachability",
        denominator=denominator,
        aggregation="distinct_modules",
        authority="module_import_graph",
        coverage_ref=MODULE_COVERAGE_REF,
        evidence_ref=aggregate_value_evidence(
            "module_dag",
            "source_modules_not_reachable_from_chosen_roots_count",
            authority="module_import_graph",
        ),
    )
    return total, unreachable_signal


def root_subset_witness(roots: Sequence[str]) -> dict[str, Any]:
    """Point to the population, subset count, and explicit roots."""

    return {
        "type": "population-subset",
        "populationPointer": "#/sections/module_dag/module_count",
        "subsetPointer": (
            "#/sections/module_dag/"
            "source_modules_not_reachable_from_chosen_roots_count"
        ),
        "rootsPointer": "#/sections/module_dag/chosen_roots",
        "roots": list(roots),
        "authority": "module_import_graph",
    }


def unreachable_headline(
    module_count: int,
    unreachable: int,
) -> dict[str, Any]:
    """Expose one homogeneous subset count rather than a synthetic sum."""

    return {
        "metric": "unreachable_modules",
        "value": unreachable,
        "unit": "module",
        "population": "selected_module_inventory",
        "scope": "explicit_root_reachability",
        "denominator": known_denominator(
            module_count,
            unit="module",
            population="selected_module_inventory",
        ),
        "aggregation": "distinct_modules",
    }


def classify_root_scope(module_dag: dict[str, Any]) -> dict[str, Any]:
    """Classify why explicit-root reachability is narrow."""

    root = first_chosen_root(module_dag)
    closure = top_root_closure(module_dag)
    return {
        "classification": root_scope_classification(root, closure),
        "chosen_root": root,
        "unreachable_ratio": unreachable_ratio(module_dag),
        "largest_direct_import_closure": int(closure["value"]) if closure else 0,
    }


def root_scope_classification(
    root: str | None,
    closure: dict[str, Any] | None,
) -> str:
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

    roots = valid_string_sequence(module_dag.get("chosen_roots"))
    return roots[0] if roots else None


def unreachable_ratio(module_dag: dict[str, Any]) -> float:
    """Return unreachable modules divided by total modules."""

    module_count = nonnegative_integer_value(module_dag.get("module_count"))
    unreachable = nonnegative_integer_value(
        module_dag.get(
            "source_modules_not_reachable_from_chosen_roots_count"
        )
    )
    if not module_count or unreachable is None:
        return 0.0
    return round(unreachable / module_count, 3)


def root_scope_message(root_scope: dict[str, Any]) -> str:
    """Build a root-scope pressure message with classification context."""

    classification = root_scope["classification"]
    return (
        "The explicit root reaches a narrow slice of a broad inventory; "
        f"classification={classification}. Treat inventory rows as "
        "review-scope pressure."
    )


def proof_family_import_findings(
    module_dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Join a repeated declaration family to a broad root/import structure."""

    if declaration_graph is None or not root_views_applicable(module_dag):
        return []
    candidate = strongest_proof_family_candidate(
        module_dag,
        declaration_graph,
    )
    if candidate is None:
        return []
    closure = root_closure_signal(
        module_dag,
        candidate.closure_index,
        candidate.closure,
    )
    family = metric_row_signal(
        declaration_graph,
        "declaration_name_families",
        candidate.family_index,
        candidate.family,
        "count",
    )
    witnesses = proof_family_witnesses(module_dag, candidate)
    join = build_structural_join(
        "proof_family_import_pressure",
        canonical_sections={
            "module_dag": module_dag,
            "declaration_graph": declaration_graph,
        },
        component_metrics=(
            "root_import_closure",
            "declaration_family_size",
        ),
        component_refs=component_refs((closure, family)),
        witness_refs=witnesses,
        population="declarations_contained_by_root_import_structure",
        scope=str(closure["measure"]["scope"]),
        authority=COMPOSITE_AUTHORITY,
        coverage_refs=(MODULE_COVERAGE_REF, DECLARATION_COVERAGE_REF),
    )
    if join is None:
        return []
    headline = joined_family_headline(closure, family, candidate)
    join["joinedMeasure"] = headline
    return [
        composite_finding(
            "proof_family_import_pressure",
            family["subject"],
            (
                "Repeated declaration-family members are witnessed in a broad "
                "root/import structure; this is proof-architecture pressure."
            ),
            [closure, family],
            join=join,
            headline_measure=headline,
        )
    ]


def proof_family_witnesses(
    module_dag: Mapping[str, Any],
    candidate: Any,
) -> tuple[dict[str, Any], ...]:
    """Build root, declaration-containment, and graph-path witnesses."""

    path_witnesses = tuple(
        witness
        for _, path in candidate.module_paths
        for witness in [graph_path_witness(module_dag.get("edges"), path)]
        if witness is not None
    )
    return (
        root_applicability_witness(module_dag),
        declaration_containment_witness(
            candidate.joined_members,
            root=row_string(candidate.closure, "root"),
        ),
        *path_witnesses,
    )


def declaration_containment_witness(
    members: Sequence[tuple[int, Mapping[str, Any]]],
    *,
    root: str,
) -> dict[str, Any]:
    """Return bounded exact declaration pointers plus the complete joined count."""

    member_refs = [
        {
            "declaration": row_string(row, "declaration"),
            "module": row_string(row, "module"),
            "pointer": f"#/sections/declaration_graph/declarations/{index}",
        }
        for index, row in members[:12]
    ]
    return {
        "type": "declaration-containment",
        "pointer": "#/sections/declaration_graph/declarations",
        "root": root,
        "joinedDeclarationCount": len(members),
        "sampleMemberRefs": member_refs,
        "sampleOmitted": max(0, len(members) - len(member_refs)),
        "authority": "declaration_graph_and_module_import_graph",
    }


def joined_family_headline(
    closure: Mapping[str, Any],
    family: Mapping[str, Any],
    candidate: Any,
) -> dict[str, Any]:
    """Expose the deduplicated joined declaration population."""

    return {
        "metric": "joined_declaration_family_size",
        "value": len(candidate.joined_members),
        "unit": "declaration",
        "population": "declarations_contained_by_root_import_structure",
        "scope": str(closure["measure"]["scope"]),
        "denominator": known_denominator(
            family["value"],
            unit="declaration",
            population="declaration_name_family",
        ),
        "aggregation": "distinct_declarations",
    }


def composite_finding(
    kind: str,
    subject: str,
    message: str,
    component_signals: list[dict[str, Any]],
    *,
    join: Mapping[str, Any] | None = None,
    headline_measure: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one composite only when its structural join is available."""

    if join is None:
        raise ValueError("composite findings require structural join evidence")
    evidence_refs = component_refs(component_signals)
    if len(evidence_refs) != len(component_signals):
        raise ValueError(
            "composite findings require one canonical reference per component"
        )
    row = composite_base(
        kind,
        subject,
        message,
        component_signals,
        evidence_refs=evidence_refs,
        join=join,
    )
    if headline_measure is not None:
        add_headline_measure(row, headline_measure)
    return row


def composite_base(
    kind: str,
    subject: str,
    message: str,
    component_signals: Sequence[Mapping[str, Any]],
    *,
    evidence_refs: list[dict[str, Any]],
    join: Mapping[str, Any],
) -> dict[str, Any]:
    """Build common composite fields without inventing a numeric headline."""

    public_signals = [
        {key: value for key, value in signal.items() if key != "evidenceRef"}
        for signal in component_signals
    ]
    authorities = sorted(
        {
            str(signal.get("authority", "ladon_derived_heuristic"))
            for signal in component_signals
        }
    )
    return {
        "kind": kind,
        "severity": "info",
        "subject": subject,
        "stable_key": f"{kind}:{subject}",
        "message": message,
        "authority": COMPOSITE_AUTHORITY,
        "componentAuthorities": authorities,
        "component_signals": public_signals,
        "join": dict(join),
        "coverage": dict(join.get("coverage", {})),
        "nonclaims": [JOIN_NONCLAIM],
        "evidenceRefs": evidence_refs,
    }


def add_headline_measure(
    row: dict[str, Any],
    headline_measure: Mapping[str, Any],
) -> None:
    """Attach one validated homogeneous headline measure."""

    headline = dict(headline_measure)
    value = nonnegative_integer_value(headline.get("value"))
    if value is None:
        raise ValueError("headline measure value must be non-negative")
    row["count"] = value
    row["metric"] = str(headline.get("metric", ""))
    row["headlineMeasure"] = headline


def root_applicability_witness(
    module_dag: Mapping[str, Any],
) -> dict[str, Any]:
    """Reference explicit applicability, or the legacy chosen-root field."""

    envelope = module_dag.get("root_reachability")
    if isinstance(envelope, Mapping):
        return {
            "type": "root-applicability",
            "pointer": "#/sections/module_dag/root_reachability",
            "status": envelope.get("status"),
            "authority": str(
                envelope.get("authority", "module_import_graph")
            ),
        }
    return {
        "type": "legacy-root-applicability",
        "pointer": "#/sections/module_dag/chosen_roots",
        "authority": "module_import_graph",
    }


__all__ = [
    "architecture_pressure_findings",
    "classify_root_scope",
    "component_signal",
    "composite_finding",
    "facade_fanout_findings",
    "import_pressure_findings",
    "proof_family_import_findings",
    "root_scope_findings",
    "top_metric_row",
    "top_root_closure",
]
