from __future__ import annotations

import json

from ladon.entrypoint import main


def test_doctor_json_is_read_only_and_reports_pin(tmp_path, capsys) -> None:
    (tmp_path / "lean-toolchain").write_text("leanprover/lean4:v4.20.0\n", encoding="utf-8")
    assert main(["doctor", "--json", "--repo-root", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "ladon-doctor-result-v1"
    assert payload["readiness"]["preflight"] == "not-run"
    assert payload["posture"]["targetExecution"] == "not-run"
    assert payload["posture"]["targetTrustRequirement"] == "trusted-repository-only"
    assert payload["posture"]["initializerIsolation"] == "absent"
    assert payload["repository"]["toolchainPinDigest"].startswith("sha256:")
