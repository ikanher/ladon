"""An earlier deadline on the backward request still constrains source work."""

import importlib
from datetime import UTC, datetime, timedelta
from time import monotonic

from test_proof_contract_source_obligation_boundaries import _invalid_request

from ladon.proof_contract_obligations import BackwardTransformRequest


def test_expired_backward_deadline_starts_no_source_verification(monkeypatch):
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("source-work")
        raise AssertionError("source work started after inherited deadline")

    monkeypatch.setattr(api, "verify_formal_snapshot", forbidden)
    request = _invalid_request()
    request["backwardRequest"] = BackwardTransformRequest(
        desired_contract={}, rule_evidence={}, premise_interfaces=[], output_interface={},
        bounds={"deadlineUtc": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()},
    )
    result = api.instantiate_source_bound_premise(request)
    assert result["status"] == "incomplete"
    assert calls == []


def test_earlier_backward_deadline_clamps_the_source_deadline_without_mutation():
    api = importlib.import_module("ladon.proof_contract_source_obligations")
    original = monotonic() + 120
    request = _invalid_request()
    request["deadlineMonotonic"] = original
    request["backwardRequest"] = BackwardTransformRequest(
        desired_contract={}, rule_evidence={}, premise_interfaces=[], output_interface={},
        bounds={"deadlineUtc": (datetime.now(UTC) + timedelta(seconds=2)).isoformat()},
    )
    effective = api._effective_deadline(request)
    assert 0 < effective - monotonic() <= 2
    assert request["deadlineMonotonic"] == original
