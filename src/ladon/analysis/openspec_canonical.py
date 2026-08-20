"""Canonical OpenSpec postcondition checks for reconciled legacy contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path

RECONCILIATION_CHANGE = "ladon-openspec-state-reconciliation"
ARCHIVE_CHAIN = (
    "ladon-pipeline-phase-boundaries-timing",
    "ladon-clean-core-radon-gate",
    "ladon-root-matrix-lean-expansion",
    "ladon-proof-xray-staging",
    RECONCILIATION_CHANGE,
)
DELTA_REQUIREMENTS = (
    (
        "ladon-pipeline-phase-boundaries-timing",
        "ladon-pipeline",
        "ADDED",
        "Ladon SHALL separate pure analysis kernels from side effects",
    ),
    (
        "ladon-clean-core-radon-gate",
        "ladon-python-quality",
        "ADDED",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
    ),
    (
        "ladon-root-matrix-lean-expansion",
        "ladon-root-matrix",
        "ADDED",
        "Lean-Backed Owner Matrix Entries",
    ),
    (
        RECONCILIATION_CHANGE,
        "ladon-python-quality",
        "MODIFIED",
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
    ),
    (
        RECONCILIATION_CHANGE,
        "ladon-root-matrix",
        "MODIFIED",
        "Lean-Backed Owner Matrix Entries",
    ),
)
NEGATIVE_SKIP_MARKERS = (
    " shall not ",
    " must not ",
    " without ",
    " removed ",
    " omit ",
    " no longer ",
    " does not ",
)


class CanonicalGateError(ValueError):
    """Raised when a required OpenSpec ordering or canonical contract is absent."""


def check_legacy_cli_profile(
    openspec_root: Path,
    *,
    allow_active_delta: bool = False,
    require_canonical: bool = False,
) -> str:
    """Check active reconciliation deltas or their post-archive canonical state."""

    active = openspec_root / "changes" / RECONCILIATION_CHANGE
    if require_canonical:
        check_canonical_state(openspec_root)
        return "canonical"
    if not allow_active_delta:
        raise CanonicalGateError("select --allow-active-delta or --require-canonical")
    if active.is_dir():
        check_active_delta_state(openspec_root)
        return "active-delta"
    check_canonical_state(openspec_root)
    return "canonical"


def check_active_delta_state(openspec_root: Path) -> None:
    """Verify the explicit source-addition and reconciliation delta ordering."""

    ledger = load_json(openspec_root / "reconciliation" / "legacy-state-ledger.json")
    rows = ledger.get("archiveBatches")
    if not isinstance(rows, list):
        raise CanonicalGateError("reconciliation ledger has no archiveBatches list")
    observed = tuple(str(row.get("change") or "") for row in rows if isinstance(row, dict))
    if observed != ARCHIVE_CHAIN:
        raise CanonicalGateError(
            f"archive chain must be {' -> '.join(ARCHIVE_CHAIN)}; observed {' -> '.join(observed)}"
        )
    for change, capability, delta_kind, requirement in DELTA_REQUIREMENTS:
        text = read_change_delta(openspec_root, change, capability)
        require_delta(text, delta_kind, requirement, change, capability)


def check_canonical_state(openspec_root: Path) -> None:
    """Verify reconciliation was uniquely archived and legacy CLI deltas landed."""

    active = openspec_root / "changes" / RECONCILIATION_CHANGE
    if active.exists():
        raise CanonicalGateError(f"active reconciliation packet still exists: {active}")
    archives = archived_change_paths(openspec_root, RECONCILIATION_CHANGE)
    if len(archives) != 1:
        raise CanonicalGateError(
            f"expected one reconciliation archive, found {len(archives)}: "
            f"{[str(path) for path in archives]}"
        )
    python_quality = read_canonical_spec(openspec_root, "ladon-python-quality")
    root_matrix = read_canonical_spec(openspec_root, "ladon-root-matrix")
    require_text(
        python_quality,
        "Ladon's clean core SHALL preserve tested module-DAG reporting",
        "canonical ladon-python-quality requirement",
    )
    require_text(
        python_quality,
        "without `--build`",
        "canonical no-build smoke scenario",
    )
    require_text(
        root_matrix,
        "Lean-Backed Owner Matrix Entries",
        "canonical ladon-root-matrix requirement",
    )
    require_text(
        root_matrix,
        "SHALL NOT include the removed",
        "canonical removed-flag scenario",
    )
    positive_lines = positive_skip_build_scenarios(openspec_root)
    if positive_lines:
        raise CanonicalGateError(
            "canonical scenarios positively prescribe --skip-build: "
            + "; ".join(positive_lines)
        )


def read_change_delta(openspec_root: Path, change: str, capability: str) -> str:
    """Read one delta from an active packet or its unique dated archive."""

    active = openspec_root / "changes" / change / "specs" / capability / "spec.md"
    if active.is_file():
        return active.read_text(encoding="utf-8")
    archives = archived_change_paths(openspec_root, change)
    if len(archives) != 1:
        raise CanonicalGateError(
            f"{change} must be active or have one archive; found {[str(path) for path in archives]}"
        )
    archived = archives[0] / "specs" / capability / "spec.md"
    if not archived.is_file():
        raise CanonicalGateError(f"missing archived delta: {archived}")
    return archived.read_text(encoding="utf-8")


def archived_change_paths(openspec_root: Path, change: str) -> list[Path]:
    """Return dated archive directories for a stable change ID."""

    archive_root = openspec_root / "changes" / "archive"
    if not archive_root.is_dir():
        return []
    return sorted(path for path in archive_root.glob(f"????-??-??-{change}") if path.is_dir())


def require_delta(
    text: str,
    delta_kind: str,
    requirement: str,
    change: str,
    capability: str,
) -> None:
    """Require a delta header and requirement in one source packet."""

    require_text(text, f"## {delta_kind} Requirements", f"{change}/{capability} delta header")
    require_text(text, f"### Requirement: {requirement}", f"{change}/{capability} requirement")


def read_canonical_spec(openspec_root: Path, capability: str) -> str:
    """Read one required canonical capability."""

    path = openspec_root / "specs" / capability / "spec.md"
    if not path.is_file():
        raise CanonicalGateError(f"missing canonical spec: {path}")
    return path.read_text(encoding="utf-8")


def positive_skip_build_scenarios(openspec_root: Path) -> list[str]:
    """Return scenario lines that positively prescribe the removed flag."""

    rows: list[str] = []
    specs_root = openspec_root / "specs"
    for path in sorted(specs_root.glob("*/spec.md")) if specs_root.is_dir() else []:
        in_scenario = False
        bullet_context = ""
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("#### Scenario:"):
                in_scenario = True
                bullet_context = ""
                continue
            if line.startswith("### "):
                in_scenario = False
                bullet_context = ""
            normalized = f" {re.sub(r'[`*_]', '', line).lower()} "
            bullet_context = logical_bullet_context(line, normalized, bullet_context)
            if in_scenario and "--skip-build" in normalized and not any(
                marker in bullet_context for marker in NEGATIVE_SKIP_MARKERS
            ):
                rows.append(f"{path}:{number}: {line.strip()}")
    return rows


def logical_bullet_context(line: str, normalized: str, previous: str) -> str:
    """Return one Markdown bullet plus any indented continuation text."""

    stripped = line.lstrip()
    if stripped.startswith("- "):
        return normalized
    if line[:1].isspace() and stripped and previous:
        return f"{previous} {normalized}"
    return normalized


def require_text(text: str, expected: str, label: str) -> None:
    """Require one exact contract fragment."""

    if expected not in text:
        raise CanonicalGateError(f"missing {label}: {expected}")


def load_json(path: Path) -> dict:
    """Load one required JSON object."""

    if not path.is_file():
        raise CanonicalGateError(f"missing JSON file: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CanonicalGateError(f"invalid JSON in {path}: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise CanonicalGateError(f"JSON root must be an object: {path}")
    return payload
