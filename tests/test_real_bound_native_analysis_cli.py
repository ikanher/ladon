"""The Real analysis operations have distinct public CLI dispatch."""

import json

from ladon.proof_contract_cli import contract_main


def test_real_comparison_cli_routes_to_fresh_profile_operation(tmp_path, capsys, monkeypatch):
    import ladon.real_bound_native_analysis as analysis

    left, right = tmp_path / "left.json", tmp_path / "right.json"
    left.write_text('{"schema":"ladon-real-bound-production-v1","authority":"none"}')
    right.write_text('{"schema":"ladon-real-bound-production-v1","authority":"none"}')
    called = []

    def compare(a, b, root, *, timeout_seconds):
        called.append((a, b, root, timeout_seconds))
        return {"schema": "ladon-real-bound-analysis-v1", "stage": "comparison",
                "status": "unresolved"}

    monkeypatch.setattr(analysis, "compare_real_bounds", compare)
    status = contract_main(["compare-real-bounds", "--left", str(left), "--right", str(right),
                            "--root", str(tmp_path), "--timeout-seconds", "19"])

    assert status == 2
    assert len(called) == 1 and called[0][2:] == (tmp_path, 19.0)
    result = json.loads(capsys.readouterr().out)
    assert result["stage"] == "comparison"
    assert result["status"] == "unresolved"


def test_real_identity_propagation_cli_does_not_call_nat_graph_route(
    tmp_path, capsys, monkeypatch
):
    import ladon.real_bound_native_analysis as analysis

    one, two = tmp_path / "one.json", tmp_path / "two.json"
    for path in (one, two):
        path.write_text('{"schema":"ladon-real-bound-production-v1","authority":"none"}')
    called = []

    def propagate(values, root, *, timeout_seconds):
        called.append((values, root, timeout_seconds))
        return {"schema": "ladon-real-bound-analysis-v1", "stage": "propagation",
                "status": "unresolved", "complete": False}

    monkeypatch.setattr(analysis, "propagate_real_bound_identity", propagate)
    status = contract_main(["propagate-real-bound-identity", "--production", str(one),
                            "--production", str(two), "--root", str(tmp_path)])

    assert status == 2
    assert len(called) == 1 and len(called[0][0]) == 2
    assert called[0][1:] == (tmp_path, 600.0)
    assert json.loads(capsys.readouterr().out)["stage"] == "propagation"
