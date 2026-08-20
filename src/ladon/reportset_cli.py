"""Installed ordinary CLI handlers for Ladon's existing report-set engines."""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ladon.atlas import (
    atlas_reviewer_cards,
    build_report_atlas,
    render_atlas_markdown,
    render_reviewer_cards_markdown,
)
from ladon.atlas_diff import diff_atlases, load_atlas, render_atlas_diff_markdown
from ladon.atlas_sqlite import (
    CANNED_QUERIES,
    run_coverage_aware_query,
    write_atlas_sqlite,
)
from ladon.atlas_workflow import (
    build_atlas_workflow,
    render_atlas_workflow_markdown,
)
from ladon.cli_execution import EXIT_INVOCATION, EXIT_OPERATIONAL, EXIT_SUCCESS
from ladon.configuration import (
    ConfigurationError,
    policy_fingerprint_options,
    resolve_policy_configuration,
)
from ladon.finding_workflow import (
    inspect_findings,
    load_finding_report,
    parse_finding_filter,
)
from ladon.inspection_adapters import load_inspection_dataset
from ladon.inspection_models import (
    INSPECTION_NOUNS,
    InspectionCompatibilityError,
    InspectionInvocationError,
    InspectionNotFoundError,
)
from ladon.inspection_query import (
    DEFAULT_INSPECTION_LIMIT,
    FILTERS_BY_NOUN,
    inspect_dataset,
    parse_inspection_filter,
    positive_inspection_limit,
)
from ladon.inspection_render import render_inspection_text
from ladon.lean_runtime import DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS
from ladon.progress import RunLimits
from ladon.runset_bundle_reader import bundle_report_set
from ladon.scope import SUPPORTED_SCOPE_KINDS, ScopePlanningError
from ladon.scope_runtime import resolve_analysis_scope

REPORTSET_COMMANDS = frozenset(
    {
        "atlas",
        "query",
        "diff",
        "cards",
        "workflow",
        "findings",
        "inspect",
        "preview",
    }
)


def reportset_main(argv: Sequence[str]) -> int:
    """Run one installed report-set operation with shared stream discipline."""

    parser = build_reportset_parser()
    args = parser.parse_args(list(argv))
    try:
        payload, text = execute_reportset(args)
        write_selected_output(args, payload, text)
        return EXIT_SUCCESS
    except (
        ConfigurationError,
        InspectionInvocationError,
        ScopePlanningError,
    ) as exc:
        print(f"ladon: invalid invocation: {exc}", file=sys.stderr)
        return EXIT_INVOCATION
    except (InspectionCompatibilityError, InspectionNotFoundError) as exc:
        print(f"ladon: inspection failed [{exc.code}]: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL
    except Exception as exc:  # noqa: BLE001 - CLI boundary renders unexpected failures
        print(f"ladon: report-set operation failed: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL


def build_reportset_parser() -> argparse.ArgumentParser:
    """Build the installed report-set subcommand parser."""

    parser = argparse.ArgumentParser(
        prog="ladon",
        description="Ladon installed report-set operations",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_atlas_parser(subparsers)
    add_query_parser(subparsers)
    add_diff_parser(subparsers)
    add_cards_parser(subparsers)
    add_workflow_parser(subparsers)
    add_findings_parser(subparsers)
    add_inspect_parser(subparsers)
    add_preview_parser(subparsers)
    return parser


def add_common_output(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--output", default="-", help="Output path, or - for stdout.")


def add_atlas_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("atlas", help="Build an atlas from reports.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--reports-root")
    source.add_argument(
        "--bundle",
        help="Validated ladon-analysis-bundle-v1 manifest.",
    )
    parser.add_argument("--output-sqlite")
    parser.add_argument("--output-cards")
    add_common_output(parser)


def add_query_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("query", help="Run a canned atlas query.")
    parser.add_argument("--db", required=True)
    parser.add_argument("--query", required=True, choices=sorted(CANNED_QUERIES))
    parser.add_argument(
        "--exhaustive",
        action="store_true",
        help=(
            "Require complete authority for every source collection needed "
            "by this query; otherwise return an unavailable diagnostic."
        ),
    )
    add_common_output(parser)


def add_diff_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("diff", help="Diff two explicit atlas files.")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    add_common_output(parser)


def add_cards_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("cards", help="Render reviewer cards.")
    parser.add_argument("--atlas", required=True)
    add_common_output(parser)


def add_workflow_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("workflow", help="Build workflow summaries.")
    parser.add_argument("--atlas", required=True)
    parser.add_argument("--before")
    add_common_output(parser)


def add_findings_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "findings",
        help="Inspect findings from one existing report without rerunning analysis.",
    )
    parser.add_argument("--report", required=True)
    parser.add_argument("--id", dest="finding_id")
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        type=finding_filter_argument,
        metavar="FIELD=VALUE",
    )
    add_common_output(parser)


def add_inspect_parser(subparsers: Any) -> None:
    """Register caller-neutral, artifact-only inspection."""

    filters = "\n".join(
        f"  {noun}: {', '.join(sorted(fields))}"
        for noun, fields in FILTERS_BY_NOUN.items()
    )
    parser = subparsers.add_parser(
        "inspect",
        help="Inspect canonical rows from one existing report or source index.",
        description=(
            "Inspect canonical analysis rows without rerunning discovery, "
            "Lake, Lean, VCS, an initializer, or a build."
        ),
        epilog=(
            "Repeatable filters by noun:\n"
            f"{filters}\n\n"
            "Cursors are opaque and bind the artifact fingerprint, normalized "
            "query, page size, and last stable ordering key. Lexical evidence "
            "does not imply elaboration, proof success, or theorem quality."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("noun", choices=INSPECTION_NOUNS)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--report", help="Canonical Ladon report JSON.")
    source.add_argument(
        "--source-index",
        help="Compatible canonical Ladon source-index JSON.",
    )
    parser.add_argument(
        "--filter",
        action="append",
        default=[],
        type=inspection_filter_argument,
        metavar="FIELD=VALUE",
        help="Finite noun-specific exact filter; repeat to combine predicates.",
    )
    parser.add_argument("--id", dest="inspection_id", help="Exact stable row ID.")
    parser.add_argument("--cursor", help="Opaque next-page cursor.")
    parser.add_argument(
        "--limit",
        type=inspection_limit_argument,
        default=DEFAULT_INSPECTION_LIMIT,
        help="Rows per page (1-500; cursor-bound).",
    )
    parser.add_argument(
        "--repo-root",
        help=(
            "Explicitly bind source-index inspection to current repository "
            "source/configuration fingerprints."
        ),
    )
    add_common_output(parser)


def add_preview_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser(
        "preview",
        help="Resolve an analysis scope without running analysis, Lake, or Lean.",
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--root", action="append", default=[])
    parser.add_argument(
        "--scope",
        choices=sorted(SUPPORTED_SCOPE_KINDS),
        default="owner",
    )
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--changed-manifest")
    parser.add_argument("--max-modules", type=positive_integer_argument)
    parser.add_argument("--max-context-modules", type=positive_integer_argument)
    parser.add_argument("--lean-batch-size", type=positive_integer_argument, default=8)
    parser.add_argument(
        "--lean-timeout",
        type=positive_number_argument,
        default=DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
    )
    parser.add_argument("--extraction-backend", choices=["text", "lean"], default="text")
    parser.add_argument("--architecture-policy")
    parser.add_argument("--source-pattern-policy")
    parser.add_argument("--generated-family-policy")
    parser.add_argument("--overall-timeout", type=positive_number_argument)
    parser.add_argument("--max-rss-mib", type=positive_integer_argument)
    parser.add_argument("--max-report-bytes", type=positive_integer_argument)
    parser.add_argument("--cache-dir")
    parser.add_argument("--no-cache", action="store_true")
    add_common_output(parser)


def positive_integer_argument(value: str) -> int:
    """Parse a positive integer without importing the analysis CLI."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def positive_number_argument(value: str) -> float:
    """Parse one finite positive preview deadline."""

    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return parsed


def finding_filter_argument(value: str) -> tuple[str, str]:
    """Expose finding-filter validation as an argparse invocation error."""

    try:
        return parse_finding_filter(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def inspection_filter_argument(value: str) -> tuple[str, str]:
    """Expose finite inspection-filter syntax as an argparse error."""

    try:
        return parse_inspection_filter(value)
    except InspectionInvocationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def inspection_limit_argument(value: str) -> int:
    """Expose the bounded inspection page size as an argparse error."""

    try:
        return positive_inspection_limit(value)
    except InspectionInvocationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def execute_reportset(args: argparse.Namespace) -> tuple[Any, str]:
    """Delegate a parsed operation to the existing owning library."""

    if args.command == "atlas":
        return execute_atlas(args)
    if args.command == "query":
        payload = run_coverage_aware_query(
            Path(args.db),
            args.query,
            exhaustive=args.exhaustive,
        )
        return payload, render_query_result_text(payload)
    if args.command == "diff":
        payload = diff_atlases(
            load_atlas(Path(args.before)),
            load_atlas(Path(args.after)),
        )
        return payload, render_atlas_diff_markdown(payload)
    if args.command == "cards":
        atlas = load_atlas(Path(args.atlas))
        return (
            atlas_reviewer_cards(atlas),
            render_reviewer_cards_markdown(atlas),
        )
    if args.command == "findings":
        return execute_findings(args)
    if args.command == "inspect":
        return execute_inspect(args)
    if args.command == "preview":
        return execute_preview(args)
    return execute_workflow(args)


def execute_atlas(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Build an atlas and any explicitly requested derived artifacts."""

    atlas = selected_report_atlas(args)
    if args.output_sqlite:
        write_atlas_sqlite(atlas, Path(args.output_sqlite))
    if args.output_cards:
        atomic_write_text(
            Path(args.output_cards),
            render_reviewer_cards_markdown(atlas),
        )
    return atlas, render_atlas_markdown(atlas)


def selected_report_atlas(args: argparse.Namespace) -> dict[str, Any]:
    """Build from a directory or from exact reports plus bundle state."""

    if not args.bundle:
        return build_report_atlas(Path(args.reports_root))
    with bundle_report_set(Path(args.bundle)) as report_set:
        return build_report_atlas(
            report_set.root,
            workflow_diagnostics=report_set.workflow_diagnostics,
        )


def execute_workflow(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Build the existing combined atlas workflow projection."""

    atlas = load_atlas(Path(args.atlas))
    before = load_atlas(Path(args.before)) if args.before else None
    workflow = build_atlas_workflow(
        atlas,
        before_atlas=before,
    )
    return workflow, render_atlas_workflow_markdown(workflow)


def execute_findings(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Inspect one existing canonical finding set with exact selection."""

    payload = inspect_findings(
        load_finding_report(Path(args.report)),
        identifier=args.finding_id,
        filters=args.filter,
    )
    return payload, render_findings_text(payload)


def execute_inspect(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Inspect one immutable artifact through the shared page model."""

    artifact_path = Path(args.report or args.source_index)
    artifact_kind = "report" if args.report else "source-index"
    dataset = load_inspection_dataset(
        artifact_path,
        args.noun,
        artifact_kind=artifact_kind,
        repo_root=Path(args.repo_root) if args.repo_root else None,
    )
    page = inspect_dataset(
        dataset,
        filters=args.filter,
        identifier=args.inspection_id,
        cursor=args.cursor,
        limit=args.limit,
    )
    return page.to_dict(), render_inspection_text(page)


def execute_preview(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Resolve one source index and scope without starting target processes."""

    repo_root = Path(args.repo_root)
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    policies = resolve_policy_configuration(
        repo_root,
        architecture_policy=optional_path(args.architecture_policy),
        source_pattern_policy=optional_path(args.source_pattern_policy),
        generated_family_policy=optional_path(args.generated_family_policy),
    )
    resolved = resolve_analysis_scope(
        repo_root,
        scope_kind=args.scope,
        roots=args.root,
        changed_paths=args.changed_path,
        changed_manifest=args.changed_manifest,
        max_modules=args.max_modules,
        max_context_modules=args.max_context_modules,
        lean_batch_size=args.lean_batch_size,
        cache_dir=cache_dir,
        use_cache=not args.no_cache,
        index_options=policy_fingerprint_options(policies),
    )
    payload = resolved.preview_payload(
        cache_dir=cache_dir,
        extraction_backend=args.extraction_backend,
        policies=policies,
        resources=preview_resources(args),
    )
    return payload, render_preview_text(payload)


def render_findings_text(payload: dict[str, Any]) -> str:
    """Render deterministic owner-oriented finding rows."""

    rows = payload["findings"]
    if not rows:
        return "No matching findings.\n"
    lines = [
        f"Findings: {payload['selected']} selected, {payload['omitted']} omitted"
    ]
    for row in rows:
        lines.append(
            " | ".join(
                (
                    str(row.get("id", "")),
                    str(row.get("severity", "")),
                    str(row.get("kind", "")),
                    str(row.get("subject", "")),
                )
            )
        )
        for reference in row.get("evidenceRefs", []):
            if not isinstance(reference, dict):
                continue
            location = reference.get("path") or reference.get("section")
            if location:
                lines.append(f"  evidence: {location}")
        command = row.get("nextCommand")
        if isinstance(command, dict):
            arguments = command.get("arguments", [])
            if isinstance(arguments, list):
                lines.append(
                    "  next: "
                    + " ".join(
                        [str(command.get("program", "ladon"))]
                        + [str(value) for value in arguments]
                    )
                )
    return "\n".join(lines) + "\n"


def render_preview_text(payload: dict[str, Any]) -> str:
    """Render a bounded human preview with populations and cache expectations."""

    index = payload["sourceIndex"]
    scope = payload["scope"]
    primary = scope["primaryPopulation"]
    context = scope["contextPopulation"]
    helper = scope["leanHelperPlan"]
    cache = index["cache"]
    policies = payload["policies"]
    resources = payload["resources"]
    lines = [
        "Ladon analysis preview",
        f"Scope: {scope['requestedScope']} -> {scope['effectiveScope']}",
        "Resolved roots: " + ", ".join(scope["resolvedRoots"]),
        (
            f"Primary modules: {primary['selectedCount']} selected, "
            f"{primary['omittedCount']} omitted"
        ),
        (
            f"Context modules: {context['selectedCount']} selected, "
            f"{context['omittedCount']} omitted"
        ),
        f"Inventory modules: {index['inventoryModules']}",
        (
            f"Lean helper batches: {helper['expectedBatches']} "
            f"(batch size {helper['batchSize']})"
        ),
        f"Source-index cache: {cache['status']} ({cache['reason']})",
        f"Scope fingerprint: {scope['fingerprint']}",
        "Policies: "
        + ", ".join(
            f"{name}={row['status']}"
            for name, row in sorted(policies.items())
        ),
        (
            "Limits: "
            f"wall={resources['requested']['wallSeconds']}, "
            f"rssBytes={resources['requested']['rssBytes']}, "
            f"reportBytes={resources['requested']['reportBytes']}, "
            f"leanTimeout={resources['leanHelperTimeoutSeconds']}"
        ),
        "Execution: no Lake, Lean, version-control, or analysis process started",
    ]
    return "\n".join(lines) + "\n"


def preview_resources(args: argparse.Namespace) -> dict[str, Any]:
    """Return requested limits and explicit preview-only observations."""

    limits = RunLimits(
        wall_seconds=args.overall_timeout,
        rss_bytes=(
            args.max_rss_mib * 1024 * 1024
            if args.max_rss_mib is not None
            else None
        ),
        report_bytes=args.max_report_bytes,
    )
    return {
        "requested": limits.to_dict(),
        "leanHelperTimeoutSeconds": args.lean_timeout,
        "observed": None,
        "crossed": None,
        "previewOnly": True,
    }


def optional_path(value: str | None) -> Path | None:
    """Convert an optional policy argument at the preview boundary."""

    return Path(value) if value else None


def write_selected_output(
    args: argparse.Namespace,
    payload: Any,
    text: str,
) -> None:
    """Write exactly one selected representation to stdout or one file."""

    content = (
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.format == "json"
        else text
    )
    if args.output == "-":
        sys.stdout.write(content)
    else:
        atomic_write_text(Path(args.output), content)


def atomic_write_text(path: Path, content: str) -> None:
    """Atomically publish one UTF-8 derived artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def load_json_files(paths: Sequence[str]) -> list[dict[str, Any]]:
    """Load explicit bridge artifacts without source-checkout assumptions."""

    return [load_json(Path(path)) for path in paths]


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object or fail with its input path."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return payload


def tabular_text(rows: list[dict[str, Any]]) -> str:
    """Return deterministic bounded text for canned query rows."""

    if not rows:
        return "No query rows.\n"
    keys = sorted({key for row in rows for key in row})
    lines = ["\t".join(keys)]
    lines.extend(
        "\t".join(str(row.get(key, "")) for key in keys)
        for row in rows
    )
    return "\n".join(lines) + "\n"


def render_query_result_text(payload: dict[str, Any]) -> str:
    """Render query status before bounded rows so absence is never ambiguous."""

    lines = [
        f"Query: {payload.get('query', '')}",
        f"Status: {payload.get('status', '')}",
        f"Exhaustive: {str(payload.get('exhaustive') is True).lower()}",
    ]
    nonclaim = payload.get("nonclaim")
    if nonclaim:
        lines.append(f"Nonclaim: {nonclaim}")
    rows = payload.get("rows")
    table = tabular_text(rows if isinstance(rows, list) else [])
    return "\n".join(lines) + "\n\n" + table
