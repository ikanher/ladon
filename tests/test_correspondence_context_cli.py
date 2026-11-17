"""Real native bundles expose source/application context through the public CLI."""

import json
from pathlib import Path

import pytest

from ladon.entrypoint import main
from ladon.proof_slice import extract_proof_slice

FIXTURE = Path(__file__).parent / 'fixtures/correspondence_m1'


def aligned_bundle(tmp_path):
    proof_slice = extract_proof_slice(
        FIXTURE, 'Proof.lean', 'Proof', 'Correspondence.term', 'Correspondence.bridge',
    )
    assert proof_slice['complete'] is True
    slice_path, interpretation, aligned = [tmp_path / name for name in ('slice.json', 'i.json', 'a.json')]
    slice_path.write_text(json.dumps(proof_slice))
    assert main(['investigation', 'interpret', '--record', str(FIXTURE / 'positive.json'),
                 '--root', str(FIXTURE), '--slice', str(slice_path),
                 '--output', str(interpretation)]) == 0
    assert main(['investigation', 'align', '--interpretation', str(interpretation),
                 '--slice', str(slice_path), '--map', str(FIXTURE / 'map.json'),
                 '--root', str(FIXTURE), '--output', str(aligned)]) == 0
    return aligned


def test_public_inspection_delivers_and_bounds_real_native_context(tmp_path):
    aligned = aligned_bundle(tmp_path)
    outputs = []
    for allowance in (1, 8 * 1024**2):
        output = tmp_path / f'inspected-{allowance}.json'
        assert main(['investigation', 'inspect', '--plan', str(aligned),
                     '--context-max-bytes', str(allowance), '--output', str(output)]) == 0
        outputs.append(json.loads(output.read_text()))
    assert outputs[0]['native']['context']['interpretation']['status'] == 'omitted'
    assert outputs[0]['native']['coverage']['complete'] is False
    assert_delivered_context(outputs[1], aligned)


def assert_delivered_context(output, aligned):
    native = output['native']
    stored = json.loads(aligned.read_text())
    artifact = next(row for row in stored['artifacts'] if row['artifactKind'] == 'proofir.correspondence')
    assert native['context']['formalSlice']['value'] == artifact['payload']['slice']
    assert native['context']['interpretation']['value']['record'] == json.loads(
        (FIXTURE / 'positive.json').read_text())
    assert native['coverage']['complete'] is True
    assert output['schema'] == 'ladon-correspondence-inspection-v1'
    assert native['schema'] == 'ladon-native-correspondence-inspection-v2'


@pytest.mark.parametrize('allowance', ['0', '-1', '8388609'])
def test_public_invalid_context_bound_fails_before_loading_plan(tmp_path, capsys, allowance):
    output = tmp_path / 'unused.json'
    assert main(['investigation', 'inspect', '--plan', str(tmp_path / 'missing.json'),
                 '--context-max-bytes', allowance, '--output', str(output)]) == 2
    assert 'context byte allowance' in capsys.readouterr().out
    assert not output.exists()


def test_public_checked_bundle_retains_obligation_targets(tmp_path):
    aligned = aligned_bundle(tmp_path)
    checked, output = tmp_path / 'checked.json', tmp_path / 'inspection.json'
    assert main(['investigation', 'check', '--plan', str(aligned),
                 '--terms', str(FIXTURE / 'positive-terms.json'), '--repo', str(FIXTURE),
                 '--root', str(FIXTURE), '--output', str(checked)]) == 0
    assert main(['investigation', 'inspect', '--plan', str(checked),
                 '--output', str(output)]) == 0
    bundle, inspection = json.loads(checked.read_text()), json.loads(output.read_text())
    assert bundle['parentSupport'] == 'supported-for-attributed-interpretation'
    evidence = inspection['native']['checkEvidence']
    assert len(evidence['rows']) == len(bundle['checks'])
    assert {row['binding']['status'] for row in evidence['rows']} == {'matched-stored-records'}
    assert evidence['unboundObligations'] == []
    assert inspection['native']['coverage']['checkEvidenceComplete'] is True
    assert_inspected_targets(evidence['rows'], bundle['checks'])


def assert_inspected_targets(evidence, checks):
    targets = {row['obligation']: row for row in checks}
    for row in evidence:
        receipt = row['receipt']['value']
        original = targets[receipt['obligation']]
        assert receipt['checkedGoal'] == original['goal']
        assert receipt['status'] == original['status']
