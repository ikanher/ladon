from pathlib import Path
from dataclasses import asdict
import hashlib, json, os, shutil
from ladon.process_supervisor import run_bounded_target_process

root=Path('/home/codex/projects/ladon')
run=Path((root/'.codex/state/source-goal-cli-r56/run-path').read_text().strip())
out=run/'field'; out.mkdir()
repo=out/'repo'; repo.mkdir()
lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean')
(repo/'lean-toolchain').write_text('leanprover/lean4:v4.32.1\n')
source=('namespace Owner\nsection Inside\nvariable (α : Type)\nopen Nat\nset_option pp.universes true\nexample (x : α) (h : x = x) : (x = x) ∧ (x = x) := by\n  let x : α := x\n  constructor\n  · skip\n    exact h\n  · skip\n    exact h\nend Inside\nend Owner\n')
(repo/'Owner.lean').write_text(source)
(repo/'Done.lean').write_text('example : True := by trivial\n')
(repo/'Modular.lean').write_text('module\nexample : True := by trivial\n')
(repo/'Mismatch.lean').write_text('structure Box where\n  value : Nat\nexample : Box := { value := True }\n')
before={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()}
environment=dict(os.environ)
for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'): environment.pop(key,None)
base=[str(run/'py311/bin/ladon'),'proof-search','goal']
common=['--repo-root',str(repo),'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','20']
rows=[]; payloads={}
def call(name,args,expected,*,text=False):
 argv=base+args+common+['--format','text' if text else 'json']
 result=run_bounded_target_process(argv,cwd=Path('/tmp'),env=environment,timeout_seconds=55,max_output_bytes=64*1024**2,max_rss_bytes=32*1024**3)
 (out/(name+'.stdout')).write_text(result.stdout)
 (out/(name+'.stderr')).write_text(result.stderr)
 record=asdict(result); record.pop('stdout'); record.pop('stderr'); record['name']=name
 rows.append(record)
 (out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n')
 assert not (result.timed_out or result.memory_limited or result.output_limited), record
 assert result.returncode==expected,(name,record,result.stdout,result.stderr)
 if text: return result.stdout
 payload=json.loads(result.stdout); payloads[name]=payload
 print(name,payload['status'],round(result.elapsed_seconds,3),flush=True)
 return payload
capture=['capture','--source','Owner.lean','--module','Owner','--line','8','--column','13']
a=call('ambiguous',capture,1); assert a['status']=='ambiguous' and a['capture'] is None
x=call('ordinal-0',capture+['--goal-ordinal','0'],0)
y=call('ordinal-1',capture+['--goal-ordinal','1'],0)
ac,bc=x['capture'],y['capture']
assert ac['goal']['goalCount']==bc['goal']['goalCount']==2
assert ac['goal']['goalId']!=bc['goal']['goalId']
locals=ac['goal']['localContext']; visible=[r for r in locals if not r['implementationDetail']]
shadow=[r for r in visible if r['userName']=='x']; assert len(shadow)==2,visible
assert shadow[0]['localId']!=shadow[1]['localId']
assert shadow[1]['valueDisplay'] and shadow[0]['localId'] in shadow[1]['dependencies']
assert ac['source']['position']['byteOffset']==len(source[:source.index('  constructor')+13].encode())
assert ac['source']['digest']=='sha256:'+before['Owner.lean']
assert ac['environment']['namespace']=='Owner'
assert 'Nat' in ac['environment']['openDeclarationsStructural']
assert 'pp.universes' in ac['environment']['optionsStructural']
assert ac['environment']['compiledInventory']
txt=call('ordinal-0-text',capture+['--goal-ordinal','0','--progress'],0,text=True)
assert 'goal: '+ac['goal']['typeDisplay'] in txt and '#/capture/goal/localContext' in txt
assert txt.index('goal:')<txt.index('capture identity:')
assert (out/'ordinal-0-text.stderr').read_text(), 'progress must be on stderr'
stale=call('stale',capture+['--expected-source-digest','sha256:'+'0'*64],1)
assert stale['status']=='stale' and stale['capture'] is None and not stale['processReceipts']
done=call('no-active-goal',['capture','--source','Done.lean','--module','Done','--line','1','--column','0'],1)
assert done['status']=='unavailable' and done['capture'] is None
mod=call('modular',['capture','--source','Modular.lean','--module','Modular','--line','2','--column','22'],1)
assert mod['status']=='unavailable' and mod['capture'] is None
# Generate the query with the actual pinned compiler; rejection is intentional.
diagnostic=run_bounded_target_process([str(lean),'Mismatch.lean'],cwd=repo,env=environment,timeout_seconds=20,max_output_bytes=8*1024**2,max_rss_bytes=32*1024**3)
assert diagnostic.returncode==1 and not diagnostic.timed_out
(out/'compiler.stdout').write_text(diagnostic.stdout); (out/'compiler.stderr').write_text(diagnostic.stderr)
(out/'compiler.command.json').write_text(json.dumps(asdict(diagnostic),indent=2)+'\n')
query=['diagnostic','--diagnostic-file',str(out/'compiler.stdout'),'--module','Mismatch']
d=call('compiler-diagnostic',query,1)
q=d['queryEvidence']; selected=q['selected']
assert q['status']=='parsed' and q['evidenceBasis']=='caller-supplied-compiler-text'
assert selected['line']==3 and selected['column']==28
assert selected['expression']=='True' and selected['actualType']=='Prop' and selected['expectedType']=='Nat'
assert d['status']=='unavailable' and d['captureResult']['capture'] is None
m=call('diagnostic-override-mismatch',query+['--source','Owner.lean'],1)
assert m['queryEvidence']==q and m['captureResult'] is None
(out/'outside-diagnostic.txt').write_text(diagnostic.stdout.replace('Mismatch.lean',str(out/'Outside.lean')))
outside=call('diagnostic-outside',['diagnostic','--diagnostic-file',str(out/'outside-diagnostic.txt'),'--module','Mismatch'],1)
assert outside['queryEvidence']['status']=='parsed' and outside['captureResult'] is None
after={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()}
assert after==before,(before,after)
capture_results=[p.get('captureResult') if p.get('schema')=='ladon-source-goal-query-result-v1' else p for p in payloads.values()]
receipts=[r for p in capture_results if p for r in p.get('processReceipts',[])]
summary={'status':'passed','candidate':json.loads((run/'candidate-identity.json').read_text()),'sourceBefore':before,'sourceAfter':after,'innerHelperCalls':len(receipts),'helperElapsedSeconds':sum(r['elapsedSeconds'] for r in receipts),'helperPeakRssBytes':max((r['peakRssBytes'] or 0 for r in receipts),default=0),'outerCliPeakRssBytes':max(r['peak_rss_bytes'] or 0 for r in rows),'commandCount':len(rows),'textResourceLimitation':'text rendering omits helper accounting; outer process-tree receipt retained, helper conservative bound charged separately'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
