"""Ordinary CLI can retain an observed discrepancy without native extraction."""

import json

from test_investigation_findings import legacy, observation_case

from ladon.entrypoint import main


def test_public_observation_workflow(tmp_path, capsys):
    original, captured = observation_case(tmp_path)
    record = captured["observations"][0]["record"]
    plan_path, record_path = tmp_path / "plan.json", tmp_path / "record.json"
    plan_path.write_text(json.dumps(original))
    record_path.write_text(json.dumps(record))
    observed_path = tmp_path / "observed.json"
    shared = ["--root", str(tmp_path)]
    assert main(["investigation", "observe", "--plan", str(plan_path), *shared,
                 "--record", str(record_path), "--output", str(observed_path)]) == 0
    subject = _inspect_captured(observed_path, plan_path, original, record, shared, capsys)
    reviewed_path = _review_captured(tmp_path, observed_path, shared, subject)
    _finalize_and_report(tmp_path, reviewed_path, observed_path, shared)


def _inspect_captured(observed_path, plan_path, original, record, shared, capsys):
    observed = json.loads(observed_path.read_text())
    assert json.loads(plan_path.read_text()) == original
    subject = observed["observations"][0]["observationId"]
    assert main(["investigation", "inspect-observations", "--plan", str(observed_path), *shared]) == 0
    inspected = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert inspected["observations"][0]["record"] == record
    return subject


def _review_captured(tmp_path, observed_path, shared, subject):
    packet_path = tmp_path / "challenge.json"
    assert main(["investigation", "challenge", "--plan", str(observed_path), *shared,
                 "--claim", subject, "--output", str(packet_path)]) == 0
    packet = json.loads(packet_path.read_text())
    assert "comparison" not in packet and "evidence" not in packet
    response_path = tmp_path / "response.json"
    response_path.write_text(json.dumps({"reviewer": "independent-reader", "subject": subject,
        "challengeDigest": packet["challengeDigest"], "classification": "mismatch",
        "method": "different", "sourceFidelity": "faithful", "evidence": "Exact comparison."}))
    reviewed_path = tmp_path / "reviewed.json"
    assert main(["investigation", "ingest", "--plan", str(observed_path), *shared,
                 "--packet", str(packet_path), "--response", str(response_path),
                 "--output", str(reviewed_path)]) == 0
    return reviewed_path


def _finalize_and_report(tmp_path, reviewed_path, observed_path, shared):
    terminal_path, report_path = tmp_path / "terminal.json", tmp_path / "report.json"
    assert main(["investigation", "finalize", "--plan", str(reviewed_path), *shared,
                 "--output", str(terminal_path)]) == 0
    terminal = json.loads(terminal_path.read_text())
    assert terminal["findings"][0]["statementRelation"] == "mismatch"
    assert terminal["formalCorrespondence"] == "incomplete-no-counterpart"
    assert main(["investigation", "report", "--plan", str(reviewed_path),
                 "--plan", str(observed_path), *shared, "--output", str(report_path)]) == 0
    report = json.loads(report_path.read_text())
    assert len(report["observations"]) == 1
    assert any(b["next"] for b in report["branches"])
    assert main(["investigation", "report", "--plan", str(reviewed_path), *shared,
                 "--output", str(report_path)]) == 2


def test_stale_observation_cli_creates_no_output(tmp_path, capsys):
    original, captured = observation_case(tmp_path)
    plan_path, record_path = tmp_path / "plan.json", tmp_path / "record.json"
    plan_path.write_text(json.dumps(original))
    record_path.write_text(json.dumps(captured["observations"][0]["record"]))
    (tmp_path / "source.txt").write_text("Changed source.\n")
    output = tmp_path / "invalid-output.json"
    assert main(["investigation", "observe", "--plan", str(plan_path), "--root", str(tmp_path),
                 "--record", str(record_path), "--output", str(output)]) == 2
    assert not output.exists()
    assert "stale" in capsys.readouterr().out
    assert original["startedAt"] == legacy(tmp_path)["startedAt"]
