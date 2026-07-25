"""Fingerprints, preflight, and terminal records for runset execution."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

from ladon.process_supervisor import ProcessSignal
from ladon.runset_contract import (
    BundleEntry,
    EntryValidity,
    RunsetEntry,
    RunsetManifest,
    RunsetManifestError,
    canonical_json_bytes,
    content_sha256,
)
from ladon.runset_runtime import (
    REUSABLE_ARTIFACTS,
    EventSink,
    ValidityResolver,
)
from ladon.runset_storage import RUNSET_STATE_NAME


DEFAULT_VALIDITY_VERSION = "ladon-runset-default-validity-v1"


def default_validity(entry: RunsetEntry, repository_root: Path) -> EntryValidity:
    """Compute a sound conservative fingerprint without starting target code."""

    inventory = tuple(sorted(repository_root.rglob("*.lean")))
    layout = tuple(
        path
        for name in (
            "lean-toolchain",
            "lakefile.toml",
            "lakefile.lean",
            "lake-manifest.json",
        )
        for path in (repository_root / name,)
        if path.is_file()
    )
    source_index = paths_fingerprint(repository_root, (*layout, *inventory))
    selected = selected_validity_paths(entry, repository_root, inventory)
    input_fingerprint = paths_fingerprint(
        repository_root,
        (*layout, *selected),
        missing_tokens=(entry.root,),
    )
    lean_reason = (
        "aggregate_lean_cache_fingerprint_unavailable"
        if entry.backend == "lean"
        else "backend_does_not_use_lean_cache"
    )
    return EntryValidity(
        input_fingerprint=input_fingerprint,
        source_index_fingerprint=source_index,
        lean_cache_fingerprint=None,
        components={
            "resolver": content_sha256(DEFAULT_VALIDITY_VERSION.encode("utf-8"))
        },
        reuse_unavailable_reasons={"lean-cache": lean_reason},
    )


def resolve_validities(
    manifest: RunsetManifest,
    repository: Path,
    resolver: ValidityResolver,
) -> tuple[dict[str, EntryValidity], dict[str, str]]:
    """Resolve every input before the first target-capable runner call."""

    validities: dict[str, EntryValidity] = {}
    fingerprints: dict[str, str] = {}
    for entry in manifest.execution_order:
        validity = _resolved_entry_validity(entry, repository, resolver)
        dependencies = {
            identifier: fingerprints[identifier]
            for identifier in entry.depends_on
        }
        payload = {
            "dependencies": dependencies,
            "entry": entry.to_payload(),
            "runIdentity": entry.run_identity,
            "runsetExecution": {
                "policy": manifest.policy.to_payload(),
                "repository": manifest.repository,
                "resources": manifest.resources.to_payload(),
            },
            "validity": validity.analysis_payload(),
        }
        validities[entry.identifier] = validity
        fingerprints[entry.identifier] = content_sha256(
            canonical_json_bytes(payload)
        )
    return validities, fingerprints


def _resolved_entry_validity(
    entry: RunsetEntry,
    repository: Path,
    resolver: ValidityResolver,
) -> EntryValidity:
    try:
        validity = resolver(entry, repository)
    except Exception as exc:
        raise RunsetManifestError(
            f"cannot resolve validity for entry {entry.identifier}: {exc}"
        ) from exc
    if not isinstance(validity, EntryValidity):
        raise RunsetManifestError(
            f"validity resolver returned no EntryValidity for {entry.identifier}"
        )
    return validity


def selected_validity_paths(
    entry: RunsetEntry,
    repository: Path,
    inventory: tuple[Path, ...],
) -> tuple[Path, ...]:
    """Select the semantic file population for the conservative resolver."""

    if entry.scope.get("kind") in {"inventory", "multi-root", "changed-set"}:
        return inventory
    resolved_paths = tuple(
        raw
        for raw in entry.scope.get("resolvedPaths", [])
        if isinstance(raw, str)
    )
    if not resolved_paths:
        return inventory
    candidates = [root_candidate(repository, entry.root)]
    for raw in resolved_paths:
        if isinstance(raw, str):
            candidates.append(repository / raw)
    selected: set[Path] = set()
    for candidate in candidates:
        if candidate.is_dir():
            selected.update(candidate.rglob("*.lean"))
        elif candidate.is_file():
            selected.add(candidate)
    return tuple(sorted(selected))


def root_candidate(repository: Path, root: str) -> Path:
    """Resolve either a repository path or a dotted Lean module name."""

    direct = repository / root
    if direct.exists():
        return direct
    module_path = repository / f"{root.replace('.', '/')}.lean"
    return module_path if module_path.exists() else direct


def paths_fingerprint(
    repository: Path,
    paths: tuple[Path, ...],
    *,
    missing_tokens: tuple[str, ...] = (),
) -> str:
    """Stream path/content identities into one stable validity digest."""

    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        try:
            relative = path.relative_to(repository).as_posix()
        except ValueError as exc:
            raise RunsetManifestError(
                f"validity path escapes repository: {path}"
            ) from exc
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        _update_file_digest(digest, path)
    for token in sorted(missing_tokens):
        digest.update(f"requested:{token}\0".encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"


def _update_file_digest(digest: Any, path: Path) -> None:
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    digest.update(b"\0")


def resolved_repository(workspace: Path, repository: str) -> Path:
    """Resolve one manifest repository without allowing workspace escape."""

    resolved = (workspace / repository).resolve()
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise RunsetManifestError("runset repository escapes workspace root") from exc
    if not resolved.is_dir():
        raise RunsetManifestError(
            f"runset repository does not exist or is not a directory: {repository}"
        )
    return resolved


def preflight_destinations(
    manifest: RunsetManifest,
    destination: Path,
    bundle_name: str,
) -> None:
    """Reject control-file collisions and resolved output escapes."""

    reserved = {bundle_name, RUNSET_STATE_NAME}
    collisions = reserved & {entry.output for entry in manifest.entries}
    if collisions:
        raise RunsetManifestError(
            f"runset outputs collide with control files: {sorted(collisions)}"
        )
    for entry in manifest.entries:
        resolved = (destination / entry.output).resolve()
        try:
            resolved.relative_to(destination)
        except ValueError as exc:
            raise RunsetManifestError(
                f"entry {entry.identifier} output escapes bundle directory"
            ) from exc


def reuse_record(
    validity: EntryValidity,
    shared: Mapping[str, Any],
) -> dict[str, Any]:
    """Record exact cache compatibility rather than an inferred hit."""

    rows: dict[str, Any] = {}
    for kind, attribute in REUSABLE_ARTIFACTS.items():
        fingerprint = getattr(validity, attribute)
        unsupported = _unsupported_reuse(validity, kind)
        rows[kind] = {
            "fingerprint": fingerprint,
            "status": (
                unsupported["status"]
                if unsupported is not None
                else ("hit" if kind in shared else "miss")
            ),
        }
        if unsupported is not None:
            rows[kind]["reason"] = unsupported["reason"]
    rows["decision"] = "shared" if shared else "cold"
    return rows


def _unsupported_reuse(
    validity: EntryValidity,
    kind: str,
) -> dict[str, str] | None:
    if kind in validity.reuse_bypass_reasons:
        return {
            "status": "bypassed",
            "reason": validity.reuse_bypass_reasons[kind],
        }
    if kind in validity.reuse_unavailable_reasons:
        return {
            "status": "unavailable",
            "reason": validity.reuse_unavailable_reasons[kind],
        }
    attribute = REUSABLE_ARTIFACTS[kind]
    if getattr(validity, attribute) is None:
        return {
            "status": "unavailable",
            "reason": "fingerprint_unavailable",
        }
    return None


def resume_reuse_record(validity: EntryValidity) -> dict[str, Any]:
    """Identify state/report validation as the reason no runner launched."""

    row = reuse_record(validity, {})
    row["decision"] = "resume-hit"
    for kind in REUSABLE_ARTIFACTS:
        if row[kind]["fingerprint"] is not None:
            row[kind]["status"] = "resume-hit"
    return row


def skipped_record(
    entry: RunsetEntry,
    validity: EntryValidity,
    fingerprint: str,
    reason: str,
) -> BundleEntry:
    """Represent work intentionally not launched."""

    return BundleEntry(
        identifier=entry.identifier,
        run_identity=entry.run_identity,
        root=entry.root,
        scope=entry.scope,
        required=entry.required,
        status="skipped",
        entry_fingerprint=fingerprint,
        validity=validity,
        report=None,
        reuse=reuse_record(validity, {}),
        phase_summary={},
        resource_counters={},
        diagnostics=(diagnostic("runset.entry_skipped", reason),),
    )


def interrupted_record(
    entry: RunsetEntry,
    validity: EntryValidity,
    fingerprint: str,
    reason: str,
    *,
    reuse: Mapping[str, Any] | None = None,
) -> BundleEntry:
    """Represent bounded cancellation before a report outcome returned."""

    return BundleEntry(
        identifier=entry.identifier,
        run_identity=entry.run_identity,
        root=entry.root,
        scope=entry.scope,
        required=entry.required,
        status="interrupted",
        entry_fingerprint=fingerprint,
        validity=validity,
        report=None,
        reuse=reuse or reuse_record(validity, {}),
        phase_summary={},
        resource_counters={},
        diagnostics=(diagnostic("runset.entry_interrupted", reason),),
    )


def failed_record(
    entry: RunsetEntry,
    validity: EntryValidity,
    fingerprint: str,
    identifier: str,
    message: str,
    *,
    reuse: Mapping[str, Any],
) -> BundleEntry:
    """Represent an isolated runner or output-publication failure."""

    return BundleEntry(
        identifier=entry.identifier,
        run_identity=entry.run_identity,
        root=entry.root,
        scope=entry.scope,
        required=entry.required,
        status="failed",
        entry_fingerprint=fingerprint,
        validity=validity,
        report=None,
        reuse=reuse,
        phase_summary={},
        resource_counters={},
        diagnostics=(diagnostic(f"runset.{identifier}", message),),
    )


def diagnostic(identifier: str, message: str) -> dict[str, Any]:
    """Return one stable bundle diagnostic."""

    return {
        "id": identifier,
        "message": message,
        "severity": "error",
    }


def blocked_dependency(
    entry: RunsetEntry,
    records: Mapping[str, BundleEntry],
) -> bool:
    """Whether any declared prerequisite lacks a usable complete report."""

    return any(
        records[identifier].status not in {"complete", "resume-hit"}
        for identifier in entry.depends_on
    )


def stop_reason(
    manifest: RunsetManifest,
    record: BundleEntry,
) -> str | None:
    """Apply required/advisory continuation policy to one terminal record."""

    if record.status == "interrupted":
        return "runset_cancelled"
    if record.status in {"complete", "resume-hit"}:
        return None
    if record.required and manifest.policy.stop_on_required_failure:
        return "required_entry_failed"
    if not record.required and not manifest.policy.continue_on_advisory_failure:
        return "advisory_entry_failed"
    return None


def aggregate_exit_code(records: tuple[BundleEntry, ...]) -> int:
    """Return operational failure only for interruption or required work."""

    if any(record.status == "interrupted" for record in records):
        return 1
    return int(
        any(
            record.required
            and record.status not in {"complete", "resume-hit"}
            for record in records
        )
    )


def exception_reason(exc: BaseException) -> str:
    """Preserve a signal identity while avoiding empty exception diagnostics."""

    if isinstance(exc, ProcessSignal):
        return f"target process interrupted by signal {exc.signum}"
    message = str(exc)
    return message or exc.__class__.__name__


def emit(
    sink: EventSink | None,
    entry: RunsetEntry,
    status: str,
) -> None:
    """Send lifecycle data only to an explicit progress/event destination."""

    if sink is not None:
        sink(
            {
                "entry": entry.identifier,
                "runIdentity": entry.run_identity,
                "status": status,
            }
        )
