"""Optional policy and witness phases for Ladon's analysis pipeline.

This module owns optional filesystem-backed inputs and their phase wrappers.
It depends only on analysis boundaries and a structural context contract, so
the pipeline facade can re-export these helpers without introducing a cycle.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, ContextManager, Iterator, Mapping, Protocol

from ladon.analysis.architecture_policy import (
    skipped_architecture_policy_report,
    summarize_architecture_policy,
)
from ladon.analysis.import_diet import summarize_import_diet
from ladon.analysis.module_readiness import summarize_module_readiness
from ladon.analysis.population_calibration import (
    GeneratedFamilyPolicy,
    parse_generated_family_policy,
)
from ladon.analysis.proof_xray import summarize_proof_xray
from ladon.analysis.source_patterns import SourceDocument, summarize_source_patterns
from ladon.configuration import (
    ARCHITECTURE_POLICY_CANDIDATES,
    GENERATED_FAMILY_POLICY_CANDIDATES,
    SOURCE_PATTERN_POLICY_CANDIDATES,
)
from ladon.ir import LeanModule


__all__ = [
    "ARCHITECTURE_POLICY_CANDIDATES",
    "GENERATED_FAMILY_POLICY_CANDIDATES",
    "SOURCE_PATTERN_POLICY_CANDIDATES",
    "discover_architecture_policy_path",
    "discover_source_pattern_policy_path",
    "load_architecture_policy",
    "load_json_object",
    "load_source_pattern_policy",
    "resolve_architecture_policy",
    "resolve_generated_family_policy",
    "resolve_optional_json",
    "resolve_source_pattern_policy",
    "run_architecture_policy_phase",
    "run_import_diet_phase",
    "run_module_readiness_phase",
    "run_proof_xray_phase",
    "run_source_pattern_phase",
    "source_documents",
]


class _OptionalPhaseContext(Protocol):
    """Structural subset of ``RunContext`` used by optional phases."""

    repo_root: Path
    architecture_policy_path: Path | None
    architecture_policy: dict[str, Any] | None
    source_pattern_policy_path: Path | None
    source_pattern_policy: dict[str, Any] | None
    generated_family_policy_path: Path | None
    generated_family_policy: dict[str, Any] | None
    module_system_witness_path: Path | None
    module_system_witness: dict[str, Any] | None
    import_diet_witness_path: Path | None
    import_diet_witness: dict[str, Any] | None
    proof_xray_path: Path | None
    proof_xray: dict[str, Any] | None
    phase: Callable[[str], ContextManager[dict[str, int]]]
    record_skipped: Callable[[str, str], None]


def run_architecture_policy_phase(
    context: _OptionalPhaseContext,
    dag: dict[str, Any],
) -> dict[str, Any] | None:
    """Run or skip the optional project-supplied architecture policy phase."""

    with context.phase("architecture_policy") as counters:
        policy, source = resolve_architecture_policy(context)
        if policy is None:
            architecture_policy = skipped_architecture_policy_report(
                dag,
                searched_paths=[
                    str(context.repo_root / candidate)
                    for candidate in ARCHITECTURE_POLICY_CANDIDATES
                ],
            )
            counters["findings"] = len(architecture_policy["findings"])
            return architecture_policy
        architecture_policy = summarize_architecture_policy(
            dag,
            policy,
        )
        architecture_policy["source"] = source
        counters["groups"] = int(architecture_policy["groupCount"])
        counters["rules"] = int(architecture_policy["ruleCount"])
        counters["findings"] = len(architecture_policy["findings"])
        return architecture_policy


def run_module_readiness_phase(
    context: _OptionalPhaseContext,
    dag: dict[str, Any],
    declaration_graph: dict[str, Any] | None,
) -> dict[str, Any]:
    """Run Lean module-readiness analysis with optional witness metadata."""

    with context.phase("module_readiness") as counters:
        witness, source = resolve_optional_json(
            inline=context.module_system_witness,
            path=context.module_system_witness_path,
            label="module-system witness",
        )
        report = summarize_module_readiness(dag, declaration_graph, witness)
        if source:
            report["source"] = source
        counters["rows"] = len(report["rows"])
        counters["findings"] = len(report["findings"])
        return report


def run_import_diet_phase(
    context: _OptionalPhaseContext,
    dag: dict[str, Any],
) -> dict[str, Any] | None:
    """Run optional import-diet witness analysis."""

    witness, source = resolve_optional_json(
        inline=context.import_diet_witness,
        path=context.import_diet_witness_path,
        label="import-diet witness",
    )
    if witness is None:
        context.record_skipped("import_diet", "no import-diet witness supplied")
        return None
    with context.phase("import_diet") as counters:
        report = summarize_import_diet(dag, witness)
        report["source"] = source
        counters["rows"] = len(report["rows"])
        counters["findings"] = len(report["findings"])
        return report


def run_proof_xray_phase(
    context: _OptionalPhaseContext,
) -> dict[str, Any] | None:
    """Run optional proof-xray witness analysis."""

    witness, source = resolve_optional_json(
        inline=context.proof_xray,
        path=context.proof_xray_path,
        label="proof-xray witness",
    )
    if witness is None:
        context.record_skipped("proof_xray", "no proof-xray witness supplied")
        return None
    with context.phase("proof_xray") as counters:
        report = summarize_proof_xray(witness)
        report["source"] = source
        counters["rows"] = len(report["rows"])
        counters["findings"] = len(report["findings"])
        return report


def run_source_pattern_phase(
    context: _OptionalPhaseContext,
    modules: Mapping[str, LeanModule],
) -> dict[str, Any] | None:
    """Run or skip optional project-supplied source-pattern scans."""

    policy, source = resolve_source_pattern_policy(context)
    if policy is None:
        context.record_skipped(
            "source_patterns",
            "no source-pattern policy supplied",
        )
        return None
    with context.phase("source_patterns") as counters:
        documents = tuple(source_documents(context.repo_root, modules))
        source_patterns = summarize_source_patterns(documents, policy)
        source_patterns["source"] = source
        counters["patterns"] = int(source_patterns["patternCount"])
        counters["matches"] = int(source_patterns["matchCount"])
        counters["findings"] = len(source_patterns["findings"])
        return source_patterns


def source_documents(
    repo_root: Path,
    modules: Mapping[str, LeanModule],
) -> Iterator[SourceDocument]:
    """Yield source text rows for modules whose files are still available."""

    for module in modules.values():
        path = repo_root / module.path
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        yield SourceDocument(
            module=module.name,
            path=module.path,
            text=text,
            tags=module.tags,
        )


def resolve_source_pattern_policy(
    context: _OptionalPhaseContext,
) -> tuple[dict[str, Any] | None, str]:
    """Return explicit or discovered source-pattern policy data."""

    if context.source_pattern_policy is not None:
        return context.source_pattern_policy, "inline"
    if context.source_pattern_policy_path is not None:
        return (
            load_source_pattern_policy(context.source_pattern_policy_path),
            str(context.source_pattern_policy_path),
        )
    discovered = discover_source_pattern_policy_path(context.repo_root)
    if discovered is None:
        return None, ""
    return load_source_pattern_policy(discovered), str(discovered)


def resolve_generated_family_policy(
    context: _OptionalPhaseContext,
) -> tuple[GeneratedFamilyPolicy | None, str]:
    """Return validated inline, explicit, or repository-local family policy."""

    if context.generated_family_policy is not None:
        return (
            parse_generated_family_policy(context.generated_family_policy),
            "inline",
        )
    selected = context.generated_family_policy_path
    if selected is None:
        selected = next(
            (
                context.repo_root / candidate
                for candidate in GENERATED_FAMILY_POLICY_CANDIDATES
                if (context.repo_root / candidate).is_file()
            ),
            None,
        )
    if selected is None:
        return None, ""
    with selected.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(
            f"generated-family policy {selected} must be a JSON object"
        )
    return parse_generated_family_policy(payload), str(selected)


def discover_source_pattern_policy_path(repo_root: Path) -> Path | None:
    """Return the first repo-local source-pattern policy path if present."""

    for candidate in SOURCE_PATTERN_POLICY_CANDIDATES:
        path = repo_root / candidate
        if path.is_file():
            return path
    return None


def load_source_pattern_policy(
    policy_path: Path | None,
) -> dict[str, Any] | None:
    """Load an optional JSON source-pattern policy from disk."""

    if policy_path is None:
        return None
    with policy_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(
            f"source-pattern policy {policy_path} must be a JSON object"
        )
    return payload


def resolve_optional_json(
    *,
    inline: dict[str, Any] | None,
    path: Path | None,
    label: str,
) -> tuple[dict[str, Any] | None, str]:
    """Return optional inline or path-loaded JSON object."""

    if inline is not None:
        return inline, "inline"
    if path is None:
        return None, ""
    return load_json_object(path, label), str(path)


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    """Load a JSON object from a path with a targeted error message."""

    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{label} {path} must be a JSON object")
    return payload


def resolve_architecture_policy(
    context: _OptionalPhaseContext,
) -> tuple[dict[str, Any] | None, str]:
    """Return explicit or discovered architecture policy data."""

    if context.architecture_policy is not None:
        return context.architecture_policy, "inline"
    if context.architecture_policy_path is not None:
        return (
            load_architecture_policy(context.architecture_policy_path),
            str(context.architecture_policy_path),
        )
    discovered = discover_architecture_policy_path(context.repo_root)
    if discovered is None:
        return None, ""
    return load_architecture_policy(discovered), str(discovered)


def discover_architecture_policy_path(repo_root: Path) -> Path | None:
    """Return the first repo-local architecture policy path if present."""

    for candidate in ARCHITECTURE_POLICY_CANDIDATES:
        path = repo_root / candidate
        if path.is_file():
            return path
    return None


def load_architecture_policy(
    policy_path: Path | None,
) -> dict[str, Any] | None:
    """Load an optional JSON architecture policy from disk."""

    if policy_path is None:
        return None
    with policy_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"architecture policy {policy_path} must be a JSON object")
    return payload
