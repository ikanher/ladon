"""Inspect replays planned native probe semantics without claiming fresh proof."""
import json

from test_proof_contract_application_probe_contract import TEMPLATE, api, fixture

from ladon.proof_contract_cli import contract_main


def test_ordinary_inspect_replays_probe_plan_and_rejects_rehashed_goal(tmp_path, capsys):
    builder, _, _, _ = api()
    from ladon.proofir_v3 import detached_content_id

    data = fixture()
    artifact = builder(data['context'], *data['sides'], TEMPLATE, analysis_id='analysis:inspect')
    native, context = tmp_path / 'artifact.json', tmp_path / 'context.json'
    native.write_text(json.dumps(artifact))
    context.write_text(json.dumps(data['context']))
    args = ['inspect', '--input', str(native), '--context', str(context)]
    assert contract_main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result == artifact
    assert result['payload']['result']['checkerAuthority'] == 'none'
    artifact['payload']['result']['goals'][1]['goal'] += ' ∧ True'
    artifact['artifactId'] = detached_content_id(artifact)
    native.write_text(json.dumps(artifact))
    assert contract_main(args) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'rejected'
