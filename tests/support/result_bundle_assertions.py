"""Shared assertions preserve the frozen bundle report and text contracts."""
import json


def assert_integrity_report(result):
    assert result["operation"] == "verify"
    assert result["status"] == "verified"
    assert result["integrity"] == "passed"
    assert result["replay"] == "not-run"
    assert result["replayCoverage"] == "unknown"
    assert result["checking"] == "not-assessed"
    assert result["correspondence"] == "not-assessed"
    assert result.get("authenticity", "not-assessed") == "not-assessed"


def parse_text(text):
    return {key: json.loads(value) for key, value in
            (line.split(': ', 1) for line in text.splitlines())}
