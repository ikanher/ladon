"""Precomputed inventory facts and rankings for module-DAG analysis."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ladon.ir import LeanModule


@dataclass(frozen=True)
class ModuleInventoryIndex:
    """Structural classifications reused throughout one DAG summary."""

    facade_subtypes: Mapping[str, str]
    roles: Mapping[str, tuple[str, ...]]
    tags: Mapping[str, frozenset[str]]


def build_module_inventory_index(
    modules: Mapping[str, LeanModule],
) -> ModuleInventoryIndex:
    """Index namespace, facade, role, and tag facts in linear inventory time."""

    namespace_parents = namespace_parent_names(modules)
    subtypes = {
        name: classify_facade_subtype(
            module,
            import_count=len(set(module.imports)),
            has_namespace_children=module.name in namespace_parents,
        )
        for name, module in modules.items()
    }
    return ModuleInventoryIndex(
        facade_subtypes=subtypes,
        roles={
            name: ("facade", subtype) if subtype else ()
            for name, subtype in subtypes.items()
        },
        tags={
            name: frozenset(module.tags)
            for name, module in modules.items()
        },
    )


def namespace_parent_names(
    modules: Mapping[str, LeanModule],
) -> frozenset[str]:
    """Return module names that prefix at least one discovered child."""

    candidates = {module.name for module in modules.values()}
    parents: set[str] = set()
    for child in modules:
        separator = child.find(".")
        while separator >= 0:
            candidate = child[:separator]
            if candidate in candidates:
                parents.add(candidate)
            separator = child.find(".", separator + 1)
    return frozenset(parents)


def classify_facade_subtype(
    module: LeanModule,
    *,
    import_count: int,
    has_namespace_children: bool,
) -> str:
    """Classify one module from already-computed inventory facts."""

    if import_count == 0:
        return ""
    if "generated" in module.tags and module.name.rsplit(".", 1)[-1] == "All":
        return "generated_all"
    if has_namespace_children and import_count >= 5:
        return "public_root_facade"
    if not module.declarations:
        return "pure_barrel"
    if import_count >= 5:
        return "mixed_barrel_and_theorems"
    return ""


def facade_names(inventory: ModuleInventoryIndex) -> list[str]:
    """Return sorted facade names from an inventory classification."""

    return sorted(
        name
        for name, subtype in inventory.facade_subtypes.items()
        if subtype
    )


def facade_subtype_counts(
    inventory: ModuleInventoryIndex,
) -> dict[str, int]:
    """Count indexed facade-like modules by subtype."""

    counts: dict[str, int] = defaultdict(int)
    for subtype in inventory.facade_subtypes.values():
        if subtype:
            counts[subtype] += 1
    return dict(sorted(counts.items()))


def top_facade_rows(
    modules: Mapping[str, LeanModule],
    inventory: ModuleInventoryIndex,
) -> list[dict[str, Any]]:
    """Return facade-like modules with subtype and import breadth."""

    rows = [
        {
            "module": module.name,
            "path": module.path,
            "fan_out": len(set(module.imports)),
            "declarationCount": len(module.declarations),
            "subtype": subtype,
            "tags": list(module.tags),
        }
        for name, module in modules.items()
        for subtype in [inventory.facade_subtypes[name]]
        if subtype
    ]
    return sorted(rows, key=lambda row: (-int(row["fan_out"]), row["module"]))[:20]


def top_fan_in_rows(
    modules: Mapping[str, LeanModule],
    reverse_edges: Mapping[str, Sequence[str]],
    inventory: ModuleInventoryIndex,
    *,
    included_tags: Sequence[str] = (),
    excluded_tags: Sequence[str] = (),
    included_importer_tags: Sequence[str] = (),
    excluded_importer_tags: Sequence[str] = (),
    population: str = "all_importers_to_all_targets",
) -> list[dict[str, Any]]:
    """Rank fan-in with filter and importer populations computed once."""

    ranked = sorted(
        (
            (
                name,
                indexed_fan_in_importers(
                    name,
                    modules,
                    reverse_edges,
                    inventory,
                    included_tags=included_importer_tags,
                    excluded_tags=excluded_importer_tags,
                ),
            )
            for name in matching_module_names(
                inventory,
                included_tags=included_tags,
                excluded_tags=excluded_tags,
            )
        ),
        key=lambda item: (len(item[1]), item[0]),
        reverse=True,
    )[:15]
    return [
        {
            "module": name,
            "path": modules[name].path,
            "fan_in": len(importers),
            "sample_importers": importers[:12],
            "population": population,
            "authority": "module_import_graph",
        }
        for name, importers in ranked
    ]


def indexed_fan_in_importers(
    target: str,
    modules: Mapping[str, LeanModule],
    reverse_edges: Mapping[str, Sequence[str]],
    inventory: ModuleInventoryIndex,
    *,
    included_tags: Sequence[str],
    excluded_tags: Sequence[str],
) -> list[str]:
    """Return sorted importers using precomputed tag sets."""

    included = frozenset(included_tags)
    excluded = frozenset(excluded_tags)
    return sorted(
        importer
        for importer in reverse_edges.get(target, ())
        if importer in modules
        and (not included or not inventory.tags[importer].isdisjoint(included))
        and inventory.tags[importer].isdisjoint(excluded)
    )


def top_fan_out_rows(
    modules: Mapping[str, LeanModule],
    edges: Mapping[str, Sequence[str]],
    inventory: ModuleInventoryIndex,
    *,
    excluded_tags: Sequence[str] = (),
    included_roles: Sequence[str] = (),
    excluded_roles: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """Rank fan-out using one reusable structural classification index."""

    return [
        {
            "module": name,
            "path": modules[name].path,
            "fan_out": len(edges.get(name, ())),
            "sample_imports": list(edges.get(name, ()))[:12],
            "roles": list(inventory.roles[name]),
        }
        for name in sorted(
            matching_module_names(
                inventory,
                excluded_tags=excluded_tags,
                included_roles=included_roles,
                excluded_roles=excluded_roles,
            ),
            key=lambda item: (len(edges.get(item, ())), item),
            reverse=True,
        )[:15]
    ]


def matching_module_names(
    inventory: ModuleInventoryIndex,
    *,
    included_tags: Sequence[str] = (),
    excluded_tags: Sequence[str] = (),
    included_roles: Sequence[str] = (),
    excluded_roles: Sequence[str] = (),
) -> list[str]:
    """Filter names against precomputed tag and structural-role sets."""

    included_tag_set = frozenset(included_tags)
    excluded_tag_set = frozenset(excluded_tags)
    included_role_set = frozenset(included_roles)
    excluded_role_set = frozenset(excluded_roles)
    return [
        name
        for name, tags in inventory.tags.items()
        if (not included_tag_set or not tags.isdisjoint(included_tag_set))
        and tags.isdisjoint(excluded_tag_set)
        and (
            not included_role_set
            or not included_role_set.isdisjoint(inventory.roles[name])
        )
        and excluded_role_set.isdisjoint(inventory.roles[name])
    ]
