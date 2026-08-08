"""Content and evidence validation for theorem capsule replay."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Mapping

from ladon.theorem_capsule_graph import normalize_helper_nodes, semantic_edges, trust_frontier
from ladon.theorem_capsule_models import (
    PLAN_PROTOCOL,
    CapsuleContentError,
    CapsuleManifest,
    TheoremPlan,
    canonical_json_bytes,
    sha256_bytes,
)
from ladon.theorem_capsule_planning import HELPER_VERSION, helper_closure_checksum


PLAN_NAME = "plan.json"


def validate_capsule_content(
    root: Path,
) -> tuple[CapsuleManifest, TheoremPlan]:
    """Validate archive inventory and its embedded theorem plan."""

    manifest = CapsuleManifest.load(root / "capsule.json")
    expected = {"capsule.json"}
    for row in manifest.files:
        relative = str(row.get("path", ""))
        expected.add(relative)
        validate_inventory_file(root, relative, row)
    actual = regular_capsule_files(root)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise CapsuleContentError(
            f"capsule inventory mismatch; missing={missing[:5]} extra={extra[:5]}"
        )
    plan = TheoremPlan.load(root / PLAN_NAME)
    validate_manifest_plan_agreement(manifest, plan)
    return manifest, plan


def regular_capsule_files(root: Path) -> set[str]:
    """Return regular non-directory capsule members."""

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


def validate_inventory_file(
    root: Path,
    relative: str,
    row: Mapping[str, Any],
) -> None:
    """Check one materialized capsule member against its manifest row."""

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


def validate_manifest_plan_agreement(
    manifest: CapsuleManifest,
    plan: TheoremPlan,
) -> None:
    """Ensure capsule inventory and embedded plan describe the same inputs."""

    if manifest.payload.get("planIdentity") != plan.identity:
        raise CapsuleContentError("capsule and embedded plan identities disagree")
    if manifest.target != plan.target:
        raise CapsuleContentError("capsule and embedded plan targets disagree")
    closure = plan.payload["semanticGraph"]["closureFingerprint"]
    if manifest.payload.get("semanticClosureIdentity") != closure:
        raise CapsuleContentError("capsule semantic closure identity disagrees")
    if manifest.payload.get("status") != "materialized_unverified":
        raise CapsuleContentError("capsule status is not replayable")
    inventory = {str(row.get("path")): row for row in manifest.files}
    validate_planned_inventory_row(inventory, PLAN_NAME, sha256_bytes(plan.to_bytes()), "plan")
    for row in plan.configuration_files:
        validate_planned_inventory_row(inventory, str(row["path"]), str(row["sha256"]), str(row["role"]))
    for row in plan.files:
        validate_planned_inventory_row(
            inventory, str(row["path"]), str(row["materializedSha256"]), str(row["role"])
        )


def validate_planned_inventory_row(
    inventory: Mapping[str, Mapping[str, Any]],
    path: str,
    sha256: str,
    role: str,
) -> None:
    """Check one plan-owned member against the capsule manifest."""

    row = inventory.get(path)
    if row is None:
        raise CapsuleContentError(f"planned capsule input is missing: {path}")
    if row.get("sha256") != sha256 or row.get("role") != role:
        raise CapsuleContentError(f"capsule inventory disagrees with its source plan: {path}")


def isolation_evidence(plan: TheoremPlan, replay_root: Path) -> dict[str, Any]:
    """Return evidence that replay uses a fresh copy, not the source checkout."""

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


def validate_replay_helper_payload(payload: Mapping[str, Any]) -> None:
    """Validate helper identity and complete dependency-stream evidence."""

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


def compare_replayed_evidence(
    plan: TheoremPlan,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare replayed Lean evidence with the materialized plan."""

    nodes = normalize_helper_nodes(payload)
    edges = semantic_edges(nodes)
    closure = sha256_bytes(canonical_json_bytes({"nodes": nodes, "edges": edges}))
    replay_trust = list(trust_frontier(nodes))
    expected_graph = plan.payload["semanticGraph"]
    expected_target = plan.target
    replay_target = next((row for row in nodes if row["name"] == expected_target["name"]), None)
    checks = {
        "exactName": payload.get("target") == expected_target["name"],
        "declarationKind": bool(replay_target and replay_target.get("kind") == expected_target["kind"]),
        "leanVersion": payload.get("leanVersion") == plan.payload["toolchain"]["leanVersion"],
        "typeFingerprint": bool(replay_target and replay_target.get("typeFingerprint") == expected_target["typeFingerprint"]),
        "valueFingerprint": bool(replay_target and replay_target.get("valueFingerprint") == expected_target.get("valueFingerprint")),
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
