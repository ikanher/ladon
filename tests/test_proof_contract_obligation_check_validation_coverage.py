"""Known plan coverage survives evidence pressure after native validation."""
from test_proof_contract_obligation_bundles import _request
from test_proof_contract_obligation_check_resources import (
    _mock_native_validation,
    _workflow_request,
)

from ladon.proof_contract_obligation_checks import check_obligation_sources
from ladon.proofir_v3 import detached_content_id


def test_validated_demand_coverage_survives_large_native_artifact(tmp_path, monkeypatch):
    _, plan = _request()
    request = _workflow_request(tmp_path, plan)
    request['sourceBindings']['providers'] = []
    artifact = request['analysisArtifact']
    artifact['extensions']['test.large-opaque-note/v1'] = ['x' * 1024**2 for _ in range(4)]
    artifact['artifactId'] = detached_content_id(artifact)
    _mock_native_validation(monkeypatch, artifact)
    report = check_obligation_sources(request)
    assert len(report['sourceChecks']) == 2
    assert len(report['routes']) == 1
    assert report['wholeMethodAuthority'] == 'none'
    assert report['resourceAccounting']['evidenceBytes'] <= 8 * 1024**2
