"""Checkout-independent Lean replay for materialized theorem capsules."""

from __future__ import annotations

import os
import re
import shutil
import stat
import tarfile
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.theorem_capsule_models import (
    NONCLAIMS,
    PLAN_PROTOCOL,
    CapsuleContentError,
    CapsuleInvocationError,
    CapsuleManifest,
    CapsuleOperationalError,
    TheoremPlan,
    canonical_json_bytes,
    replay_receipt,
    sha256_bytes,
)
from ladon.theorem_capsule_planning import (
    DEFAULT_CAPSULE_HELPER,
    HELPER_VERSION,
    helper_closure_checksum,
    normalize_helper_nodes,
    parse_helper_payload,
    semantic_edges,
    trust_frontier,
)


PROCESS_OUTPUT_LIMIT_BYTES = 16 * 1024 * 1024
MANIFEST_NAME = "capsule.json"
PLAN_NAME = "plan.json"
SUPPORTED_NETWORK_POLICIES = frozenset({"deny", "allow"})
STATUS_CONTENT_INVALID = "content-invalid"
STATUS_ENVIRONMENT_UNAVAILABLE = "environment-unavailable"
STATUS_DEPENDENCY_UNAVAILABLE = "dependency-unavailable"
STATUS_UNSUPPORTED = "unsupported-facet"
STATUS_RESOURCE_LIMIT = "resource-limit"
STATUS_LEAN_REJECTED = "Lean-rejected"
STATUS_IDENTITY_MISMATCH = "identity-mismatch"
STATUS_ISOLATION_VIOLATION = "isolation-violation"
STATUS_VERIFIED = "verified"


def replay_theorem_capsule(
    capsule: Path,
    *,
    timeout_seconds: float = 120.0,
    max_rss_bytes: int | None = None,
    network: str = "deny",
) -> dict[str, Any]:
    """Replay a capsule and return a receipt for success or classified failure."""

    if timeout_seconds <= 0:
        raise CapsuleInvocationError("replay timeout must be positive")
    if max_rss_bytes is not None and max_rss_bytes <= 0:
        raise CapsuleInvocationError("replay RSS limit must be positive")
    if network not in SUPPORTED_NETWORK_POLICIES:
        raise CapsuleInvocationError(f"unsupported replay network policy: {network}")
    try:
        return _replay_validated(
            capsule,
            timeout_seconds,
            max_rss_bytes,
            network,
        )
    except CapsuleContentError as exc:
        return _failure_receipt(
            STATUS_CONTENT_INVALID,
            "content_validation",
            str(exc),
        )
    except OSError as exc:
        return _failure_receipt(
            STATUS_ENVIRONMENT_UNAVAILABLE,
            "environment_setup",
            str(exc),
        )


def _replay_validated(
    capsule: Path,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    network: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ladon-capsule-source-") as source_temp:
        source = _capsule_source(capsule, Path(source_temp))
        manifest, plan = _validate_capsule_content(source)
        with tempfile.TemporaryDirectory(prefix="ladon-capsule-replay-") as replay_temp:
            replay_root = Path(replay_temp) / "repository"
            shutil.copytree(source, replay_root)
            isolation = _isolation_evidence(plan, replay_root)
            if not isolation["passed"]:
                return _receipt(
                    manifest,
                    plan,
                    STATUS_ISOLATION_VIOLATION,
                    stages=[],
                    isolation=isolation,
                    comparisons={},
                )
            return _execute_replay(
                manifest,
                plan,
                replay_root,
                timeout_seconds,
                max_rss_bytes,
                network,
                isolation,
            )


def _capsule_source(capsule: Path, temporary: Path) -> Path:
    path = capsule.resolve()
    if path.is_dir():
        return path
    if not path.is_file():
        raise CapsuleContentError(f"capsule does not exist: {capsule}")
    destination = temporary / "unpacked"
    destination.mkdir()
    _extract_safe_archive(path, destination)
    return destination


def _extract_safe_archive(archive_path: Path, destination: Path) -> None:
    seen: set[str] = set()
    collision_keys: set[str] = set()
    try:
        archive = tarfile.open(archive_path, mode="r:*")
    except (tarfile.TarError, OSError) as exc:
        raise CapsuleContentError(f"capsule archive is unreadable: {exc}") from exc
    with archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                raise CapsuleContentError(
                    f"capsule archive contains an unsupported entry: {member.name}"
                )
            relative = _safe_relative(member.name)
            _reject_archive_collision(relative, seen, collision_keys)
            stream = archive.extractfile(member)
            if stream is None:
                raise CapsuleContentError(
                    f"capsule archive entry is unreadable: {relative}"
                )
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(stream.read())
            output.chmod(0o644)


def _safe_relative(value: str) -> str:
    if not value or "\x00" in value or "\\" in value:
        raise CapsuleContentError(f"capsule path is unsafe: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CapsuleContentError(f"capsule path escapes replay root: {value}")
    return path.as_posix()


def _reject_archive_collision(
    path: str,
    seen: set[str],
    collision_keys: set[str],
) -> None:
    key = unicodedata.normalize("NFC", path).casefold()
    if path in seen or key in collision_keys:
        raise CapsuleContentError(f"capsule archive paths collide: {path}")
    seen.add(path)
    collision_keys.add(key)


def _validate_capsule_content(
    root: Path,
) -> tuple[CapsuleManifest, TheoremPlan]:
    manifest = CapsuleManifest.load(root / MANIFEST_NAME)
    expected = {MANIFEST_NAME}
    for row in manifest.files:
        relative = _safe_relative(str(row.get("path", "")))
        expected.add(relative)
        _validate_inventory_file(root, relative, row)
    actual = _regular_capsule_files(root)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise CapsuleContentError(
            f"capsule inventory mismatch; missing={missing[:5]} extra={extra[:5]}"
        )
    plan = TheoremPlan.load(root / PLAN_NAME)
    _validate_manifest_plan_agreement(manifest, plan)
    return manifest, plan


def _regular_capsule_files(root: Path) -> set[str]:
    actual: set[str] = set()
    for path in root.rglob("*"):
        metadata = path.lstat()
        if stat.S_ISDIR(metadata.st_mode):
            continue
        relative = path.relative_to(root).as_posix()
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise CapsuleContentError(
                f"capsule contains an unsupported filesystem entry: {relative}"
            )
        actual.add(relative)
    return actual


def _validate_inventory_file(
    root: Path,
    relative: str,
    row: Mapping[str, Any],
) -> None:
    path = root / relative
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapsuleContentError(f"capsule file is missing: {relative}") from exc
    if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
        raise CapsuleContentError(f"capsule entry is not a regular file: {relative}")
    content = path.read_bytes()
    if sha256_bytes(content) != row.get("sha256"):
        raise CapsuleContentError(f"capsule file hash mismatch: {relative}")
    if len(content) != row.get("bytes"):
        raise CapsuleContentError(f"capsule file size mismatch: {relative}")
    if row.get("mode") != "0644" or stat.S_IMODE(metadata.st_mode) != 0o644:
        raise CapsuleContentError(f"capsule file mode mismatch: {relative}")


def _validate_manifest_plan_agreement(
    manifest: CapsuleManifest,
    plan: TheoremPlan,
) -> None:
    if manifest.payload.get("planIdentity") != plan.identity:
        raise CapsuleContentError("capsule and embedded plan identities disagree")
    if manifest.target != plan.target:
        raise CapsuleContentError("capsule and embedded plan targets disagree")
    closure = plan.payload["semanticGraph"]["closureFingerprint"]
    if manifest.payload.get("semanticClosureIdentity") != closure:
        raise CapsuleContentError("capsule semantic closure identity disagrees")
    if manifest.payload.get("status") != "materialized_unverified":
        raise CapsuleContentError("capsule status is not replayable")
    inventory = {
        str(row.get("path")): row
        for row in manifest.files
    }
    _validate_planned_inventory_row(
        inventory,
        PLAN_NAME,
        sha256_bytes(plan.to_bytes()),
        "plan",
    )
    for row in plan.configuration_files:
        _validate_planned_inventory_row(
            inventory,
            str(row["path"]),
            str(row["sha256"]),
            str(row["role"]),
        )
    for row in plan.files:
        _validate_planned_inventory_row(
            inventory,
            str(row["path"]),
            str(row["materializedSha256"]),
            str(row["role"]),
        )


def _validate_planned_inventory_row(
    inventory: Mapping[str, Mapping[str, Any]],
    path: str,
    sha256: str,
    role: str,
) -> None:
    row = inventory.get(path)
    if row is None:
        raise CapsuleContentError(f"planned capsule input is missing: {path}")
    if row.get("sha256") != sha256 or row.get("role") != role:
        raise CapsuleContentError(
            f"capsule inventory disagrees with its source plan: {path}"
        )


def _isolation_evidence(
    plan: TheoremPlan,
    replay_root: Path,
) -> dict[str, Any]:
    original = Path(str(plan.repository["root"]))
    passed = (
        replay_root.resolve() != original.resolve()
        and not replay_root.resolve().is_relative_to(original.resolve())
        and not original.resolve().is_relative_to(replay_root.resolve())
    )
    return {
        "level": "fresh_copy_sanitized_environment",
        "passed": passed,
        "originalCheckoutReferencedByCommand": False,
        "originalCheckoutReferencedByEnvironment": False,
        "replayRootRole": "fresh_temporary_repository",
    }


def _execute_replay(
    manifest: CapsuleManifest,
    plan: TheoremPlan,
    replay_root: Path,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    network: str,
    isolation: Mapping[str, Any],
) -> dict[str, Any]:
    stages: list[dict[str, Any]] = []
    environment = _replay_environment(network)
    locked_external = _locked_external_imports(plan)
    if network == "allow" and locked_external:
        update = _run_stage(
            ["lake", "update"],
            replay_root,
            timeout_seconds,
            max_rss_bytes,
            environment,
            stage="dependency_resolution",
            display_command=("lake", "update"),
        )
        stages.append(update["row"])
        if update["status"] is not None:
            update_status = (
                STATUS_RESOURCE_LIMIT
                if update["status"] == STATUS_RESOURCE_LIMIT
                else STATUS_DEPENDENCY_UNAVAILABLE
            )
            return _receipt(
                manifest,
                plan,
                update_status,
                stages,
                isolation,
                comparisons={},
            )
    target_module = str(plan.target["module"])
    build = _run_stage(
        ["lake", "build", target_module],
        replay_root,
        timeout_seconds,
        max_rss_bytes,
        environment,
        stage="lean_build",
        display_command=("lake", "build", "<target-module>"),
    )
    stages.append(build["row"])
    if build["status"] is not None:
        status = _classify_build_failure(
            build["status"],
            build["result"],
            locked_external=bool(locked_external),
            network=network,
        )
        return _receipt(
            manifest,
            plan,
            status,
            stages,
            isolation,
            comparisons={},
        )
    helper = _run_replay_helper(
        plan,
        replay_root,
        timeout_seconds,
        max_rss_bytes,
        environment,
    )
    stages.append(helper["row"])
    if helper["status"] is not None:
        return _receipt(
            manifest,
            plan,
            helper["status"],
            stages,
            isolation,
            comparisons={},
        )
    comparisons = _compare_replayed_evidence(plan, helper["payload"])
    status = STATUS_VERIFIED if comparisons["matched"] else STATUS_IDENTITY_MISMATCH
    return _receipt(
        manifest,
        plan,
        status,
        stages,
        isolation,
        comparisons,
    )


def _replay_environment(network: str) -> dict[str, str]:
    allowed = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "HOME", "ELAN_HOME", "LANG", "LC_ALL", "TMPDIR"}
    }
    allowed["GIT_TERMINAL_PROMPT"] = "0"
    allowed["LADON_CAPSULE_REPLAY"] = "1"
    if network == "deny":
        allowed.update(
            {
                "GIT_CONFIG_COUNT": "2",
                "GIT_CONFIG_KEY_0": "url.file:///nonexistent/.insteadOf",
                "GIT_CONFIG_VALUE_0": "https://",
                "GIT_CONFIG_KEY_1": "url.file:///nonexistent/.insteadOf",
                "GIT_CONFIG_VALUE_1": "http://",
            }
        )
    return allowed


def _locked_external_imports(plan: TheoremPlan) -> tuple[str, ...]:
    rows = plan.payload["buildGraph"].get("externalImports", [])
    if not isinstance(rows, list):
        raise CapsuleContentError("plan external imports are malformed")
    return tuple(
        sorted(
            str(row["module"])
            for row in rows
            if isinstance(row, Mapping)
            and row.get("kind") == "locked_external_import"
        )
    )


def _run_stage(
    command: list[str],
    cwd: Path,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    environment: Mapping[str, str],
    *,
    stage: str,
    display_command: tuple[str, ...],
) -> dict[str, Any]:
    result = run_bounded_target_process(
        command,
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        max_output_bytes=PROCESS_OUTPUT_LIMIT_BYTES,
        max_rss_bytes=max_rss_bytes,
        env=environment,
    )
    status = _process_failure_status(result)
    return {
        "status": status,
        "result": result,
        "row": _process_stage_row(stage, display_command, result, cwd),
    }


def _process_failure_status(result: ProcessResult) -> str | None:
    if result.timed_out or result.output_limited or result.memory_limited:
        return STATUS_RESOURCE_LIMIT
    if result.returncode != 0:
        return STATUS_LEAN_REJECTED
    return None


def _classify_build_failure(
    status: str,
    result: ProcessResult,
    *,
    locked_external: bool,
    network: str,
) -> str:
    if status == STATUS_RESOURCE_LIMIT:
        return status
    text = f"{result.stderr}\n{result.stdout}".lower()
    dependency_markers = ("package", "clone", "manifest", "dependency", "unknown module")
    if locked_external and (
        network == "deny" or any(marker in text for marker in dependency_markers)
    ):
        return STATUS_DEPENDENCY_UNAVAILABLE
    return STATUS_LEAN_REJECTED


def _run_replay_helper(
    plan: TheoremPlan,
    replay_root: Path,
    timeout_seconds: float,
    max_rss_bytes: int | None,
    environment: Mapping[str, str],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ladon-capsule-helper-") as temporary:
        modules_file = Path(temporary) / "repository-modules.txt"
        modules_file.write_text(
            "\n".join(
                sorted(
                    str(row["module"])
                    for row in plan.payload["buildGraph"]["modules"]
                )
            )
            + "\n",
            encoding="utf-8",
        )
        result = run_bounded_target_process(
            [
                "lake",
                "env",
                "lean",
                "--run",
                str(DEFAULT_CAPSULE_HELPER),
                str(plan.target["module"]),
                str(plan.target["path"]),
                str(plan.target["name"]),
                str(modules_file),
            ],
            cwd=replay_root,
            timeout_seconds=timeout_seconds,
            max_output_bytes=PROCESS_OUTPUT_LIMIT_BYTES,
            max_rss_bytes=max_rss_bytes,
            env=environment,
        )
    row = _process_stage_row(
        "theorem_query",
        ("lake", "env", "lean", "--run", "<ladon-helper>", "<target>"),
        result,
        replay_root,
    )
    failure = _process_failure_status(result)
    if failure is not None:
        return {"status": failure, "row": row, "payload": None}
    try:
        payload = parse_helper_payload(result.stdout)
        _validate_replay_helper_payload(payload)
    except (CapsuleContentError, CapsuleOperationalError, ValueError) as exc:
        row["diagnostic"] = str(exc)
        return {
            "status": STATUS_ENVIRONMENT_UNAVAILABLE,
            "row": row,
            "payload": None,
        }
    return {"status": None, "row": row, "payload": payload}


def _validate_replay_helper_payload(payload: Mapping[str, Any]) -> None:
    if payload.get("helperVersion") != HELPER_VERSION:
        raise CapsuleContentError("replay helper version is incompatible")
    if payload.get("protocolVersion") != PLAN_PROTOCOL:
        raise CapsuleContentError("replay helper protocol is incompatible")
    if payload.get("status") != "complete" or payload.get("complete") is not True:
        raise CapsuleContentError(
            f"replay helper did not confirm theorem: {payload.get('status')}"
        )
    nodes = payload.get("nodes")
    end = payload.get("endRecord")
    if not isinstance(nodes, list) or not isinstance(end, Mapping):
        raise CapsuleContentError("replay helper completion record is malformed")
    if end.get("kind") != "end" or end.get("nodeCount") != len(nodes):
        raise CapsuleContentError("replay helper dependency stream is incomplete")
    if end.get("checksum") != helper_closure_checksum(nodes):
        raise CapsuleContentError("replay helper dependency checksum disagrees")


def _compare_replayed_evidence(
    plan: TheoremPlan,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    nodes = normalize_helper_nodes(payload)
    edges = semantic_edges(nodes)
    closure = sha256_bytes(canonical_json_bytes({"nodes": nodes, "edges": edges}))
    replay_trust = list(trust_frontier(nodes))
    expected_graph = plan.payload["semanticGraph"]
    expected_target = plan.target
    replay_target = next(
        (row for row in nodes if row["name"] == expected_target["name"]),
        None,
    )
    checks = {
        "exactName": payload.get("target") == expected_target["name"],
        "declarationKind": bool(
            replay_target and replay_target.get("kind") == expected_target["kind"]
        ),
        "leanVersion": payload.get("leanVersion")
        == plan.payload["toolchain"]["leanVersion"],
        "typeFingerprint": bool(
            replay_target
            and replay_target.get("typeFingerprint")
            == expected_target["typeFingerprint"]
        ),
        "valueFingerprint": bool(
            replay_target
            and replay_target.get("valueFingerprint")
            == expected_target.get("valueFingerprint")
        ),
        "semanticClosure": closure == expected_graph["closureFingerprint"],
        "trustFrontier": replay_trust == expected_graph["trustFrontier"],
    }
    return {
        "matched": all(checks.values()),
        "checks": checks,
        "expectedSemanticClosure": expected_graph["closureFingerprint"],
        "replayedSemanticClosure": closure,
        "expectedTrustFrontier": expected_graph["trustFrontier"],
        "replayedTrustFrontier": replay_trust,
    }


def _process_stage_row(
    stage: str,
    command: tuple[str, ...],
    result: ProcessResult,
    replay_root: Path,
) -> dict[str, Any]:
    stdout = _sanitize_output(result.stdout, replay_root)
    stderr = _sanitize_output(result.stderr, replay_root)
    return {
        "stage": stage,
        "command": list(command),
        "returncode": result.returncode,
        "timedOut": result.timed_out,
        "outputLimited": result.output_limited,
        "memoryLimited": result.memory_limited,
        "peakRssBytes": result.peak_rss_bytes,
        "stdoutSha256": sha256_bytes(stdout.encode()),
        "stderrSha256": sha256_bytes(stderr.encode()),
        "stdoutExcerpt": stdout[:1000],
        "stderrExcerpt": stderr[:1000],
    }


def _sanitize_output(value: str, replay_root: Path) -> str:
    sanitized = value.replace(str(replay_root), "<replay-root>")
    sanitized = re.sub(
        r"/tmp/ladon-[^/\s:]+(?:/[^\s:]+)?",
        "<temporary>",
        sanitized,
    )
    home = os.environ.get("HOME")
    if home:
        sanitized = sanitized.replace(home, "<home>")
    sanitized = re.sub(r"\(\d+(?:\.\d+)?m?s\)", "(<duration>)", sanitized)
    return _redact_secrets(sanitized)


def _redact_secrets(value: str) -> str:
    sanitized = re.sub(
        r"(?i)\b(token|password|secret|api[_-]?key)=\S+",
        r"\1=<redacted>",
        value,
    )
    sanitized = re.sub(
        r"(?i)\b(authorization:\s*(?:bearer|basic))\s+\S+",
        r"\1 <redacted>",
        sanitized,
    )
    return re.sub(
        r"(?i)(https?://)[^/\s:@]+:[^/\s@]+@",
        r"\1<redacted>@",
        sanitized,
    )


def _receipt(
    manifest: CapsuleManifest,
    plan: TheoremPlan,
    status: str,
    stages: list[dict[str, Any]],
    isolation: Mapping[str, Any],
    comparisons: Mapping[str, Any],
) -> dict[str, Any]:
    return replay_receipt(
        {
            "status": status,
            "capsuleIdentity": manifest.identity,
            "planIdentity": plan.identity,
            "target": {
                "name": plan.target["name"],
                "module": plan.target["module"],
            },
            "toolchain": dict(plan.payload["toolchain"]),
            "isolation": dict(isolation),
            "stages": stages,
            "comparisons": dict(comparisons),
            "trustFrontier": list(
                plan.payload["semanticGraph"].get("trustFrontier", [])
            ),
            "nonclaims": list(NONCLAIMS),
        }
    )


def _failure_receipt(status: str, stage: str, diagnostic: str) -> dict[str, Any]:
    return replay_receipt(
        {
            "status": status,
            "capsuleIdentity": None,
            "planIdentity": None,
            "target": None,
            "toolchain": None,
            "isolation": {
                "level": "not_started",
                "passed": False,
            },
            "stages": [
                {
                    "stage": stage,
                    "diagnostic": _sanitize_failure_diagnostic(diagnostic)[:2000],
                }
            ],
            "comparisons": {},
            "trustFrontier": [],
            "nonclaims": list(NONCLAIMS),
        }
    )


def _sanitize_failure_diagnostic(value: str) -> str:
    home = os.environ.get("HOME")
    sanitized = value.replace(home, "<home>") if home else value
    sanitized = re.sub(
        r"/(?:tmp|private/tmp)/[^\s:]+",
        "<temporary-path>",
        sanitized,
    )
    return _redact_secrets(sanitized)


__all__ = [
    "STATUS_VERIFIED",
    "replay_theorem_capsule",
]
