"""Large pending requests reserve evidence space before further work is retained."""
from test_proof_contract_obligation_bundles import _request
from test_proof_contract_obligation_check_resources import (
    _mock_native_validation,
    _workflow_request,
)

from ladon import proof_contract_provider_expansion as expansion
from ladon.proof_contract_obligation_checks import check_obligation_sources


def test_pending_provider_request_admission_retains_earlier_target(tmp_path,monkeypatch):
    _,plan=_request();request=_workflow_request(tmp_path,plan)
    request['sourceBindings']['providers']=[]
    _mock_native_validation(monkeypatch,request['analysisArtifact'])
    # Synthetic bookkeeping only; no source or proof observation is asserted.
    monkeypatch.setattr(expansion,'make_provider_slice_request',lambda *args: {
        'status':'not-dispatched','scope':'synthetic-budget-control','padding':'x'*(7*1024**2)})
    report=check_obligation_sources(request)
    assert report['status']=='incomplete'
    assert len(report['providerSliceRequests'])==1
    assert len(report['sourceChecks'])==2
    assert report['resourceAccounting']['evidenceBytes']<=8*1024**2
    assert 'budget' in report['stopReason']
    assert sum(p.stat().st_size for p in (tmp_path/'source-run').rglob('*') if p.is_file())<=8*1024**2
