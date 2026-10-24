"""Public native obligation inspection must use the bounded replay worker."""
from test_proof_contract_obligation_bundles import _request

from ladon.proof_contract_obligation_artifacts import obligations_artifact


def test_public_inspect_supervises_obligations_replay(monkeypatch):
    from ladon import proof_contract_obligation_supervision as supervision
    from ladon import proofir_v3
    from ladon.proof_contract_cli import _inspect_native

    _, request = _request()
    artifact = obligations_artifact(request, analysis_id='analysis:supervised-inspect')
    context = {'artifacts': [request.derivation_artifact, *request.contract_artifacts]}
    calls = []

    def checked(value, batch, **bounds):
        calls.append((value, batch, bounds))
        return {'status': 'completed', 'result': value}

    def forbidden(*_args, **_kwargs):
        raise AssertionError('inspection must not replay untrusted obligations in the CLI process')

    monkeypatch.setattr(supervision, 'run_obligation_validation', checked)
    monkeypatch.setattr(proofir_v3, 'validate_envelope_batch', forbidden)
    assert _inspect_native(artifact, context) == artifact
    assert len(calls) == 1
    assert calls[0][:2] == (artifact, context)
    assert calls[0][2]['deadline_monotonic'] > 0
