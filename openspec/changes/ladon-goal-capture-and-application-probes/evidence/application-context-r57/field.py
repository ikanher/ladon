from pathlib import Path
from dataclasses import asdict
import hashlib,json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/application-context-r57'
run=Path((state/'run-path').read_text().strip());out=run/'field';out.mkdir();repo=out/'repo';repo.mkdir()
lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean')
source='namespace BinderFixture\ntheorem use {α : Type} ⦃β : Type⦄ [Inhabited α]\n    (x : α) (y : β) (h : x = x) (k : y = y) : (x = x) ∧ (y = y) :=\n  And.intro h k\nend BinderFixture\n'
(repo/'lean-toolchain').write_text('leanprover/lean4:v4.32.1\n');(repo/'BinderFixture.lean').write_text(source)
compiled=repo/'.lake/build/lib/lean';compiled.mkdir(parents=True)
env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
rows=[]
budget_remaining=json.loads((state/'pre-final-field-budget.json').read_text())['remainingSeconds']
def record(name,argv,cwd,expected=0):
 global budget_remaining
 helper=name not in {'owned-fixture-build','stored-check'}
 assert not helper or budget_remaining>0
 deadline=min(30,budget_remaining) if helper else 30
 r=run_bounded_target_process(argv,cwd=cwd,env=env,timeout_seconds=deadline,max_output_bytes=64*1024**2,max_rss_bytes=32*1024**3)
 (out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr)
 if helper:budget_remaining-=r.elapsed_seconds
 row=asdict(r);row.pop('stdout');row.pop('stderr');row['name']=name;rows.append(row)
 (out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert not any([r.timed_out,r.memory_limited,r.output_limited]),row
 assert r.returncode==expected,(name,r.stdout,r.stderr)
 return r.stdout
record('owned-fixture-build',[str(lean),'-o',str(compiled/'BinderFixture.olean'),'BinderFixture.lean'],repo)
before={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()}
base=[str(run/'py311/bin/ladon'),'proof-search','check','candidate','--repo-root',str(repo),'--module','BinderFixture','--candidate','BinderFixture.use','--toolchain-mode','explicit','--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','20','--evidence-store',str(out/'registry.sqlite3')]
goal='∀ (α β : Type) [Inhabited α] (x : α) (y : β), (x = x) ∧ (y = y)'
raw=json.loads(record('partial-audit',base+['--goal',goal,'--projection','audit','--format','json'],Path('/tmp')))
assert raw['status']=='applicable-with-residuals',raw
assert raw['applicationObservationVersion']==4 and raw['semanticProtocol']=='ladon-lean-semantic-v4/check-candidate'
assert [r['typeDisplay'] for r in raw['residualPremises']]==['x = x','y = y']
assert len(raw['residualContexts'])==2
assert len(raw['selectedDeclaration']['binders'])==7
for ctx in raw['residualContexts']:
 assert any(l['userName']=='x' and l['dependencies'] for l in ctx['localContext'])
compact=json.loads(record('partial-compact',base+['--goal',goal,'--format','json'],Path('/tmp')))
check=compact['candidate']['check'];assert check['status']=='applicable-with-residuals'
assert check['selectedDeclaration']['name']=='BinderFixture.use'
assert check['residualContexts'][0]['residualOrdinal']==0
text=record('partial-text',base+['--goal',goal,'--format','text','--progress'],Path('/tmp'))
assert 'remaining goal 0: x = x' in text and 'selected declaration type:' in text
assert 'x : α' in text and 'implicit' in text
assert text.index('remaining goal')<text.index('evidenceReceipt:')
ref=check['checkRunRef']
expanded=json.loads(record('stored-check',[str(run/'py311/bin/ladon'),'proof-search','evidence','semantic-check',ref['artifactRef'],'--local-id',ref['localId'],'--repo-root',str(repo),'--evidence-store',str(out/'registry.sqlite3'),'--format','json'],Path('/tmp')))
assert expanded['status']=='available' and expanded['evidenceReceipt']['observationState']=='stored'
owner=next(s for s in expanded['artifact']['subjectRefs'] if s['kind']=='candidate-application')
assert owner['searchShape']['residualContexts']==raw['residualContexts']
assert owner['searchShape']['selectedDeclaration']==raw['selectedDeclaration']
valid='∀ (α β : Type) [Inhabited α] (x : α) (y : β), x = x → y = y → (x = x) ∧ (y = y)'
accepted=json.loads(record('valid-application',base+['--goal',valid,'--format','json'],Path('/tmp')))
assert accepted['candidate']['check']['status']=='accepted'
after={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()};assert before==after
summary={'status':'passed','scope':'ordinary installed handwritten candidate exploration; not captured-source completion or theorem discovery','candidate':json.loads((run/'identity.json').read_text()),'commands':len(rows),'outerProcessTreePeakRssBytes':max(r['peak_rss_bytes'] or 0 for r in rows),'outerProcessWallSeconds':sum(r['elapsed_seconds'] for r in rows),'sourceBefore':before,'sourceAfter':after,'comparison':'compact,text,audit and stored expansion share observed partial application meaning; valid application remains exploration acceptance','helperBudgetConservativeChargeSeconds':sum(r['elapsed_seconds'] for r in rows if r['name'] not in {'owned-fixture-build','stored-check'})}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
