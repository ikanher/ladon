"""Actual source-bound constant readings survive native consumers and replay."""
import copy
import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

TEMPLATE = {'familyId': 'constant-uniformity', 'version': 'constant-uniformity-v2',
            'direction': 'right-to-left', 'kind': 'counterexample'}
ROOT = Path(__file__).resolve().parents[1]


def inputs():
    context = json.loads((ROOT / 'tests/fixtures/proof_contract_application_probes/constant-context.json').read_text())
    sides = []
    for index in range(3):
        contract = next(a for a in context['artifacts'] if a['artifactKind'] == 'proofir.contract'
                        and a['payload']['contractId'] == f'contract:uniform-reading-{index}')
        correspondence = next(a for a in context['artifacts'] if a['artifactKind'] == 'proofir.correspondence'
            and a['payload']['interpretationRef']['localId'] == f'uniform-reading-{index}')
        sides.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                                     'localId': contract['payload']['contractId']},
            'correspondenceRef': {'artifactRef': correspondence['artifactId'], 'kind': 'correspondence',
                                 'localId': correspondence['payload']['correspondenceId']}})
    return context, sides


def build(context, left, right):
    from ladon.proof_contract_probe_artifacts import application_probe_artifact

    return application_probe_artifact(context, left, right, TEMPLATE, analysis_id='analysis:uniformity-test')


def test_actual_native_constant_pair_generates_open_goals_with_original_quantifiers():
    from ladon.proofir_v3 import validate_envelope_batch

    context, sides = inputs()
    artifact = build(context, *sides[:2])
    validate_envelope_batch([*context['artifacts'], artifact])
    result = artifact['payload']['result']
    assert result['status'] == 'planned'
    assert result['scope'] == 'closed-nat-constant-uniformity-v2'
    assert result['checkerAuthority'] == 'none'
    assert artifact['payload']['checkRunRefs'] == []
    assert [g['status'] for g in result['goals']] == ['open', 'open']
    assert result['goals'][1]['goal'].count('∃') == 2
    assert result['goals'][1]['goal'].count('∀') == 4


def test_rehashing_both_goal_and_artifact_cannot_change_native_probe_semantics():
    from ladon.proofir_v3 import detached_content_id, validate_envelope_batch

    context, sides = inputs()
    artifact = build(context, *sides[:2])
    goal = artifact['payload']['result']['goals'][1]
    goal['goal'] += ' ∧ True'
    goal['goalDigest'] = 'sha256:' + hashlib.sha256(goal['goal'].encode()).hexdigest()
    artifact['artifactId'] = detached_content_id(artifact)
    with pytest.raises(ValueError, match='recomputation'):
        validate_envelope_batch([*context['artifacts'], artifact])


def test_structurally_valid_but_wrong_permission_summary_cannot_override_original_ast():
    from ladon.proofir_v3 import detached_content_id, validate_envelope_batch

    context, sides = inputs()
    right = copy.deepcopy(sides[1])
    contract = next(a for a in context['artifacts'] if a['artifactId'] == right['contractRef']['artifactRef'])
    features = contract['payload']['record']['features']
    features['constantDependencies']['allowedBinderIds'] = []
    features['witnessDependencies'][0]['allowedBinderIds'] = []
    contract['artifactId'] = detached_content_id(contract)
    right['contractRef']['artifactRef'] = contract['artifactId']
    validate_envelope_batch(context['artifacts'])
    with pytest.raises(ValueError):
        build(context, sides[0], right)


def test_v2_native_plan_roundtrips_through_ordinary_inspect_and_sqlite(tmp_path, capsys):
    from ladon.proof_contract_cli import contract_main
    from ladon.proofir_sqlite_v3 import project_envelopes, validate_v3_database

    context, sides = inputs()
    artifact = build(context, *sides[:2])
    native, batch = tmp_path / 'native.json', tmp_path / 'context.json'
    native.write_text(json.dumps(artifact))
    batch.write_text(json.dumps(context))
    assert contract_main(['inspect', '--input', str(native), '--context', str(batch)]) == 0
    assert json.loads(capsys.readouterr().out) == artifact
    connection = sqlite3.connect(':memory:')
    project_envelopes(connection, [*context['artifacts'], artifact])
    validate_v3_database(connection)
    assert connection.execute('SELECT stage FROM proofir_v3_contract_analyses').fetchone() == ('probes',)
    assert connection.execute('SELECT count(*) FROM proofir_v3_contract_analysis_inputs').fetchone() == (2,)


def test_historical_v1_unsupported_artifact_replays_without_relabeling():
    from ladon.proofir_v3 import validate_envelope_batch

    archive = (ROOT / 'openspec/changes/archive/2026-10-19-ladon-proof-contract-probes'
               / 'evidence/REGULARITY-APPLICATION-20261019')
    request = json.loads((archive / 'request.json').read_text())
    artifact = json.loads((archive / 'unsupported-constant-uniformity.json').read_text())['artifact']
    validate_envelope_batch([*request['context']['artifacts'], artifact])
    assert artifact['payload']['result']['status'] == 'unsupported'
    assert artifact['payload']['template']['version'] == 'constant-uniformity-v1'
