"""Root-only bounded feasibility for exact quantified-constant source readings."""
import copy
import hashlib
import json
import shutil
import time
from pathlib import Path

from ladon.correspondence_check import prepare_correspondence
from ladon.correspondence_interpretation import lower_formula
from ladon.proof_contract_bridge import _accepted_check
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_context_bridge import plan_context_bridge
from ladon.proof_contract_source import produce_prose_contract
from ladon.proofir_correspondence import bind_native_interpretation, correspondence_artifacts

p = Path('.codex/state/proof-contract-analysis/constant-probes/feasibility')
root = (p / 'repo').resolve()
root.mkdir()
shutil.copyfile('tests/fixtures/proof_contract_planned_source/lean-toolchain', root / 'lean-toolchain')
source = '''import Lean
import Std
namespace UniformProbe
def M (s _x : Nat) : Nat := s
def N (_s _x : Nat) : Nat := 1
def F (x : Nat) : Nat := x
theorem weak (_tag : Unit) : ∀ s : Nat, ∃ c : Nat, ∀ x : Nat,
    M s (F x) ≤ c * N (s + 0) x := by
  intro s
  refine ⟨s, ?_⟩
  intro x
  simp [M, N, F]
theorem use : ∀ s : Nat, ∃ c : Nat, ∀ x : Nat,
    M s (F x) ≤ c * N (s + 0) x := weak ()
end UniformProbe
'''
(root / 'Bridge.lean').write_text(source)
started = time.monotonic()
deadline = started + 1800
limits = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3, 'max_output_bytes': 8 * 1024**2}


def save(name, value):
    with (p / (name + '.json')).open('x') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2)


save('START', {'startedMonotonic': started, 'deadlineMonotonic': deadline,
    'budgetSeconds': 1800, 'limits': limits, 'scope': 'Feasibility only, before production edits'})
observed = run_bridge_job('extract-provider', {'repoRoot': str(root), 'sourcePath': 'Bridge.lean',
    'sourceDigest': 'sha256:' + hashlib.sha256(source.encode()).hexdigest(),
    'declaration': 'UniformProbe.use', 'application': 'UniformProbe.weak'},
    deadline_monotonic=deadline, limits=limits)
save('extraction', observed)
assert observed['status'] == 'completed', observed.get('diagnostic')
actual = observed['result']
assert actual['complete'] and not actual['localContext'] and not actual['nodes'][0]['premises']
save('actual', actual)
symbols = {k: {'leanName': n, 'leanType': t} for k, n, t in [
    ('M', 'UniformProbe.M', 'Nat → Nat → Nat'), ('N', 'UniformProbe.N', 'Nat → Nat → Nat'),
    ('F', 'UniformProbe.F', 'Nat → Nat'), ('mul', 'Nat.mul', 'Nat → Nat → Nat'),
    ('add', 'Nat.add', 'Nat → Nat → Nat')]}


def var(identity):
    return {'tag': 'var', 'id': identity}


def app(symbol, *args):
    return {'tag': 'app', 'symbol': symbol, 'args': list(args)}


snapshots, batch = [], []
for index in (0, 1, 2):
    strong = index == 0
    order = [('c', 'exists'), ('s', 'forall'), ('x', 'forall')] if strong else [
        ('s', 'forall'), ('c', 'exists'), ('x', 'forall')]
    body = {'tag': 'le', 'left': app('M', var('s'), app('F', var('x'))),
        'right': app('mul', var('c'), app('N', app('add', var('s'), {'tag': 'const', 'name': '0'}), var('x')))}
    formula = copy.deepcopy(body)
    for identity, quantifier in reversed(order):
        formula = {'tag': quantifier, 'binder': {'id': identity, 'name': identity, 'domain': 'Nat'}, 'body': formula}
    quote = ('There is a natural c such that for every natural s and x, M s (F x) <= c * N (s + 0) x.'
        if strong else 'For every natural s there is a natural c such that for every natural x, M s (F x) <= c * N (s + 0) x.')
    raw = (quote + '\n').encode()
    filename = f'reading-{index}.txt'
    (root / filename).write_bytes(raw)
    reading = {'id': f'uniform-reading-{index}', 'source': {'path': filename, 'startLine': 1, 'endLine': 1,
        'quote': quote, 'sha256': hashlib.sha256(raw).hexdigest()}, 'formula': formula, 'symbols': symbols}
    permitted = [] if strong else ['s']
    contract = {'profileId': 'norm-scale-v1', 'endpointId': 'estimate:UniformProbe.F',
        'context': {'objectId': 'operator:UniformProbe.F', 'domainId': 'domain:Nat',
                    'scaleId': 'scale:UniformProbe.N', 'representationId': 'representation:original'},
        'telescope': [{'binderId': identity, 'typeId': 'Nat', 'quantifier': q} for identity, q in order],
        'assumptions': [], 'conclusionId': 'estimate:UniformProbe.bound', 'features': {
            'regularity': {'state': 'known', 'scaleId': 'scale:UniformProbe.N', 'offset': 0, 'reason': None},
            'constantDependencies': {'binderId': 'c', 'state': 'known', 'allowedBinderIds': permitted, 'reason': None},
            'witnessDependencies': [{'binderId': 'c', 'state': 'known', 'allowedBinderIds': permitted, 'reason': None}]}}
    origins = {'regularity': ['/formula/body/body/body/right/args/1/args/0/args/1'],
               'constantDependencies': ['/formula'], 'witnessDependencies': ['/formula']}
    snapshot = produce_prose_contract(root, reading, contract, origins,
        alternative_id=reading['id'], environment_ref=actual['environment'])
    snapshots.append(snapshot)
    batch.extend(snapshot['artifacts'])
sides = []
for snapshot in snapshots:
    native = correspondence_artifacts(bind_native_interpretation(
        prepare_correspondence(snapshot['interpretation'], actual, {}), batch, source_root=root))
    batch.append(native)
    contract = next(a for a in snapshot['artifacts'] if a['artifactKind'] == 'proofir.contract')
    sides.append({'contractRef': {'artifactRef': contract['artifactId'], 'kind': 'contract',
                                 'localId': contract['payload']['contractId']},
        'correspondenceRef': {'artifactRef': native['artifactId'], 'kind': 'correspondence',
                              'localId': native['payload']['correspondenceId']}})
save('snapshots', snapshots)
save('context', {'artifacts': batch})
save('sides', sides)
request = {'repoRoot': str(root), 'context': {'artifacts': batch},
    'correspondenceRef': sides[0]['correspondenceRef'], 'deadlineMonotonic': deadline, 'limits': limits}
save('context-request', request)
prepared = plan_context_bridge(request)
save('context-prepared', prepared)
assert prepared['status'] == 'planned', prepared.get('diagnostic')
left, right = [lower_formula(s['interpretation']['formula'], symbols) for s in snapshots[:2]]
terms = {'formal-reading': 'Iff.rfl', 'probe': '''by
  constructor
  · exact UniformProbe.weak ()
  · intro h
    obtain ⟨c, hc⟩ := h
    have bad : c + 1 ≤ c := by
      simpa [UniformProbe.M, UniformProbe.N, UniformProbe.F] using hc (c + 1) 0
    exact Nat.not_succ_le_self c bad'''}
save('terms', terms)
for name, goal in [('formal-reading', f'({right}) ↔ ({actual["nodes"][0]["closedType"]})'),
                   ('probe', f'({right}) ∧ ¬({left})')]:
    checked = run_bridge_job('check-goal', {**prepared['adapter'], 'goal': goal,
        'term': terms[name], 'symbols': symbols}, deadline_monotonic=deadline, limits=limits)
    save(name, checked)
    assert checked['status'] == 'completed' and _accepted_check(checked['result']), (name, checked.get('diagnostic'))
    print(name, 'accepted', time.monotonic() - started, flush=True)
save('RESULT', {'status': 'PASS', 'elapsedSeconds': time.monotonic() - started,
    'nativeInterpretations': 3, 'actualCheckedGoals': 2, 'scope': 'Feasibility; not production qualification'})
