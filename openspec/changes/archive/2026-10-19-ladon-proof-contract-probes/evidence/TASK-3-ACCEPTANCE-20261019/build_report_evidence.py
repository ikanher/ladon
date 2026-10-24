"""Rebuild source-bound transport/report evidence from the checked test helpers."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
INPUTS = (
    "tests/fixtures/correspondence_m1/representation.txt",
    "tests/fixtures/correspondence_m1/Representation.lean",
    "tests/fixtures/proof_contract_production/RestrictedTransport.lean",
)
PRODUCER_REPO_PATHS = (
    "tests/test_correspondence_investigation_reporting.py",
    "src/ladon/correspondence_check.py",
    "src/ladon/correspondence_evidence.py",
    "src/ladon/investigation_correspondence.py",
    "src/ladon/investigation_correspondence_inputs.py",
    "src/ladon/investigation_correspondence_status.py",
    "src/ladon/investigation_findings.py",
    "src/ladon/investigation_reporting.py",
    "src/ladon/proofir_correspondence.py",
)
PRODUCER_EVIDENCE_NAMES = (
    "build_report_evidence.py",
    "verify_manifest.py",
    "REPORT.md",
)
ARTIFACTS = (
    "checked-correspondence.json",
    "control-plan.json",
    "application-plan.json",
    "report.json",
    "checked-nonimplication.json",
)


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(evidence: Path, subject: str) -> dict:
    producers = [ROOT / name for name in PRODUCER_REPO_PATHS]
    producers.extend(evidence / name for name in PRODUCER_EVIDENCE_NAMES)
    return {
        "schema": "ladon-task-3-evidence-manifest-v1",
        "scope": "constructed local controls only",
        "reportSubject": subject,
        "inputs": [{"path": name, "sha256": _file_hash(ROOT / name)} for name in INPUTS],
        "producers": [{"path": str(path.relative_to(ROOT)), "sha256": _file_hash(path)}
                      for path in producers],
        "artifacts": [{"path": name,
                       "sha256": _file_hash(evidence / name),
                       "bytes": (evidence / name).stat().st_size}
                      for name in ARTIFACTS],
        "nonimplicationIsUnrelatedToApplicationFinding": True,
    }


def manifest_only() -> int:
    evidence = Path(__file__).resolve().parent
    control = json.loads((evidence / "control-plan.json").read_text())
    subject = control["correspondenceBundles"][0]["subject"]
    manifest = _manifest(evidence, subject)
    _write_json(evidence / "MANIFEST.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "tests"))
    from test_correspondence_investigation_reporting import (
        NOW,
        _assert_report_preserves_separate_evidence,
        _checked_fin_representation_bundle,
        _reviewed_application_difference,
        _reviewed_transport_control,
    )

    from ladon.investigation_reporting import aggregate_report
    from ladon.process_supervisor import run_bounded_target_process
    from ladon.proof_slice import pinned_toolchain
    from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

    evidence = Path(__file__).resolve().parent
    correspondence_root = ROOT / "tests/fixtures/correspondence_m1"
    source = correspondence_root / "representation.txt"
    checked_bundle = _checked_fin_representation_bundle(correspondence_root)
    control, subject = _reviewed_transport_control(correspondence_root, source, checked_bundle)
    application = _reviewed_application_difference(control, correspondence_root, source)
    report = aggregate_report([control, application], correspondence_root, now=NOW)
    _assert_report_preserves_separate_evidence(report, subject)
    if not checked_bundle["checkRunRefs"] or not checked_bundle["artifacts"]:
        raise ValueError("checked transport bundle did not retain native checker provenance")

    erased_root = ROOT / "tests/fixtures/proof_contract_production"
    toolchain = pinned_toolchain(erased_root)
    nonimplication = run_bounded_target_process(
        [str(toolchain.lean_path), "RestrictedTransport.lean"], cwd=erased_root,
        env=dict(toolchain.environment), timeout_seconds=60,
        max_output_bytes=1024**2,
        max_rss_bytes=DEFAULT_MAX_RSS_BYTES,
    )
    if not nonimplication.succeeded or "sorryAx" in nonimplication.stdout:
        print(nonimplication.stdout + nonimplication.stderr, file=sys.stderr)
        return 1

    artifacts = {
        "checked-correspondence.json": checked_bundle,
        "control-plan.json": control,
        "application-plan.json": application,
        "report.json": report,
        "checked-nonimplication.json": {
            "source": "tests/fixtures/proof_contract_production/RestrictedTransport.lean",
            "theorem": "membership_erasure_is_not_equivalent",
            "command": [str(toolchain.lean_path), "RestrictedTransport.lean"],
            "returncode": nonimplication.returncode,
            "stdout": nonimplication.stdout,
            "stderr": nonimplication.stderr,
            "timeoutSeconds": 60,
            "maxOutputBytes": 1024**2,
        },
    }
    for name, payload in artifacts.items():
        _write_json(evidence / name, payload)

    manifest = _manifest(evidence, subject)
    _write_json(evidence / "MANIFEST.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(manifest_only() if "--manifest-only" in sys.argv else main())
