"""Deadline, source-race and closed-input regressions for refinement consumers."""
import copy
import json
import time

import pytest
from test_proof_contract_refinement_workflow import (
    _historical_artifact,
    _positive_owner_result,
    _request,
    _seal,
)

from ladon import proof_contract_lift_check
from ladon.entrypoint import main
from ladon.proof_contract_refinement_workflow import inspect_refinement, refine


def test_expired_deadline_never_starts_owner(monkeypatch, tmp_path):
    request = _request(tmp_path)
    monkeypatch.setattr(proof_contract_lift_check, 'check_nat_rational_lift',
                        lambda *_: pytest.fail('expired attempt started a worker'))
    result = refine(request, tmp_path, deadline_monotonic=time.monotonic() - 1)
    assert result['status'] == 'incomplete'
    assert result['branches'] == []
    assert result['request'] == request
    assert inspect_refinement(result, tmp_path)['liftAuthority'] == 'unverified-saved-result'


@pytest.mark.parametrize('field', ['refinementConstraints', 'repairConstraints'])
def test_either_branch_can_be_requested_alone(monkeypatch, tmp_path, field):
    request = _request(tmp_path)
    request[field] = []
    original = copy.deepcopy(request)
    monkeypatch.setattr(proof_contract_lift_check, 'check_nat_rational_lift',
                        lambda owned, plan_id, term: _positive_owner_result(
                            owned, plan_id, owned['witness'], term=term))
    result = refine(request, tmp_path, deadline_monotonic=time.monotonic() + 10)
    assert result['status'] == 'completed'
    assert len(result['branches']) == 1
    assert request == original
    assert inspect_refinement(result, tmp_path)['artifact'] == result


def test_source_changed_during_lift_cannot_publish_completed_branch(monkeypatch, tmp_path):
    request = _request(tmp_path)

    def changed(owned, plan_id, term):
        result = _positive_owner_result(owned, plan_id, owned['witness'], term=term)
        (tmp_path / 'Fixture.lean').write_text('-- changed during owner\n')
        return result

    monkeypatch.setattr(proof_contract_lift_check, 'check_nat_rational_lift', changed)
    with pytest.raises(ValueError, match='source|digest'):
        refine(request, tmp_path, deadline_monotonic=time.monotonic() + 10)


@pytest.mark.parametrize('mutation', [
    lambda a: a['branches'].clear(),
    lambda a: a['branches'].reverse(),
    lambda a: a['branches'][0]['check'].update(originalClaimRefuted=True),
    lambda a: a['liftResult']['binding'].update(termDigest='sha256:' + '0' * 64),
    lambda a: a['liftResult'].update(mode='realization'),
    lambda a: a.update(originalClaimRefuted=0),
    lambda a: a.update(unknown='field'),
])
def test_resealed_inconsistent_saved_evidence_is_rejected(tmp_path, mutation):
    artifact = _historical_artifact(_request(tmp_path), tmp_path)
    mutation(artifact)
    _seal(artifact)
    with pytest.raises((TypeError, ValueError)):
        inspect_refinement(artifact, tmp_path)


@pytest.mark.parametrize('option,value', [
    ('--timeout-seconds', 'nan'), ('--timeout-seconds', '0'),
    ('--timeout-seconds', '3601'), ('--deadline-monotonic', 'inf'),
    ('--max-rss-mib', '0'), ('--max-rss-mib', '12289'),
])
def test_invalid_cli_limits_fail_without_native_work(monkeypatch, tmp_path, capsys, option, value):
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(_request(tmp_path)))
    monkeypatch.setattr(proof_contract_lift_check, 'check_nat_rational_lift',
                        lambda *_: pytest.fail('invalid CLI options started a worker'))
    assert main(['investigation', 'contract', 'refine', '--input', str(path),
                 '--root', str(tmp_path), option, value]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'


def test_dangling_output_link_and_duplicate_json_reject_before_owner(monkeypatch, tmp_path, capsys):
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(_request(tmp_path)))
    output = tmp_path / 'dangling.json'
    output.symlink_to(tmp_path / 'absent')
    monkeypatch.setattr(proof_contract_lift_check, 'check_nat_rational_lift',
                        lambda *_: pytest.fail('invalid publication/input started a worker'))
    argv = ['investigation', 'contract', 'refine', '--input', str(path), '--root', str(tmp_path)]
    assert main([*argv, '--output', str(output)]) == 2
    assert output.is_symlink()
    path.write_text('{"schema":"bad","schema":"bad"}')
    assert main(argv) == 2
    assert 'duplicate' in capsys.readouterr().out


def test_unsupported_cli_preserves_findings_and_exits_two(tmp_path, capsys):
    request = _request(tmp_path)
    request['lift']['interpretation']['profile'] = 'unsupported-profile'
    request['lift']['term'] = None
    path = tmp_path / 'request.json'
    path.write_text(json.dumps(request))
    assert main(['investigation', 'contract', 'refine', '--input', str(path),
                 '--root', str(tmp_path)]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'unsupported'
    assert result['request'] == request
    assert inspect_refinement(result, tmp_path)['leanReplayed'] is False
