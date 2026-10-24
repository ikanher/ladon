"""Independent native-audit regressions for preparse bounds and limitations."""

import json

import pytest
from test_proof_contract_propagation_native import artifact, inputs

import ladon.proof_contract_cli as cli
from ladon.proofir_v3 import make_envelope, validate_envelope_batch


def test_cli_rejects_aggregate_raw_inputs_before_any_json_parser(tmp_path, monkeypatch, capsys):
    # Each file fits the cap; together they exceed it. No native decode is needed.
    paths = [tmp_path / f"input{i}.json" for i in range(2)]
    for path in paths:
        path.write_text('{"padding":"' + 'x' * 4_300_000 + '"}')

    def forbidden_parse(*_args, **_kwargs):
        raise AssertionError("aggregate raw admission must precede JSON parsing")

    monkeypatch.setattr(json, "loads", forbidden_parse)
    output = tmp_path / "analysis.json"
    code = cli.contract_main([
        "propagate", "--derivation", str(paths[0]), "--request", str(paths[1]),
        "--analysis-id", "analysis:cap", "--output", str(output),
    ])
    assert code == 2
    assert not output.exists()
    assert "aggregate" in capsys.readouterr().out


def test_native_analysis_cannot_remove_the_deadline_non_authentication_limitation():
    graph, contracts, request = inputs()
    request["bounds"] = {"deadlineUtc": "2000-01-01T00:00:00Z"}
    original = artifact(graph, contracts, request)
    with pytest.raises(ValueError, match="deadline-observation-unverified"):
        stripped = make_envelope(
            artifact_kind=original["artifactKind"], producer=original["producer"],
            environment_ref=original["environmentRef"], subject_refs=original["subjectRefs"],
            coverage=original["coverage"], payload=original["payload"],
            limitations=[row for row in original["limitations"]
                         if row["id"] != "deadline-observation-unverified"],
        ).to_dict()
        validate_envelope_batch([graph, *contracts, stripped])
