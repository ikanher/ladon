"""Owned content, environment, subject, and generation identities for ProofIR v3."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

from ladon.proofir_v3 import canonical_bytes


def _owned(value: Any) -> Any:
    """Copy through canonical JSON so public values never retain caller containers."""

    return __import__("json").loads(
        canonical_bytes(copy.deepcopy(value)).decode("utf-8")
    )


def _digest(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _closed_string_object(
    value: Any, required: set[str], pointer: str
) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(  # noqa: TRY004
            f"{pointer} must contain exactly {sorted(required)}"
        )
    missing = sorted(required - set(value))
    if missing:
        raise ValueError(f"{pointer}/{missing[0]} is required")
    extra = sorted(set(value) - required)
    if extra:
        raise ValueError(f"{pointer}/{extra[0]} is not supported")
    result = dict(value)
    for key in sorted(required):
        if not isinstance(result[key], str) or not result[key]:
            raise ValueError(f"{pointer}/{key} must be a non-empty string")
    return result


def _validate_environment_manifest(value: Mapping[str, Any]) -> None:
    _closed_string_object(value["prover"], {"name", "version"}, "/prover")
    _closed_string_object(
        value["toolchain"], {"name", "version", "commit"}, "/toolchain"
    )
    _validate_dependencies(value["dependencies"])
    _validate_compiled_modules(value["compiledModules"])
    if not isinstance(value["options"], Mapping):
        raise ValueError("/options must be an object")  # noqa: TRY004
    _validate_trust(value["trust"])
    _closed_string_object(
        value["fingerprintScheme"], {"name", "version"}, "/fingerprintScheme"
    )


def _validate_dependencies(dependencies: Any) -> None:
    if not isinstance(dependencies, list):
        raise ValueError("/dependencies must be an array")  # noqa: TRY004
    for index, dependency in enumerate(dependencies):
        parsed = _closed_string_object(
            dependency,
            {"name", "version", "source", "digest"},
            f"/dependencies/{index}",
        )
        if not _digest(parsed["digest"]):
            raise ValueError(f"/dependencies/{index}/digest must be a sha256 digest")


def _validate_compiled_modules(modules: Any) -> None:
    if not isinstance(modules, list):
        raise ValueError("/compiledModules must be an array")  # noqa: TRY004
    for index, module in enumerate(modules):
        parsed = _closed_string_object(
            module, {"module", "digest"}, f"/compiledModules/{index}"
        )
        if not _digest(parsed["digest"]):
            raise ValueError(f"/compiledModules/{index}/digest must be a sha256 digest")


def _validate_trust(trust: Any) -> None:
    if not isinstance(trust, Mapping) or set(trust) != {
        "axiomsAllowed",
        "unsafeAllowed",
    }:
        raise ValueError("/trust must contain axiomsAllowed and unsafeAllowed")
    if not isinstance(trust["axiomsAllowed"], list) or not all(
        isinstance(axiom, str) and axiom for axiom in trust["axiomsAllowed"]
    ):
        raise ValueError("/trust/axiomsAllowed must be an array of non-empty strings")
    if not isinstance(trust["unsafeAllowed"], bool):
        raise ValueError("/trust/unsafeAllowed must be a boolean")  # noqa: TRY004


def content_id(value: Mapping[str, Any]) -> str:
    """Return a stable detached identity for canonical content."""

    detached = dict(value)
    detached.pop("contentArtifactId", None)
    detached.pop("artifactId", None)
    detached.pop("observationId", None)
    return _hash(detached)


@dataclass(frozen=True)
class EnvironmentManifest:
    """A deeply-owned, content-addressed exact prover environment profile."""

    _value: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "_value", _owned(self._value))

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> EnvironmentManifest:
        required = {
            "prover",
            "toolchain",
            "dependencies",
            "compiledModules",
            "options",
            "trust",
            "fingerprintScheme",
        }
        if set(value) != required:
            raise ValueError("environment manifest must use the closed native profile")
        _validate_environment_manifest(value)
        return cls(_owned(value))

    def to_dict(self) -> dict[str, Any]:
        return _owned(self._value)

    @property
    def environment_ref(self) -> str:
        return _hash(self._value)


@dataclass(frozen=True)
class FingerprintScheme:
    name: str
    version: str

    def __post_init__(self) -> None:
        if not self.name or not self.version:
            raise ValueError("fingerprint scheme name and version must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "version": self.version}


@dataclass(frozen=True)
class Fingerprint:
    scheme: FingerprintScheme
    digest: str

    def __post_init__(self) -> None:
        if not _digest(self.digest):
            raise ValueError("fingerprint digest must be a sha256 digest")

    def to_dict(self) -> dict[str, Any]:
        return {"scheme": self.scheme.to_dict(), "digest": self.digest}


@dataclass(frozen=True)
class _SubjectDescriptor:
    local_id: str
    fingerprint: Fingerprint | None = None
    display: str | None = None
    search_shape: Mapping[str, Any] | None = None
    opaque_payload_ref: str | None = None
    kind: ClassVar[str]
    _search_shape: dict[str, Any] | None = field(init=False, repr=False, compare=True)

    def __post_init__(self) -> None:
        if not self.local_id:
            raise ValueError("subject local ID must be non-empty")
        if self.display is not None and not self.display:
            raise ValueError("subject display must be non-empty when supplied")
        if self.opaque_payload_ref is not None and not _digest(self.opaque_payload_ref):
            raise ValueError("opaque payload reference must be a sha256 digest")
        if self.search_shape is not None:
            object.__setattr__(self, "search_shape", _owned(self.search_shape))
        object.__setattr__(
            self,
            "_search_shape",
            _owned(self.search_shape) if self.search_shape is not None else None,
        )

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"kind": self.kind, "localId": self.local_id}
        if self.fingerprint is not None:
            value["fingerprint"] = self.fingerprint.to_dict()
        if self.display is not None:
            value["display"] = self.display
        if self._search_shape is not None:
            value["searchShape"] = _owned(self._search_shape)
        if self.opaque_payload_ref is not None:
            value["opaquePayloadRef"] = self.opaque_payload_ref
        return value


@dataclass(frozen=True)
class StatementDescriptor(_SubjectDescriptor):
    kind: ClassVar[str] = "statement"


@dataclass(frozen=True)
class DeclarationDescriptor(_SubjectDescriptor):
    kind: ClassVar[str] = "declaration"


@dataclass(frozen=True)
class CandidateApplicationDescriptor(_SubjectDescriptor):
    """Identity of a checked application shape, distinct from its conclusion."""

    kind: ClassVar[str] = "candidate-application"


@dataclass(frozen=True)
class ValueDescriptor(_SubjectDescriptor):
    """Optional declaration-value/proof identity, not declaration identity."""

    kind: ClassVar[str] = "value"


@dataclass(frozen=True)
class TermDescriptor(_SubjectDescriptor):
    kind: ClassVar[str] = "term"


@dataclass(frozen=True)
class LocalContextDescriptor(_SubjectDescriptor):
    kind: ClassVar[str] = "local-context"


@dataclass(frozen=True)
class LocalSubjectRef:
    kind: str
    local_id: str

    def __post_init__(self) -> None:
        if not self.kind or not self.local_id:
            raise ValueError("local subject kind and local ID must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "localId": self.local_id}


@dataclass(frozen=True)
class ExternalSubjectRef:
    owner_content_artifact_id: str
    kind: str
    local_id: str

    def __post_init__(self) -> None:
        if not _digest(self.owner_content_artifact_id):
            raise ValueError("external subject owner must be a sha256 digest")
        if not self.kind or not self.local_id:
            raise ValueError("external subject kind and local ID must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "artifactRef": self.owner_content_artifact_id,
            "kind": self.kind,
            "localId": self.local_id,
        }


@dataclass(frozen=True)
class QualifiedSubjectRef:
    owner_content_artifact_id: str
    environment_ref: str
    kind: str
    local_id: str

    def __post_init__(self) -> None:
        if not _digest(self.owner_content_artifact_id):
            raise ValueError("qualified subject owner must be a sha256 digest")
        if not _digest(self.environment_ref):
            raise ValueError("qualified subject environment must be a sha256 digest")
        if not self.kind or not self.local_id:
            raise ValueError("qualified subject kind and local ID must be non-empty")

    def to_dict(self) -> dict[str, str]:
        return {
            "ownerArtifactId": self.owner_content_artifact_id,
            "environmentRef": self.environment_ref,
            "kind": self.kind,
            "localId": self.local_id,
        }


@dataclass(frozen=True)
class GenerationObservation:
    generation_id: str
    relative_path: str
    content_artifact_id: str

    def __post_init__(self) -> None:
        if not self.generation_id:
            raise ValueError("generation ID must be non-empty")
        if not self.relative_path:
            raise ValueError("relative path must be non-empty")
        if not _digest(self.content_artifact_id):
            raise ValueError("content artifact ID must be a sha256 digest")

    @property
    def observation_id(self) -> str:
        return observation_id(
            generation_id=self.generation_id,
            relative_path=self.relative_path,
            content_artifact_id=self.content_artifact_id,
        )


def observation_id(
    *, generation_id: str, relative_path: str, content_artifact_id: str
) -> str:
    return _hash(
        {
            "generationId": generation_id,
            "path": relative_path,
            "contentArtifactId": content_artifact_id,
        }
    )


__all__ = [
    "CandidateApplicationDescriptor",
    "DeclarationDescriptor",
    "EnvironmentManifest",
    "ExternalSubjectRef",
    "Fingerprint",
    "FingerprintScheme",
    "GenerationObservation",
    "LocalContextDescriptor",
    "LocalSubjectRef",
    "QualifiedSubjectRef",
    "StatementDescriptor",
    "TermDescriptor",
    "ValueDescriptor",
    "content_id",
    "observation_id",
]
