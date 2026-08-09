"""Frozen contract for ProofIR's owned, immutable identity value types."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from ladon import proofir_identity


def _type(name: str) -> type[Any]:
    result = getattr(proofir_identity, name, None)
    assert result is not None, f"proofir_identity.{name} is missing"
    return result


def _environment_source() -> dict[str, Any]:
    return {
        "prover": {"name": "Lean", "version": "4.20.0"},
        "toolchain": {
            "name": "elan",
            "version": "1.0",
            "commit": "abc123",
        },
        "dependencies": [
            {
                "name": "mathlib",
                "version": "v4.20.0",
                "source": "lake-manifest",
                "digest": "sha256:" + "2" * 64,
            }
        ],
        "compiledModules": [{"module": "Fixture.Main", "digest": "sha256:" + "3" * 64}],
        "options": {"autoImplicit": False},
        "trust": {"axiomsAllowed": [], "unsafeAllowed": False},
        "fingerprintScheme": {"name": "lean-expr", "version": "1"},
    }


def test_environment_manifest_is_content_addressed_and_owns_its_input() -> None:
    environment_type = _type("EnvironmentManifest")
    source = _environment_source()
    environment = environment_type.from_dict(source)
    identity = environment.environment_ref

    source["toolchain"]["version"] = "mutated"
    source["compiledModules"][0]["digest"] = "sha256:" + "9" * 64
    assert environment.environment_ref == identity
    assert environment.to_dict()["toolchain"]["version"] == "1.0"
    assert identity.startswith("sha256:") and len(identity) == 71


@pytest.mark.parametrize(
    ("path", "replacement", "message"),
    [
        (("prover", "version"), None, "/prover/version"),
        (("toolchain", "commit"), "", "/toolchain/commit"),
        (("dependencies", 0, "digest"), "not-a-digest", "/dependencies/0/digest"),
        (("compiledModules", 0, "module"), "", "/compiledModules/0/module"),
        (("trust", "unsafeAllowed"), "false", "/trust/unsafeAllowed"),
        (("fingerprintScheme", "version"), "", "/fingerprintScheme/version"),
    ],
)
def test_environment_manifest_rejects_incomplete_nested_identity(
    path: tuple[str | int, ...], replacement: Any, message: str
) -> None:
    source = _environment_source()
    target: Any = source
    for component in path[:-1]:
        target = target[component]
    if replacement is None:
        del target[path[-1]]
    else:
        target[path[-1]] = replacement
    with pytest.raises(ValueError, match=message):
        _type("EnvironmentManifest").from_dict(source)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("prover", "version"), "4.21.0"),
        (("toolchain", "commit"), "def456"),
        (("dependencies", 0, "digest"), "sha256:" + "a" * 64),
        (("compiledModules", 0, "digest"), "sha256:" + "a" * 64),
        (("options", "autoImplicit"), True),
        (("trust", "unsafeAllowed"), True),
        (("fingerprintScheme", "version"), "2"),
    ],
)
def test_environment_identity_changes_with_semantic_inputs(
    path: tuple[str | int, ...], replacement: Any
) -> None:
    environment_type = _type("EnvironmentManifest")
    original = _environment_source()
    changed = copy.deepcopy(original)
    target: Any = changed
    for component in path[:-1]:
        target = target[component]
    target[path[-1]] = replacement
    assert (
        environment_type.from_dict(original).environment_ref
        != environment_type.from_dict(changed).environment_ref
    )


def test_typed_subject_descriptors_keep_identity_separate_from_search_metadata() -> (
    None
):
    fingerprint = _type("Fingerprint")(
        scheme=_type("FingerprintScheme")("lean-expr", "1"),
        digest="sha256:" + "4" * 64,
    )
    descriptor_types = {
        "statement": "StatementDescriptor",
        "declaration": "DeclarationDescriptor",
        "term": "TermDescriptor",
        "local-context": "LocalContextDescriptor",
    }
    for kind, type_name in descriptor_types.items():
        descriptor = _type(type_name)(
            local_id=f"{kind}:one",
            fingerprint=fingerprint,
            display="Human-facing only",
            search_shape={"head": "Fixture.head", "arity": 2},
            opaque_payload_ref="sha256:" + "5" * 64,
        )
        encoded = descriptor.to_dict()
        assert encoded["kind"] == kind
        assert encoded["localId"] == f"{kind}:one"
        assert encoded["fingerprint"]["scheme"] == {
            "name": "lean-expr",
            "version": "1",
        }
        assert encoded["display"] == "Human-facing only"
        assert encoded["searchShape"] == {"head": "Fixture.head", "arity": 2}
        assert encoded["opaquePayloadRef"] == "sha256:" + "5" * 64


def test_local_external_and_qualified_references_have_distinct_closed_shapes() -> None:
    owner = "sha256:" + "6" * 64
    environment = "sha256:" + "7" * 64
    local = _type("LocalSubjectRef")("statement", "statement:goal")
    external = _type("ExternalSubjectRef")(owner, "statement", "statement:goal")
    qualified = _type("QualifiedSubjectRef")(
        owner, environment, "statement", "statement:goal"
    )

    assert local.to_dict() == {"kind": "statement", "localId": "statement:goal"}
    assert external.to_dict() == {
        "artifactRef": owner,
        "kind": "statement",
        "localId": "statement:goal",
    }
    assert qualified.owner_content_artifact_id == owner
    assert qualified.environment_ref == environment
    assert (
        _type("QualifiedSubjectRef")(
            qualified.to_dict()["ownerArtifactId"],
            qualified.to_dict()["environmentRef"],
            qualified.to_dict()["kind"],
            qualified.to_dict()["localId"],
        )
        == qualified
    )
    assert qualified != _type("QualifiedSubjectRef")(
        "sha256:" + "8" * 64,
        environment,
        "statement",
        "statement:goal",
    )


def test_generation_observation_is_distinct_from_stable_content_identity() -> None:
    content = "sha256:" + "9" * 64
    observation_type = _type("GenerationObservation")
    first = observation_type("generation:1", "proofir/a.json", content)
    second = observation_type("generation:2", "proofir/a.json", content)
    relocated = observation_type("generation:1", "proofir/b.json", content)

    assert first.content_artifact_id == second.content_artifact_id == content
    assert (
        len({first.observation_id, second.observation_id, relocated.observation_id})
        == 3
    )


def test_obsolete_environment_bearing_reference_adapters_are_absent() -> None:
    assert not hasattr(proofir_identity, "EnvironmentRef")
    assert not hasattr(proofir_identity, "SubjectRef")


@pytest.mark.parametrize(
    ("type_name", "arguments"),
    [
        ("LocalSubjectRef", ("", "statement:goal")),
        ("LocalSubjectRef", ("statement", "")),
        ("ExternalSubjectRef", ("not-a-digest", "statement", "statement:goal")),
        (
            "QualifiedSubjectRef",
            ("sha256:" + "1" * 64, "not-a-digest", "statement", "statement:goal"),
        ),
        ("GenerationObservation", ("", "proofir/a.json", "sha256:" + "2" * 64)),
        ("GenerationObservation", ("generation:1", "", "sha256:" + "2" * 64)),
        ("GenerationObservation", ("generation:1", "proofir/a.json", "bad")),
    ],
)
def test_identity_values_reject_missing_or_invalid_scope(
    type_name: str, arguments: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        _type(type_name)(*arguments)
