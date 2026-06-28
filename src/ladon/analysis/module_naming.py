"""Module-name inventory signals for generated and overly dense Lean names."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

from ladon.ir import LeanModule


MAX_GENERATED_FAMILY_ROWS = 20
LONG_MODULE_NAME_THRESHOLD = 90
LONG_SEGMENT_THRESHOLD = 40
CAMEL_TOKEN_THRESHOLD = 8
GENERATED_PATH_DEPTH_THRESHOLD = 5
CAMEL_TOKEN_RE = re.compile(r"[0-9]+p[0-9]+|[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|[0-9]+")
ENCODED_NUMBER_RE = re.compile(r"\d+p\d|[A-Za-z]+[0-9][A-Za-z0-9]*")
ENCODED_DECIMAL_RE = re.compile(r"\d+p\d")
ENUMERATED_GENERATED_SEGMENT_RE = re.compile(r"(?:^|[A-Z])(?:Case|Row|Chunk|Part|Step|F)\d+")
GENERATED_LIFECYCLE_RE = re.compile(
    r"(?:Smoke|Candidate|Prototype|Draft|Temp|Temporary|Experimental|Production)",
    re.IGNORECASE,
)


def module_name_smell_rows(modules: Mapping[str, LeanModule]) -> list[dict[str, Any]]:
    """Return generic module-name triage rows for generated and long names."""

    rows = [
        module_name_smell_row(module, reasons)
        for module in sorted(modules.values(), key=lambda item: item.name)
        for reasons in [module_name_smell_reasons(module)]
        if reasons
    ]
    return sorted(rows, key=lambda row: (-module_name_smell_score(row), row["module"]))


def module_name_smell_row(module: LeanModule, reasons: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Build one module-name smell row."""

    segments = module.name.split(".")
    return {
        "module": module.name,
        "path": module.path,
        "generated": "generated" in module.tags,
        "tags": list(module.tags),
        "moduleLength": len(module.name),
        "pathDepth": len(segments),
        "maxSegmentLength": max((len(segment) for segment in segments), default=0),
        "problematicSegments": sorted({str(reason.get("segment", "")) for reason in reasons if reason.get("segment")}),
        "reasonKinds": sorted({str(reason["kind"]) for reason in reasons}),
        "reasons": list(reasons),
        "suggestedAction": module_name_smell_action(module, reasons),
    }


def module_name_smell_reasons(module: LeanModule) -> list[dict[str, Any]]:
    """Return generic reasons why a module name deserves review attention."""

    generated = "generated" in module.tags
    segments = module.name.split(".")
    reasons: list[dict[str, Any]] = []
    if len(module.name) >= LONG_MODULE_NAME_THRESHOLD:
        reasons.append({
            "kind": "long_module_name",
            "value": len(module.name),
            "threshold": LONG_MODULE_NAME_THRESHOLD,
        })
    if generated and len(segments) >= GENERATED_PATH_DEPTH_THRESHOLD:
        reasons.append({
            "kind": "deep_generated_path",
            "value": len(segments),
            "threshold": GENERATED_PATH_DEPTH_THRESHOLD,
        })
    for segment in segments:
        reasons.extend(segment_name_smell_reasons(segment, generated))
    return reasons


def segment_name_smell_reasons(segment: str, generated: bool) -> list[dict[str, Any]]:
    """Return review reasons for one module path segment."""

    reasons: list[dict[str, Any]] = []
    if len(segment) >= LONG_SEGMENT_THRESHOLD:
        reasons.append({
            "kind": "long_segment",
            "segment": segment,
            "value": len(segment),
            "threshold": LONG_SEGMENT_THRESHOLD,
        })
    token_count = len(camel_tokens(segment))
    if token_count >= CAMEL_TOKEN_THRESHOLD:
        reasons.append({
            "kind": "dense_camel_segment",
            "segment": segment,
            "value": token_count,
            "threshold": CAMEL_TOKEN_THRESHOLD,
        })
    if not generated:
        return reasons
    if encoded_parameter_segment(segment):
        reasons.append({"kind": "generated_encoded_parameters", "segment": segment})
    if ENUMERATED_GENERATED_SEGMENT_RE.search(segment):
        reasons.append({"kind": "generated_enumerated_case_segment", "segment": segment})
    if GENERATED_LIFECYCLE_RE.search(segment):
        reasons.append({"kind": "generated_lifecycle_label", "segment": segment})
    return reasons


def camel_tokens(segment: str) -> list[str]:
    """Split a CamelCase-ish segment into rough review tokens."""

    return CAMEL_TOKEN_RE.findall(segment)


def encoded_parameter_segment(segment: str) -> bool:
    """Return whether a segment appears to encode parameter values."""

    matches = ENCODED_NUMBER_RE.findall(segment)
    return bool(ENCODED_DECIMAL_RE.search(segment)) or len(matches) >= 2


def module_name_smell_score(row: dict[str, Any]) -> int:
    """Sort the most actionable naming rows first."""

    reason_bonus = 10 * len(row.get("reasonKinds", []))
    generated_bonus = 5 if row.get("generated") else 0
    return (
        reason_bonus
        + generated_bonus
        + int(row.get("moduleLength", 0))
        + int(row.get("pathDepth", 0))
        + int(row.get("maxSegmentLength", 0))
    )


def module_name_smell_action(
    module: LeanModule,
    reasons: Sequence[dict[str, Any]],
) -> str:
    """Return generic fix guidance for naming-pressure rows."""

    generated = "generated" in module.tags
    reason_kinds = {str(reason["kind"]) for reason in reasons}
    if generated and (
        "generated_encoded_parameters" in reason_kinds
        or "generated_enumerated_case_segment" in reason_kinds
        or "generated_lifecycle_label" in reason_kinds
    ):
        return (
            "move generated parameters/cases/status into a manifest or generator output boundary; "
            "keep source module names stable and reviewable"
        )
    if generated:
        return "keep generated modules under an explicit generated-artifact boundary and avoid hand edits"
    return "split long semantic module names or move proof-case detail into lower-level declarations/data"


def module_name_smell_summary(rows: Sequence[dict[str, Any]]) -> dict[str, int]:
    """Count module-name smell reasons by kind."""

    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        for kind in row.get("reasonKinds", []):
            counts[str(kind)] += 1
    return dict(sorted(counts.items()))


def generated_family_summary(modules: Mapping[str, LeanModule]) -> list[dict[str, Any]]:
    """Summarize generated families independently from duplicate imports."""

    grouped: dict[str, list[LeanModule]] = defaultdict(list)
    for module in modules.values():
        if "generated" not in module.tags:
            continue
        grouped[generator_family(module) or "(generated)"].append(module)
    return [
        generated_family_row(family, items)
        for family, items in sorted(
            grouped.items(),
            key=lambda item: (-len(item[1]), item[0]),
        )[:MAX_GENERATED_FAMILY_ROWS]
    ]


def generated_family_row(family: str, modules: Sequence[LeanModule]) -> dict[str, Any]:
    """Build one generated-family inventory row."""

    reason_counts: dict[str, int] = defaultdict(int)
    for module in modules:
        for reason in module_name_smell_reasons(module):
            reason_counts[str(reason["kind"])] += 1
    return {
        "generatorFamily": family,
        "moduleCount": len(modules),
        "maxModuleLength": max((len(module.name) for module in modules), default=0),
        "maxPathDepth": max((len(module.name.split(".")) for module in modules), default=0),
        "reasonSummary": dict(sorted(reason_counts.items())),
        "sampleModules": [module.name for module in sorted(modules, key=lambda item: item.name)[:5]],
        "suggestedAction": "review the generator output boundary, naming manifest, and whether generated files should be edited directly",
    }


def generator_family(module: LeanModule) -> str:
    """Return a generic generated-family label."""

    generated_segment = first_generated_segment(module.name.split("."))
    if generated_segment:
        return generated_segment
    if "generated" in module.tags:
        return module.name.rsplit(".", 1)[-1]
    return ""


def first_generated_segment(segments: Sequence[str]) -> str:
    """Return the first path/module segment naming generated output."""

    for segment in segments:
        lower = segment.lower()
        if lower in {"generated", "autogenerated"} or lower.startswith(("generated", "autogenerated")):
            return segment
    return ""
