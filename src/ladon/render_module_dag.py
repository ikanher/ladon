"""Text rendering for module-DAG, scope, population, and audit sections."""

from __future__ import annotations

from typing import Any


def module_dag_detail_lines(dag: dict[str, Any]) -> list[str]:
    """Render grouped module-DAG detail sections."""

    lines: list[str] = []
    lines.extend(module_fan_lines("Top Module Fan-In", dag.get("top_fan_in", []), "fan_in"))
    lines.extend(module_fan_lines("Top Module Fan-Out", dag.get("top_fan_out", []), "fan_out"))
    lines.extend(
        module_fan_lines(
            "Top Target-Owned Importer to Target-Owned Target Fan-In",
            dag.get("top_target_owned_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Facade/Barrel Module Fan-Out",
            dag.get("top_facade_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Implementation Module Fan-Out",
            dag.get("top_implementation_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Handwritten-Importer to Handwritten-Target Fan-In",
            dag.get("top_handwritten_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Generated-Importer Fan-In Contributions",
            dag.get("top_generated_importer_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Generated-Target Fan-In",
            dag.get("top_generated_target_fan_in", []),
            "fan_in",
        )
    )
    lines.extend(
        module_fan_lines(
            "Top Handwritten Module Fan-Out",
            dag.get("top_handwritten_fan_out", []),
            "fan_out",
        )
    )
    lines.extend(large_module_lines(dag.get("top_large_handwritten_modules", [])))
    lines.extend(module_name_smell_lines(dag))
    lines.extend(generated_family_lines(dag.get("generated_family_summary", [])))
    lines.extend(duplicate_import_lines(dag.get("duplicate_imports", [])))
    lines.extend(duplicate_family_lines(dag.get("duplicate_import_family_summary", [])))
    lines.extend(facade_subtype_lines(dag))
    lines.extend(missing_internal_import_lines(dag.get("missing_internal_imports", [])))
    lines.extend(lexical_marker_lines(dag))
    lines.extend(root_import_closure_lines(dag.get("root_direct_import_closures", [])))
    lines.extend(named_module_lines("Facade Modules", dag.get("facade_modules", [])))
    lines.extend(unreachable_module_lines(dag))
    return lines


def scope_lines(dag: dict[str, Any]) -> list[str]:
    """Render explicit primary/context and inventory populations."""

    scope = dag.get("analysis_scope")
    if not isinstance(scope, dict):
        return []
    primary = scope.get("primaryPopulation", {})
    context = scope.get("contextPopulation", {})
    inventory = scope.get("inventoryBoundary", {})
    return [
        "Analysis Scope",
        (
            f"- requested/effective: {scope.get('requestedScope', '')}/"
            f"{scope.get('effectiveScope', '')}"
        ),
        f"- resolved roots: {', '.join(scope.get('resolvedRoots', []))}",
        (
            f"- primary: {primary.get('selectedCount', 0)} selected, "
            f"{primary.get('omittedCount', 0)} omitted"
        ),
        (
            f"- context: {context.get('selectedCount', 0)} selected, "
            f"{context.get('omittedCount', 0)} omitted"
        ),
        f"- inventory: {inventory.get('moduleCount', 0)} modules",
        f"- fingerprint: {scope.get('fingerprint', '')}",
        "",
    ]


def population_lines(dag: dict[str, Any]) -> list[str]:
    """Render raw and calibrated ownership/generation populations."""

    calibration = dag.get("population_calibration")
    if not isinstance(calibration, dict):
        return []
    summary = calibration.get("summary", {})
    counts = summary.get("populationCounts", {})
    lines = [
        "Population Calibration",
        (
            f"- selected: {summary.get('selectedPopulation', '')} "
            f"{summary.get('numerator', 0)}/{summary.get('denominator', 0)}"
        ),
    ]
    lines.extend(
        f"- {name}: {count}" for name, count in sorted(counts.items())
    )
    families = calibration.get("generatedFamilies", [])
    lines.append(f"- generated families: {len(families)}")
    return [*lines, ""]


def audit_surface_lines(dag: dict[str, Any]) -> list[str]:
    """Render bounded audit/resource navigation with honest totals."""

    summary = dag.get("audit_summary")
    if not _has_audit_summary(summary):
        return []
    commands = _audit_rows(dag, "auditCommands")
    directives = _audit_rows(dag, "resourceDirectives")
    visible_commands = commands[:10]
    visible_directives = directives[:10]
    lines = _audit_summary_lines(
        summary,
        commands,
        visible_commands,
        directives,
        visible_directives,
    )
    lines.extend(_audit_command_line(row) for row in visible_commands)
    lines.extend(_resource_directive_line(row) for row in visible_directives)
    return [*lines, ""]


def _audit_summary_lines(
    summary: dict[str, Any],
    commands: list[dict[str, Any]],
    visible_commands: list[dict[str, Any]],
    directives: list[dict[str, Any]],
    visible_directives: list[dict[str, Any]],
) -> list[str]:
    """Render audit totals separately from bounded row details."""

    return [
        "Lean Audit Surfaces",
        _audit_count_line("commands", commands, visible_commands),
        _audit_count_line(
            "resource directives",
            directives,
            visible_directives,
        ),
        f"- command-only modules: {summary.get('commandOnlyModules', 0)}",
    ]


def _audit_count_line(
    label: str,
    rows: list[dict[str, Any]],
    visible: list[dict[str, Any]],
) -> str:
    """Render one total and omitted audit-row count."""

    return f"- {label}: {len(rows)} total, {len(rows) - len(visible)} omitted"


def _has_audit_summary(summary: Any) -> bool:
    """Return whether an audit summary names at least one supported row."""

    return isinstance(summary, dict) and bool(
        summary.get("auditCommands") or summary.get("resourceDirectives")
    )


def _audit_rows(dag: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """Flatten one typed audit collection across module surfaces."""

    return [
        row
        for surface in dag.get("audit_surfaces", [])
        if isinstance(surface, dict)
        for row in surface.get(key, [])
        if isinstance(row, dict)
    ]


def _audit_command_line(row: dict[str, Any]) -> str:
    """Render one bounded lexical audit command."""

    return (
        f"- {row.get('id', '')} {row.get('module', '')} "
        f"{row.get('kind', '')}: {row.get('subject', '')} "
        f"status={row.get('resultStatus', '')} "
        f"authority={row.get('authority', '')}"
    )


def _resource_directive_line(row: dict[str, Any]) -> str:
    """Render one bounded lexical resource directive."""

    return (
        f"- {row.get('id', '')} {row.get('module', '')} "
        f"{row.get('option', '')}={row.get('rawValue', '')} "
        f"scope={row.get('lexicalScope', '')} "
        f"authority={row.get('authority', '')}"
    )


def large_module_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render largest non-generated source files."""

    visible = [row for row in rows if row.get("lineCount", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Largest Handwritten Modules"]
    lines.extend(f"- {row['module']}: {row['lineCount']} lines" for row in visible)
    return [*lines, ""]


def module_name_smell_lines(dag: dict[str, Any]) -> list[str]:
    """Render module-name pressure summaries and samples."""

    summary = dag.get("module_name_smell_summary", {})
    rows = dag.get("module_name_smells", [])
    if not summary and not rows:
        return []
    lines = ["Module Naming Smells"]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(module_name_smell_line(row) for row in rows[:5])
    return [*lines, ""]


def module_name_smell_line(row: dict[str, Any]) -> str:
    """Render one module naming-smell row."""

    reasons = ",".join(row.get("reasonKinds", [])[:4])
    action = row.get("suggestedAction", "review module naming")
    return (
        f"- {row['module']}: generated={row.get('generated', False)} "
        f"reasons={reasons}; {action}"
    )


def generated_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render generated families even when no duplicate imports exist."""

    if not rows:
        return []
    lines = ["Generated Families"]
    lines.extend(generated_family_line(row) for row in rows[:5])
    return [*lines, ""]


def generated_family_line(row: dict[str, Any]) -> str:
    """Render one generated-family summary row."""

    reasons = row.get("reasonSummary", {})
    reason_text = ",".join(
        f"{kind}={count}"
        for kind, count in sorted(reasons.items())[:4]
    )
    suffix = f" reasons={reason_text}" if reason_text else ""
    return (
        f"- {row.get('generatorFamily') or '(generated)'}: "
        f"{row['moduleCount']} modules maxDepth={row.get('maxPathDepth', 0)}{suffix}"
    )


def duplicate_import_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render duplicate import targets with compact line evidence."""

    if not rows:
        return []
    lines = ["Duplicate Imports"]
    lines.extend(duplicate_import_line(row) for row in rows[:5])
    return [*lines, ""]


def duplicate_import_line(row: dict[str, Any]) -> str:
    """Render one duplicate import row."""

    lines = row.get("lines", [])
    line_suffix = f" lines={','.join(str(line) for line in lines[:5])}" if lines else ""
    action = row.get("suggestedAction", "deduplicate the import target")
    return f"- {row['module']} -> {row['target']}: {row['count']}{line_suffix}; {action}"


def duplicate_family_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render duplicate imports grouped by generated family and target."""

    if not rows:
        return []
    lines = ["Duplicate Import Families"]
    lines.extend(
        (
            f"- {row.get('generatorFamily') or '(handwritten)'} -> {row['target']}: "
            f"{row['duplicateModuleCount']} modules generated={row.get('generated', False)}"
        )
        for row in rows[:5]
    )
    return [*lines, ""]


def facade_subtype_lines(dag: dict[str, Any]) -> list[str]:
    """Render facade subtype counts and top facade-like modules."""

    summary = dag.get("facade_subtype_summary", {})
    rows = dag.get("top_facade_like_modules", [])
    if not summary and not rows:
        return []
    lines = ["Facade Subtypes"]
    lines.extend(f"- {name}: {count}" for name, count in sorted(summary.items()))
    lines.extend(
        f"- {row['module']}: {row['subtype']} imports={row['fan_out']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def missing_internal_import_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render missing internal import targets."""

    if not rows:
        return []
    lines = ["Missing Internal Import Targets"]
    lines.extend(
        f"- {row['sourcePath']}:{row.get('line', '')} imports {row['targetModule']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def lexical_marker_lines(dag: dict[str, Any]) -> list[str]:
    """Render lexical marker summary and samples."""

    summary = dag.get("lexical_marker_summary", {})
    rows = dag.get("lexical_markers", [])
    lines = ["Lexical Markers"]
    if not summary:
        return [*lines, "- none", ""]
    lines.extend(f"- {kind}: {count}" for kind, count in sorted(summary.items()))
    lines.extend(
        f"- {row['path']}:{row['line']} {row['kind']}"
        for row in rows[:5]
    )
    return [*lines, ""]


def module_fan_lines(
    title: str,
    rows: list[dict[str, Any]],
    metric: str,
) -> list[str]:
    """Render module graph fan-in or fan-out rows."""

    visible = [row for row in rows if row.get(metric, 0) > 0][:5]
    if not visible:
        return []
    lines = [title]
    lines.extend(
        (
            f"- {row['module']}: {row[metric]}"
            f"{fan_population_suffix(row)}"
        )
        for row in visible
    )
    return [*lines, ""]


def fan_population_suffix(row: dict[str, Any]) -> str:
    """Render the exact raw-metric population and authority when supplied."""

    population = str(row.get("population", ""))
    authority = str(row.get("authority", ""))
    if not population and not authority:
        return ""
    return f" population={population or 'unspecified'} authority={authority or 'unspecified'}"


def named_module_lines(title: str, modules: list[str]) -> list[str]:
    """Render a named module list section."""

    if not modules:
        return []
    return [title, *[f"- {module}" for module in modules[:5]], ""]


def root_import_closure_lines(rows: list[dict[str, Any]]) -> list[str]:
    """Render direct root-import closure sizes."""

    visible = [row for row in rows if row.get("reachable_module_count", 0) > 0][:5]
    if not visible:
        return []
    lines = ["Root Direct Import Closures"]
    lines.extend(
        f"- {row['root']} -> {row['direct_import']}: {row['reachable_module_count']}"
        for row in visible
    )
    return [*lines, ""]


def unreachable_module_lines(dag: dict[str, Any]) -> list[str]:
    """Render modules outside chosen-root reachability, if any."""

    count = int(dag.get("source_modules_not_reachable_from_chosen_roots_count", 0))
    modules = dag.get("source_modules_not_reachable_from_chosen_roots", [])
    if count == 0:
        return []
    return [
        "Modules Not Reachable From Chosen Roots",
        f"- count: {count}",
        *[f"- {module}" for module in modules[:5]],
        "",
    ]
