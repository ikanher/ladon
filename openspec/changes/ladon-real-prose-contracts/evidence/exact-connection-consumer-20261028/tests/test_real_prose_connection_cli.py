"""Connection commands require explicit original inputs and preserve saved files."""

import json

import pytest
from test_real_prose_connection_history import qualified as _qualified

from ladon.proof_contract_cli import contract_main
from ladon.proofir_v3 import validate_envelope_batch
from ladon.real_bound_native_production import inspect_real_bound
from ladon.real_prose_native_production import validate_production

qualified = _qualified


def test_report_and_generic_inspection_remain_historical(qualified,tmp_path,capsys):
    snapshot,*_ = qualified
    source = tmp_path/'connection.json'
    source.write_text(json.dumps(snapshot))
    for command in ['report-real-prose-connection','inspect']:
        code = contract_main([command,'--input',str(source)])
        report = json.loads(capsys.readouterr().out)
        assert code == 0
        assert report['authority'] == 'none' and report['freshCheck'] is False
        assert report['evidenceAuthentication'] == 'not-established'


def test_replay_parser_requires_both_original_inputs(tmp_path,capsys):
    with pytest.raises(SystemExit) as stopped:
        contract_main(['replay-real-prose-connection','--input',str(tmp_path/'old.json')])
    assert stopped.value.code == 2
    assert '--formal' in capsys.readouterr().err


def test_report_will_not_overwrite_an_existing_file(qualified,tmp_path,capsys):
    snapshot,*_ = qualified
    source,output = tmp_path/'saved.json',tmp_path/'existing.json'
    source.write_text(json.dumps(snapshot))
    output.write_text('retain existing experiment')
    assert contract_main(['report-real-prose-connection','--input',str(source),'--output',str(output)]) == 2
    assert output.read_text() == 'retain existing experiment'
    assert json.loads(capsys.readouterr().out)['status'] == 'invalid'


def test_unsupported_old_consumers_reject_the_new_connection_snapshot(qualified):
    snapshot,*_ = qualified
    for consumer in [inspect_real_bound,validate_production]:
        with pytest.raises(ValueError):
            consumer(snapshot)
    with pytest.raises(ValueError):
        validate_envelope_batch([snapshot])
