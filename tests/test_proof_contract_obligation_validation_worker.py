"""Native replay validation uses the same hard process bounds as planning."""
import importlib
from dataclasses import replace
from time import monotonic

from test_proof_contract_obligation_bundles import _request
from test_proof_contract_obligation_native import _artifact

from ladon.process_supervisor import ProcessResult


def _inputs():
    _, request = _request()
    request = replace(request, bounds={'deadlineUtc': '2000-01-01T00:00:00Z'})
    artifact = _artifact(request)
    context = {'artifacts': [request.derivation_artifact, *request.contract_artifacts]}
    return artifact, context


def _api():
    return importlib.import_module('ladon.proof_contract_obligation_supervision').run_obligation_validation


def test_historical_native_validation_runs_bounded_and_preserves_exact_artifact():
    artifact, context = _inputs()
    checked = _api()(artifact, context, deadline_monotonic=monotonic()+30)
    assert checked['status'] == 'completed', checked
    assert checked['result'] == artifact
    assert checked['processReceipt']['requestedMaxRssBytes'] == 12 * 1024**3


def test_native_validation_memory_stop_keeps_report_back_instruction():
    artifact, context = _inputs()
    calls = []

    def runner(command, **kwargs):
        calls.append(kwargs)
        return ProcessResult(tuple(command), -9, '', '', 0.01, memory_limited=True)

    checked = _api()(artifact, context, deadline_monotonic=monotonic()+30, runner=runner)
    assert checked['status'] == 'incomplete'
    assert 'Stop progress and report back to user' in checked['diagnostic']['message']
    assert len(calls) == 1


def test_oversized_native_context_never_launches_worker():
    artifact, context = _inputs()
    context['extra'] = 'x' * (8 * 1024**2)
    calls = []
    checked = _api()(artifact, context, deadline_monotonic=monotonic()+30,
                     runner=lambda *a, **k: calls.append(True))
    assert checked['status'] == 'rejected'
    assert calls == []
