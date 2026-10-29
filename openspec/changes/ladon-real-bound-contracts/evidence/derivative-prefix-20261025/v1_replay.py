"""Root-owned real CLI controls; each process is bounded and each output immutable."""
from pathlib import Path
from dataclasses import asdict
from copy import deepcopy
import json,shutil,sys,time
from ladon.proof_contract_formal import produce_formal_snapshot, _replay_summary
from ladon.proof_contract_source import snapshot_identity
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

BASE=Path('.codex/state/derivative-prefix').resolve()
OUT=BASE/'v1-replay';OUT.mkdir(exist_ok=False)
ORIGINAL=BASE.parent/'real-bound-admission/consumer-project'
TERM='by intro P inst; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
ROWS=[]

def save(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2)

def project(name,fixture,replace=None):
    root=OUT/name;root.mkdir();shutil.copy2(ORIGINAL/'lean-toolchain',root/'lean-toolchain')
    (root/'.lake').mkdir();(root/'.lake/packages').symlink_to(ORIGINAL/'.lake/packages',target_is_directory=True)
    text=Path(fixture).read_text()
    if replace:text=text.replace(*replace)
    (root/'Case.lean').write_text(text)
    return root

def observation(root,declaration,name):
    formal=produce_formal_snapshot(root,'Case.lean','Case',declaration)
    assert formal['observation']['status']=='observed',formal['residuals']
    result=observe_bound_snapshot(formal,root)
    assert result['status']=='observed',result['residuals']
    save(OUT/(name+'-formal.json'),formal);save(OUT/(name+'-observation.json'),result)
    return result

def cli(name,args):
    command=[sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)]
    result=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=660,
        max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
    save(OUT/(name+'-command.json'),asdict(result))
    assert not result.timed_out and not result.memory_limited and not result.output_limited, name
    return result

def check(name,root,observed,measure,term,expected,detail=None):
    op=OUT/(name+'-input.json');save(op,observed)
    mp=OUT/(name+'-measure.json');save(mp,measure)
    plan=OUT/(name+'-plan.json')
    planned=cli(name+'-plan',['plan-bound-prefix','--root',root,'--input',op,'--measure',mp,'--output',plan])
    assert planned.returncode==2 and plan.exists(),(name,planned.stdout,planned.stderr)
    pp=OUT/(name+'-proof.json');save(pp,{'term':term})
    output=OUT/(name+'-result.json')
    run=cli(name,['check-bound-prefix','--root',root,'--input',plan,'--proof',pp,'--timeout-seconds','600','--output',output])
    result=json.loads(output.read_text());assert result['status']==expected,(name,result['status'])
    assert run.returncode==(0 if expected=='checked-binding' else 2)
    assert result['admission']=='unresolved' and result['contract'] is None
    actual=result['supervision']['result']['check']['evidence']
    if detail:detail(actual)
    row={'case':name,'status':result['status'],'exitCode':run.returncode,'seconds':run.elapsed_seconds,
         'peakRssBytes':run.peak_rss_bytes,'checkStatus':actual['status'],
         'diagnostic':actual.get('completion',{}).get('diagnostic') or actual.get('diagnostic')}
    ROWS.append(row);print(json.dumps(row),flush=True)
    (OUT/'progress.json').write_text(json.dumps(ROWS,indent=2))
    return result

def no_false(actual):
    assert 'False' not in actual['typedSubject']['subject']['display']

def placeholder_rejected(actual):
    c=actual.get('completion',{});assert c['status']!='completed'
    assert 'sorryAx' in json.dumps(c)

root=project('dependent','tests/fixtures/real_bound_binding/DependentBounds.lean')
obs=observation(root,'DependentBounds.estimate','dependent')
measure={'declaration':'DependentBounds.sample','arguments':['b0','b1']}
check('dependent-positive',root,obs,measure,TERM,'checked-binding')
check('wrong-measure',root,obs,{**measure,'declaration':'DependentBounds.wrongSample'},TERM,'unresolved')
check('sorry',root,obs,measure,'by sorry','unresolved',placeholder_rejected)
bad=observation(root,'DependentBounds.misleading','misleading')
check('unused-false-no-rescue',root,bad,measure,'by intros; assumption','unresolved',no_false)

# A rehashed, internally coherent syntax snapshot still cannot redirect the live theorem.
fake=deepcopy(obs['statementSnapshot'])
expr=json.dumps(fake['observation']['normalizedTypeExpr']).replace('DependentBounds.envelope','DependentBounds.exactOrder')
fake['observation']['normalizedTypeExpr']=json.loads(expr)
fake.update(_replay_summary(fake,fake['observation'],fake['selection']['declaration']))
fake['snapshotId']=snapshot_identity(fake)
forged=observe_bound_snapshot(fake,root)
check('forged-live-expression',root,forged,measure,TERM,'unresolved')

changed=project('changed-definition','tests/fixtures/real_bound_binding/DependentBounds.lean',('∀ j ≤ n,','∀ j < n,'))
changedobs=observation(changed,'DependentBounds.estimate','changed-definition')
check('same-name-changed-definition',changed,changedobs,measure,TERM,'unresolved')

choices=project('choices','tests/fixtures/real_bound_binding/ParameterControls.lean')
choiceobs=observation(choices,'ChoiceBounds.estimate','choices')
# Lean's actual J uses the explicit second Inhabited parameter, b2.
cm={'declaration':'ChoiceBounds.sample','arguments':['b0','b2']}
check('unused-false-positive',choices,choiceobs,cm,TERM,'checked-binding',no_false)
wrongterm='by intro P first second; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
check('changed-instance',choices,choiceobs,{**cm,'arguments':['b0','b1']},wrongterm,'unresolved')
pobs=observation(choices,'ChoiceBounds.proofParameter','proof-parameter')
check('retained-proof-parameter',choices,pobs,{'declaration':'ChoiceBounds.sample','arguments':['b0','b1']},'by intros; assumption','unresolved')
save(OUT/'RESULTS.json',ROWS)
print('followup matrix completed',len(ROWS),flush=True)
