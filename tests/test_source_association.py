"""Scratch pytest proposal for the frozen public source-association API.

Imports of the new module are runtime-local so the contract collects before
the producer is implemented.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import ProcessResult
from ladon.proofir_v3 import validate_envelope, validate_envelope_batch
from ladon.result_manifest_io import content_revision
from ladon.result_resolution import resolve_result_manifest
from ladon.semantic_candidate_worker import (
    DEFAULT_HELPER,
    SemanticCandidateRequest,
    _accepted_artifacts,
)

SOURCE = "theorem Owner.target : True := by trivial\n"
OLEAN = b"deterministic whole-module compiled fixture"


def _api():
    from ladon.source_association import (
        SourceAssociationRequest,
        capture_source_association,
    )

    return SourceAssociationRequest, capture_source_association


def _context(root: Path, source: str = SOURCE):
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.33.0\n")
    tools = root / "tools"
    tools.mkdir()
    lake = tools / "lake"
    lean = tools / "lean"
    lake.write_text("#!/bin/sh\nprintf 'Lake version 4.33.0\\n'\n")
    lean.write_text("#!/bin/sh\nprintf 'Lean version 4.33.0\\n'\n")
    lake.chmod(0o755)
    lean.chmod(0o755)
    lib = root / ".lake" / "build" / "lib" / "lean"
    lib.mkdir(parents=True)
    owner_olean = lib / "Owner.olean"
    owner_olean.write_bytes(OLEAN)
    (root / "Owner.lean").write_text(source, encoding="utf-8", newline="")
    return resolve_toolchain_context(
        root,
        lake_path=lake,
        lean_path=lean,
        selection_mode="explicit",
        environment={"PATH": os.defpath, "LANG": "C"},
    ), owner_olean


def _stored_checked_artifacts(root: Path, context: Any) -> list[dict[str, Any]]:
    candidate = "Owner.target"
    request = SemanticCandidateRequest(
        root, "Owner", "True", candidate, toolchain=context,
    )
    payload = {
        "leanVersion": "4.33.0",
        "leanCommit": context.lean_commit or "unknown",
        "executablePath": str(context.lean_path),
        "universePolicy": "lean-level-mvar-succ-zero/v1",
        "importedModules": [{"module": "Owner", "oleanPath": str(owner_path(root))}],
        "probe": {
            "name": "probe",
            "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []",
        },
        "candidate": {
            "name": candidate,
            "typeDisplay": "True",
            "typeStructural": "Lean.Expr.const `True []",
        },
        "localContext": [],
        "substitutions": [],
        "residualPremises": [],
        "dischargedHypotheses": [],
        "applicationTerm": candidate,
    }
    artifacts = _accepted_artifacts(
        request,
        DEFAULT_HELPER,
        ProcessResult((str(context.lean_path),), 0, "", "", 0.01),
        payload,
        helper_identity="sha256:" + "1" * 64,
    )
    validate_envelope_batch(list(artifacts))
    return list(artifacts)


def owner_path(root: Path) -> Path:
    return root / ".lake" / "build" / "lib" / "lean" / "Owner.olean"


def _request(root: Path, context: Any, artifacts: list[dict[str, Any]],
             source_path: str = "Owner.lean", subject_artifact_id: str | None = None,
             **kwargs: Any):
    SourceAssociationRequest, _ = _api()
    owner = next(row for row in artifacts if row["artifactKind"] == "proofir.check-run")
    return SourceAssociationRequest(
        repo_root=root,
        module="Owner",
        source_path=source_path,
        candidate="Owner.target",
        subject_artifact_id=subject_artifact_id or owner["artifactId"],
        toolchain=context,
        **kwargs,
    )


def _ilean(source: str = SOURCE, *, version: Any = 5, module: str = "Owner",
           positions: list[Any] | None = None, name: str = "Owner.target") -> bytes:
    end = len(source.rstrip("\n").encode("utf-16-le")) // 2
    return json.dumps({
        "version": version,
        "module": module,
        "directImports": [],
        "references": {},
        "decls": {name: positions or [0, 0, 0, end, 0, 8, 0, end]},
    }).encode()


def _runner(*, ilean: bytes | None = None, olean: bytes = OLEAN,
            mutate_source: bool = False, mutate_dependency: bool = False,
            timeout: bool = False):
    observed: dict[str, Any] = {}

    def run(command, *, cwd, input_bytes, timeout_seconds, max_output_bytes,
            max_rss_bytes, **_kwargs):
        observed.update(command=tuple(command), input_bytes=input_bytes,
                        timeout_seconds=timeout_seconds, max_output_bytes=max_output_bytes,
                        max_rss_bytes=max_rss_bytes)
        assert input_bytes == (cwd / "Owner.lean").read_bytes()
        if "--setup" in command:
            observed["normalized_setup"] = json.loads(Path(command[command.index("--setup") + 1]).read_text())
        if mutate_source:
            (cwd / "Owner.lean").write_text(SOURCE + "-- changed after snapshot\n", encoding="utf-8")
        if mutate_dependency:
            owner_path(cwd).write_bytes(b"changed stored dependency")
        if "-o" in command:
            Path(command[command.index("-o") + 1]).write_bytes(olean)
        if ilean is not None and "-i" in command:
            Path(command[command.index("-i") + 1]).write_bytes(ilean)
        return ProcessResult(tuple(command), 0 if not timeout else -9, "", "",
                             0.1, timed_out=timeout, peak_rss_bytes=1024)

    run.observed = observed
    return run


def _manifest(owner: dict[str, Any], environment: dict[str, Any], source_digest: str):
    fixture = Path(__file__).parent / "fixtures" / "result_manifest" / "finite-map.json"
    manifest = json.loads(fixture.read_text())
    declaration = next(s for s in owner["subjectRefs"] if s["kind"] == "declaration")
    target = manifest["targets"][0]
    target.update(
        name="Owner.target",
        typeText="True",
        source={"path": "Owner.lean", "digest": source_digest, "projectRevision": "fixture"},
        environment={"toolchain": "leanprover/lean4:v4.33.0", "digest": owner["environmentRef"]},
        subjectRef={"artifactId": owner["artifactId"], "subjectId": declaration["localId"]},
    )
    for row in manifest["targets"]:
        row["revision"] = content_revision("target", row)
    manifest["revision"] = content_revision("manifest", manifest)
    return manifest


def _associated(result: dict[str, Any]) -> dict[str, Any]:
    assert result["schema"] == "ladon-source-association-v1"
    assert result["operation"] == "source-compiled-coherence"
    assert result["status"] == "associated", result
    assert len(result["artifacts"]) == 1
    source_map = result["artifacts"][0]
    assert source_map["artifactKind"] == "proofir.source-map"
    validate_envelope(source_map)
    return source_map


def test_public_api_emits_canonical_map_that_resolves_unchanged(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    owner = next(row for row in artifacts if row["artifactKind"] == "proofir.check-run")
    source_bytes = (tmp_path / "Owner.lean").read_bytes()
    runner = _runner(ilean=_ilean())

    result = capture(_request(tmp_path, context, artifacts), artifacts, process_runner=runner)
    source_map = _associated(result)
    _assert_exact_anchor(source_map, owner, source_bytes)
    assert result["nonclaims"]
    _assert_resolved_source(owner, artifacts, source_map)


def _assert_exact_anchor(source_map, owner, source_bytes):
    anchor = source_map["payload"]["anchors"][0]
    declaration = next(s for s in owner["subjectRefs"] if s["kind"] == "declaration")
    assert anchor["subjectRef"]["artifactRef"] == owner["artifactId"]
    assert anchor["subjectRef"]["localId"] == declaration["localId"]
    assert anchor["declarationFingerprint"] == declaration["fingerprint"]["digest"]
    assert anchor["sourcePath"] == "Owner.lean"
    assert anchor["contentDigest"] == "sha256:" + hashlib.sha256(source_bytes).hexdigest()
    assert source_map["environmentRef"] == owner["environmentRef"]



def _assert_resolved_source(owner, artifacts, source_map):
    anchor = source_map["payload"]["anchors"][0]
    environment = next(row for row in artifacts if row["artifactKind"] == "proofir.environment")
    manifest = _manifest(owner, environment, anchor["contentDigest"])
    resolved = resolve_result_manifest(manifest, [*artifacts, source_map])
    assert resolved["targetResolutions"][0]["status"] == "resolved"
    assert resolved["targetResolutions"][0]["checking"] == "not-assessed"
    assert resolved["targetResolutions"][0]["sourceFreshness"] == "not-assessed"



def test_utf16_positions_convert_using_exact_crlf_and_unicode_source_bytes(tmp_path: Path) -> None:
    _, capture = _api()
    source = "-- 💡\r\ntheorem Owner.target : True := by trivial\r\n"
    context, _ = _context(tmp_path, source=source)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    declaration_line = source.splitlines()[1]
    end_utf16 = len(declaration_line.encode("utf-16-le")) // 2
    ilean = _ilean(
        source,
        positions=[1, 0, 1, end_utf16, 1, 8, 1, end_utf16],
    )
    result = capture(
        _request(tmp_path, context, artifacts), artifacts,
        process_runner=_runner(ilean=ilean),
    )
    anchor = _associated(result)["payload"]["anchors"][0]
    prefix_bytes = len("-- 💡\r\n".encode())
    line_bytes = len(declaration_line.encode("utf-8"))
    assert anchor["start"]["byte"] == prefix_bytes
    assert anchor["end"]["byte"] == prefix_bytes + line_bytes
    assert anchor["start"]["line"] == 2 and anchor["start"]["column"] == 1
    assert anchor["end"]["line"] == 2 and anchor["end"]["column"] == len(declaration_line) + 1

def test_compiled_parity_rejects_sibling_source_drift_with_same_candidate_type(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    # The target declaration's identity/type and its .ilean range remain the
    # same; only the freshly compiled complete module differs.
    result = capture(
        _request(tmp_path, context, artifacts), artifacts,
        process_runner=_runner(ilean=_ilean(), olean=b"different sibling changed whole module"),
    )
    assert result["status"] == "stale"
    assert result["artifacts"] == []


def test_source_snapshot_mutation_fails_closed(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(
        _request(tmp_path, context, artifacts), artifacts,
        process_runner=_runner(ilean=_ilean(), mutate_source=True),
    )
    assert result["status"] in {"stale", "failed"}
    assert result["artifacts"] == []


def test_stored_dependency_mutation_fails_closed(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(
        _request(tmp_path, context, artifacts), artifacts,
        process_runner=_runner(ilean=_ilean(), mutate_dependency=True),
    )
    assert result["status"] in {"stale", "failed"}
    assert result["artifacts"] == []


@pytest.mark.parametrize("ilean", [None, b"not-json", _ilean(version=4), _ilean(module="Other"),
                                    _ilean(name="Owner.other"),
                                    _ilean(positions=[0, 0, 100, 0, 0, 8, 100, 0])])
def test_missing_wrong_or_out_of_bounds_ilean_fails_closed(tmp_path: Path, ilean: bytes | None) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    result = capture(
        _request(tmp_path, context, artifacts), artifacts,
        process_runner=_runner(ilean=ilean),
    )
    assert result["status"] in {"unavailable", "stale", "failed"}
    assert result["artifacts"] == []




def test_malformed_or_wrong_selected_owner_artifacts_fail_before_launch(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    runner = _runner(ilean=_ilean())
    malformed = copy.deepcopy(artifacts)
    malformed[0]["artifactId"] = "sha256:" + "0" * 64
    rejected = capture(_request(tmp_path, context, artifacts), malformed, process_runner=runner)
    assert rejected["status"] in {"unavailable", "failed"}
    assert rejected["artifacts"] == []
    assert not runner.observed

    environment = next(row for row in artifacts if row["artifactKind"] == "proofir.environment")
    wrong_owner = _request(
        tmp_path, context, artifacts, subject_artifact_id=environment["artifactId"],
    )
    rejected = capture(wrong_owner, artifacts, process_runner=runner)
    assert rejected["status"] in {"unavailable", "failed"}
    assert rejected["artifacts"] == []


def test_selected_executable_identity_change_fails_before_launch(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    context.lean_path.write_text("#!/bin/sh\nprintf 'Lean version 4.33.0\\n'\nprintf changed\n")
    context.lean_path.chmod(0o755)
    runner = _runner(ilean=_ilean())
    result = capture(_request(tmp_path, context, artifacts), artifacts, process_runner=runner)
    assert result["status"] in {"unavailable", "stale", "failed"}
    assert result["artifacts"] == []
    assert not runner.observed

def test_source_symlink_escape_fails_before_publication(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    outside = tmp_path.parent / (tmp_path.name + "-outside.lean")
    outside.write_text(SOURCE, encoding="utf-8")
    owner_source = tmp_path / "Owner.lean"
    owner_source.unlink()
    owner_source.symlink_to(outside)
    runner = _runner(ilean=_ilean())
    result = capture(
        _request(tmp_path, context, artifacts), artifacts, process_runner=runner,
    )
    assert result["status"] in {"unavailable", "stale", "failed"}
    assert result["artifacts"] == []
    outside.unlink()


def test_malformed_setup_and_unknown_profile_fields_fail_before_launch(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    setup = tmp_path / "unknown.json"
    setup.write_text(json.dumps({
        "name": "Owner", "package": "fixture", "isModule": False,
        "options": {}, "importArts": {}, "plugins": [], "dynlibs": [],
        "surprise": True,
    }))
    runner = _runner(ilean=_ilean())
    result = capture(
        _request(tmp_path, context, artifacts, setup_path=setup.name), artifacts,
        process_runner=runner,
    )
    assert result["status"] in {"unavailable", "failed"}
    assert result["artifacts"] == []
    assert not runner.observed

def test_supplied_importarts_are_removed_but_plugins_and_dynlibs_are_rejected(tmp_path: Path) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)
    setup = tmp_path / "setup.json"
    setup.write_text(json.dumps({
        "name": "Owner", "package": "fixture", "isModule": False,
        "options": {"autoImplicit": False},
        "importArts": {"Owner": "/untrusted/Owner.olean"},
        "plugins": [], "dynlibs": [],
    }))
    runner = _runner(ilean=_ilean())
    result = capture(
        _request(tmp_path, context, artifacts, setup_path="setup.json"), artifacts,
        process_runner=runner,
    )
    _associated(result)
    normalized = runner.observed["normalized_setup"]
    assert normalized["importArts"] == {}
    assert normalized["plugins"] == [] and normalized["dynlibs"] == []

    for field in ("plugins", "dynlibs"):
        rejected = tmp_path / f"bad-{field}.json"
        rejected.write_text(json.dumps({
            "name": "Owner", "package": "fixture", "isModule": False,
            "options": {}, "importArts": {}, field: ["untrusted-entry"],
        }))
        never_launched = _runner(ilean=_ilean())
        failed = capture(
            _request(tmp_path, context, artifacts, setup_path=rejected.name), artifacts,
            process_runner=never_launched,
        )
        assert failed["status"] in {"unavailable", "failed"}
        assert failed["artifacts"] == []
        assert not never_launched.observed


@pytest.mark.parametrize("outcome,status", [
    ("timeout", "timeout"),
    ("memory", "memory-limited"),
    ("output", "output-limited"),
])
def test_bounded_process_outcomes_never_publish_a_map(tmp_path: Path, outcome: str, status: str) -> None:
    _, capture = _api()
    context, _ = _context(tmp_path)
    artifacts = _stored_checked_artifacts(tmp_path, context)

    def run(command, *, cwd, input_bytes, timeout_seconds, max_output_bytes,
            max_rss_bytes, **_kwargs):
        assert input_bytes == (cwd / "Owner.lean").read_bytes()
        return ProcessResult(
            tuple(command), -9, "", "", 0.1,
            timed_out=outcome == "timeout",
            memory_limited=outcome == "memory",
            output_limited=outcome == "output",
            peak_rss_bytes=max_rss_bytes,
        )

    result = capture(_request(tmp_path, context, artifacts), artifacts, process_runner=run)
    assert result["status"] == status
    assert result["artifacts"] == []
