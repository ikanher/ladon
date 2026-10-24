"""Resume only the nonsemantic receipt-normalization join, same original clock."""
import json
import sys
import time
from pathlib import Path

from ladon._proof_contract_context_preparation import _native_plan
from ladon.correspondence_interpretation import lower_formula
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job

p = Path('.codex/state/proof-contract-analysis/application-probes/feasibility')
start = json.loads((p / (sys.argv[1] if len(sys.argv) > 1 else 'START.json')).read_text())
request = json.loads((p / 'request.json').read_text())
prepared = json.loads((p / 'prepared.json').read_text())
snapshots = json.loads((p / 'snapshots.json').read_text())
root = Path(request['repoRoot'])
left_plan, _, _ = _native_plan(request, root)
owners = [a for a in request['context']['artifacts'] if a['artifactKind'] == 'proofir.correspondence']
other = next(a for a in owners if a['artifactId'] != request['correspondenceRef']['artifactRef'])
other_ref = {'artifactRef': other['artifactId'], 'kind': 'correspondence',
             'localId': other['payload']['correspondenceId']}
right_plan, _, _ = _native_plan({**request, 'correspondenceRef': other_ref}, root)
assert left_plan['slice'] == right_plan['slice'] and left_plan['objectMap'] == right_plan['objectMap'] == {}
actual = json.loads((p / 'actual.json').read_text())
assert actual['sliceId'] == left_plan['slice']['sliceId']
symbols = snapshots[0]['interpretation']['symbols']
left, right = [lower_formula(s['interpretation']['formula'], symbols) for s in snapshots]
goals = [('formal-reading', f'({right}) ↔ ({actual["nodes"][0]["closedType"]})', 'Iff.rfl'),
    ('counterexample', f'({right}) ∧ ¬ ({left})', '''by
  constructor
  · exact AppProbe.weak ()
  · intro h
    have bad := h 0 0
    simpa [AppProbe.M, AppProbe.N, AppProbe.F, AppProbe.C] using bad''')]
for name, goal, term in goals:
    checked = run_bridge_job('check-goal', {**prepared['adapter'], 'goal': goal, 'term': term,
        'symbols': symbols}, deadline_monotonic=start['deadlineMonotonic'], limits=request['limits'])
    (p / (name + '.json')).write_text(json.dumps(checked, ensure_ascii=False, separators=(',', ':')))
    assert checked['status'] == 'completed' and _accepted_check(checked['result']), (name, checked.get('diagnostic'), checked.get('result', {}).get('status'))
    print(name, 'accepted', time.monotonic()-start['startedMonotonic'], flush=True)
(p / 'RESULT.json').write_text(json.dumps({'status': 'PASS',
    'elapsedSeconds': time.monotonic()-start['startedMonotonic'], 'budgetSeconds': start['budgetSeconds'],
    'actualClosedSource': True, 'nativeContracts': 2, 'checkedGoals': 2,
    'prefixExcludesParent': True, 'nativeSlicesExactlyEqual': True,
    'scope': 'regularity only; authored reading contracts; not task1.1 acceptance'}, indent=2))
