"""Source discovery and backend extraction phases for Ladon's pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from ladon.analysis.generated_family_candidate_profile import (
    BUILTIN_CANDIDATE_PROFILE,
    CandidateProfile,
    load_explicit_candidate_profile,
)
from ladon.changed_set import capture_changed_set_manifest
from ladon.configuration import (
    policy_display_path,
    policy_fingerprint_options,
    resolve_policy_inputs,
)
from ladon.elaborated_extraction import augment_with_elaborated_surfaces
from ladon.extraction import ModuleDiscovery
from ladon.ir import ExtractionBundle, LeanDeclaration, LeanModule
from ladon.lean_extraction import extract_with_lean_helper
from ladon.pipeline_models import RunContext
from ladon.pipeline_snapshot import register_captured_bytes
from ladon.scope_runtime import (
    ResolvedAnalysisScope,
    resolve_analysis_scope,
    source_index_cache_payload,
    source_index_inventory_count,
)
from ladon.snapshot import (
    register_policy_snapshot,
    snapshot_from_source_index_manifest,
)
from ladon.snapshot_registry import (
    directory_registry_path,
    snapshot_registry_path,
)

_ValueT = TypeVar("_ValueT")
_INLINE_EVIDENCE_INPUTS = (
    (
        "moduleSystemWitness",
        "module-system-witness",
        "module_system_witness",
    ),
    (
        "importDietWitness",
        "import-diet-witness",
        "import_diet_witness",
    ),
    ("proofXray", "proof-xray-witness", "proof_xray"),
)


def adapt_modules(modules: Mapping[str, LeanModule]) -> dict[str, LeanModule]:
    """Normalize current extraction modules into Ladon's stable IR map."""

    return dict(sorted(modules.items()))


def merge_module_inventory(
    text_modules: Mapping[str, LeanModule],
    helper_modules: Mapping[str, LeanModule],
) -> dict[str, LeanModule]:
    """Merge text inventory with helper rows, preferring helper rows."""

    return adapt_modules(
        {
            **text_modules,
            **{
                name: merge_module_row(text_modules.get(name), module)
                for name, module in helper_modules.items()
            },
        }
    )


def merge_module_row(
    text_module: LeanModule | None,
    helper_module: LeanModule,
) -> LeanModule:
    """Preserve text import source evidence when helper rows omit it."""

    if text_module is None:
        return helper_module
    return LeanModule(
        name=helper_module.name,
        path=helper_module.path,
        imports=helper_module.imports,
        import_sites=_prefer_nonempty(
            helper_module.import_sites,
            text_module.import_sites,
        ),
        line_count=_prefer_nonempty(
            helper_module.line_count,
            text_module.line_count,
        ),
        tags=_prefer_nonempty(helper_module.tags, text_module.tags),
        lexical_markers=_prefer_nonempty(
            helper_module.lexical_markers,
            text_module.lexical_markers,
        ),
        declarations=helper_module.declarations,
        declaration_evidence=_prefer_nonempty(
            helper_module.declaration_evidence,
            text_module.declaration_evidence,
        ),
        scope_context_commands=_prefer_nonempty(
            helper_module.scope_context_commands,
            text_module.scope_context_commands,
        ),
        scope_contexts=_prefer_nonempty(
            helper_module.scope_contexts,
            text_module.scope_contexts,
        ),
        option_rows=_prefer_nonempty(
            helper_module.option_rows,
            text_module.option_rows,
        ),
        resource_settings=_prefer_nonempty(
            helper_module.resource_settings,
            text_module.resource_settings,
        ),
        proof_mechanisms=_prefer_nonempty(
            helper_module.proof_mechanisms,
            text_module.proof_mechanisms,
        ),
        audit_commands=_prefer_nonempty(
            helper_module.audit_commands,
            text_module.audit_commands,
        ),
        audit_commands_complete=(
            helper_module.audit_commands_complete
            and text_module.audit_commands_complete
        ),
        command_skeletons=_prefer_nonempty(
            helper_module.command_skeletons,
            text_module.command_skeletons,
        ),
        command_skeletons_complete=(
            helper_module.command_skeletons_complete
            and text_module.command_skeletons_complete
        ),
    )


def _prefer_nonempty(primary: _ValueT, fallback: _ValueT) -> _ValueT:
    """Prefer backend evidence while retaining its lexical fallback."""

    return primary or fallback


def text_extraction_bundle(discovery: ModuleDiscovery) -> ExtractionBundle:
    """Adapt text extraction to the backend-neutral bundle shape."""

    return ExtractionBundle(
        modules=adapt_modules(discovery.modules),
        declarations={},
    )


def run_extraction_phases(
    context: RunContext,
) -> tuple[ModuleDiscovery, dict[str, LeanModule], dict[str, LeanDeclaration]]:
    """Run discovery, selected extraction backend, and normalized indexing."""

    with context.phase("discover") as counters:
        resolved = indexed_discovery(context)
        discovery = resolved.discovery
        counters["modules"] = len(discovery.modules)
        add_index_counters(counters, resolved)
        finalize_discovery_phase(context, resolved)

    bundle, discovery = run_selected_extraction_backend(context, discovery)
    declarations = bundle.declarations or {}

    with context.phase("indexing") as counters:
        modules = adapt_modules(bundle.modules)
        counters["modules"] = len(modules)
    return discovery, modules, declarations


def indexed_discovery(context: RunContext) -> ResolvedAnalysisScope:
    """Resolve the shared source index and explicit analysis population."""

    captured_inputs = capture_analysis_inputs(context)
    roots = context.requested_roots or (
        (context.requested_root,) if context.requested_root else ()
    )
    resolved_policies = resolve_policy_inputs(
        context.repo_root,
        architecture_policy=context.architecture_policy_path,
        source_pattern_policy=context.source_pattern_policy_path,
        generated_family_policy=context.generated_family_policy_path,
        architecture_inline=context.architecture_policy,
        source_pattern_inline=context.source_pattern_policy,
        generated_family_inline=context.generated_family_policy,
    )
    policies = {
        name: dict(resolved.identity) for name, resolved in resolved_policies.items()
    }
    policies["generatedFamilyCandidateProfile"] = candidate_profile_policy_identity(
        context
    )
    resolved = resolve_analysis_scope(
        context.repo_root,
        scope_kind=context.analysis_scope,
        roots=roots,
        changed_paths=context.changed_paths,
        changed_manifest=context.captured_changed_manifest,
        max_modules=context.max_scope_modules,
        max_context_modules=context.max_context_modules,
        lean_batch_size=context.lean_batch_size,
        cache_dir=context.source_cache_dir,
        use_cache=context.source_cache_enabled,
        index_options=policy_fingerprint_options(policies),
        progress_callback=context.progress_update,
    )
    context.scope_plan = resolved.scope_plan
    context.source_index = resolved.source_index.index
    context.analysis_snapshot = register_policy_snapshot(
        snapshot_from_source_index_manifest(
            source_index_fingerprint=resolved.source_index.index.fingerprint,
            manifest=resolved.source_index.index.fingerprint_manifest,
            configuration=analysis_snapshot_configuration(
                context,
                resolved,
                policies,
                captured_inputs,
            ),
        ),
        policies,
    )
    register_changed_manifest_snapshot(context)
    context.source_index_cache = source_index_cache_payload(resolved.source_index.cache)
    context.inventory_module_count = source_index_inventory_count(
        resolved.source_index.index
    )
    context.indexed_module_count = len(resolved.source_index.index.entries)
    context.source_index_status = resolved.source_index.phase_status
    context.source_index_diagnostics = tuple(
        dict(row) for row in resolved.source_index.index.diagnostics
    )
    context.policy_inputs = policies
    context.policy_payloads = {
        name: dict(policy.payload)
        for name, policy in resolved_policies.items()
        if policy.payload is not None
    }
    context.policy_paths = {
        name: policy.path
        for name, policy in resolved_policies.items()
        if policy.path is not None
    }
    context.retained_discovery = resolved.discovery
    context.retained_modules = dict(resolved.discovery.modules)
    return resolved


def analysis_snapshot_configuration(
    context: RunContext,
    resolved: ResolvedAnalysisScope,
    policies: Mapping[str, Mapping[str, Any]],
    captured_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Return stable analysis settings joined to the indexed source bytes."""

    index = resolved.source_index.index
    return {
        "sourceIndex": {
            "schema": index.schema,
            "options": dict(index.options),
        },
        "scopeFingerprint": resolved.scope_plan.fingerprint,
        "extraction": {
            "backend": context.extraction_backend,
            "scope": context.lean_extraction_scope,
            "batchSize": context.lean_batch_size,
            "strict": context.lean_strict,
        },
        "policies": {name: dict(row) for name, row in sorted(policies.items())},
        **dict(captured_inputs),
    }


def capture_analysis_inputs(context: RunContext) -> dict[str, Any]:
    """Freeze non-filesystem inputs consumed after source discovery."""

    context.captured_changed_manifest = (
        capture_changed_set_manifest(context.changed_manifest)
        if context.changed_manifest is not None
        else None
    )
    evidence: dict[str, dict[str, Any]] = {}
    payloads: dict[str, bytes] = {}
    for name, namespace, attribute in _INLINE_EVIDENCE_INPUTS:
        raw = getattr(context, attribute)
        if raw is None:
            continue
        content = _canonical_inline_evidence(raw, name)
        payloads[namespace] = content
        evidence[name] = {
            "source": "inline",
            "schema": "json-object",
            "bytes": len(content),
            "sha256": f"sha256:{hashlib.sha256(content).hexdigest()}",
        }
    context.inline_evidence_payloads = payloads
    context.captured_packet_dirs = tuple(context.packet_dirs)
    context.captured_packet_profile = (
        context.packet_profile if context.captured_packet_dirs else None
    )
    return {
        "changedManifest": _changed_manifest_configuration(context),
        "inlineEvidence": evidence,
        "packetEvidence": _packet_input_configuration(context),
    }


def register_changed_manifest_snapshot(context: RunContext) -> None:
    """Bind captured changed-set bytes to their physical final-drift source."""

    captured = context.captured_changed_manifest
    path = context.changed_manifest
    if captured is None or captured.content is None or path is None:
        return
    register_captured_bytes(
        context,
        path,
        captured.content,
        kind="configuration",
        collection_refs=(
            "module_dag.modules",
            "declaration_graph.declarations",
            "report.findings",
            "report.review_regions",
        ),
        namespace="changed-manifest",
    )


def _changed_manifest_configuration(context: RunContext) -> dict[str, Any]:
    """Describe the exact changed-set document captured for scope planning."""

    captured = context.captured_changed_manifest
    path = context.changed_manifest
    if captured is None or path is None:
        return {"status": "not_requested"}
    content = captured.content
    return {
        "status": captured.status,
        "path": snapshot_registry_path(
            context.repo_root,
            path,
            namespace="changed-manifest",
        ),
        "bytes": len(content) if content is not None else 0,
        "sha256": (
            f"sha256:{hashlib.sha256(content).hexdigest()}"
            if content is not None
            else None
        ),
    }


def _canonical_inline_evidence(
    raw: Mapping[str, Any],
    name: str,
) -> bytes:
    try:
        return json.dumps(
            dict(raw),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError(f"inline {name} evidence must be JSON-compatible") from exc


def _packet_input_configuration(context: RunContext) -> dict[str, Any]:
    directories = context.captured_packet_dirs or ()
    if not directories:
        return {"status": "not_requested"}
    return {
        "status": "selected",
        "profile": context.captured_packet_profile,
        "directories": [
            directory_registry_path(
                context.repo_root,
                path,
                namespace=f"packet-{index}",
            )
            for index, path in enumerate(directories)
        ],
    }


def candidate_profile_policy_identity(
    context: RunContext,
    *,
    reload_explicit: bool = False,
) -> dict[str, Any]:
    """Resolve the built-in, inline, or explicit candidate-profile identity."""

    path = context.generated_family_candidate_profile_path
    profile = context.generated_family_candidate_profile
    if path is not None and (profile is None or reload_explicit):
        profile = load_explicit_candidate_profile(path)
        if not reload_explicit:
            context.generated_family_candidate_profile = profile
    if profile is None:
        profile = BUILTIN_CANDIDATE_PROFILE
        source = "built_in"
    else:
        source = "explicit" if path is not None else "inline"
    if not isinstance(profile, CandidateProfile):
        raise TypeError("generated-family candidate profile must be a CandidateProfile")
    return {
        "status": "selected",
        "source": source,
        "path": policy_display_path(context.repo_root, path),
        "schema": profile.schema,
        "profileVersion": profile.profile_version,
        "sha256": profile.digest,
    }


def finalize_discovery_phase(
    context: RunContext,
    resolved: ResolvedAnalysisScope,
) -> None:
    """Publish retained-unit state when source indexing is partial."""

    if resolved.source_index.phase_status != "partial":
        return
    failed = resolved.source_index.cache.failed_entries
    retained = len(resolved.source_index.index.entries)
    total = source_index_inventory_count(resolved.source_index.index)
    context.mark_phase_partial(
        "discover",
        (
            f"source index retained {retained} of {total} modules; "
            f"{failed} source unit(s) failed"
        ),
    )


def add_index_counters(
    counters: dict[str, int],
    resolved: ResolvedAnalysisScope,
) -> None:
    """Expose selected/inventory/cache populations on progress and timings."""

    outcome = resolved.source_index.cache
    counters["inventory_modules"] = source_index_inventory_count(
        resolved.source_index.index
    )
    counters["indexed_modules"] = len(resolved.source_index.index.entries)
    counters["primary_modules"] = len(resolved.scope_plan.primary_modules)
    counters["context_modules"] = len(resolved.scope_plan.context_modules)
    counters["source_cache_hits"] = outcome.reused_entries
    counters["source_cache_rebuilt"] = outcome.rebuilt_entries
    counters["source_cache_failed"] = outcome.failed_entries


def run_selected_extraction_backend(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> tuple[ExtractionBundle, ModuleDiscovery]:
    """Run the selected extraction backend and return backend-owned inventory."""

    if context.extraction_backend != "lean":
        context.record_skipped("lean_extraction", "text backend selected")
        return text_extraction_bundle(discovery), discovery

    with context.phase("lean_extraction") as counters:
        bundle = coerce_extraction_bundle(run_lean_extractor(context, discovery))
        modules = merge_module_inventory(discovery.modules, bundle.modules)
        bundle = ExtractionBundle(
            modules=modules,
            declarations=bundle.declarations,
            counters=bundle.counters,
            diagnostics=bundle.diagnostics,
            runtime=bundle.runtime,
            audit_queries=bundle.audit_queries,
        )
        discovery = discovery_with_modules(discovery, bundle.modules)
        context.retained_discovery = discovery
        context.retained_modules = dict(bundle.modules)
        context.lean_audit_queries = dict(bundle.audit_queries)
        declarations = bundle.declarations or {}
        context.lean_runtime = lean_extraction_phase_data(discovery, bundle)
        counters["modules"] = len(bundle.modules)
        counters["declarations"] = len(declarations)
        counters.update(bundle.counters)
        if int(bundle.counters.get("failed", 0)) or bundle.diagnostics:
            context.mark_phase_partial(
                "lean_extraction",
                lean_partial_reason(bundle),
            )
    return bundle, discovery


def lean_partial_reason(bundle: ExtractionBundle) -> str:
    """Return the first stable helper diagnostic controlling partial state."""

    diagnostics = [row for row in bundle.diagnostics if isinstance(row, Mapping)]
    if not diagnostics:
        failed = int(bundle.counters.get("failed", 0))
        return f"Lean extraction reported {failed} failed module record(s)"
    first = diagnostics[0]
    identifier = str(first.get("id", "lean.partial"))
    subject = str(first.get("subject", "")).strip()
    message = str(first.get("message", "")).strip() or (
        "Lean extraction returned incomplete evidence"
    )
    location = f" for {subject}" if subject else ""
    return f"{identifier}{location}: {message}"


def lean_extraction_phase_data(
    discovery: ModuleDiscovery,
    bundle: ExtractionBundle,
) -> dict[str, Any]:
    """Return report-v2 owner data for runtime and discovery evidence."""

    return {
        **bundle.runtime,
        "diagnostics": list(bundle.diagnostics),
        "discovery": {
            "status": discovery.discovery_status,
            "sourceRoots": list(discovery.source_roots),
            "diagnostics": list(discovery.diagnostics),
        },
    }


def coerce_extraction_bundle(
    extracted: ExtractionBundle | dict[str, LeanModule],
) -> ExtractionBundle:
    """Accept legacy module maps from tests while preferring bundles."""

    if isinstance(extracted, ExtractionBundle):
        return extracted
    modules = adapt_modules(extracted)
    return ExtractionBundle(
        modules=modules,
        declarations=declarations_from_modules(modules),
    )


def declarations_from_modules(
    modules: Mapping[str, LeanModule],
) -> dict[str, LeanDeclaration]:
    """Create declaration rows without references from module declaration names."""

    return {
        declaration_name: LeanDeclaration(
            name=declaration_name,
            module=module.name,
            source_path=module.path,
            extraction_backend="text_inventory",
            name_resolution_method="module_declaration_inventory",
            confidence="derived",
        )
        for module in modules.values()
        for declaration_name in module.declarations
    }


def reference_inventory_names(
    modules: Mapping[str, LeanModule],
) -> tuple[str, ...]:
    """Return declaration names known from text or helper module inventory."""

    names = {
        variant
        for module in modules.values()
        for declaration in module.declarations
        for variant in declaration_name_variants(declaration)
    }
    return tuple(sorted(names))


def declaration_name_variants(declaration: str) -> tuple[str, str]:
    """Return full and basename variants for one declaration name."""

    return declaration, declaration.rsplit(".", 1)[-1]


def declaration_roots_for_modules(
    module_names: Sequence[str],
    declarations: Mapping[str, LeanDeclaration],
) -> tuple[str, ...]:
    """Use non-compiler declarations in each selected module as review roots."""

    selected = set(module_names)
    return tuple(
        name
        for name, declaration in sorted(declarations.items())
        if declaration.module in selected and declaration.compiler_generated is not True
    )


def analysis_module_roots(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> tuple[str, ...]:
    """Return explicit graph-navigation roots without using the report anchor."""

    plan = context.scope_plan
    if plan is None:
        # Compatibility for legacy callers that construct a discovery directly.
        return (discovery.analysis_root_module,)
    if plan.scope_kind == "inventory":
        return tuple(sorted(plan.resolved_navigation_roots))
    selected = set(discovery.modules)
    selection_roots = plan.resolved_selection_roots or plan.resolved_roots
    return tuple(root for root in sorted(selection_roots) if root in selected)


def discovery_with_modules(
    discovery: ModuleDiscovery,
    modules: dict[str, LeanModule],
) -> ModuleDiscovery:
    """Return an immutable discovery record with backend-selected modules."""

    return ModuleDiscovery(
        repo_root=discovery.repo_root,
        analysis_root_file=discovery.analysis_root_file,
        analysis_root_module=discovery.analysis_root_module,
        inventory_root=discovery.inventory_root,
        modules=modules,
        discovery_status=discovery.discovery_status,
        diagnostics=discovery.diagnostics,
        source_roots=discovery.source_roots,
    )


def count_declarations(modules: Mapping[str, LeanModule]) -> int:
    """Count declarations in a backend-normalized module map."""

    return sum(len(module.declarations) for module in modules.values())


def run_lean_extractor(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> ExtractionBundle | dict[str, LeanModule]:
    """Run the configured Lean extractor or the bundled parser-helper backend."""

    extractor = context.lean_extractor or default_lean_extractor
    return extractor(context, discovery)


def default_lean_extractor(
    context: RunContext,
    discovery: ModuleDiscovery,
) -> ExtractionBundle:
    """Run parser extraction, then add bounded Lean-elaborated surfaces."""

    parser_bundle = extract_with_lean_helper(
        discovery,
        scope=context.lean_extraction_scope,
        cache_dir=context.lean_cache_dir,
        batch_size=context.lean_batch_size,
        timeout_seconds=context.lean_helper_timeout_seconds,
        strict=context.lean_strict,
        cancel_event=context.cancel_event,
        build_requested=context.build_requested,
    )
    return augment_with_elaborated_surfaces(
        discovery,
        parser_bundle,
        scope=context.lean_extraction_scope,
        timeout_seconds=context.lean_helper_timeout_seconds,
        cancel_event=context.cancel_event,
    )
