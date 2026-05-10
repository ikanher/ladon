"""Generic evidence-completeness inspection for review/witness packets."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


CheckPredicate = Callable[[list[Path]], bool]

METADATA_NAMES = {
    "manifest.json",
    "metadata.json",
    "atlas_manifest.json",
    "validation-summary.json",
}
COMMAND_NAMES = {
    "VERIFY_PACKET.sh",
    "verify_packet.sh",
    "commands.txt",
    "RUNS.md",
    "verification.md",
}
OWNER_MARKERS = ("Lean", "theorem", "owner", "proof")
PROFILE_REQUIRED_CHECKS = {
    "generic": (
        "metadata",
        "witness_json",
        "checker_script",
        "tests",
        "verification_commands",
        "owner_references",
    ),
    "review_packet": ("metadata", "tests", "owner_references"),
    "witness_bundle": (
        "metadata",
        "witness_json",
        "checker_script",
        "tests",
        "verification_commands",
        "owner_references",
    ),
    "release_bundle": ("metadata", "verification_commands", "owner_references"),
}


def summarize_packet_evidence(packet_dir: Path, *, profile: str = "generic") -> dict[str, Any]:
    """Return a generic evidence-completeness summary for one packet."""

    ensure_known_profile(profile)
    if not packet_dir.is_dir():
        return missing_packet_summary(packet_dir, profile=profile)
    files = packet_files(packet_dir)
    checks = evidence_checks(packet_dir, files)
    score = sum(1 for check in checks if check["passed"])
    return {
        "packet_dir": str(packet_dir),
        "exists": True,
        "status": packet_status(score, len(checks)),
        **profile_summary(checks, profile),
        "score": score,
        "max_score": len(checks),
        "file_count": len(files),
        "checks": checks,
    }


def missing_packet_summary(packet_dir: Path, *, profile: str = "generic") -> dict[str, Any]:
    """Return the stable shape for absent packet paths."""

    ensure_known_profile(profile)
    return {
        "packet_dir": str(packet_dir),
        "exists": False,
        "status": "missing",
        "profile": profile,
        "profile_status": "missing",
        "required_checks": list(PROFILE_REQUIRED_CHECKS[profile]),
        "missing_required_checks": list(PROFILE_REQUIRED_CHECKS[profile]),
        "score": 0,
        "max_score": len(check_definitions()),
        "file_count": 0,
        "checks": [
            {"name": name, "passed": False, "examples": []}
            for name, _predicate in check_definitions()
        ],
    }


def profile_summary(checks: list[dict[str, Any]], profile: str) -> dict[str, Any]:
    """Return profile-specific completeness fields."""

    required = list(PROFILE_REQUIRED_CHECKS[profile])
    passed = {check["name"] for check in checks if check["passed"]}
    missing = [name for name in required if name not in passed]
    return {
        "profile": profile,
        "profile_status": "complete" if not missing else "partial",
        "required_checks": required,
        "missing_required_checks": missing,
    }


def ensure_known_profile(profile: str) -> None:
    """Reject unknown packet-evidence profiles with a direct error."""

    if profile not in PROFILE_REQUIRED_CHECKS:
        known = ", ".join(sorted(PROFILE_REQUIRED_CHECKS))
        raise ValueError(f"unknown packet evidence profile {profile!r}; expected one of: {known}")


def packet_files(packet_dir: Path) -> list[Path]:
    """Return regular packet files relative to the packet root."""

    return sorted(path.relative_to(packet_dir) for path in packet_dir.rglob("*") if path.is_file())


def evidence_checks(packet_dir: Path, files: list[Path]) -> list[dict[str, Any]]:
    """Run all evidence checks against packet files."""

    return [
        {
            "name": name,
            "passed": predicate(files),
            "examples": matching_examples(packet_dir, files, name),
        }
        for name, predicate in check_definitions()
    ]


def check_definitions() -> list[tuple[str, CheckPredicate]]:
    """Return named evidence predicates."""

    return [
        ("metadata", has_metadata),
        ("witness_json", has_witness_json),
        ("checker_script", has_checker_script),
        ("tests", has_tests),
        ("verification_commands", has_verification_commands),
        ("owner_references", has_owner_references),
    ]


def matching_examples(packet_dir: Path, files: list[Path], check_name: str) -> list[str]:
    """Return up to three example files supporting a check."""

    examples = [
        str(path)
        for path in files
        if example_matches(packet_dir, path, check_name)
    ]
    return examples[:3]


def example_matches(packet_dir: Path, path: Path, check_name: str) -> bool:
    """Return whether one relative path is an example for a named check."""

    return {
        "metadata": is_metadata_file,
        "witness_json": is_witness_json_file,
        "checker_script": is_checker_script,
        "tests": is_test_file,
        "verification_commands": is_verification_command_file,
        "owner_references": lambda item: has_owner_markers(packet_dir / item),
    }[check_name](path)


def has_metadata(files: list[Path]) -> bool:
    return any(is_metadata_file(path) for path in files)


def has_witness_json(files: list[Path]) -> bool:
    return any(is_witness_json_file(path) for path in files)


def has_checker_script(files: list[Path]) -> bool:
    return any(is_checker_script(path) for path in files)


def has_tests(files: list[Path]) -> bool:
    return any(is_test_file(path) for path in files)


def has_verification_commands(files: list[Path]) -> bool:
    return any(is_verification_command_file(path) for path in files)


def has_owner_references(files: list[Path]) -> bool:
    return any(path.suffix.lower() in {".md", ".txt", ".tex"} for path in files)


def is_metadata_file(path: Path) -> bool:
    return path.name in METADATA_NAMES


def is_witness_json_file(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    return path.suffix == ".json" and bool(parts & {"witness", "witnesses", "artifacts"})


def is_checker_script(path: Path) -> bool:
    return path.suffix == ".py" and ("check" in path.name or "checker" in path.name)


def is_test_file(path: Path) -> bool:
    return path.suffix == ".py" and (path.name.startswith("test_") or "tests" in path.parts)


def is_verification_command_file(path: Path) -> bool:
    return path.name in COMMAND_NAMES or path.name.startswith("VERIFY_")


def has_owner_markers(path: Path) -> bool:
    """Return whether a text file mentions source/proof-owner concepts."""

    if path.suffix.lower() not in {".md", ".txt", ".tex"}:
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    return any(marker in text for marker in OWNER_MARKERS)


def packet_status(score: int, max_score: int) -> str:
    """Return an evidence completeness label."""

    if score == max_score:
        return "complete"
    if score == 0:
        return "empty"
    return "partial"
