"""Policy-driven architecture boundary checks for module import DAGs.

The policy language is intentionally project-defined. Ladon supplies only the
generic graph machinery: module groups come from glob patterns in the policy,
and rules say which group-to-group imports should be reviewed.
"""

from __future__ import annotations

from collections import defaultdict, deque
from fnmatch import fnmatchcase
from typing import Any

from ladon.analysis.architecture_policy_suggestions import draft_policy_suggestions
from ladon.analysis.architecture_policy_summary import (
    direct_context_summary,
    direct_offending_file_summary,
    direct_pair_summary,
    finding_summary,
    group_membership_counts,
    shared_dependency_summary,
)


DEFAULT_MAX_FINDINGS = 30
DEFAULT_MAX_PATH_LENGTH = 12
DEFAULT_BRIDGE_TOKENS = ("Bridge", "Transport", "Comparison", "Calibration", "Surface")


def skipped_architecture_policy_report(
    module_dag: dict[str, Any],
    *,
    searched_paths: list[str],
) -> dict[str, Any]:
    """Return a visible report when no project architecture policy is present."""

    suggestions = draft_policy_suggestions(module_dag)
    finding_row = finding(
        "architecture_policy.skipped_no_policy",
        "architecture_policy",
        "info",
        (
            "No architecture policy was supplied or discovered; Ladon did not "
            "enforce project-specific module boundary rules."
        ),
        searchedPaths=searched_paths,
        suggestedPolicyCount=len(suggestions),
    )
    return {
        "artifactKind": "ladon_architecture_policy_report",
        "schemaVersion": 1,
        "policyId": "",
        "status": "skipped_no_policy",
        "groupCount": 0,
        "ruleCount": 0,
        "matchedModuleCount": 0,
        "summary": {"architecture_policy.skipped_no_policy": 1},
        "groupMembershipCounts": {},
        "directPairSummary": [],
        "directContextSummary": [],
        "directOffendingFileSummary": [],
        "sharedDependencySummary": [],
        "draftPolicySuggestions": suggestions,
        "trustNote": "No architecture policy supplied; draft suggestions are name-prefix heuristics, not enforced boundary claims.",
        "findings": [finding_row],
    }


def summarize_architecture_policy(
    module_dag: dict[str, Any],
    policy: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return policy findings for a module DAG and user-supplied policy."""

    if not policy:
        return empty_policy_report()
    groups = normalize_groups(policy.get("groups", {}))
    rules = normalize_rules(policy.get("rules", []))
    edges = normalized_edges(module_dag.get("edges", {}))
    import_sites = normalized_import_sites(module_dag.get("import_sites", {}))
    module_metadata = normalized_module_metadata(module_dag.get("module_metadata", {}))
    membership = module_membership(edges, groups)
    findings: list[dict[str, Any]] = []
    findings.extend(ambiguous_membership_findings(membership))
    for rule in rules:
        findings.extend(rule_findings(rule, edges, import_sites, membership, module_metadata))
    findings = dedupe_findings(findings)
    return {
        "artifactKind": "ladon_architecture_policy_report",
        "schemaVersion": 1,
        "policyId": str(policy.get("id") or policy.get("policyId") or ""),
        "groupCount": len(groups),
        "ruleCount": len(rules),
        "matchedModuleCount": sum(1 for matched in membership.values() if matched),
        "summary": finding_summary(findings),
        "groupMembershipCounts": group_membership_counts(membership),
        "directPairSummary": direct_pair_summary(findings),
        "directContextSummary": direct_context_summary(findings),
        "directOffendingFileSummary": direct_offending_file_summary(findings),
        "sharedDependencySummary": shared_dependency_summary(findings),
        "trustNote": "Architecture policy findings enforce project-supplied import boundaries only; they are not proof, theorem, or semantic dependency claims.",
        "findings": findings,
    }


def empty_policy_report() -> dict[str, Any]:
    """Return the stable empty policy report."""

    return {
        "artifactKind": "ladon_architecture_policy_report",
        "schemaVersion": 1,
        "policyId": "",
        "groupCount": 0,
        "ruleCount": 0,
        "matchedModuleCount": 0,
        "summary": {},
        "groupMembershipCounts": {},
        "directPairSummary": [],
        "directContextSummary": [],
        "directOffendingFileSummary": [],
        "sharedDependencySummary": [],
        "draftPolicySuggestions": [],
        "trustNote": "No architecture policy supplied.",
        "findings": [],
    }


def normalize_groups(raw_groups: Any) -> dict[str, tuple[str, ...]]:
    """Normalize policy group declarations to id -> glob patterns."""

    if not isinstance(raw_groups, dict):
        return {}
    groups: dict[str, tuple[str, ...]] = {}
    for group_id, spec in raw_groups.items():
        patterns = group_patterns(spec)
        if patterns:
            groups[str(group_id)] = tuple(patterns)
    return groups


def group_patterns(spec: Any) -> list[str]:
    """Return glob patterns from supported group policy shapes."""

    if isinstance(spec, str):
        return [spec]
    if isinstance(spec, list):
        return [str(item) for item in spec if str(item)]
    if isinstance(spec, dict):
        patterns = spec.get("patterns", spec.get("match", []))
        if isinstance(patterns, str):
            return [patterns]
        if isinstance(patterns, list):
            return [str(item) for item in patterns if str(item)]
    return []


def normalize_rules(raw_rules: Any) -> list[dict[str, Any]]:
    """Keep supported rule rows with normalized defaults."""

    if not isinstance(raw_rules, list):
        return []
    rules = []
    for index, raw_rule in enumerate(raw_rules):
        if not isinstance(raw_rule, dict):
            continue
        kind = str(raw_rule.get("kind", ""))
        if kind not in {"forbid_imports", "forbid_direct_imports", "forbid_transitive_imports"}:
            continue
        rule = dict(raw_rule)
        rule.setdefault("id", f"rule-{index + 1}")
        rule.setdefault("severity", "warning")
        rule.setdefault("excludeSameGroup", True)
        rule.setdefault("includeTransitive", kind == "forbid_transitive_imports")
        rule.setdefault("maxFindings", DEFAULT_MAX_FINDINGS)
        rule.setdefault("maxPathLength", DEFAULT_MAX_PATH_LENGTH)
        rule.setdefault("sharedDependencyMode", "policy_targets")
        return_if_missing_groups(rule)
        rules.append(rule)
    return rules


def return_if_missing_groups(rule: dict[str, Any]) -> None:
    """Fill old/new group selector aliases in-place."""

    if "from" not in rule and "fromGroups" in rule:
        rule["from"] = rule["fromGroups"]
    if "to" not in rule and "toGroups" in rule:
        rule["to"] = rule["toGroups"]


def normalized_edges(raw_edges: Any) -> dict[str, tuple[str, ...]]:
    """Return importer -> imported module edges from a DAG report."""

    if not isinstance(raw_edges, dict):
        return {}
    return {
        str(source): tuple(str(target) for target in targets if str(target))
        for source, targets in raw_edges.items()
        if isinstance(targets, list)
    }


def normalized_import_sites(raw_sites: Any) -> dict[tuple[str, str], dict[str, Any]]:
    """Return source evidence keyed by (source module, target module)."""

    if not isinstance(raw_sites, dict):
        return {}
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for source, targets in raw_sites.items():
        if not isinstance(targets, dict):
            continue
        for target, site in targets.items():
            if isinstance(site, dict):
                rows[(str(source), str(target))] = {
                    "sourcePath": str(site.get("sourcePath", "")),
                    "line": site.get("line"),
                    "importText": str(site.get("importText", "")),
                }
    return rows


def normalized_module_metadata(raw_metadata: Any) -> dict[str, dict[str, Any]]:
    """Return module metadata keyed by module name."""

    if not isinstance(raw_metadata, dict):
        return {}
    return {
        str(module): metadata
        for module, metadata in raw_metadata.items()
        if isinstance(metadata, dict)
    }


def module_membership(
    edges: dict[str, tuple[str, ...]],
    groups: dict[str, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    """Return group memberships for every module mentioned in the graph."""

    modules = sorted(set(edges) | {target for targets in edges.values() for target in targets})
    return {
        module: tuple(
            group_id
            for group_id, patterns in groups.items()
            if any(fnmatchcase(module, pattern) for pattern in patterns)
        )
        for module in modules
    }


def ambiguous_membership_findings(membership: dict[str, tuple[str, ...]]) -> list[dict[str, Any]]:
    """Warn when a policy pattern puts one module in multiple groups."""

    return [
        finding(
            "architecture_policy.ambiguous_group_match",
            module,
            "warning",
            f"{module} matches multiple architecture policy groups: {', '.join(groups)}.",
            groups=list(groups),
        )
        for module, groups in sorted(membership.items())
        if len(groups) > 1
    ][:DEFAULT_MAX_FINDINGS]


def rule_findings(
    rule: dict[str, Any],
    edges: dict[str, tuple[str, ...]],
    import_sites: dict[tuple[str, str], dict[str, Any]],
    membership: dict[str, tuple[str, ...]],
    module_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return findings for one normalized policy rule."""

    rows = []
    if rule.get("kind") != "forbid_transitive_imports":
        rows.extend(direct_import_findings(rule, edges, import_sites, membership, module_metadata))
    if bool(rule.get("includeTransitive")) or rule.get("kind") == "forbid_transitive_imports":
        rows.extend(transitive_import_findings(rule, edges, import_sites, membership))
    if bool(rule.get("suggestCommonDependencies", False)):
        rows.extend(shared_dependency_findings(rule, edges, membership))
    return rows


def direct_import_findings(
    rule: dict[str, Any],
    edges: dict[str, tuple[str, ...]],
    import_sites: dict[tuple[str, str], dict[str, Any]],
    membership: dict[str, tuple[str, ...]],
    module_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return direct forbidden import findings for one rule."""

    rows = []
    for source, targets in sorted(edges.items()):
        for target in sorted(targets):
            pairs = forbidden_group_pairs(rule, source, target, membership)
            if not pairs or ignored_edge(rule, source, target):
                continue
            site = import_sites.get((source, target), {})
            context = direct_policy_context(rule, source, target, site, module_metadata)
            rows.append(
                finding(
                    "architecture_policy.direct_forbidden_import",
                    f"{source} -> {target}",
                    str(rule.get("severity", "warning")),
                    direct_import_message(rule, source, target, pairs),
                    policyRule=str(rule["id"]),
                    sourceModule=source,
                    targetModule=target,
                    sourceGroup=pairs[0][0],
                    targetGroup=pairs[0][1],
                    policyContext=context["policyContext"],
                    triageSeverity=context["triageSeverity"],
                    contextTokens=context["matchedTokens"],
                    suggestedAction=context["suggestedAction"],
                    groupPairs=[
                        {"sourceGroup": source_group, "targetGroup": target_group}
                        for source_group, target_group in pairs
                    ],
                    sourcePath=site.get("sourcePath"),
                    line=site.get("line"),
                    importText=site.get("importText"),
                )
            )
    return rows[:int(rule.get("maxFindings", DEFAULT_MAX_FINDINGS))]


def direct_policy_context(
    rule: dict[str, Any],
    source: str,
    target: str,
    site: dict[str, Any],
    module_metadata: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Classify a direct policy violation for triage without suppressing it."""

    source_metadata = module_metadata.get(source, {})
    target_metadata = module_metadata.get(target, {})
    text = " ".join([source, target, str(site.get("sourcePath", "")), str(site.get("importText", ""))])
    matched = matched_context_tokens(text, context_tokens(rule, "bridgeTokens", DEFAULT_BRIDGE_TOKENS))
    if matched:
        return policy_context("bridge-ish", "warning", matched, bridge_action())
    if has_facade_role(source_metadata) or has_facade_role(target_metadata):
        return policy_context("facade-ish", "warning", matched, facade_action())
    return policy_context("core-looking", str(rule.get("severity", "warning")), matched, core_action())


def context_tokens(rule: dict[str, Any], key: str, defaults: tuple[str, ...]) -> tuple[str, ...]:
    """Return configurable context classifier tokens."""

    raw = rule.get(key)
    if raw is None:
        raw = rule.get("contextClassifiers", {}).get(key) if isinstance(rule.get("contextClassifiers"), dict) else None
    values = string_list(raw)
    return tuple(values or defaults)


def matched_context_tokens(text: str, tokens: tuple[str, ...]) -> list[str]:
    """Return classifier tokens found in a policy finding context."""

    lowered = text.lower()
    return [token for token in tokens if token.lower() in lowered]


def has_facade_role(metadata: dict[str, Any]) -> bool:
    """Return whether module metadata marks a module as facade-like."""

    roles = metadata.get("roles", [])
    return isinstance(roles, list) and "facade" in roles


def policy_context(
    context: str,
    severity: str,
    tokens: list[str],
    action: str,
) -> dict[str, Any]:
    """Build one direct policy triage context payload."""

    return {
        "policyContext": context,
        "triageSeverity": severity,
        "matchedTokens": tokens,
        "suggestedAction": action,
    }


def core_action() -> str:
    """Return fix guidance for core-looking peer imports."""

    return "consider extracting shared content to a neutral lower layer or removing an obsolete peer import"


def bridge_action() -> str:
    """Return fix guidance for bridge-looking peer imports."""

    return "make the bridge explicit in policy or move bridge glue to a neutral integration layer"


def facade_action() -> str:
    """Return fix guidance for facade-looking peer imports."""

    return "review whether this is public aggregation; allow explicitly or move implementation imports lower"


def direct_import_message(
    rule: dict[str, Any],
    source: str,
    target: str,
    pairs: list[tuple[str, str]],
) -> str:
    """Build a direct import violation message."""

    groups = ", ".join(f"{source_group}->{target_group}" for source_group, target_group in pairs)
    return (
        f"{source} imports {target}; policy rule {rule['id']} forbids this "
        f"group pair ({groups})."
    )


def transitive_import_findings(
    rule: dict[str, Any],
    edges: dict[str, tuple[str, ...]],
    import_sites: dict[tuple[str, str], dict[str, Any]],
    membership: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Return one transitive witness path per violating source module."""

    rows = []
    for source in sorted(edges):
        if ignored_source(rule, source) or not source_groups(rule, source, membership):
            continue
        path = first_forbidden_transitive_path(rule, source, edges, membership)
        if not path or len(path) <= 2:
            continue
        target = path[-1]
        source_group = first_matching_group(source_groups(rule, source, membership))
        target_group = first_matching_group(target_groups(rule, target, membership))
        rows.append(
            finding(
                "architecture_policy.transitive_forbidden_import",
                f"{source} -> {target}",
                str(rule.get("severity", "warning")),
                (
                    f"{source} in group {source_group} reaches {target} in group "
                    f"{target_group} through a forbidden transitive import path."
                ),
                policyRule=str(rule["id"]),
                sourceModule=source,
                targetModule=target,
                sourceGroup=source_group,
                targetGroup=target_group,
                path=path,
                pathImportSites=path_import_sites(path, import_sites),
                pathLength=len(path) - 1,
            )
        )
    return rows[:int(rule.get("maxFindings", DEFAULT_MAX_FINDINGS))]


def shared_dependency_findings(
    rule: dict[str, Any],
    edges: dict[str, tuple[str, ...]],
    membership: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    """Suggest lower-level extraction candidates for shared peer dependencies."""

    incoming: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    mode = shared_dependency_mode(rule)
    for source, targets in edges.items():
        if ignored_source(rule, source):
            continue
        for source_group in source_groups(rule, source, membership):
            for target in targets:
                if ignored_target(rule, target):
                    continue
                if shared_dependency_target_selected(rule, target, membership, mode):
                    incoming[target][source_group].append(source)
    rows = []
    for target, group_sources in sorted(incoming.items()):
        if len(group_sources) < 2:
            continue
        confidence = common_layer_confidence(group_sources)
        rows.append(
            finding(
                "architecture_policy.shared_dependency_candidate",
                target,
                "info",
                (
                    f"{target} is imported by modules from multiple policy groups "
                    f"({', '.join(sorted(group_sources))}); consider moving shared content "
                    "to a lower group if the imports are intentional."
                ),
                policyRule=str(rule["id"]),
                targetModule=target,
                sourceGroups=sorted(group_sources),
                sourceGroupCount=len(group_sources),
                importerCount=shared_dependency_importer_count(group_sources),
                dependencyScope=mode,
                confidence=confidence["label"],
                confidenceScore=confidence["score"],
                confidenceReason=confidence["reason"],
                sampleImporters={
                    group: sorted(importers)[:5]
                    for group, importers in sorted(group_sources.items())
                },
            )
        )
    return rows[:int(rule.get("maxFindings", DEFAULT_MAX_FINDINGS))]


def shared_dependency_mode(rule: dict[str, Any]) -> str:
    """Return the rule's common-dependency search mode."""

    mode = str(
        rule.get("sharedDependencyMode")
        or rule.get("commonDependencyMode")
        or "policy_targets"
    )
    if mode in {"all", "all_imports", "all_multi_group_imports"}:
        return "all_multi_group_imports"
    return "policy_targets"


def shared_dependency_target_selected(
    rule: dict[str, Any],
    target: str,
    membership: dict[str, tuple[str, ...]],
    mode: str,
) -> bool:
    """Return whether a target participates in shared-dependency scanning."""

    if mode == "all_multi_group_imports":
        return True
    return bool(target_groups(rule, target, membership))


def shared_dependency_importer_count(group_sources: dict[str, list[str]]) -> int:
    """Return unique importer count across policy source groups."""

    return len({source for sources in group_sources.values() for source in sources})


def common_layer_confidence(group_sources: dict[str, list[str]]) -> dict[str, Any]:
    """Rank how strongly a shared dependency looks like lower-layer material."""

    source_group_count = len(group_sources)
    importer_count = shared_dependency_importer_count(group_sources)
    score = source_group_count * 10 + min(importer_count, 10)
    if source_group_count >= 3 or importer_count >= 5:
        label = "high"
    elif importer_count >= 3:
        label = "medium"
    else:
        label = "low"
    return {
        "label": label,
        "score": score,
        "reason": (
            f"imported from {source_group_count} policy groups by "
            f"{importer_count} unique modules"
        ),
    }


def first_forbidden_transitive_path(
    rule: dict[str, Any],
    source: str,
    edges: dict[str, tuple[str, ...]],
    membership: dict[str, tuple[str, ...]],
) -> list[str]:
    """Return the first shortest path from source to a forbidden target."""

    max_path_length = int(rule.get("maxPathLength", DEFAULT_MAX_PATH_LENGTH))
    queue: deque[list[str]] = deque([[source]])
    seen = {source}
    while queue:
        path = queue.popleft()
        if len(path) > max_path_length + 1:
            continue
        current = path[-1]
        for target in sorted(edges.get(current, ())):
            if target in seen or ignored_edge(rule, current, target):
                continue
            next_path = [*path, target]
            if forbidden_group_pairs(rule, source, target, membership):
                return next_path
            seen.add(target)
            queue.append(next_path)
    return []


def path_import_sites(
    path: list[str],
    import_sites: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return source evidence for each import edge on a witness path."""

    rows = []
    for source, target in zip(path, path[1:]):
        site = import_sites.get((source, target), {})
        rows.append({
            "sourceModule": source,
            "targetModule": target,
            **{key: value for key, value in site.items() if value not in {"", None}},
        })
    return rows


def forbidden_group_pairs(
    rule: dict[str, Any],
    source: str,
    target: str,
    membership: dict[str, tuple[str, ...]],
) -> list[tuple[str, str]]:
    """Return forbidden source/target group pairs for one edge."""

    pairs = [
        (source_group, target_group)
        for source_group in source_groups(rule, source, membership)
        for target_group in target_groups(rule, target, membership)
        if not bool(rule.get("excludeSameGroup", True)) or source_group != target_group
    ]
    return sorted(set(pairs))


def source_groups(
    rule: dict[str, Any],
    module: str,
    membership: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Return source groups selected by a rule for one module."""

    return selected_groups(rule.get("from", []), membership.get(module, ()))


def target_groups(
    rule: dict[str, Any],
    module: str,
    membership: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    """Return target groups selected by a rule for one module."""

    return selected_groups(rule.get("to", []), membership.get(module, ()))


def selected_groups(raw_selected: Any, module_groups: tuple[str, ...]) -> tuple[str, ...]:
    """Intersect a rule group selector with a module's groups."""

    selected = string_list(raw_selected)
    if "*" in selected:
        return module_groups
    selected_set = set(selected)
    return tuple(group for group in module_groups if group in selected_set)


def ignored_edge(rule: dict[str, Any], source: str, target: str) -> bool:
    """Return whether a rule exclusion suppresses one edge."""

    return ignored_source(rule, source) or ignored_target(rule, target) or any(
        fnmatchcase(source, str(row.get("source", "")))
        and fnmatchcase(target, str(row.get("target", "")))
        for row in dict_list(rule.get("ignoreEdges", []))
    )


def ignored_source(rule: dict[str, Any], module: str) -> bool:
    """Return whether source module exclusions match."""

    return any(fnmatchcase(module, pattern) for pattern in string_list(rule.get("ignoreSource", [])))


def ignored_target(rule: dict[str, Any], module: str) -> bool:
    """Return whether target module exclusions match."""

    return any(fnmatchcase(module, pattern) for pattern in string_list(rule.get("ignoreTarget", [])))


def string_list(value: Any) -> list[str]:
    """Return string values from common policy list shapes."""

    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return []


def dict_list(value: Any) -> list[dict[str, Any]]:
    """Return dict rows from a list-like policy field."""

    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def first_matching_group(groups: tuple[str, ...]) -> str:
    """Return a display group from a non-empty tuple."""

    return groups[0] if groups else ""


def finding(kind: str, subject: str, severity: str, message: str, **extra: Any) -> dict[str, Any]:
    """Build one architecture policy finding row."""

    row: dict[str, Any] = {
        "kind": kind,
        "severity": severity,
        "subject": subject,
        "count": int(extra.pop("pathLength", 1)),
        "message": message,
    }
    row.update({key: value for key, value in extra.items() if present(value)})
    return row


def present(value: Any) -> bool:
    """Return whether optional finding metadata should be retained."""

    return value is not None and value != ""


def dedupe_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate policy findings produced by overlapping rules."""

    rows = []
    seen = set()
    for row in findings:
        signature = finding_signature(row)
        if signature in seen:
            continue
        seen.add(signature)
        rows.append(row)
    return rows


def finding_signature(row: dict[str, Any]) -> tuple[Any, ...]:
    """Return a stable uniqueness key for one finding."""

    kind = row.get("kind")
    if kind == "architecture_policy.direct_forbidden_import":
        return (
            kind,
            row.get("sourceModule"),
            row.get("targetModule"),
        )
    if kind == "architecture_policy.transitive_forbidden_import":
        return (
            kind,
            row.get("sourceModule"),
            row.get("targetModule"),
            row.get("sourceGroup"),
            row.get("targetGroup"),
            tuple(row.get("path", [])),
        )
    if kind == "architecture_policy.shared_dependency_candidate":
        return (kind, row.get("targetModule"), tuple(row.get("sourceGroups", [])))
    return (kind, row.get("subject"))
