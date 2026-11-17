"""Verify retained targets, identities and replay receipts; no fresh Lean replay."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text())


def inspect_case(name):
    checked = load(BASE / name / 'checked.json')
    inspection = load(BASE / name / 'inspection.json')['native']
    assert inspection['coverage']['complete']
    assert inspection['checkEvidence']['unboundObligations'] == []
    for row in checked['checks']:
        completion = row['completion']
        assert completion['status'] == 'completed'
        assert completion['replay']['status'] == 'accepted'
        assert completion['trust']['accepted'] is True
    targets = {row['obligation']: row for row in checked['checks']}
    for row in inspection['checkEvidence']['rows']:
        assert row['binding']['status'] == 'matched-stored-records'
        receipt = row['receipt']['value']
        original = targets[receipt['obligation']]
        goal = original['goal']
        assert receipt['checkedGoal'] == (goal if receipt['mode'] == 'prove' else '¬ (' + goal + ')')
        assert receipt['status'] == original['status']
    return checked, inspection


def main():
    inputs = load(BASE / 'INPUTS.json')
    for file, digest in inputs['implementationFiles'].items():
        assert hashlib.sha256(Path(file).read_bytes()).hexdigest() == digest
    for file, digest in inputs['primaryInputs'].items():
        assert hashlib.sha256((BASE / file).read_bytes()).hexdigest() == digest
    faithful, fi = inspect_case('faithful')
    wrong, wi = inspect_case('wrong-map')
    uniform, _uniform_inspection = inspect_case('uniform')
    assert faithful['parentSupport'] == 'supported-for-attributed-interpretation'
    assert wrong['parentSupport'] == uniform['parentSupport'] == 'refuted-correspondence'
    assert wrong['premiseEstablishment'] == 'refuted'
    assert fi['interpretationRef'] == wi['interpretationRef']
    assert faithful['planId'] != wrong['planId']
    assert fi['objectMap'] != wi['objectMap']
    assert any(r['obligation'] == 'premise-1' and r['status'] == 'refuted' for r in wrong['checks'])
    assert any(r['obligation'] == 'conclusion' and r['status'] == 'refuted' for r in uniform['checks'])
    original = load(BASE / 'source-control.process.json')
    assert original['returncode'] == 0
    assert "'ContextFixture.original_source' does not depend on any axioms" in original['stdout']
    refutation = load(BASE / 'source-refutation.process.json')
    assert refutation['returncode'] == 0
    assert "'uniform_source_false' does not depend on any axioms" in refutation['stdout']
    result = {'qualification': 'passed', 'cases': 3, 'nativeReplayChecks': sum(
        len(bundle['checks']) for bundle in (faithful, wrong, uniform)),
        'faithfulSourceTrue': 'separately compiled without axioms',
        'wrongMap': 'selected route refuted; identical source claim is true',
        'uniform': 'conclusion transfer refuted; attributed source proposition separately refuted in ordinary Lean',
        'representationGap': 'none observed on these exposed controls',
        'discoveryOrReaderBenefit': 'not measured'}
    (BASE / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
