"""Installed ``ladon runset`` orchestration over the ordinary analysis CLI."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any, Mapping, Sequence

from ladon.analysis.generated_family_policy import (
    PolicyValidationError,
    parse_generated_family_policy,
)
from ladon.cli_execution import (
    EXIT_INVOCATION,
    EXIT_OPERATIONAL,
    InvocationError,
    output_plan,
)
from ladon.configuration import (
    ConfigurationError,
    policy_fingerprint_options,
    resolve_policy_configuration,
)
from ladon.process_supervisor import ProcessSignal
from ladon.progress import ProgressEvent, ProgressReporter
from ladon.runset_contract import (
    EntryValidity,
    RunsetEntry,
    RunsetManifest,
    RunsetManifestError,
    content_sha256,
    load_runset_manifest,
)
from ladon.runset_storage import atomic_write_bytes
from ladon.runsets import (
    AnalysisOutcome,
    ReusableArtifact,
    RunsetAnalysisRequest,
    RunsetExecutionResult,
    execute_runset,
)
from ladon.scope import ScopePlanningError
from ladon.scope_runtime import ResolvedAnalysisScope, resolve_analysis_scope


PATH_OPTIONS = {
    "architecturePolicy": "--architecture-policy",
    "sourcePatternPolicy": "--source-pattern-policy",
    "generatedFamilyPolicy": "--generated-family-policy",
    "moduleSystemWitness": "--module-system-witness",
    "importDietWitness": "--import-diet-witness",
    "proofXray": "--proof-xray",
}
LIST_PATH_OPTIONS = {
    "docFiles": "--doc-file",
    "packetDirs": "--packet-dir",
}
SCALAR_OPTIONS = {
    "buildTimeout": "--build-timeout",
    "leanExtractionScope": "--lean-extraction-scope",
    "leanBatchSize": "--lean-batch-size",
    "leanTimeout": "--lean-timeout",
    "packetProfile": "--packet-profile",
}
RUNSET_ENTRY_VALIDITY_VERSION = "ladon-runset-entry-validity-v1"


def build_runset_parser() -> argparse.ArgumentParser:
    """Build the ordinary installed runset command parser."""

    parser = argparse.ArgumentParser(
        prog="ladon runset",
        description="Run a versioned set of ordinary Ladon analyses.",
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument(
        "--workspace-root",
        help="Base for the manifest's repository path; defaults to manifest parent.",
    )
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--cache-dir")
    parser.add_argument("--lean-cache-dir")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--progress",
        choices=["auto", "plain", "json", "off"],
        default="auto",
    )
    parser.add_argument("--format", choices=["json", "text"], default="json")
    parser.add_argument("--output", default="-", help="Bundle output path, or -.")
    return parser


def runset_main(argv: Sequence[str] | None = None) -> int:
    """Execute one installed runset with shared exit and stream discipline."""

    arguments = list(argv) if argv is not None else sys.argv[1:]
    args = build_runset_parser().parse_args(arguments)
    try:
        manifest_path = Path(args.manifest).resolve()
        manifest = load_runset_manifest(manifest_path)
        workspace = (
            Path(args.workspace_root).resolve()
            if args.workspace_root
            else manifest_path.parent
        )
        bundle_dir = Path(args.bundle_dir).resolve()
        validate_selected_output(args, bundle_dir)
        adapter = OrdinaryCliRunsetAdapter(
            manifest=manifest,
            workspace_root=workspace,
            progress_mode=args.progress,
            cache_dir=Path(args.cache_dir).resolve() if args.cache_dir else None,
            lean_cache_dir=(
                Path(args.lean_cache_dir).resolve()
                if args.lean_cache_dir
                else None
            ),
            use_cache=not args.no_cache,
        )
        adapter.preflight()
        result = execute_runset(
            manifest,
            workspace_root=workspace,
            bundle_dir=bundle_dir,
            runner=adapter.run_entry,
            validity_resolver=adapter.resolve_validity,
            resume=args.resume,
            event_sink=RunsetProgress(args.progress, manifest),
        )
        write_runset_output(args, result)
        emit_runset_status(result)
        return result.exit_code
    except (
        ConfigurationError,
        InvocationError,
        PolicyValidationError,
        RunsetManifestError,
        ScopePlanningError,
    ) as exc:
        print(f"ladon: invalid runset invocation: {exc}", file=sys.stderr)
        return EXIT_INVOCATION
    except ProcessSignal as exc:
        return 128 + exc.signum
    except Exception as exc:
        print(f"ladon: runset operation failed: {exc}", file=sys.stderr)
        return EXIT_OPERATIONAL


@dataclass
class OrdinaryCliRunsetAdapter:
    """Translate manifest entries into the existing single-analysis CLI."""

    manifest: RunsetManifest
    workspace_root: Path
    progress_mode: str
    cache_dir: Path | None
    lean_cache_dir: Path | None
    use_cache: bool
    resolved_scopes: dict[str, ResolvedAnalysisScope] = field(
        default_factory=dict
    )

    @property
    def repository_root(self) -> Path:
        """Return the repository selected by the generic manifest."""

        return (self.workspace_root / self.manifest.repository).resolve()

    def preflight(self) -> None:
        """Validate every ordinary invocation before any analyzer can start."""

        from ladon.cli import build_parser, common_preflight

        with tempfile.TemporaryDirectory(prefix="ladon-runset-preflight-") as raw:
            root = Path(raw)
            for entry in self.manifest.execution_order:
                namespace = build_parser().parse_args(
                    self.analysis_arguments(entry, root / f"{entry.identifier}.json")
                )
                common_preflight(namespace, output_plan(namespace))
                preflight_generated_family_policy(namespace)

    def resolve_validity(
        self,
        entry: RunsetEntry,
        repository_root: Path,
    ) -> EntryValidity:
        """Resolve the same source index and scope the analysis will consume."""

        scope = entry.scope
        policies = resolve_entry_policies(entry, repository_root)
        resolved = resolve_analysis_scope(
            repository_root,
            scope_kind=str(scope["kind"]),
            roots=scope_roots(entry),
            changed_paths=tuple(scope.get("changedPaths", ())),
            changed_manifest=resolved_manifest_path(
                repository_root,
                scope.get("changedManifest"),
            ),
            max_modules=optional_int(scope.get("maxModules")),
            max_context_modules=optional_int(
                scope.get("maxContextModules")
            ),
            lean_batch_size=int(
                scope.get(
                    "leanBatchSize",
                    entry.options.get("leanBatchSize", 8),
                )
            ),
            cache_dir=self.cache_dir,
            use_cache=self.use_cache,
            index_options=policy_fingerprint_options(policies),
        )
        self.resolved_scopes[entry.identifier] = resolved
        lean_unavailable, lean_bypassed = self._lean_cache_reuse_state(entry)
        return EntryValidity(
            input_fingerprint=entry_analysis_fingerprint(
                resolved,
                policies,
            ),
            source_index_fingerprint=labeled_digest(
                resolved.source_index.index.fingerprint
            ),
            components={
                "entryOptions": content_sha256(
                    canonical_mapping_bytes(entry.options)
                ),
                "policyInputs": content_sha256(
                    canonical_mapping_bytes(policies)
                ),
            },
            reuse_unavailable_reasons=lean_unavailable,
            reuse_bypass_reasons=lean_bypassed,
        )

    def _lean_cache_reuse_state(
        self,
        entry: RunsetEntry,
    ) -> tuple[dict[str, str], dict[str, str]]:
        """Explain why no unsound aggregate Lean-cache identity is claimed."""

        if entry.backend != "lean":
            return {"lean-cache": "backend_does_not_use_lean_cache"}, {}
        if not self.use_cache:
            return {}, {"lean-cache": "cache_disabled"}
        if selected_lean_cache(
            entry,
            self.repository_root,
            self.lean_cache_dir,
        ) is None:
            return {"lean-cache": "cache_not_configured"}, {}
        return {
            "lean-cache": (
                "aggregate_fingerprint_unavailable; "
                "per-module fingerprints remain in the canonical report"
            )
        }, {}

    def run_entry(self, request: RunsetAnalysisRequest) -> AnalysisOutcome:
        """Run one entry through the existing parser and ``cli.execute``."""

        from ladon.cli import build_parser, execute

        with tempfile.TemporaryDirectory(prefix="ladon-runset-entry-") as raw:
            output = Path(raw) / "report.json"
            namespace = build_parser().parse_args(
                self.analysis_arguments(request.entry, output)
            )
            status = execute(namespace)
            content = output.read_bytes() if output.is_file() else None
        outcome_status = analysis_outcome_status(status, content)
        diagnostics = analysis_exit_diagnostics(status)
        resolved = self.resolved_scopes[request.entry.identifier]
        reusable: Mapping[str, Any] = {}
        if outcome_status == "complete" and self.use_cache:
            reusable = {
                "source-index": ReusableArtifact(
                    fingerprint=labeled_digest(
                        resolved.source_index.index.fingerprint
                    ),
                    value=resolved.source_index.index,
                )
            }
        return AnalysisOutcome(
            status=outcome_status,
            report_bytes=content,
            diagnostics=diagnostics,
            resource_counters={
                "analysisExitCode": status,
                "sourceIndexReusedEntries": (
                    resolved.source_index.cache.reused_entries
                ),
                "sourceIndexRebuiltEntries": (
                    resolved.source_index.cache.rebuilt_entries
                ),
            },
            reusable_artifacts=reusable,
        )

    def analysis_arguments(
        self,
        entry: RunsetEntry,
        output: Path,
    ) -> list[str]:
        """Return only documented ordinary CLI arguments for one entry."""

        arguments = self._base_arguments(entry, output)
        add_scope_arguments(arguments, entry, self.repository_root)
        add_entry_options(arguments, entry, self.repository_root)
        add_resource_arguments(arguments, self.manifest)
        if self.cache_dir is not None:
            arguments.extend(("--cache-dir", str(self.cache_dir)))
        if not self.use_cache:
            arguments.append("--no-cache")
        lean_cache = selected_lean_cache(
            entry,
            self.repository_root,
            self.lean_cache_dir,
        )
        if lean_cache is not None:
            arguments.extend(("--lean-cache-dir", str(lean_cache)))
        return arguments

    def _base_arguments(
        self,
        entry: RunsetEntry,
        output: Path,
    ) -> list[str]:
        return [
            "--repo-root",
            str(self.repository_root),
            "--scope",
            str(entry.scope["kind"]),
            "--extraction-backend",
            entry.backend,
            "--format",
            "json",
            "--output",
            str(output),
            "--report-version",
            entry.report_version,
            "--projection",
            entry.projection,
            "--progress",
            self.progress_mode,
        ]


class RunsetProgress:
    """Adapt entry lifecycle events to Ladon's existing stderr reporter."""

    def __init__(self, mode: str, manifest: RunsetManifest) -> None:
        self.reporter = ProgressReporter(
            mode=mode,
            run_id=f"runset-{manifest.fingerprint.removeprefix('sha256:')[:16]}",
        )
        self.started: dict[str, float] = {}

    def __call__(self, raw: Mapping[str, Any]) -> None:
        entry = str(raw["entry"])
        status = str(raw["status"])
        if status == "started":
            self.started[entry] = monotonic()
        started = self.started.get(entry, monotonic())
        event = "start" if status == "started" else "finish"
        self.reporter.emit(
            ProgressEvent(
                run_id=self.reporter.run_id,
                phase=f"runset.{entry}",
                kind=event,
                status="running" if status == "started" else status,
                elapsed_seconds=max(0.0, monotonic() - started),
                cache={"resume_hits": int(status == "resume-hit")},
            )
        )


def add_scope_arguments(
    arguments: list[str],
    entry: RunsetEntry,
    repository_root: Path,
) -> None:
    """Append explicit scope controls without inventing hidden roots."""

    scope = entry.scope
    for root in scope_roots(entry):
        arguments.extend(("--root", root))
    for path in scope.get("changedPaths", ()):
        arguments.extend(("--changed-path", str(path)))
    changed_manifest = resolved_manifest_path(
        repository_root,
        scope.get("changedManifest"),
    )
    if changed_manifest is not None:
        arguments.extend(("--changed-manifest", str(changed_manifest)))
    append_optional(arguments, "--max-modules", scope.get("maxModules"))
    append_optional(
        arguments,
        "--max-context-modules",
        scope.get("maxContextModules"),
    )


def add_entry_options(
    arguments: list[str],
    entry: RunsetEntry,
    repository_root: Path,
) -> None:
    """Map validated manifest options onto the documented analysis parser."""

    options = entry.options
    if options.get("build") is True:
        arguments.append("--build")
    for key, flag in SCALAR_OPTIONS.items():
        append_optional(arguments, flag, options.get(key))
    for selector in options.get("failOn", ()):
        arguments.extend(("--fail-on", str(selector)))
    for key, flag in PATH_OPTIONS.items():
        value = options.get(key)
        if value is not None:
            arguments.extend((flag, str(repository_root / str(value))))
    for key, flag in LIST_PATH_OPTIONS.items():
        for value in options.get(key, ()):
            arguments.extend((flag, str(repository_root / str(value))))


def add_resource_arguments(
    arguments: list[str],
    manifest: RunsetManifest,
) -> None:
    """Forward the runset's finite per-analysis resource ceilings."""

    resources = manifest.resources
    append_optional(
        arguments,
        "--overall-timeout",
        resources.overall_timeout_seconds,
    )
    append_optional(arguments, "--max-rss-mib", resources.max_rss_mib)
    append_optional(
        arguments,
        "--max-report-bytes",
        resources.max_report_bytes,
    )


def scope_roots(entry: RunsetEntry) -> tuple[str, ...]:
    """Return explicit scope roots, falling back only to the entry root."""

    roots = entry.scope.get("roots")
    if isinstance(roots, list) and roots:
        return tuple(str(root) for root in roots)
    return (entry.root,)


def selected_lean_cache(
    entry: RunsetEntry,
    repository_root: Path,
    global_cache: Path | None,
) -> Path | None:
    """Resolve an entry override or the explicit global Lean cache."""

    selected = entry.options.get("leanCacheDir")
    return repository_root / str(selected) if selected is not None else global_cache


def resolve_entry_policies(
    entry: RunsetEntry,
    repository_root: Path,
) -> dict[str, dict[str, Any]]:
    """Resolve the exact explicit or discovered policies used by one entry."""

    return resolve_policy_configuration(
        repository_root,
        architecture_policy=entry_option_path(
            entry,
            repository_root,
            "architecturePolicy",
        ),
        source_pattern_policy=entry_option_path(
            entry,
            repository_root,
            "sourcePatternPolicy",
        ),
        generated_family_policy=entry_option_path(
            entry,
            repository_root,
            "generatedFamilyPolicy",
        ),
    )


def entry_analysis_fingerprint(
    resolved: ResolvedAnalysisScope,
    policies: Mapping[str, Mapping[str, Any]],
) -> str:
    """Fingerprint only inputs that can change this entry's report semantics."""

    index = resolved.source_index.index
    plan = resolved.scope_plan
    scope = plan.to_payload()
    scope.pop("fingerprint")
    scope.pop("sourceIndexFingerprint")
    selected = set(plan.selected_modules)
    manifest = index.fingerprint_manifest
    payload = {
        "version": RUNSET_ENTRY_VALIDITY_VERSION,
        "sourceIndexContract": {
            "algorithmVersion": manifest.get("algorithmVersion"),
            "fingerprintVersion": manifest.get("fingerprintVersion"),
            "indexSchema": manifest.get("indexSchema"),
            "layout": manifest.get("layout"),
            "options": manifest.get("options"),
        },
        "indexStatus": index.index_status,
        "indexDiagnostics": [dict(row) for row in index.diagnostics],
        "scope": scope,
        "selectedEntries": [
            row.to_payload()
            for row in index.entries
            if row.name in selected
        ],
        "policies": {
            name: dict(row)
            for name, row in sorted(policies.items())
        },
    }
    return content_sha256(canonical_mapping_bytes(payload))


def entry_option_path(
    entry: RunsetEntry,
    repository_root: Path,
    name: str,
) -> Path | None:
    """Resolve one validated portable path-valued entry option."""

    selected = entry.options.get(name)
    return (
        repository_root / str(selected)
        if selected is not None
        else None
    )


def preflight_generated_family_policy(namespace: argparse.Namespace) -> None:
    """Validate the explicit generated-family policy before any entry starts."""

    value = getattr(namespace, "generated_family_policy", None)
    if not value:
        return
    try:
        payload = json.loads(Path(value).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyValidationError(
            f"cannot load generated-family policy: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise PolicyValidationError("generated-family policy must be an object")
    parse_generated_family_policy(payload)


def analysis_outcome_status(status: int, content: bytes | None) -> str:
    """Classify an ordinary CLI exit while retaining any partial report."""

    if status == 0:
        return "complete"
    if status == EXIT_OPERATIONAL and content is not None:
        return "partial"
    return "failed"


def analysis_exit_diagnostics(
    status: int,
) -> tuple[Mapping[str, Any], ...]:
    """Attach a stable diagnostic when ordinary CLI policy or operation failed."""

    if status == 0:
        return ()
    return (
        {
            "id": "runset.analysis_exit",
            "severity": "error",
            "message": f"ordinary Ladon analysis exited with status {status}",
        },
    )


def write_runset_output(
    args: argparse.Namespace,
    result: RunsetExecutionResult,
) -> None:
    """Write one selected bundle representation without touching report files."""

    content = (
        result.bundle.to_bytes()
        if args.format == "json"
        else render_runset_text(result).encode("utf-8")
    )
    if args.output == "-":
        sys.stdout.write(content.decode("utf-8"))
        return
    destination = Path(args.output).resolve()
    if destination == result.bundle_path and args.format == "json":
        return
    atomic_write_bytes(destination, content)


def render_runset_text(result: RunsetExecutionResult) -> str:
    """Render a compact human index without merging report authority."""

    lines = [
        "Ladon analysis runset",
        f"Name: {result.bundle.name}",
        f"Completeness: {result.bundle.completeness}",
        f"Analyzer launches: {result.analyzer_launches}",
        f"Resume hits: {result.resume_hits}",
        "Entries:",
    ]
    for entry in result.bundle.entries:
        report = entry.report.path if entry.report is not None else "-"
        lines.append(
            f"- {entry.identifier}: {entry.status} | {entry.root} | {report}"
        )
    return "\n".join(lines) + "\n"


def validate_selected_output(args: argparse.Namespace, bundle_dir: Path) -> None:
    """Prevent a text selection from overwriting the canonical bundle JSON."""

    if args.output == "-":
        return
    destination = Path(args.output).resolve()
    canonical = bundle_dir / "bundle.json"
    if destination == canonical and args.format != "json":
        raise RunsetManifestError(
            "text output cannot replace the canonical bundle.json"
        )


def emit_runset_status(result: RunsetExecutionResult) -> None:
    """Explain incomplete aggregate state without adding bytes to stdout."""

    if result.bundle.completeness == "complete":
        return
    print(
        f"ladon: runset {result.bundle.completeness}; "
        f"inspect bundle {result.bundle_path}",
        file=sys.stderr,
    )


def append_optional(
    arguments: list[str],
    flag: str,
    value: Any,
) -> None:
    if value is not None:
        arguments.extend((flag, str(value)))


def resolved_manifest_path(
    repository_root: Path,
    value: Any,
) -> Path | None:
    return repository_root / str(value) if value is not None else None


def optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def labeled_digest(value: str) -> str:
    return value if value.startswith("sha256:") else f"sha256:{value}"


def canonical_mapping_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


if __name__ == "__main__":
    raise SystemExit(runset_main())
