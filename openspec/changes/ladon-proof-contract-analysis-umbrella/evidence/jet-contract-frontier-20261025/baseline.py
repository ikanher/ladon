import json,subprocess,os,hashlib,datetime
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
repo=Path('/home/codex/projects/ladon')
base=repo/'openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/jet-contract-frontier-20261025'
root=repo/'.codex/state/navier-stokes-informed-diagnostic/formalization'
source=root/'NavierStokes/SmoothFamilyTorusInverse.lean'
meta={'startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtime':{str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [repo/'src/ladon/proof_contract_recognition.py',repo/'src/ladon/proof_contract_rules.py',repo/'src/ladon/proof_contract_formal.py',repo/'src/ladon/proof_contract_production.py']},'scope':'Three existing real source declarations; no authored feature overrides, no producer/profile changes. Existing current-checkout formal snapshot producer.'}
(base/'BASELINE.json').write_text(json.dumps(meta,indent=2)+'\n')
for name in ['inverse_finiteJets','applyMultiplier_finiteJets','nonbarPart_finiteJets']:
 cmd=[str(repo/'.venv/bin/python'),'-m','ladon.entrypoint','investigation','contract','produce','--channel','formal','--root',str(root),'--file','NavierStokes/SmoothFamilyTorusInverse.lean','--module','NavierStokes.SmoothFamilyTorusInverse','--declaration','NavierStokes.SmoothFamilyTorusInverse.'+name,'--timeout-seconds','60','--max-rss-mib','12288','--output',str(base/(name+'.json'))]
 r=run_bounded_target_process(cmd,cwd=repo,env={**os.environ,'PYTHONPATH':str(repo/'src')},timeout_seconds=120,max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
 (base/(name+'-command.json')).write_text(json.dumps({'command':cmd,'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'memoryLimited':r.memory_limited,'timedOut':r.timed_out,'outputLimited':r.output_limited,'stdout':r.stdout,'stderr':r.stderr},indent=2)+'\n')
 print(json.dumps({'name':name,'returncode':r.returncode,'elapsedSeconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes}),flush=True)
 if r.memory_limited:raise SystemExit('Stop progress and report back to user: the 12 GiB memory limit was not enough.')
 if r.timed_out or r.output_limited:raise SystemExit(2)
 if not (base/(name+'.json')).exists():raise SystemExit(r.stderr)
 v=json.loads((base/(name+'.json')).read_text());print(json.dumps({'status':v['status'],'coverage':v['coverage'],'residuals':v['residuals'],'observationStatus':v.get('observation',{}).get('status')}),flush=True)
