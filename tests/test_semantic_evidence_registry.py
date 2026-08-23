from __future__ import annotations

import copy
import os
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from support.proofir_v3_native import check_run_artifact, environment_artifact

from ladon import _semantic_evidence_registry_sqlite as registry_sqlite
from ladon.proofir_v3 import detached_content_id, validate_envelope_batch
from ladon.semantic_evidence_registry import (
    REGISTRY_APPLICATION_ID,
    REGISTRY_SCHEMA_VERSION,
    SemanticEvidenceRegistry,
    SemanticEvidenceRegistryBusy,
    SemanticEvidenceRegistryConflict,
    SemanticEvidenceRegistryNotFound,
    SemanticEvidenceRegistrySchemaError,
    default_semantic_evidence_registry_path,
)

_DATABASE_LIMIT = 4 * 1024 * 1024


def _semantic_artifacts(*, check_digit: str = "1") -> tuple[dict[str, Any], dict[str, Any]]:
    environment = environment_artifact()
    check = copy.deepcopy(check_run_artifact())
    check["environmentRef"] = environment["environmentRef"]
    check["payload"]["inputs"]["environmentRef"] = environment["environmentRef"]
    check["payload"]["inputs"]["artifactRefs"] = [environment["artifactId"]]
    check["payload"]["checkRunId"] = "check:" + check_digit * 64
    check["payload"]["outputs"]["stdoutDigest"] = "sha256:" + check_digit * 64
    check["artifactId"] = detached_content_id(check)
    validate_envelope_batch([environment, check])
    return environment, check


def _registry(path: Path, *, busy_timeout_ms: int = 5_000) -> SemanticEvidenceRegistry:
    return SemanticEvidenceRegistry(
        path,
        max_database_bytes=_DATABASE_LIMIT,
        busy_timeout_ms=busy_timeout_ms,
    )


def _counts(path: Path) -> tuple[int, int, int]:
    with sqlite3.connect(path) as connection:
        return tuple(
            int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            for table in ("artifacts", "environments", "typed_refs")
        )


def test_registry_uses_explicit_private_wal_database_with_finite_page_cap(
    tmp_path: Path,
) -> None:
    path = tmp_path / "external-cache" / "semantic-evidence.sqlite"
    _registry(path)

    assert path.is_file()
    assert os.stat(path).st_mode & 0o777 == 0o600
    status = _registry(path).inspect()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone() == ("wal",)
        assert connection.execute("PRAGMA application_id").fetchone() == (REGISTRY_APPLICATION_ID,)
        assert connection.execute("PRAGMA user_version").fetchone() == (REGISTRY_SCHEMA_VERSION,)
    assert status["journalMode"] == "wal"
    assert status["synchronous"] == 2
    assert status["foreignKeys"] is True
    assert status["pageSize"] * status["maxPageCount"] <= _DATABASE_LIMIT


def test_bundle_registration_is_atomic_idempotent_and_deduplicates_environment(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, first_check = _semantic_artifacts(check_digit="1")
    _same_environment, second_check = _semantic_artifacts(check_digit="2")

    first = registry.register_bundle([environment, first_check, second_check])
    second = registry.register_bundle([environment, first_check, second_check])

    assert len(first["insertedArtifactRefs"]) == 3
    assert first["existingArtifactRefs"] == []
    assert second["insertedArtifactRefs"] == []
    assert len(second["existingArtifactRefs"]) == 3
    assert _counts(registry.path) == (3, 1, 4)
    assert first["environmentRefs"] == [environment["environmentRef"]]
    expected_refs = [
        {
            "artifactRef": first_check["artifactId"],
            "kind": "check-run",
            "localId": first_check["payload"]["checkRunId"],
        },
        {
            "artifactRef": second_check["artifactId"],
            "kind": "check-run",
            "localId": second_check["payload"]["checkRunId"],
        },
    ]
    assert first["checkRunRefs"] == sorted(expected_refs, key=lambda row: row["artifactRef"])


def test_check_can_reference_previously_registered_environment(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    registry.register_bundle([environment])

    result = registry.register_bundle([check])

    assert result["insertedArtifactRefs"] == [check["artifactId"]]
    assert _counts(registry.path) == (2, 1, 2)
    assert registry.resolve_environment(environment["environmentRef"]) == environment
    assert registry.resolve_artifact(check["artifactId"]) == check


def test_payload_check_identity_resolves_without_a_check_subject_descriptor(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    assert not any(row["kind"] == "check-run" for row in check["subjectRefs"])
    result = registry.register_bundle([environment, check])
    reference = result["checkRunRefs"][0]

    resolved = registry.resolve_typed_ref(reference)

    assert resolved["reference"] == reference
    assert resolved["sourcePointer"] == "/payload/checkRunId"
    assert resolved["artifact"] == check


def test_typed_resolution_rejects_tampered_cached_source_pointer(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    result = registry.register_bundle([environment, check])
    with sqlite3.connect(registry.path) as connection:
        connection.execute(
            "UPDATE typed_refs SET source_pointer='/tampered' "
            "WHERE artifact_ref=? AND kind='check-run'",
            (check["artifactId"],),
        )

    with pytest.raises(SemanticEvidenceRegistryConflict, match="projection is inconsistent"):
        registry.resolve_typed_ref(result["checkRunRefs"][0])


def test_dangling_input_reference_rolls_back_complete_bundle(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    check["payload"]["inputs"]["artifactRefs"] = ["sha256:" + "9" * 64]
    check["artifactId"] = detached_content_id(check)

    with pytest.raises(SemanticEvidenceRegistryNotFound):
        registry.register_bundle([environment, check])

    assert _counts(registry.path) == (0, 0, 0)


def test_unregistered_environment_rolls_back_check(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    _environment, check = _semantic_artifacts()
    check["payload"]["inputs"]["artifactRefs"] = []
    check["environmentRef"] = "sha256:" + "f" * 64
    check["payload"]["inputs"]["environmentRef"] = check["environmentRef"]
    check["artifactId"] = detached_content_id(check)

    with pytest.raises(SemanticEvidenceRegistryNotFound):
        registry.register_bundle([check])

    assert _counts(registry.path) == (0, 0, 0)


def test_conflicting_stored_bytes_are_never_treated_as_an_idempotent_hit(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, _check = _semantic_artifacts()
    registry.register_bundle([environment])
    with sqlite3.connect(registry.path) as connection:
        connection.execute(
            "UPDATE artifacts SET canonical_json='{}',canonical_byte_count=2 WHERE artifact_ref=?",
            (environment["artifactId"],),
        )

    with pytest.raises(SemanticEvidenceRegistryConflict):
        registry.register_bundle([environment])
    with pytest.raises(SemanticEvidenceRegistryConflict):
        registry.resolve_artifact(environment["artifactId"])


def test_typed_resolution_requires_exact_owner_kind_and_local_id(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    registry.register_bundle([environment, check])

    with pytest.raises(SemanticEvidenceRegistryNotFound):
        registry.resolve_typed_ref(
            {
                "artifactRef": environment["artifactId"],
                "kind": "check-run",
                "localId": check["payload"]["checkRunId"],
            }
        )
    with pytest.raises(ValueError, match="artifactRef, kind, and localId"):
        registry.resolve_typed_ref({"artifactRef": check["artifactId"]})


def test_check_resolution_revalidates_its_registered_environment(tmp_path: Path) -> None:
    registry = _registry(tmp_path / "semantic.sqlite")
    environment, check = _semantic_artifacts()
    result = registry.register_bundle([environment, check])
    with sqlite3.connect(registry.path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute(
            "DELETE FROM environments WHERE environment_ref=?",
            (environment["environmentRef"],),
        )

    with pytest.raises(SemanticEvidenceRegistryConflict, match="environment"):
        registry.resolve_typed_ref(result["checkRunRefs"][0])


def test_writer_contention_fails_with_stable_busy_error_and_no_partial_rows(
    tmp_path: Path,
) -> None:
    registry = _registry(tmp_path / "semantic.sqlite", busy_timeout_ms=5)
    environment, _check = _semantic_artifacts()
    blocker = sqlite3.connect(registry.path, isolation_level=None)
    blocker.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(SemanticEvidenceRegistryBusy):
            registry.register_bundle([environment])
    finally:
        blocker.rollback()
        blocker.close()
    assert _counts(registry.path) == (0, 0, 0)


def test_unknown_schema_fails_closed_without_reinitializing_database(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite"
    registry = _registry(path)
    environment, _check = _semantic_artifacts()
    registry.register_bundle([environment])
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version=99")
    before = path.read_bytes()

    with pytest.raises(SemanticEvidenceRegistrySchemaError):
        _registry(path)

    assert path.read_bytes() == before
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM artifacts").fetchone() == (1,)


def test_known_version_schema_spoof_fails_during_open(tmp_path: Path) -> None:
    path = tmp_path / "semantic.sqlite"
    with sqlite3.connect(path, isolation_level=None) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        connection.execute(f"PRAGMA application_id={REGISTRY_APPLICATION_ID}")
        connection.execute(f"PRAGMA user_version={REGISTRY_SCHEMA_VERSION}")
        connection.execute(
            "CREATE TABLE registry_meta("
            "singleton INTEGER PRIMARY KEY, schema_name TEXT, schema_version INTEGER)"
        )
        connection.execute(
            "INSERT INTO registry_meta VALUES(1,'ladon-semantic-evidence-registry-v1',1)"
        )
        for table in ("artifacts", "environments", "typed_refs"):
            connection.execute(f"CREATE TABLE {table}(lookalike TEXT)")

    with pytest.raises(SemanticEvidenceRegistrySchemaError, match="structure"):
        _registry(path)


def test_unsupported_sqlite_fails_lazily_with_stable_schema_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "semantic.sqlite"
    registry_sqlite._expected_schema_fingerprint.cache_clear()
    monkeypatch.setattr(registry_sqlite.sqlite3, "sqlite_version_info", (3, 36, 0))
    monkeypatch.setattr(registry_sqlite.sqlite3, "sqlite_version", "3.36.0")

    try:
        with pytest.raises(
            SemanticEvidenceRegistrySchemaError,
            match=r"requires SQLite 3\.37\.0 or newer",
        ):
            _registry(path)
    finally:
        registry_sqlite._expected_schema_fingerprint.cache_clear()

    assert not path.exists()


def test_known_schema_rejects_altered_index_and_preserves_normal_compatibility(
    tmp_path: Path,
) -> None:
    path = tmp_path / "semantic.sqlite"
    registry = _registry(path)
    environment, check = _semantic_artifacts()
    registry.register_bundle([environment, check])

    reopened = _registry(path)
    assert (
        reopened.resolve_typed_ref(
            {
                "artifactRef": check["artifactId"],
                "kind": "check-run",
                "localId": check["payload"]["checkRunId"],
            }
        )["sourcePointer"]
        == "/payload/checkRunId"
    )

    with sqlite3.connect(path) as connection:
        connection.execute("DROP INDEX idx_semantic_artifact_environment")
        connection.execute(
            "CREATE INDEX idx_semantic_artifact_environment ON artifacts(artifact_kind)"
        )

    with pytest.raises(SemanticEvidenceRegistrySchemaError, match="structure"):
        _registry(path)


def test_known_schema_requires_persistent_wal_mode(tmp_path: Path) -> None:
    path = tmp_path / "semantic.sqlite"
    _registry(path)
    with sqlite3.connect(path, isolation_level=None) as connection:
        assert connection.execute("PRAGMA journal_mode=DELETE").fetchone() == ("delete",)

    with pytest.raises(SemanticEvidenceRegistrySchemaError, match="pragmas"):
        _registry(path)


def test_registry_rejects_symbolic_link_destination(tmp_path: Path) -> None:
    target = tmp_path / "target.sqlite"
    link = tmp_path / "semantic.sqlite"
    target.write_bytes(b"")
    link.symlink_to(target.name)

    with pytest.raises(Exception, match="must not be a symbolic link"):
        _registry(link)


@pytest.mark.parametrize(
    ("platform", "environ", "relative"),
    [
        ("linux", {"XDG_CACHE_HOME": "/cache"}, Path("/cache/ladon")),
        ("linux", {}, Path("/home/test/.cache/ladon")),
        (
            "win32",
            {"LOCALAPPDATA": "/local"},
            Path("/local/ladon"),
        ),
        ("win32", {}, Path("/home/test/AppData/Local/ladon")),
        ("darwin", {}, Path("/home/test/Library/Caches/ladon")),
    ],
)
def test_default_path_uses_platform_cache_and_repository_scope_without_writes(
    tmp_path: Path,
    platform: str,
    environ: dict[str, str],
    relative: Path,
) -> None:
    repository = tmp_path / "repo"
    other = tmp_path / "other"
    home = Path("/home/test")

    first = default_semantic_evidence_registry_path(
        repository,
        environ=environ,
        platform=platform,
        home=home,
    )
    repeated = default_semantic_evidence_registry_path(
        repository,
        environ=environ,
        platform=platform,
        home=home,
    )
    distinct = default_semantic_evidence_registry_path(
        other,
        environ=environ,
        platform=platform,
        home=home,
    )

    assert first.parent == relative / "semantic-evidence-v1"
    assert first == repeated
    assert first != distinct
    assert first.suffix == ".sqlite"
    assert not repository.exists()
    assert not other.exists()


def test_registry_secures_only_a_newly_created_cache_namespace(tmp_path: Path) -> None:
    new_parent = tmp_path / "new" / "semantic-evidence-v1"
    _registry(new_parent / "registry.sqlite")
    assert os.stat(new_parent).st_mode & 0o777 == 0o700

    existing_parent = tmp_path / "existing"
    existing_parent.mkdir(mode=0o755)
    os.chmod(existing_parent, 0o755)
    _registry(existing_parent / "registry.sqlite")
    assert os.stat(existing_parent).st_mode & 0o777 == 0o755
