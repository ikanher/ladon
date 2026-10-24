"""Root serial real-source controls; no target paper or reference answer inputs."""
import hashlib
import json
import os
import shutil
import sys
import time
from dataclasses import asdict
from pathlib import Path

from ladon.correspondence_check import prepare_correspondence
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_contract_context_bridge import check_context_bridge, plan_context_bridge
from ladon.proofir_correspondence import (
    bind_native_interpretation, correspondence_artifacts, interpretation_artifacts,
)

OUT = Path(sys.argv[1]).resolve()
ROOT = Path(sys.argv[2]).resolve()
LIMITS = {'timeout_seconds': 30, 'max_rss_bytes': 12 * 1024**3,
          'max_output_bytes': 8 * 1024**2}
START = time.monotonic()
DEADLINE = START + 1200


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        f.write('\n')


def var(identity):
    return {'tag': 'var', 'id': identity}


def const(name):
    return {'tag': 'const', 'name': str(name)}


def positive(identity):
    return {'tag': 'lt', 'left': const(0), 'right': var(identity)}


def forall(identity, domain, body):
    return {'tag': 'forall', 'binder': {'id': identity, 'name': identity, 'domain': domain}, 'body': body}


def implies(premise, conclusion):
    return {'tag': 'implies', 'premise': premise, 'conclusion': conclusion}


def process(name, command, timeout):
    result = run_bounded_target_process(command, cwd=Path.cwd(), env=os.environ.copy(),
        timeout_seconds=min(timeout, DEADLINE-time.monotonic()),
        max_rss_bytes=LIMITS['max_rss_bytes'], max_output_bytes=LIMITS['max_output_bytes'])
    save(OUT/(name+'-process.json'), asdict(result))
    assert not (result.memory_limited or result.output_limited or result.timed_out), asdict(result)
    return result


def extract(name, declaration, application):
    code = ('import json,sys; from ladon.proof_slice import extract_proof_slice; '
            'print(json.dumps(extract_proof_slice(sys.argv[1],"Contexts.lean","Contexts",'
            'sys.argv[2],sys.argv[3],scoped=True),separators=(",",":")))')
    result = process(name+'-extraction', [sys.executable, '-c', code, str(ROOT), declaration, application], 30)
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual['complete'], actual
    save(OUT/(name+'-original-slice.json'), actual)
    return actual


def request(name, quote, formula, symbols, mapping, actual, budget):
    raw = (quote+'\n').encode()
    (ROOT/(name+'.txt')).write_bytes(raw)
    (OUT/(name+'.txt')).write_bytes(raw)
    reading = {'id': 'reading:'+name, 'source': {'path': name+'.txt', 'startLine': 1,
        'endLine': 1, 'quote': quote, 'sha256': hashlib.sha256(raw).hexdigest()},
        'formula': formula, 'symbols': symbols}
    prepared = prepare_correspondence(reading, actual, mapping)
    artifacts = list(interpretation_artifacts(reading, actual['environment'], source_root=ROOT))
    prepared = bind_native_interpretation(prepared, artifacts, source_root=ROOT)
    owner = correspondence_artifacts(prepared)
    artifacts.append(owner)
    req = {'repoRoot': str(ROOT), 'correspondenceRef': {'artifactRef': owner['artifactId'],
        'kind': 'correspondence', 'localId': owner['payload']['correspondenceId']},
        'context': {'artifacts': artifacts}, 'deadlineMonotonic': min(DEADLINE,time.monotonic()+budget),
        'limits': LIMITS.copy()}
    save(OUT/(name+'-input.json'), req)
    return req


def plan(name, req, cli=False):
    if cli:
        result = process(name+'-plan-cli', [sys.executable, '-m', 'ladon.entrypoint',
            'investigation', 'contract', 'context-obligations', '--input',
            str(OUT/(name+'-input.json')), '--output', str(OUT/(name+'-plan.json'))], 60)
        assert result.returncode == 0, result.stdout
        answer = json.loads((OUT/(name+'-plan.json')).read_text())
    else:
        answer = plan_context_bridge(req)
        save(OUT/(name+'-plan.json'), answer)
    assert answer['status'] == 'planned', answer['diagnostic']
    print('PLANNED',name, len(answer['goals']),flush=True)
    return answer


def check(name, req, prepared, terms, expected, cli=False):
    save(OUT/(name+'-terms.json'), terms)
    if cli:
        result = process(name+'-check-cli', [sys.executable, '-m', 'ladon.entrypoint',
            'investigation', 'contract', 'check-context-bridge', '--input',
            str(OUT/(name+'-input.json')), '--plan-id', prepared['planId'],
            '--terms', str(OUT/(name+'-terms.json')), '--output',
            str(OUT/(name+'-result.json'))], req['deadlineMonotonic']-time.monotonic())
        assert result.returncode == 0, result.stdout
        answer = json.loads((OUT/(name+'-result.json')).read_text())
    else:
        answer = check_context_bridge(req, prepared['planId'], terms)
        save(OUT/(name+'-result.json'), answer)
    print('CHECKED',name,answer['status'],answer.get('elapsedSeconds'),flush=True)
    assert answer['status'] == expected, answer['diagnostic']
    assert answer['wholeMethodAuthority']=='none' and answer['mathematicalFalsity']=='not-established'
    if expected == 'checked-support':
        assert all(g['status']=='checked-support' for g in answer['goals'])
        assert not answer['residuals']
    return answer


def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    shutil.copyfile('tests/fixtures/correspondence_m1/lean-toolchain',ROOT/'lean-toolchain')
    shutil.copyfile(ROOT/'lean-toolchain',OUT/'lean-toolchain')
    source='''import Lean
namespace Contexts
theorem both (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := And.intro hn hm
theorem bounded (n : Nat) (h : n < 5) : n < 5 := h
theorem dependent (n : Nat) (i : Fin n) : n = n := Eq.refl n
theorem ordered (n m : Nat) (hn : 0 < n) (hm : 0 < m) : 0 < n ∧ 0 < m := both n m hn hm
theorem represented (n : Nat) (h : n < 5) : n < 5 := bounded n h
end Contexts
'''
    (ROOT/'Contexts.lean').write_text(source);(OUT/'Contexts.lean').write_text(source)
    actual = extract('ordered','Contexts.ordered','Contexts.both')
    body={'tag':'and','items':[positive('n'),positive('m')]}
    formula=forall('n','Nat',forall('m','Nat',implies(positive('n'),implies(positive('m'),body))))
    req=request('ordered','Positive n and positive m give both positive.',formula,{},
        {'n':'n','m':'m'},actual,330)
    prepared=plan('ordered',req,cli=True)
    terms={'interpretation':'by intro h; exact h',
        'conditional':'by intro n m hn hm; exact And.intro hn hm',
        'domain':'by intro n m; dsimp only; exact ⟨⟨n, rfl⟩, ⟨m, rfl⟩⟩',
        'object-map':'by intro n m; trivial',
        'premise-2':'by intro n m; dsimp only; intro h; exact h.1',
        'premise-3':'by intro n m; dsimp only; intro h; exact h.2',
        'conclusion':'by intro n m; dsimp only; intro h hf; exact hf',
        'provider-2':'by intro n m hn hm; exact hn',
        'provider-3':'by intro n m hn hm; exact hm'}
    good=check('ordered',req,prepared,terms,'checked-support',cli=True)
    assert [g['occurrence'] for g in good['goals'] if g['kind']=='premise-supply']==[2,3]

    actual_rep=extract('representation','Contexts.represented','Contexts.bounded')
    val={'tag':'app','symbol':'val','args':[var('i')]}
    rep_formula=forall('i','Fin 5',{'tag':'lt','left':val,'right':const(5)})
    symbols={'val':{'leanName':'Fin.val','leanType':'Fin 5 → Nat'}}
    mapping={'n':{'symbol':'val','args':['i']}}
    rep=request('representation','A finite index below five has value below five.',rep_formula,symbols,mapping,actual_rep,270)
    rp=plan('representation',rep)
    rep_terms={'interpretation':'by intro h; exact h',
        'conditional':'by intro n h; exact h',
        'domain':'by intro i; dsimp only; exact ⟨i.val, rfl⟩',
        'object-map':'by intro i; trivial',
        'premise-1':'by intro i; dsimp only; intro h; exact i.isLt',
        'conclusion':'by intro i; dsimp only; intro h hf; exact hf',
        'provider-1':'by intro n h; exact h'}
    check('representation',rep,rp,rep_terms,'checked-support')

    actual_dep=extract('dependent','Contexts.dependent','Eq.refl')
    dep_formula=forall('n','Nat',forall('i','Fin n',{'tag':'eq','left':var('n'),'right':var('n')}))
    dep=request('dependent','For every n and index in Fin n, n equals n.',dep_formula,{},
        {'n':'n','i':'i'},actual_dep,210)
    dp=plan('dependent',dep)
    dep_terms={'interpretation':'by intro h; exact h','conditional':'by intro n i; rfl',
        'domain':'by intro n i; dsimp only; exact ⟨⟨n, rfl⟩, ⟨i, rfl⟩⟩',
        'object-map':'by intro n i; trivial',
        'conclusion':'by intro n i; dsimp only; intro h hf; exact hf'}
    check('dependent',dep,dp,dep_terms,'checked-support')

    missing_formula=forall('n','Nat',forall('m','Nat',implies(positive('n'),body)))
    missing=request('missing','Positive n gives n and m positive.',missing_formula,{},
        {'n':'n','m':'m'},actual,90)
    mp=plan('missing',missing)
    negative=check('missing',missing,mp,{'premise-3':'by intro n m; dsimp only; intro h; exact h'},'unresolved-bridge')
    assert next(g for g in negative['goals'] if g['id']=='premise-3')['status']=='unresolved'
    parent=request('parent','Positive n and positive m give both positive.',formula,{},
        {'n':'n','m':'m'},actual,90)
    pp=plan('parent',parent)
    check('parent',parent,pp,{'conclusion':'by intro n m; dsimp only; intro h hf; exact Contexts.ordered n m h.1 h.2'},'unresolved-bridge')
    one_formula=forall('i','Fin 5',{'tag':'eq','left':val,'right':const(0)})
    one=request('one-way','Every finite index below five has value zero.',one_formula,symbols,mapping,actual_rep,90)
    op=plan('one-way',one)
    check('one-way',one,op,{'conclusion':'by intro i; dsimp only; intro h hf; exact hf'},'unresolved-bridge')

    checkpoint={**one,'deadlineMonotonic':min(DEADLINE,time.monotonic()+60)}
    bad=check_context_bridge(checkpoint,rp['planId'],{})
    save(OUT/'changed-checkpoint-result.json',bad)
    assert bad['status']=='rejected' and not any('result' in g for g in bad['goals'])
    expired={**one,'deadlineMonotonic':0}
    stopped=plan_context_bridge(expired);save(OUT/'expired-result.json',stopped)
    assert stopped['status']=='incomplete' and 'preparation' not in stopped
    # Last control: intentional memory stop, never retried or raised.
    memory={**one,'deadlineMonotonic':min(DEADLINE,time.monotonic()+60),
            'limits':{**LIMITS,'max_rss_bytes':1024**2}}
    mem=plan_context_bridge(memory);save(OUT/'memory-stop-input.json',memory);save(OUT/'memory-stop-result.json',mem)
    assert mem['status']=='incomplete' and mem['memoryReportBackRequired']
    assert 'Stop progress and report back to user' in mem['diagnostic']['message']
    assert (ROOT/'Contexts.lean').read_text()==source
    save(OUT/'acceptance.json',{'status':'PASS','positiveCases':['ordered','representation','dependent'],
        'unresolvedCases':['missing','parent','one-way'],'changedCheckpoint':'rejected',
        'expired':'incomplete','intentional1MiBMemoryStop':'incomplete-no-retry',
        'elapsedSeconds':time.monotonic()-START,'budgetSeconds':1200,
        'sourceSha256':hashlib.sha256(source.encode()).hexdigest(),
        'wholeMethodAuthority':'none','detectionBenefit':'unmeasured'})


if __name__=='__main__':
    main()
