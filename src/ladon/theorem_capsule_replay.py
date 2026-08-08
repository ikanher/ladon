"""Checkout-independent Lean replay for materialized theorem capsules."""

from __future__ import annotations

import os
import re
import shutil
import stat
import tarfile
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from ladon.process_supervisor import ProcessResult, run_bounded_target_process
from ladon.theorem_capsule_models import (
    NONCLAIMS,
    CapsuleContentError,
    CapsuleInvocationError,
    CapsuleManifest,
    CapsuleOperationalError,
    TheoremPlan,
    replay_receipt,
    sha256_bytes,
)
from ladon.theorem_capsule_planning import (
    DEFAULT_CAPSULE_HELPER,
    parse_helper_payload,
)
from ladon.theorem_capsule_replay_validation import (
    compare_replayed_evidence,
    isolation_evidence,
    validate_capsule_content,
    validate_replay_helper_payload,
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
        manifest, plan = validate_capsule_content(source)
        with tempfile.TemporaryDirectory(prefix="ladon-capsule-replay-") as replay_temp:
            replay_root = Path(replay_temp) / "repository"
            shutil.copytree(source, replay_root)
            isolation = isolation_evidence(plan, replay_root)
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
    if zipfile.is_zipfile(archive_path):
        _extract_safe_zip(archive_path, destination)
        return
    _extract_safe_tar(archive_path, destination)


def _extract_safe_tar(archive_path: Path, destination: Path) -> None:
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


def _extract_safe_zip(archive_path: Path, destination: Path) -> None:
    seen: set[str] = set()
    collision_keys: set[str] = set()
    try:
        archive = zipfile.ZipFile(archive_path, mode="r")
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError) as exc:
        raise CapsuleContentError(f"capsule archive is unreadable: {exc}") from exc
    with archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            if member.flag_bits & 0x1:
                raise CapsuleContentError(
                    f"capsule archive contains an encrypted entry: {member.filename}"
                )
            mode = member.external_attr >> 16
            file_type = stat.S_IFMT(mode)
            if file_type not in {0, stat.S_IFREG}:
                raise CapsuleContentError(
                    f"capsule archive contains an unsupported entry: {member.filename}"
                )
            relative = _safe_relative(member.filename)
            _reject_archive_collision(relative, seen, collision_keys)
            try:
                content = archive.read(member)
            except (RuntimeError, zipfile.BadZipFile, OSError) as exc:
                raise CapsuleContentError(
                    f"capsule archive entry is unreadable: {relative}"
                ) from exc
            output = destination / relative
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(content)
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
    comparisons = compare_replayed_evidence(plan, helper["payload"])
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
            if isinstance(row, Mapping) and row.get("kind") == "locked_external_import"
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
    dependency_markers = (
        "package",
        "clone",
        "manifest",
        "dependency",
        "unknown module",
    )
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
                    str(row["module"]) for row in plan.payload["buildGraph"]["modules"]
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
        validate_replay_helper_payload(payload)
    except (CapsuleContentError, CapsuleOperationalError, ValueError) as exc:
        row["diagnostic"] = str(exc)
        return {
            "status": STATUS_ENVIRONMENT_UNAVAILABLE,
            "row": row,
            "payload": None,
        }
    return {"status": None, "row": row, "payload": payload}


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
