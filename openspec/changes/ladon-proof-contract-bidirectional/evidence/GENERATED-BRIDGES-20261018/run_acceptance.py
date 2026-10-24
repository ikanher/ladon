"""Reproduce three bounded API controls using saved actual source snapshots."""
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from time import monotonic

from ladon.proof_contract_bridge import check_planned_source_bridge
from ladon.proof_contract_obligation_planner import ContractObligationPlanRequest
from ladon.proof_contract_source_obligations import _plain


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        stream.write('\n')


def run_case(out, name, raw, terms, budget):
    request = deepcopy(raw)
    request['planRequest'] = ContractObligationPlanRequest(**request['planRequest'])
    request['deadlineMonotonic'] = monotonic()+budget
    started = monotonic()
    save(out/(name+'-request.json'), {'sourceRequest': _plain(request), 'terms': terms})
    result = check_planned_source_bridge(request, terms)
    elapsed = monotonic()-started
    save(out/(name+'-result.json'), result)
    if result.get('preparation', {}).get('adapter'):
        adapter = result['preparation']['adapter']
        data = (Path(adapter['repoRoot'])/adapter['sourcePath']).read_bytes()
        assert 'sha256:'+hashlib.sha256(data).hexdigest() == adapter['sourceDigest']
        (out/(name+'-Bridge.lean')).write_bytes(data)
        record = result['preparation']['correspondence']['interpretation']
        sidecar = (Path(adapter['repoRoot'])/record['source']['path']).read_bytes()
        assert hashlib.sha256(sidecar).hexdigest() == record['source']['sha256']
        (out/(name+'-requirement.txt')).write_bytes(sidecar)
    row = {'case': name, 'status': result['status'], 'elapsedSeconds': elapsed,
           'budgetSeconds': budget, 'goals': [(g['id'],g['status']) for g in result['goals']]}
    print(json.dumps(row), flush=True)
    return result, row


def main():
    out, input_dir = map(Path, sys.argv[1:3])
    positive = json.loads((input_dir/'public-positive-request.json').read_text())['sourceRequest']
    middle = json.loads((input_dir/'first/source-request.json').read_text())
    root = Path(positive['repoRoot'])
    original = (root/'ThreeSteps.lean').read_bytes()
    (out/'ThreeSteps.lean').write_bytes(original)
    (out/'lean-toolchain').write_bytes((root/'lean-toolchain').read_bytes())
    transfer = 'by intro s x; dsimp only; intro h hformal; exact hformal'
    common = {'domain':'by intro s x; exact ⟨rfl, rfl⟩',
              'object-map':'by intro s x; trivial', 'conclusion':transfer}
    pos, p = run_case(out, 'positive', positive,
        {**common,'source-requirement':'by intro s x; exact ThreeSteps.firstBound s x'},180)
    assert pos['status']=='checked-support',pos['diagnostic']
    neg, n = run_case(out, 'middle', middle,
        {**common,'source-requirement':'by intro s x; exact ThreeSteps.secondBound s x'},180)
    assert neg['status']=='unresolved-bridge',neg['diagnostic']
    assert [g['status'] for g in neg['goals']]==['unresolved','checked-support','checked-support','unresolved']
    parent, c = run_case(out, 'parent', middle,
        {'conclusion':'by intro s x; dsimp only; intro h hformal; exact ThreeSteps.endpoint s x'},90)
    assert parent['status']=='unresolved-bridge',parent['diagnostic']
    assert all(g['status']=='unresolved' for g in parent['goals'])
    assert 'Unknown identifier' in parent['goals'][-1]['result']['completion']['diagnostic']['message']
    for result in (pos,neg,parent):
        assert result['wholeMethodAuthority']=='none'
        assert result['mathematicalFalsity']=='not-established'
        preparation=result['preparation']
        assert preparation['extraction']['result']['complete'] is True
        for goal in result['goals']:
            assert goal['binding']['selectedDemand']==preparation['selectedDemand']
            assert goal['binding']['selectedDemandDigest']==preparation['selectedDemandDigest']
            if goal['status']=='checked-support':
                completion=goal['result']['completion']
                assert completion['replay']['status']=='accepted'
                assert completion['trust']['accepted'] is True
    assert original==(root/'ThreeSteps.lean').read_bytes()
    save(out/'acceptance.json', {'schema':'ladon-generated-bridge-acceptance-v1',
        'cases':[p,n,c], 'originalSourceSha256':hashlib.sha256(original).hexdigest(),
        'proseFidelity':'not-reviewed','wholeMethodAuthority':'none',
        'detectionBenefit':'unmeasured','serialLean':True})


if __name__=='__main__':
    main()
