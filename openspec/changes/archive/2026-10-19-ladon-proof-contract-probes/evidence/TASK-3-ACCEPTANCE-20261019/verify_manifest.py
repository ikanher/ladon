"""Read-only integrity and contract verification for task 3 evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parent


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"expected object in {path}")
    return value


def _verify_files(manifest: dict) -> int:
    count = 0
    for group in ("inputs", "producers", "artifacts"):
        for row in manifest[group]:
            path = EVIDENCE / row["path"] if group == "artifacts" else ROOT / row["path"]
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise ValueError(f"digest mismatch: {path}")
            if group == "artifacts" and len(data) != row["bytes"]:
                raise ValueError(f"size mismatch: {path}")
            count += 1
    return count


def _verify_transport(bundle: dict) -> None:
    checks = bundle.get("checks", [])
    if (bundle.get("parentSupport") != "supported-for-attributed-interpretation"
            or len(checks) != 6 or any(row.get("status") != "supported" for row in checks)
            or len(bundle.get("checkRunRefs", [])) != len(checks)):
        raise ValueError("checked transport does not have six supported bound receipts")


def _verify_control(control: dict) -> None:
    if (control.get("statementRelation") != "aligned"
            or control.get("methodRelation") != "different"
            or control.get("formalSupport") != "recorded-links-only"):
        raise ValueError("harmless method control was not preserved")


def _verify_observation(observation: dict) -> None:
    if (observation.get("statementRelation") != "mismatch"
            or observation.get("formalSupport") != "not-established"
            or observation.get("mathematicalFalsity") != "not-established"):
        raise ValueError("application difference was upgraded beyond attribution")


def _verify_report(report: dict) -> None:
    findings = report.get("findings", [])
    control = next((row for row in findings if row.get("kind") == "native-correspondence-review"), None)
    observation = next((row for row in findings if row.get("kind") == "observation"), None)
    if control is None or observation is None:
        raise ValueError("report is missing a control or observation finding")
    _verify_control(control)
    _verify_observation(observation)
    if (report.get("mathematicalFalsity") != "not-established"
            or report.get("wholePaperCertified") is not False):
        raise ValueError("report exceeded its investigation authority")


def _verify_counterexample(counterexample: dict) -> None:
    if (counterexample.get("returncode") != 0
            or "'membership_erasure_is_not_equivalent' does not depend on any axioms"
            not in counterexample.get("stdout", "")):
        raise ValueError("separate checked non-implication evidence is unavailable")


def _verify_claims() -> None:
    bundle = _read_json(EVIDENCE / "checked-correspondence.json")
    report = _read_json(EVIDENCE / "report.json")
    counterexample = _read_json(EVIDENCE / "checked-nonimplication.json")
    control_plan = _read_json(EVIDENCE / "control-plan.json")
    application_plan = _read_json(EVIDENCE / "application-plan.json")
    _verify_transport(bundle)
    _verify_report(report)
    _verify_counterexample(counterexample)
    sys.path.insert(0, str(ROOT / "src"))
    from ladon.investigation_reporting import aggregate_report

    rebuilt = aggregate_report(
        [control_plan, application_plan], ROOT / "tests/fixtures/correspondence_m1",
        now=datetime.fromisoformat(control_plan["startedAt"]),
    )
    if rebuilt != report:
        raise ValueError("saved report is not the projection of its source plans")


def main() -> int:
    manifest = _read_json(EVIDENCE / "MANIFEST.json")
    if manifest.get("nonimplicationIsUnrelatedToApplicationFinding") is not True:
        raise ValueError("counterexample/application separation changed")
    count = _verify_files(manifest)
    _verify_claims()
    print(f"PASS: {count} input/artifact hashes and task 3 report contracts verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
