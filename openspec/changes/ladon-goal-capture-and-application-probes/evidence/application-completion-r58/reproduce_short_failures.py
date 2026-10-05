import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,'src')
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon')
base=root/'.codex/state/application-completion-r58/feasibility'
lean='/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean'
limits={'timeoutSeconds':30,'maxOutputBytes':8*1024*1024,'maxRssBytes':32*1024**3}
# Reproduce the one-line binding omission that produced the earlier unknownIdentifier.
h=(base/'helper_nondep.lean').read_text()
h=h.replace('''  let nondep := match decl with
    | .ldecl _ _ _ _ _ nondep _ => nondep
    | .cdecl .. => false
''','')
hpath=base/'helper_failure_nondep.lean'; hpath.write_text(h)
src=base/'OwnerHave.lean'; b=src.read_bytes()
req={'protocolVersion':'ladon-lean-source-goal-v1/capture','contextRef':'nondep-failure-reproduction','module':'FidelityFixture.OwnerHave','filename':'OwnerHave.lean','sourceDigest':'sha256:'+hashlib.sha256(b).hexdigest(),'snapshotPath':str(src),'line':7,'column':13,'requestId':'nondep-failure-reproduction'}
cmd=[lean,'--run',str(hpath)]
r=run_bounded_target_process(cmd,cwd=root,timeout_seconds=30,max_output_bytes=limits['maxOutputBytes'],max_rss_bytes=limits['maxRssBytes'],input_bytes=('LADON_GOAL_REQUEST '+json.dumps(req)+'\n').encode())
(base/'helper-failure-reproduction-receipt.json').write_text(json.dumps({'kind':'exact unknown-nondep instrumentation failure reproduction','command':cmd,'cwd':str(root),'request':req,'limits':limits,'helperSha256':hashlib.sha256(h.encode()).hexdigest(),'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'outputLimited':r.output_limited,'memoryLimited':r.memory_limited,'stdout':r.stdout,'stderr':r.stderr},indent=2))
# Reproduce the initial replay script before its missing command namespace import was fixed.
rjson=json.loads((base/'synth-closure-receipt.json').read_text())
line=next(x[len('LADON_EXPERIMENT '):] for x in rjson['stdout'].splitlines() if x.startswith('LADON_EXPERIMENT ')); v=json.loads(line); items=[]
while isinstance(v,list) and len(v)==2: items.append(v[0]); v=v[1]
items.append(v); assert len(items)==7
target,proof=items[5],items[6]
replay='import Lean\n\ntheorem completionFeasibilityReplay : '+target+' :=\n  '+proof+'\n\nrun_cmd do\n  let axioms ← Lean.collectAxioms `completionFeasibilityReplay\n  let names := String.intercalate "," (axioms.toList.map toString)\n  logInfo m!"LADON_AXIOMS [{names}]"\n  if axioms.contains ``sorryAx then throwError "replay depends on sorryAx"\n'
rpath=base/'OwnerReplayNoOpen.lean'; rpath.write_text(replay)
cmd=[lean,str(rpath),'-o',str(base/'OwnerReplayNoOpen.olean')]
r=run_bounded_target_process(cmd,cwd=base,timeout_seconds=30,max_output_bytes=limits['maxOutputBytes'],max_rss_bytes=limits['maxRssBytes'])
(base/'replay-failure-reproduction-receipt.json').write_text(json.dumps({'kind':'exact missing-open command-scope failure reproduction','command':cmd,'cwd':str(base),'limits':limits,'sourceSha256':hashlib.sha256(replay.encode()).hexdigest(),'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'timedOut':r.timed_out,'outputLimited':r.output_limited,'memoryLimited':r.memory_limited,'stdout':r.stdout,'stderr':r.stderr},indent=2))
print(json.dumps({'helper':{'returncode':json.load(open(base/'helper-failure-reproduction-receipt.json'))['returncode'],'elapsedSeconds':json.load(open(base/'helper-failure-reproduction-receipt.json'))['elapsedSeconds'],'peakRssBytes':json.load(open(base/'helper-failure-reproduction-receipt.json'))['peakRssBytes'],'output':json.load(open(base/'helper-failure-reproduction-receipt.json'))['stdout'][-500:]},'replay':{'returncode':json.load(open(base/'replay-failure-reproduction-receipt.json'))['returncode'],'elapsedSeconds':json.load(open(base/'replay-failure-reproduction-receipt.json'))['elapsedSeconds'],'peakRssBytes':json.load(open(base/'replay-failure-reproduction-receipt.json'))['peakRssBytes'],'output':json.load(open(base/'replay-failure-reproduction-receipt.json'))['stdout'][-500:]}}))
