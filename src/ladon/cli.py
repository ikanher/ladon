"""Command-line orchestration for Ladon's clean core.

The CLI owns user-facing compatibility flags and filesystem orchestration. It
delegates analysis to pure modules so quality gates can keep the core small.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable, Sequence

from ladon.cli_execution import (
    EXIT_INVOCATION,
    EXIT_OPERATIONAL,
    EXIT_POLICY,
    EXIT_SUCCESS,
    FailureSelector,
    InvocationError,
    failure_policy,
    has_required_phase_failure,
    output_plan,
    parse_failure_selectors,
    validate_output_destinations,
    write_output_file,
)
from ladon.analysis.generated_family_candidate_profile import (
    CandidateProfileError,
    load_explicit_candidate_profile,
)
from ladon.configuration import ConfigurationError, validate_policy_configuration
from ladon.analysis.population_calibration import PolicyValidationError
from ladon.pipeline import (
    PipelineResult,
    RunContext,
    discovery_partial_result,
    run_pipeline,
)
from ladon.lean_runtime import (
    DEFAULT_LEAN_BATCH_SIZE,
    DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
    EXECUTION_SAFETY_WARNING,
)
from ladon.process_supervisor import ProcessSignal
from ladon.progress import (
    ProgressReporter,
    ResourceLimitExceeded,
    RunBudget,
    RunLimits,
)
from ladon.render import render_text
from ladon.render_v3 import render_report_v3_text
from ladon.report_contract import default_phase_disposition
from ladon.report_v2 import (
    Diagnostic,
    PhaseEnvelope,
    ReportV2,
    coerce_report_v2,
    mark_report_phase_required,
    replace_report_phase,
    serialize_report_bytes,
    update_report_metadata,
)
from ladon.report_v3 import (
    PROJECTION_NAMES,
    ReportV3,
    build_report_v3,
    serialize_report_v3_bytes,
    write_report_v3_file,
)
from ladon.reportset_cli import REPORTSET_COMMANDS, reportset_main
from ladon.scope import SUPPORTED_SCOPE_KINDS, ScopePlanningError
from ladon.target_build import (
    DEFAULT_BUILD_TIMEOUT_SECONDS,
    BuildPhase,
    run_lake_build,
    validate_compiled_state,
    validate_lake_preflight,
    validate_target_repository,
)


UNSUPPORTED_OPTIONS = {
    "verify_export_surface": "--verify-export-surface",
    "certificate_artifact": "--certificate-artifact",
}
PUBLIC_COMMAND_HELP = """\
commands:
  runset    Execute a versioned set of ordinary analyses.
  preview   Resolve roots, scope, policies, and costs without target execution.
  inspect   Inspect canonical rows from one existing report or source index.
  findings  List, filter, or inspect findings from one existing report.
  atlas     Build an atlas from reports or a runset bundle.
  query     Run a canned query against an atlas SQLite database.
  diff      Compare two explicit atlas files structurally.
  cards     Render reviewer cards from an atlas.
  workflow  Build a combined atlas review workflow.

Run 'ladon COMMAND --help' for command-specific options.
"""


def build_parser() -> argparse.ArgumentParser:
    """Build the clean-core CLI parser.

    Some legacy option names are accepted so users get explicit unsupported
    messages instead of argparse's generic "unknown argument" error.
    """

    parser = argparse.ArgumentParser(
        description="Ladon clean-core Lean analyzer",
        epilog=PUBLIC_COMMAND_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("target", nargs="?", help="Optional analysis root alias")
    parser.add_argument("--repo-root", default=".", help="Repository root to analyze")
    parser.add_argument(
        "--root",
        dest="analysis_roots",
        action="append",
        default=[],
        help="Lean root file or module; repeat for multi-root scope.",
    )
    parser.add_argument(
        "--scope",
        choices=sorted(SUPPORTED_SCOPE_KINDS),
        default="owner",
        help="Primary/context population contract; owner is the ordinary default.",
    )
    parser.add_argument("--changed-path", action="append", default=[])
    parser.add_argument("--changed-manifest")
    parser.add_argument("--max-modules", type=positive_integer)
    parser.add_argument("--max-context-modules", type=positive_integer)
    parser.add_argument(
        "--cache-dir",
        help="Source-index cache directory; defaults to the platform user cache.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass source-index reads and writes for this analysis.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run the target repository's lake build before dependent analysis.",
    )
    parser.add_argument(
        "--build-timeout",
        type=positive_timeout,
        default=DEFAULT_BUILD_TIMEOUT_SECONDS,
        help="Finite Lake build deadline in seconds.",
    )
    parser.add_argument(
        "--extraction-backend",
        choices=["text", "lean"],
        default="text",
        help=(
            "Select text-only discovery or Lean-backed extraction. The Lean "
            "backend loads target environments and is unsafe for untrusted repositories."
        ),
    )
    parser.add_argument(
        "--lean-extraction-scope", choices=["root", "inventory"], default="root"
    )
    parser.add_argument(
        "--lean-cache-dir",
        help="Optional cache directory for Lean helper JSON payloads",
    )
    parser.add_argument(
        "--lean-batch-size",
        type=inventory_batch_size,
        default=DEFAULT_LEAN_BATCH_SIZE,
        help="Modules per bounded Lean inventory helper invocation (minimum 2).",
    )
    parser.add_argument(
        "--lean-timeout",
        type=positive_timeout,
        default=DEFAULT_LEAN_BATCH_TIMEOUT_SECONDS,
        help="Finite deadline in seconds for each Lean helper batch.",
    )
    parser.add_argument(
        "--lean-strict",
        action="store_true",
        help="Reject partial Lean batches while preserving their rows and diagnostics.",
    )
    parser.add_argument(
        "--progress",
        choices=["auto", "plain", "json", "off"],
        default="auto",
        help="Emit long-run progress on stderr; auto is interactive-only.",
    )
    parser.add_argument(
        "--overall-timeout",
        type=positive_timeout,
        help="Optional finite deadline for the complete analysis in seconds.",
    )
    parser.add_argument(
        "--max-rss-mib",
        type=positive_integer,
        help="Optional supported process-tree resident-memory limit in MiB.",
    )
    parser.add_argument(
        "--max-report-bytes",
        type=positive_integer,
        help="Optional maximum bytes for each selected report representation.",
    )
    parser.add_argument("--format", dest="output_format", choices=["text", "json"])
    parser.add_argument("--output", help="Report path, or - for standard output.")
    parser.add_argument(
        "--emit",
        action="append",
        default=[],
        metavar="FORMAT=PATH",
        help="Add an output destination; repeat for multiple report formats.",
    )
    parser.add_argument(
        "--report-version",
        choices=["v3", "v2", "v1"],
        default=None,
        help=(
            "JSON report major. Canonical output defaults to v3; deprecated "
            "--json/--text output retains v2 unless selected explicitly."
        ),
    )
    parser.add_argument(
        "--projection",
        choices=PROJECTION_NAMES,
        default="review",
        help="Report-v3 projection; review is the ordinary default.",
    )
    parser.add_argument("--output-json", "--json", dest="legacy_json")
    parser.add_argument("--output-text", "--text", dest="legacy_text")
    parser.add_argument(
        "--fail-on",
        action="append",
        default=[],
        help=(
            "Repeatable kind:<kind>, severity:<minimum>, or "
            "phase:<name>:<skipped|partial> selector."
        ),
    )
    parser.add_argument("--generated-at-utc")
    parser.add_argument("--doc-file", action="append", default=[])
    parser.add_argument("--packet-dir", action="append", default=[])
    parser.add_argument(
        "--architecture-policy",
        help="Optional JSON policy defining project-specific module groups and forbidden imports.",
    )
    parser.add_argument(
        "--source-pattern-policy",
        help="Optional JSON policy defining project-specific source text patterns to report.",
    )
    parser.add_argument(
        "--generated-family-policy",
        help=(
            "Optional versioned JSON policy defining project-generated source "
            "families and quoted provenance."
        ),
    )
    parser.add_argument(
        "--generated-family-candidate-profile",
        help=(
            "Optional strict versioned profile for advisory generated-family "
            "candidate detection."
        ),
    )
    parser.add_argument(
        "--module-system-witness",
        help="Optional JSON witness quoting Lean module-system boundary evidence.",
    )
    parser.add_argument(
        "--import-diet-witness",
        help="Optional JSON witness quoting Lean/Lake import minimization evidence.",
    )
    parser.add_argument(
        "--proof-xray",
        help="Optional JSON witness quoting elaborated proof-shape evidence.",
    )
    parser.add_argument(
        "--packet-profile",
        choices=["generic", "review_packet", "witness_bundle", "release_bundle"],
        default="generic",
        help="Evidence profile used for --packet-dir summaries.",
    )
    parser.add_argument("--verify-export-surface", action="store_true")
    parser.add_argument("--certificate-artifact", action="append", default=[])
    return parser


def unsupported_requests(args: argparse.Namespace) -> list[str]:
    """Return requested legacy features not yet rebuilt in the clean core."""

    requested: list[str] = []
    for attr, option in UNSUPPORTED_OPTIONS.items():
        value = getattr(args, attr)
        if value:
            requested.append(option)
    return requested


def selected_root(args: argparse.Namespace) -> str | None:
    """Resolve old positional-root usage and the newer `--root` option."""

    roots = selected_roots(args)
    return roots[0] if roots else None


def selected_roots(args: argparse.Namespace) -> tuple[str, ...]:
    """Return ordered explicit roots with positional compatibility."""

    values = tuple(str(value) for value in getattr(args, "analysis_roots", ()))
    if values:
        return values
    return (str(args.target),) if args.target else ()


def delegated_command(arguments: Sequence[str]) -> int | None:
    """Dispatch an installed subcommand before parsing analysis options."""

    if arguments and arguments[0] == "runset":
        from ladon.runset_cli import runset_main

        return runset_main(arguments[1:])
    if arguments and arguments[0] in REPORTSET_COMMANDS:
        return reportset_main(arguments)
    return None


def prepared_analysis_arguments(
    arguments: Sequence[str],
) -> argparse.Namespace | int:
    """Parse ordinary analysis options and return any preflight exit."""

    if skip_build_requested(arguments):
        print(
            "ladon: --skip-build was removed; omit it to preserve no-build "
            "analysis, or use --build to request Lake execution",
            file=sys.stderr,
        )
        return EXIT_INVOCATION
    args = build_parser().parse_args(arguments)
    if args.lean_strict:
        print(
            "ladon: --lean-strict is deprecated; use "
            "--fail-on phase:lean_extraction:partial",
            file=sys.stderr,
        )
    unsupported = unsupported_requests(args)
    if unsupported:
        # Refuse partial reports for old feature flags until they are rebuilt
        # as tested clean-core modules.
        print(
            "unsupported clean-core option(s): " + ", ".join(sorted(unsupported)),
            file=sys.stderr,
        )
        return EXIT_INVOCATION
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run one clean-core Ladon analysis and return a process status code."""

    arguments = list(argv) if argv is not None else sys.argv[1:]
    delegated = delegated_command(arguments)
    if delegated is not None:
        return delegated
    prepared = prepared_analysis_arguments(arguments)
    if isinstance(prepared, int):
        return prepared
    args = prepared
    try:
        return execute(args)
    except (
        ConfigurationError,
        CandidateProfileError,
        InvocationError,
        PolicyValidationError,
        ScopePlanningError,
    ) as exc:
        print(f"ladon: invalid invocation: {exc}", file=sys.stderr)
        return EXIT_INVOCATION
    except ProcessSignal as exc:
        return 128 + exc.signum
    except ResourceLimitExceeded as exc:
        print(
            f"ladon: operational failure {exc.phase}: resource.{exc.kind}: {exc}",
            file=sys.stderr,
        )
        return EXIT_OPERATIONAL
    except Exception as exc:
        print(f"ladon: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL


def execute(args: argparse.Namespace) -> int:
    """Validate, analyze, render, and classify one parsed invocation."""

    plan = output_plan(args)
    selectors = parse_failure_selectors(effective_failure_selectors(args))
    repo_root = common_preflight(args, plan)
    context = run_context(args, repo_root)
    result, build = run_requested_analysis(args, context)
    report = result.to_report_model(copy_phase_data=False)
    if build is not None:
        report = coerce_report_v2(
            replace_report_phase(report, build_phase_envelope(build))
        )
    if args.extraction_backend == "lean":
        report = coerce_report_v2(
            mark_report_phase_required(
                report,
                "lean_extraction",
                required=True,
            )
        )
    if context.limit_failure is not None:
        report = mark_resource_limit_failure(
            report,
            context.limit_failure,
        )
    report = apply_phase_dispositions(
        report,
        selectors,
        strict_lean=args.lean_strict,
    )
    policy = failure_policy(report, selectors)
    report = coerce_report_v2(
        update_report_metadata(
            report,
            failure_policy=policy if selectors else None,
        )
    )
    warnings = emit_report(
        report,
        plan,
        budget=context.budget,
        progress=context.progress,
    )
    emit_diagnostics(plan.legacy, warnings, policy)
    status = execution_status(report, policy, build)
    emit_operational_diagnostic(report, plan, status)
    return status


def common_preflight(args: argparse.Namespace, plan) -> Path:
    """Validate caller-owned paths and configuration before analysis."""

    repo_root = validate_target_repository(Path(args.repo_root))
    validate_output_destinations(plan)
    validate_policy_configuration(
        repo_root,
        architecture_policy=optional_path(args.architecture_policy),
        source_pattern_policy=optional_path(args.source_pattern_policy),
        generated_family_policy=optional_path(args.generated_family_policy),
    )
    if args.extraction_backend == "lean" and not args.build:
        validate_lake_preflight(repo_root)
        validate_compiled_state(repo_root, build_requested=False)
    return repo_root


def run_context(args: argparse.Namespace, repo_root: Path) -> RunContext:
    """Build caller-independent pipeline state from parsed options."""

    limits = RunLimits(
        wall_seconds=args.overall_timeout,
        rss_bytes=args.max_rss_mib * 1024 * 1024 if args.max_rss_mib else None,
        report_bytes=args.max_report_bytes,
    )
    return RunContext(
        repo_root=repo_root,
        requested_root=selected_root(args),
        requested_roots=selected_roots(args),
        analysis_scope=args.scope,
        changed_paths=tuple(args.changed_path),
        changed_manifest=optional_path(args.changed_manifest),
        max_scope_modules=args.max_modules,
        max_context_modules=args.max_context_modules,
        source_cache_dir=optional_path(args.cache_dir),
        source_cache_enabled=not args.no_cache,
        build_requested=args.build,
        build_timeout_seconds=args.build_timeout,
        preflight={
            "repository": "validated",
            "output": "validated",
            "configuration": "validated",
        },
        extraction_backend=args.extraction_backend,
        lean_extraction_scope=args.lean_extraction_scope,
        lean_cache_dir=optional_path(args.lean_cache_dir),
        lean_batch_size=args.lean_batch_size,
        lean_helper_timeout_seconds=args.lean_timeout,
        lean_strict=args.lean_strict,
        packet_dirs=tuple(Path(path) for path in args.packet_dir),
        packet_profile=args.packet_profile,
        architecture_policy_path=optional_path(args.architecture_policy),
        source_pattern_policy_path=optional_path(args.source_pattern_policy),
        generated_family_policy_path=optional_path(args.generated_family_policy),
        generated_family_candidate_profile_path=optional_path(
            args.generated_family_candidate_profile
        ),
        generated_family_candidate_profile=load_candidate_profile(args),
        module_system_witness_path=optional_path(args.module_system_witness),
        import_diet_witness_path=optional_path(args.import_diet_witness),
        proof_xray_path=optional_path(args.proof_xray),
        generated_at_utc=args.generated_at_utc,
        warnings=clean_core_warnings(args),
        progress=ProgressReporter(
            mode=args.progress,
            run_id=analysis_run_id(
                repo_root,
                selected_root(args),
                args.extraction_backend,
            ),
        ),
        budget=RunBudget(limits),
    )


def load_candidate_profile(args: argparse.Namespace):
    """Load an explicit strict candidate profile before repository analysis."""

    path = optional_path(args.generated_family_candidate_profile)
    return load_explicit_candidate_profile(path) if path is not None else None


def run_requested_analysis(
    args: argparse.Namespace,
    context: RunContext,
) -> tuple[PipelineResult, BuildPhase | None]:
    """Run analysis and an explicit build in backend-safe order."""

    if not args.build:
        return run_pipeline(context), None
    if args.extraction_backend == "lean":
        build = run_context_build(context, args.build_timeout)
        if not build.status == "complete":
            reason = build_failure_reason(build)
            partial = discovery_partial_result(
                context,
                blocked_phase="lean_extraction",
                reason=reason,
            )
            return partial, build
        return run_pipeline(context), build
    result = run_pipeline(context)
    try:
        build = run_context_build(context, args.build_timeout)
    except ResourceLimitExceeded:
        build = resource_limited_build_phase(context)
    return result, build


def run_context_build(
    context: RunContext,
    timeout_seconds: float,
) -> BuildPhase:
    """Run an explicit build under the whole-run watchdog."""

    with context.phase("build") as counters:
        build = run_lake_build(
            context.repo_root,
            timeout_seconds=timeout_seconds,
            cancel_event=context.cancel_event,
        )
        counters["processes"] = 1
        return build


def resource_limited_build_phase(context: RunContext) -> BuildPhase:
    """Preserve a completed analysis when its trailing build crosses a limit."""

    failure = context.limit_failure or {}
    timing = next(
        (row for row in reversed(context.timings) if row.name == "build"),
        None,
    )
    return BuildPhase(
        status="failed",
        command=("lake", "build"),
        toolchain="",
        diagnostics=(
            str(failure.get("reason", "configured resource limit stopped lake build")),
        ),
        elapsed_seconds=timing.elapsed_seconds if timing is not None else 0.0,
        timeout_seconds=context.build_timeout_seconds,
    )


def build_phase_envelope(build: BuildPhase) -> PhaseEnvelope:
    """Adapt target-build evidence through the typed report boundary."""

    data = {
        "command": list(build.command),
        "toolchain": build.toolchain,
        "timeout_seconds": build.timeout_seconds,
    }
    if build.status == "complete":
        return PhaseEnvelope.complete(
            "build",
            required=True,
            elapsed_seconds=build.elapsed_seconds,
            data=data,
        )
    diagnostics = tuple(
        Diagnostic(
            identifier=f"build.failure.{index}",
            severity="error",
            message=message,
            phase="build",
            subject="lake build",
        )
        for index, message in enumerate(build.diagnostics, start=1)
    )
    return PhaseEnvelope.failed(
        "build",
        build_failure_reason(build),
        required=True,
        elapsed_seconds=build.elapsed_seconds,
        diagnostics=diagnostics,
        data=data,
    )


def mark_resource_limit_failure(
    report: ReportV2,
    failure: dict,
) -> ReportV2:
    """Mark the controlling phase required while preserving retained data."""

    name = str(failure.get("phase", ""))
    if name not in report.phases:
        return report
    phase = report.phases[name]
    diagnostic = Diagnostic(
        identifier=str(failure.get("id", "resource.limit")),
        severity="error",
        message=str(failure.get("reason", "configured resource limit exceeded")),
        phase=name,
        subject=name,
        data={
            "kind": failure.get("kind"),
            "observed": failure.get("observed"),
            "limit": failure.get("limit"),
        },
    )
    updated = replace_report_phase(
        report,
        replace(
            phase,
            status="failed",
            required=True,
            disposition="failed",
            reason=diagnostic.message,
            diagnostics=(*phase.diagnostics, diagnostic),
        ),
    )
    return coerce_report_v2(updated)


def apply_phase_dispositions(
    report: ReportV2,
    selectors: Sequence[FailureSelector],
    *,
    strict_lean: bool,
) -> ReportV2:
    """Record why incomplete phase evidence is accepted or rejected."""

    selected = {
        (selector.value, selector.phase_status)
        for selector in selectors
        if selector.category == "phase"
    }
    phases = dict(report.phases)
    for name, phase in phases.items():
        disposition = default_phase_disposition(phase.status, phase.required)
        if phase.status in {"partial", "skipped"}:
            if strict_lean and name == "lean_extraction":
                disposition = "strict-rejection"
            elif (name, phase.status) in selected:
                disposition = "selector-rejection"
        if phase.disposition == disposition:
            continue
        phases[name] = replace(phase, disposition=disposition)
    return replace(report, phases=phases)


def build_failure_reason(build: BuildPhase) -> str:
    """Return one concise required-phase reason."""

    return build.diagnostics[0] if build.diagnostics else "lake build failed"


def emit_report(
    payload: ReportV2,
    plan,
    *,
    budget: RunBudget | None = None,
    progress: ProgressReporter | None = None,
) -> tuple[str, ...]:
    """Render selected representations and return compatibility warnings."""

    render_artifact: ReportV2 | ReportV3 = (
        build_report_v3(payload, projection=plan.projection)
        if plan.report_version == "v3"
        else payload
    )
    warnings: list[str] = []
    for target in plan.targets:
        pulse = (
            progress.phase(
                f"serialization.{target.format}",
                completed_interval=1024 * 1024,
            )
            if progress is not None
            else None
        )
        if pulse is not None:
            pulse.start()
        try:
            selected_warnings, byte_count = emit_report_target(
                render_artifact,
                plan,
                target,
                budget=budget,
                progress_callback=(
                    (
                        lambda completed: pulse.update(
                            completed=completed,
                        )
                    )
                    if pulse is not None
                    else None
                ),
            )
        except Exception:
            if pulse is not None:
                pulse.finish(status="failed")
            raise
        if pulse is not None:
            pulse.finish(
                status="complete",
                completed=byte_count,
                total=byte_count,
            )
        warnings.extend(selected_warnings)
    return tuple(dict.fromkeys(warnings))


def emit_report_target(
    payload: ReportV2 | ReportV3,
    plan,
    target,
    *,
    budget: RunBudget | None,
    progress_callback: Callable[[int], None] | None,
) -> tuple[tuple[str, ...], int]:
    """Render one selected representation with exact completed bytes."""

    if target.format == "json":
        return emit_json_report(
            payload,
            plan,
            target.destination,
            budget,
            progress_callback=progress_callback,
        )
    text = (
        render_report_v3_text(payload)
        if isinstance(payload, ReportV3)
        else render_text(payload)
    )
    byte_count = len(text.encode("utf-8"))
    if progress_callback is not None:
        progress_callback(byte_count)
    if budget is not None:
        budget.check_report_bytes("serialization.text", byte_count)
    write_report_content(target.destination, text)
    return (), byte_count


def emit_json_report(
    payload: ReportV2 | ReportV3,
    plan,
    destination: str,
    budget: RunBudget | None,
    *,
    progress_callback: Callable[[int], None] | None,
) -> tuple[tuple[str, ...], int]:
    """Emit one versioned JSON representation through its bounded path."""

    max_bytes = budget.limits.report_bytes if budget is not None else None
    if plan.report_version == "v3":
        if destination != "-":
            written = write_report_v3_file(
                payload,
                destination,
                max_bytes=max_bytes,
                progress_callback=progress_callback,
            )
            return (), written.byte_count
        serialized_v3 = serialize_report_v3_bytes(
            payload,
            max_bytes=max_bytes,
            progress_callback=progress_callback,
        )
        sys.stdout.write(serialized_v3.content.decode("utf-8"))
        return (), len(serialized_v3.content)
    serialized = serialize_report_bytes(payload, version=plan.report_version)
    if progress_callback is not None:
        progress_callback(len(serialized.content))
    if budget is not None:
        budget.check_report_bytes("serialization.json", len(serialized.content))
    write_report_content(destination, serialized.content.decode("utf-8"))
    compatibility = (
        (
            "report v2 compatibility output duplicates large phase payloads; "
            "use report v3 for canonical bounded projections",
        )
        if plan.report_version == "v2"
        else ()
    )
    return (*serialized.warnings, *compatibility), len(serialized.content)


def write_report_content(destination: str, content: str) -> None:
    """Write one already-bounded representation to its selected destination."""

    if destination == "-":
        sys.stdout.write(content)
    else:
        write_output_file(Path(destination), content)


def emit_diagnostics(
    legacy: bool,
    warnings: Sequence[str],
    policy: dict,
) -> None:
    """Write deprecations, compatibility loss, and policy matches to stderr."""

    if legacy:
        print(
            "ladon: --json/--text file flags are deprecated; use --format and --output",
            file=sys.stderr,
        )
    for warning in warnings:
        print(f"ladon: {warning}", file=sys.stderr)
    for selector in dict.fromkeys(row["selector"] for row in policy["matches"]):
        print(f"ladon: failure policy matched {selector}", file=sys.stderr)


def execution_status(
    payload: ReportV2,
    policy: dict,
    build: BuildPhase | None,
) -> int:
    """Apply operational-over-policy exit precedence."""

    if build is not None and build.status != "complete":
        return EXIT_OPERATIONAL
    if has_required_phase_failure(payload):
        return EXIT_OPERATIONAL
    if policy["matches"]:
        return EXIT_POLICY
    return EXIT_SUCCESS


def emit_operational_diagnostic(
    payload: ReportV2,
    plan,
    status: int,
) -> None:
    """Explain every report-backed operational exit on stderr."""

    if status != EXIT_OPERATIONAL:
        return
    phase = controlling_incomplete_phase(payload)
    if phase is None:
        print(
            "ladon: operational analysis failure; inspect the report", file=sys.stderr
        )
        return
    first = controlling_phase_diagnostic(phase)
    identifier = (
        first.identifier if first is not None else f"phase.{phase.name}.{phase.status}"
    )
    reason = phase.reason or (
        first.message if first is not None else "required phase did not complete"
    )
    subject = f" subject={first.subject}" if first is not None and first.subject else ""
    destinations = ", ".join(
        "stdout" if target.destination == "-" else target.destination
        for target in plan.targets
    )
    print(
        f"ladon: operational failure {phase.name}: "
        f"{identifier}{subject}: {reason}; report: {destinations}",
        file=sys.stderr,
    )


def controlling_phase_diagnostic(
    phase: PhaseEnvelope,
) -> Diagnostic | None:
    """Prefer a diagnostic that explicitly explains incomplete phase state."""

    incomplete = next(
        (
            row
            for row in phase.diagnostics
            if row.data.get("status") in {"partial", "failed"}
        ),
        None,
    )
    if incomplete is not None:
        return incomplete
    errors = [row for row in phase.diagnostics if row.severity == "error"]
    return errors[0] if errors else next(iter(phase.diagnostics), None)


def controlling_incomplete_phase(payload: ReportV2) -> PhaseEnvelope | None:
    """Return the first required partial/failed phase in registry order."""

    return next(
        (
            phase
            for phase in payload.phases.values()
            if phase.required and phase.status in {"partial", "failed"}
        ),
        None,
    )


def clean_core_warnings(args: argparse.Namespace) -> list[str]:
    """Collect non-fatal support-boundary warnings for accepted flags."""

    warnings: list[str] = []
    if args.doc_file:
        warnings.append("doc-file audit is not implemented in clean core yet")
    if args.extraction_backend == "lean":
        warnings.append(EXECUTION_SAFETY_WARNING)
    return warnings


def optional_path(value: str | None) -> Path | None:
    """Convert optional path strings at the CLI boundary."""

    return Path(value) if value else None


def positive_timeout(value: str) -> float:
    """Parse one finite positive build deadline."""

    try:
        timeout = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("build timeout must be a number") from exc
    if timeout <= 0:
        raise argparse.ArgumentTypeError("build timeout must be greater than zero")
    return timeout


def inventory_batch_size(value: str) -> int:
    """Parse the minimum viable amortizing inventory batch size."""

    try:
        batch_size = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Lean batch size must be an integer") from exc
    if batch_size < 2:
        raise argparse.ArgumentTypeError("Lean batch size must be at least two")
    return batch_size


def positive_integer(value: str) -> int:
    """Parse one finite positive integer resource limit."""

    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("resource limit must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("resource limit must be greater than zero")
    return parsed


def effective_failure_selectors(args: argparse.Namespace) -> list[str]:
    """Map the bounded strict compatibility flag into the general selector."""

    values = list(args.fail_on)
    selector = "phase:lean_extraction:partial"
    if args.lean_strict and selector not in values:
        values.append(selector)
    return values


def analysis_run_id(
    repo_root: Path,
    root: str | None,
    backend: str,
) -> str:
    """Return a bounded stable identity for diagnostic progress correlation."""

    source = "\n".join((str(repo_root.resolve()), root or "", backend))
    return f"run-{hashlib.sha256(source.encode()).hexdigest()[:16]}"


def skip_build_requested(arguments: Sequence[str]) -> bool:
    """Detect the removed no-op flag for an actionable exit-2 migration."""

    return any(
        argument == "--skip-build" or argument.startswith("--skip-build=")
        for argument in arguments
    )


if __name__ == "__main__":
    raise SystemExit(main())
