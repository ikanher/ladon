"""Root-only feasibility: native closed source regularity pair, actual proofs."""
import copy
import hashlib
import json
import shutil
import time
from pathlib import Path

from ladon._proof_contract_context_preparation import _native_plan
from ladon.correspondence_check import prepare_correspondence
from ladon.correspondence_interpretation import lower_formula
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_context_bridge import plan_context_bridge
from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts

p = Path('.codex/state/proof-contract-analysis/application-probes/feasibility')
origin = json.loads((p / 'START.json').read_text())
started, deadline = origin['startedMonotonic'], origin['deadlineMonotonic']
root = (p / 'repo').resolve()
root.mkdir(exist_ok=True)
shutil.copyfile('tests/fixtures/proof_contract_planned_source/lean-toolchain', root / 'lean-toolchain')
source = '''import Lean
import Std
namespace AppProbe
def M (_s _x : Nat) : Nat := 1
def N (s _x : Nat) : Nat := s
def F (x : Nat) : Nat := x
def C : Nat := 1
theorem weak (_tag : Unit) : ∀ s x : Nat, M s (F x) ≤ C * N (s + 1) x := by
  intro s x
  simp [M, N, F, C]
theorem use : ∀ s x : Nat, M s (F x) ≤ C * N (s + 1) x := weak ()
end AppProbe
'''
(root / 'Bridge.lean').write_text(source)
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}


def save(name, value):
    (p / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))


observed = run_bridge_job('extract-provider', {'repoRoot': str(root), 'sourcePath': 'Bridge.lean',
    'sourceDigest': 'sha256:' + hashlib.sha256(source.encode()).hexdigest(),
    'declaration': 'AppProbe.use', 'application': 'AppProbe.weak'},
    deadline_monotonic=deadline, limits=limits)
save('extraction-supervision-second', observed)
assert observed['status'] == 'completed', observed.get('diagnostic')
actual = observed['result']
save('actual', actual)
assert actual['complete'] and not actual['localContext'] and not actual['nodes'][0]['premises'], actual.get('diagnostic')
print('Actual closed source extracted', time.monotonic()-started, flush=True)
var = lambda name: {'tag': 'var', 'id': name}
const = lambda name: {'tag': 'const', 'name': str(name)}
app = lambda name, *args: {'tag': 'app', 'symbol': name, 'args': list(args)}
symbols = {key: {'leanName': value, 'leanType': typ} for key, value, typ in [
    ('M', 'AppProbe.M', 'Nat → Nat → Nat'), ('N', 'AppProbe.N', 'Nat → Nat → Nat'),
    ('F', 'AppProbe.F', 'Nat → Nat'), ('C', 'AppProbe.C', 'Nat'),
    ('add', 'Nat.add', 'Nat → Nat → Nat'), ('mul', 'Nat.mul', 'Nat → Nat → Nat')]}
batch, snapshots, refs = [], [], []
for offset in (0, 1):
    formula = {'tag': 'le', 'left': app('M', var('s'), app('F', var('x'))),
               'right': app('mul', const('C'), app('N', app('add', var('s'), const(offset)), var('x')))}
    for name in ('x', 's'):
        formula = {'tag': 'forall', 'binder': {'id': name, 'name': name, 'domain': 'Nat'}, 'body': formula}
    quote = f'For every s and x, M s (F x) <= C * N (s + {offset}) x.'
    raw = (quote + '\n').encode()
    filename = f'reading-{offset}.txt'
    (root / filename).write_bytes(raw)
    record = {'id': f'reading-{offset}', 'source': {'path': filename, 'startLine': 1, 'endLine': 1,
        'quote': quote, 'sha256': hashlib.sha256(raw).hexdigest()}, 'formula': formula, 'symbols': symbols}
    contract = {'profileId': 'norm-scale-v1', 'endpointId': 'estimate:AppProbe.F',
        'context': {'objectId': 'operator:AppProbe.F', 'domainId': 'domain:Nat',
            'scaleId': 'scale:AppProbe.N', 'representationId': 'representation:original'},
        'telescope': [{'binderId': n, 'typeId': 'Nat', 'quantifier': 'forall'} for n in ('s', 'x')],
        'assumptions': [], 'conclusionId': 'estimate:AppProbe.bound', 'features': {
            'regularity': {'state': 'known', 'scaleId': 'scale:AppProbe.N', 'offset': offset, 'reason': None},
            'constantDependencies': {'state': 'known', 'allowedBinderIds': [], 'reason': None},
            'witnessDependencies': []}}
    origins = {'regularity': ['/formula/body/body/right/args/1/args/0/args/1'],
               'constantDependencies': ['/formula'], 'witnessDependencies': ['/formula']}
    snapshot = produce_prose_contract(root, record, contract, origins,
        alternative_id=f'reading-{offset}', environment_ref=actual['environment'])
    snapshots.append(snapshot)
    batch.extend(snapshot['artifacts'])
for snapshot in snapshots:
    plan = prepare_correspondence(snapshot['interpretation'], actual, {})
    plan = bind_native_interpretation(plan, batch, source_root=root)
    owner = correspondence_artifacts(plan)
    batch.append(owner)
    refs.append({'artifactRef': owner['artifactId'], 'kind': 'correspondence',
                 'localId': owner['payload']['correspondenceId']})
request = {'repoRoot': str(root), 'context': {'artifacts': batch}, 'correspondenceRef': refs[0],
           'deadlineMonotonic': deadline, 'limits': limits}
save('snapshots', snapshots)
save('request', request)
prepared = plan_context_bridge(request)
save('prepared', prepared)
assert prepared['status'] == 'planned', prepared.get('diagnostic')
other_request = {**request, 'correspondenceRef': refs[1]}
other, _, _ = _native_plan(other_request, root)
assert other['slice'] == actual and other['objectMap'] == {}
print('Both native owners and strict prefix prepared', time.monotonic()-started, flush=True)
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
        'symbols': symbols}, deadline_monotonic=deadline, limits=limits)
    save(name, checked)
    assert checked['status'] == 'completed' and _accepted_check(checked['result']), (name, checked.get('diagnostic'), checked.get('result', {}).get('status'))
    print(name, 'accepted', time.monotonic()-started, flush=True)
save('RESULT', {'status': 'PASS', 'elapsedSeconds': time.monotonic()-started,
    'budgetSeconds': 180, 'actualClosedSource': True, 'nativeContracts': 2, 'checkedGoals': 2,
    'prefixExcludesParent': True, 'scope': 'regularity only; prototype, not task1.1 acceptance'})
