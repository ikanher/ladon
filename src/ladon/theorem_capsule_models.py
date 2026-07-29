"""Versioned theorem-capsule artifacts and canonical identity checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


PLAN_SCHEMA = "ladon-theorem-capsule-plan-v1"
CAPSULE_SCHEMA = "ladon-theorem-capsule-v1"
REPLAY_SCHEMA = "ladon-theorem-capsule-replay-v1"
PLAN_PROTOCOL = "ladon-theorem-capsule-stream-v1"
GUARANTEE_LEVEL = "locked_rebuildable_module_prefix"
NONCLAIMS = (
    "The capsule is not claimed to be globally or declaration-level minimal.",
    "External dependencies are locked but are not necessarily vendored for offline use.",
    "Native and operating-system dependencies are not packaged hermetically.",
    "Ladon reports Lean replay evidence and is not an independent proof authority.",
)


class CapsuleError(RuntimeError):
    """Base error for a classified theorem-capsule failure."""


class CapsuleInvocationError(CapsuleError):
    """The caller supplied an invalid theorem-capsule invocation."""


class CapsuleOperationalError(CapsuleError):
    """A repository, toolchain, or filesystem operation could not complete."""


class CapsuleContentError(CapsuleError):
    """A persisted plan or capsule failed its compatibility/integrity contract."""


@dataclass(frozen=True)
class TheoremPlan:
    """One validated, canonical theorem-capsule plan."""

    payload: Mapping[str, Any]

    @property
    def identity(self) -> str:
        return str(self.payload["planIdentity"])

    @property
    def repository(self) -> Mapping[str, Any]:
        return _mapping(self.payload.get("repository"), "plan repository")

    @property
    def target(self) -> Mapping[str, Any]:
        return _mapping(self.payload.get("target"), "plan target")

    @property
    def files(self) -> tuple[Mapping[str, Any], ...]:
        return _mapping_rows(self.payload.get("files"), "plan files")

    @property
    def configuration_files(self) -> tuple[Mapping[str, Any], ...]:
        return _mapping_rows(
            self.payload.get("configurationFiles"),
            "plan configuration files",
        )

    @property
    def eligible(self) -> bool:
        return bool(self.payload.get("eligible"))

    def to_payload(self) -> dict[str, Any]:
        return dict(self.payload)

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(self.payload)

    @classmethod
    def create(cls, payload: Mapping[str, Any]) -> TheoremPlan:
        body = dict(payload)
        body.pop("planIdentity", None)
        body["schema"] = PLAN_SCHEMA
        body["protocolVersion"] = PLAN_PROTOCOL
        body["planIdentity"] = artifact_identity("plan", _plan_identity_body(body))
        return cls.from_payload(body)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> TheoremPlan:
        body = dict(payload)
        if body.get("schema") != PLAN_SCHEMA:
            raise CapsuleContentError("theorem plan schema is unsupported")
        if body.get("protocolVersion") != PLAN_PROTOCOL:
            raise CapsuleContentError("theorem plan protocol is unsupported")
        identity = body.pop("planIdentity", None)
        expected = artifact_identity("plan", _plan_identity_body(body))
        if identity != expected:
            raise CapsuleContentError("theorem plan identity does not match its content")
        body["planIdentity"] = identity
        _validate_plan_shape(body)
        return cls(body)

    @classmethod
    def load(cls, path: Path) -> TheoremPlan:
        return cls.from_payload(load_json_object(path, "theorem plan"))


@dataclass(frozen=True)
class CapsuleManifest:
    """One validated materialized capsule manifest."""

    payload: Mapping[str, Any]

    @property
    def identity(self) -> str:
        return str(self.payload["capsuleIdentity"])

    @property
    def files(self) -> tuple[Mapping[str, Any], ...]:
        return _mapping_rows(self.payload.get("files"), "capsule files")

    @property
    def target(self) -> Mapping[str, Any]:
        return _mapping(self.payload.get("target"), "capsule target")

    def to_payload(self) -> dict[str, Any]:
        return dict(self.payload)

    def to_bytes(self) -> bytes:
        return canonical_json_bytes(self.payload)

    @classmethod
    def create(cls, payload: Mapping[str, Any]) -> CapsuleManifest:
        body = dict(payload)
        body.pop("capsuleIdentity", None)
        body["schema"] = CAPSULE_SCHEMA
        body["capsuleIdentity"] = artifact_identity("capsule", body)
        return cls.from_payload(body)

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> CapsuleManifest:
        body = dict(payload)
        if body.get("schema") != CAPSULE_SCHEMA:
            raise CapsuleContentError("capsule manifest schema is unsupported")
        identity = body.pop("capsuleIdentity", None)
        expected = artifact_identity("capsule", body)
        if identity != expected:
            raise CapsuleContentError(
                "capsule manifest identity does not match its content"
            )
        body["capsuleIdentity"] = identity
        _validate_capsule_shape(body)
        return cls(body)

    @classmethod
    def load(cls, path: Path) -> CapsuleManifest:
        return cls.from_payload(load_json_object(path, "capsule manifest"))


def replay_receipt(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a canonical replay receipt with a self-verifying identity."""

    body = dict(payload)
    body.pop("receiptIdentity", None)
    body["schema"] = REPLAY_SCHEMA
    body["receiptIdentity"] = artifact_identity("replay", body)
    return body


def artifact_identity(kind: str, payload: Mapping[str, Any]) -> str:
    """Hash one canonical artifact body with a typed domain separator."""

    digest = hashlib.sha256()
    digest.update(f"ladon:{kind}:v1\0".encode())
    digest.update(canonical_json_bytes(payload))
    return f"sha256:{digest.hexdigest()}"


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize a JSON mapping with stable UTF-8 bytes."""

    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def sha256_bytes(content: bytes) -> str:
    """Return a prefixed SHA-256 identity for exact bytes."""

    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    """Load one required JSON object with a bounded diagnostic."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleContentError(f"{label} is unreadable: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise CapsuleContentError(f"{label} must be a JSON object: {path}")
    return payload


def _validate_plan_shape(payload: Mapping[str, Any]) -> None:
    target = _mapping(payload.get("target"), "plan target")
    repository = _mapping(payload.get("repository"), "plan repository")
    toolchain = _mapping(payload.get("toolchain"), "plan toolchain")
    semantic = _mapping(payload.get("semanticGraph"), "plan semantic graph")
    build = _mapping(payload.get("buildGraph"), "plan build graph")
    _required_text(payload, "plannerVersion", "theorem plan")
    _required_text(target, "name", "plan target")
    _required_text(target, "module", "plan target")
    _required_text(target, "path", "plan target")
    _required_integer(target, "prefixEndOffset", "plan target")
    _required_text(repository, "sourceInventoryFingerprint", "plan repository")
    _required_text(repository, "layoutFingerprint", "plan repository")
    _required_text(repository, "configurationFingerprint", "plan repository")
    _required_text(repository, "root", "plan repository")
    _required_text(toolchain, "leanVersion", "plan toolchain")
    _required_text(toolchain, "helperVersion", "plan toolchain")
    if toolchain.get("protocolVersion") != PLAN_PROTOCOL:
        raise CapsuleContentError("plan toolchain protocol is unsupported")
    files = _mapping_rows(payload.get("files"), "plan files")
    configuration = _mapping_rows(
        payload.get("configurationFiles"),
        "plan configuration files",
    )
    nodes = _mapping_rows(semantic.get("nodes"), "semantic graph nodes")
    edges = _mapping_rows(semantic.get("edges"), "semantic graph edges")
    _mapping_rows(
        semantic.get("stronglyConnectedComponents"),
        "semantic graph components",
    )
    modules = _mapping_rows(build.get("modules"), "build graph modules")
    _mapping_rows(build.get("edges"), "build graph edges")
    _mapping_rows(build.get("lockedPackages"), "build graph locked packages")
    _required_text(semantic, "closureFingerprint", "semantic graph")
    _required_text(semantic, "helperChecksum", "semantic graph")
    _required_text(build, "moduleDagFingerprint", "build graph")
    if semantic.get("status") != "complete" or build.get("status") != "complete":
        raise CapsuleContentError("theorem plan closure status is incomplete")
    if semantic.get("nodeCount") != len(nodes) or semantic.get("edgeCount") != len(edges):
        raise CapsuleContentError("semantic graph declared counts disagree")
    _validate_unique_paths((*files, *configuration))
    if len(modules) != len({row.get("module") for row in modules}):
        raise CapsuleContentError("build graph contains duplicate modules")
    if payload.get("guaranteeLevel") != GUARANTEE_LEVEL:
        raise CapsuleContentError("theorem plan guarantee level is unsupported")
    if not isinstance(payload.get("eligible"), bool):
        raise CapsuleContentError("theorem plan eligible flag is malformed")
    _validate_target_node(target, nodes)


def _validate_unique_paths(rows: tuple[Mapping[str, Any], ...]) -> None:
    paths = [row.get("path") for row in rows]
    if any(not isinstance(path, str) or not path for path in paths):
        raise CapsuleContentError("theorem plan contains a malformed input path")
    if len(paths) != len(set(paths)):
        raise CapsuleContentError("theorem plan contains duplicate input paths")


def _validate_capsule_shape(payload: Mapping[str, Any]) -> None:
    _required_text(payload, "planIdentity", "capsule manifest")
    _required_text(payload, "status", "capsule manifest")
    if payload.get("guaranteeLevel") != GUARANTEE_LEVEL:
        raise CapsuleContentError("capsule guarantee level is unsupported")
    _mapping(payload.get("target"), "capsule target")
    _mapping_rows(payload.get("files"), "capsule files")


def _validate_target_node(
    target: Mapping[str, Any],
    nodes: tuple[Mapping[str, Any], ...],
) -> None:
    matches = [row for row in nodes if row.get("name") == target.get("name")]
    if len(matches) != 1:
        raise CapsuleContentError(
            "theorem plan semantic graph does not contain one exact target node"
        )
    node = matches[0]
    expected = (
        target.get("kind"),
        target.get("module"),
        target.get("typeFingerprint"),
        target.get("valueFingerprint"),
    )
    observed = (
        node.get("kind"),
        node.get("ownerModule"),
        node.get("typeFingerprint"),
        node.get("valueFingerprint"),
    )
    if observed != expected:
        raise CapsuleContentError(
            "theorem plan target fingerprints disagree with its semantic node"
        )


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CapsuleContentError(f"{label} is malformed")
    return value


def _mapping_rows(value: Any, label: str) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise CapsuleContentError(f"{label} are malformed")
    return tuple(value)


def _required_text(payload: Mapping[str, Any], key: str, label: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise CapsuleContentError(f"{label} {key} is malformed")
    return value


def _required_integer(payload: Mapping[str, Any], key: str, label: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise CapsuleContentError(f"{label} {key} is malformed")
    return value


def _plan_identity_body(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Exclude the diagnostic checkout location from semantic plan identity."""

    body = dict(payload)
    repository = body.get("repository")
    if isinstance(repository, Mapping):
        normalized_repository = dict(repository)
        normalized_repository.pop("root", None)
        body["repository"] = normalized_repository
    return body
