"""Pure exact-reference graph analysis for Lean declarations.

This module intentionally performs only conservative name matching. It resolves
exact names, module-local names, and globally unique basenames, but does not
elaborate references or invoke Lean.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Collection, Mapping, Sequence
from typing import Any

from ladon.analysis.proof_family_similarity import proof_family_similarity_candidates
from ladon.ir import LeanDeclaration

EXTERNAL_REFERENCE_ROOTS = {
    "Array",
    "Bool",
    "Classical",
    "Decidable",
    "Eq",
    "False",
    "Fin",
    "Finset",
    "Fintype",
    "Function",
    "HEq",
    "Int",
    "List",
    "Nat",
    "Option",
    "Prod",
    "Prop",
    "Rat",
    "Real",
    "Set",
    "Sigma",
    "Sort",
    "Subtype",
    "True",
    "Type",
    "Unit",
}


def summarize_declaration_graph(
    declarations: Mapping[str, LeanDeclaration],
    *,
    chosen_roots: Sequence[str] = (),
    known_reference_names: Collection[str] = (),
) -> dict[str, Any]:
    """Summarize exact declaration references without side effects."""

    names = sorted(declarations)
    known_references = set(known_reference_names)
    edges = declaration_edges(declarations)
    reverse_edges = reverse_declaration_edges(names, edges)
    roots = known_declaration_roots(chosen_roots, declarations)
    unreachable = unreachable_declarations(names, edges, roots)
    unresolved_profiles = unresolved_class_profiles(declarations, known_references)
    return {
        "scope": "declaration_inventory",
        "method": "exact_declaration_reference_graph",
        "declaration_count": len(names),
        "edge_count": sum(len(targets) for targets in edges.values()),
        "unresolved_reference_count": unresolved_reference_count(declarations),
        "unresolved_reference_classes": unresolved_reference_classes(
            declarations,
            known_reference_names=known_references,
        ),
        "top_unresolved_references": top_unresolved_references(
            declarations,
            known_reference_names=known_references,
        ),
        "top_actionable_unresolved_references": top_actionable_unresolved_references(
            declarations,
            known_reference_names=known_references,
        ),
        "top_fan_in": top_fan_in(declarations, reverse_edges),
        "top_fan_out": top_fan_out(declarations, edges),
        "declaration_name_families": declaration_name_families(declarations),
        "proof_family_similarity_candidates": proof_family_similarity_candidates(
            declarations,
            edges,
            unresolved_profiles,
        ),
        "chosen_roots": list(roots),
        "declarations_not_reachable_from_chosen_roots": unreachable[:50],
        "declarations_not_reachable_from_chosen_roots_count": len(unreachable),
        "edges": edges,
    }


def declaration_edges(
    declarations: Mapping[str, LeanDeclaration],
) -> dict[str, list[str]]:
    """Return declaration -> conservatively resolved referenced declarations."""

    resolver = ReferenceResolver(declarations)
    return {
        name: sorted(
            resolved
            for reference in declaration.references
            for resolved in [resolver.resolve(declaration, reference)]
            if resolved
        )
        for name, declaration in declarations.items()
    }


def unresolved_reference_count(declarations: Mapping[str, LeanDeclaration]) -> int:
    """Count reference candidates that do not exactly match known names."""

    resolver = ReferenceResolver(declarations)
    return sum(
        1
        for declaration in declarations.values()
        for reference in declaration.references
        if resolver.resolve(declaration, reference) is None
    )


def top_unresolved_references(
    declarations: Mapping[str, LeanDeclaration],
    *,
    known_reference_names: Collection[str] = (),
) -> list[dict[str, Any]]:
    """Return unresolved reference candidates grouped by spelling."""

    resolver = ReferenceResolver(declarations)
    rows = unresolved_reference_sources(declarations, resolver)
    return unresolved_reference_rows(rows, known_reference_names)


def top_actionable_unresolved_references(
    declarations: Mapping[str, LeanDeclaration],
    *,
    known_reference_names: Collection[str] = (),
) -> list[dict[str, Any]]:
    """Return unresolved candidates that look worth human follow-up."""

    resolver = ReferenceResolver(declarations)
    rows = unresolved_reference_sources(declarations, resolver)
    return [
        row
        for row in unresolved_reference_rows(rows, known_reference_names, limit=None)
        if row["classification"] == "actionable_unknown"
    ][:15]


def unresolved_reference_classes(
    declarations: Mapping[str, LeanDeclaration],
    *,
    known_reference_names: Collection[str] = (),
) -> list[dict[str, Any]]:
    """Return total unresolved occurrences grouped by classification."""

    resolver = ReferenceResolver(declarations)
    rows = unresolved_reference_sources(declarations, resolver)
    inventory = set(known_reference_names)
    counts: dict[str, int] = {}
    for candidate, sources in rows.items():
        classification = classify_unresolved_candidate(candidate, inventory)
        counts[classification] = counts.get(classification, 0) + len(sources)
    return [
        {"classification": classification, "count": count}
        for classification, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def unresolved_class_profiles(
    declarations: Mapping[str, LeanDeclaration],
    known_reference_names: Collection[str] = (),
) -> dict[str, dict[str, int]]:
    """Return unresolved-reference class counts per source declaration."""

    resolver = ReferenceResolver(declarations)
    inventory = set(known_reference_names)
    profiles: dict[str, dict[str, int]] = {}
    for name, declaration in declarations.items():
        profile: dict[str, int] = {}
        for reference in declaration.references:
            if resolver.resolve(declaration, reference) is None:
                classification = classify_unresolved_candidate(reference, inventory)
                profile[classification] = profile.get(classification, 0) + 1
        profiles[name] = profile
    return profiles


def unresolved_reference_rows(
    rows: Mapping[str, Sequence[str]],
    known_reference_names: Collection[str] = (),
    *,
    limit: int | None = 15,
) -> list[dict[str, Any]]:
    """Convert grouped unresolved sources into stable report rows."""

    inventory = set(known_reference_names)
    sorted_rows = [
        {
            "candidate": candidate,
            "classification": classify_unresolved_candidate(candidate, inventory),
            "count": len(sources),
            "sample_sources": sources[:12],
        }
        for candidate, sources in sorted(rows.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    return sorted_rows if limit is None else sorted_rows[:limit]


def unresolved_reference_sources(
    declarations: Mapping[str, LeanDeclaration],
    resolver: ReferenceResolver,
) -> dict[str, list[str]]:
    """Group unresolved candidate references by source declaration."""

    rows: dict[str, list[str]] = {}
    for source_name, declaration in sorted(declarations.items()):
        for reference in declaration.references:
            if resolver.resolve(declaration, reference) is None:
                rows.setdefault(reference, []).append(source_name)
    return rows


def classify_unresolved_candidate(
    candidate: str,
    known_reference_names: set[str] | None = None,
) -> str:
    """Classify one unresolved reference candidate for report triage."""

    inventory = known_reference_names or set()
    if is_parser_noise_candidate(candidate):
        return "parser_noise"
    if is_external_candidate(candidate):
        return "external_candidate"
    if is_known_inventory_candidate(candidate, inventory):
        return "known_inventory_candidate"
    if is_local_or_field_candidate(candidate):
        return "local_or_field_candidate"
    return "actionable_unknown"


def is_parser_noise_candidate(candidate: str) -> bool:
    """Return whether the parser candidate is structural noise."""

    return candidate.startswith("[")


def is_external_candidate(candidate: str) -> bool:
    """Return whether a candidate looks like a Lean/library external name."""

    root = candidate.split(".", 1)[0]
    return root in EXTERNAL_REFERENCE_ROOTS


def is_known_inventory_candidate(candidate: str, known_reference_names: set[str]) -> bool:
    """Return whether text discovery saw this candidate as a declaration name."""

    return (
        candidate in known_reference_names
        or candidate.rsplit(".", 1)[-1] in known_reference_names
    )


def is_local_or_field_candidate(candidate: str) -> bool:
    """Return whether a candidate looks like a local binder or field name."""

    root = candidate.split(".", 1)[0]
    return is_bare_identifier(root) and (root[0].islower() or root.startswith("_"))


def is_bare_identifier(candidate: str) -> bool:
    """Return whether a candidate has no namespace or parser punctuation."""

    return bool(candidate) and all(char.isalnum() or char in "_'" for char in candidate)


class ReferenceResolver:
    """Conservative declaration reference resolver.

    The resolver is deliberately weaker than Lean elaboration. It resolves
    exact names, module-local names, and unique basenames only.
    """

    def __init__(self, declarations: Mapping[str, LeanDeclaration]) -> None:
        self.declarations = declarations
        self.by_basename = declarations_by_basename(declarations)

    def resolve(self, source: LeanDeclaration, candidate: str) -> str | None:
        """Resolve one candidate reference or return `None`."""

        return (
            exact_match(candidate, self.declarations)
            or exact_match(f"{source.module}.{candidate}", self.declarations)
            or unique_basename_match(candidate, self.by_basename)
        )


def declarations_by_basename(
    declarations: Mapping[str, LeanDeclaration],
) -> dict[str, list[str]]:
    """Group known declarations by final dotted name segment."""

    grouped: dict[str, list[str]] = {}
    for name in declarations:
        grouped.setdefault(name.rsplit(".", 1)[-1], []).append(name)
    return {name: sorted(matches) for name, matches in grouped.items()}


def exact_match(candidate: str, declarations: Mapping[str, LeanDeclaration]) -> str | None:
    """Return candidate when it is a known full declaration name."""

    return candidate if candidate in declarations else None


def unique_basename_match(
    candidate: str,
    by_basename: Mapping[str, Sequence[str]],
) -> str | None:
    """Resolve a candidate basename only when it is globally unique."""

    matches = by_basename.get(candidate, ())
    return matches[0] if len(matches) == 1 else None


def reverse_declaration_edges(
    names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
) -> dict[str, list[str]]:
    """Return referenced declaration -> referencing declarations."""

    reverse_edges = {name: [] for name in names}
    for source, targets in edges.items():
        for target in targets:
            reverse_edges[target].append(source)
    return {name: sorted(sources) for name, sources in reverse_edges.items()}


def known_declaration_roots(
    chosen_roots: Sequence[str],
    declarations: Mapping[str, LeanDeclaration],
) -> tuple[str, ...]:
    """Ignore requested roots that are not in the declaration inventory."""

    return tuple(root for root in chosen_roots if root in declarations)


def unreachable_declarations(
    names: Sequence[str],
    edges: Mapping[str, Sequence[str]],
    roots: Sequence[str],
) -> list[str]:
    """Return declarations not reachable from selected roots."""

    if not roots:
        return []
    reached = reachable_declarations(edges, roots)
    return sorted(name for name in names if name not in reached)


def reachable_declarations(
    edges: Mapping[str, Sequence[str]],
    roots: Sequence[str],
) -> set[str]:
    """Follow outgoing exact-reference edges from root declarations."""

    reached: set[str] = set()
    queue: deque[str] = deque(sorted(roots))
    while queue:
        declaration = queue.popleft()
        if declaration in reached:
            continue
        reached.add(declaration)
        queue.extend(target for target in edges.get(declaration, ()) if target not in reached)
    return reached


def top_fan_in(
    declarations: Mapping[str, LeanDeclaration],
    reverse_edges: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Return declarations most often referenced by known declarations."""

    return [
        {
            "declaration": name,
            "module": declarations[name].module,
            "fan_in": len(reverse_edges.get(name, ())),
            "sample_referrers": list(reverse_edges.get(name, ()))[:12],
        }
        for name in sorted(
            declarations,
            key=lambda item: (len(reverse_edges.get(item, ())), item),
            reverse=True,
        )[:15]
    ]


def top_fan_out(
    declarations: Mapping[str, LeanDeclaration],
    edges: Mapping[str, Sequence[str]],
) -> list[dict[str, Any]]:
    """Return declarations with the broadest known reference surface."""

    return [
        {
            "declaration": name,
            "module": declarations[name].module,
            "fan_out": len(edges.get(name, ())),
            "sample_references": list(edges.get(name, ()))[:12],
        }
        for name in sorted(
            declarations,
            key=lambda item: (len(edges.get(item, ())), item),
            reverse=True,
        )[:15]
    ]


def declaration_name_families(
    declarations: Mapping[str, LeanDeclaration],
) -> list[dict[str, Any]]:
    """Group declarations by basename suffix after the first underscore."""

    grouped: dict[str, list[str]] = {}
    for name in declarations:
        suffix = declaration_family_suffix(name)
        if suffix:
            grouped.setdefault(suffix, []).append(name)
    return [
        {
            "suffix": suffix,
            "count": len(names),
            "sample_declarations": sorted(names)[:12],
        }
        for suffix, names in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0]))
        if len(names) >= 2
    ][:15]


def declaration_family_suffix(name: str) -> str | None:
    """Return the repeated-shape suffix for a declaration name."""

    basename = name.rsplit(".", 1)[-1]
    if "_" not in basename:
        return None
    return basename.split("_", 1)[1]
