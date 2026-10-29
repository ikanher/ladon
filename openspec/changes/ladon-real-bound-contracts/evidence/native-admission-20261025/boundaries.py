"""Cheap public CLI rejection and historical-only checks; never compile new goals."""
from pathlib import Path
from dataclasses import asdict
import copy,json,sys
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.proof_contract_source import snapshot_identity
base=Path('.codex/state/real-native').resolve();out=base/'boundaries';out.mkdir(exist_ok=False)
old=base/'qualification';root=old/'project';rows=[]
def cli(label,args):
 actual=run_bounded_target_process([sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)],cwd=Path.cwd(),timeout_seconds=30,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (out/(label+'-command.json')).write_text(json.dumps(asdict(actual),indent=2))
 assert not any([actual.timed_out,actual.memory_limited,actual.output_limited])
 return actual
for label,timeout in [('nan','nan'),('infinite','inf'),('zero','0'),('negative','-1')]:
 r=cli('timeout-'+label,['admit-real-bound','--input',old/'canonical-plan.json','--root',root,'--proofs',old/'canonical-proofs.json','--timeout-seconds',timeout])
 assert r.returncode==2 and json.loads(r.stdout)['status']=='invalid'
 rows.append({'case':'timeout-'+label,'status':'invalid','freshCheck':False})
collision=out/'existing.json';collision.write_text('preserve original\n')
r=cli('output-collision',['plan-real-bound','--input',old/'canonical-binding.json','--root',root,'--output',collision])
assert r.returncode==2 and collision.read_text()=='preserve original\n';rows.append({'case':'output-collision','status':'invalid','preserved':True})
# Previous code identities stay offline-readable; root-aware semantic reuse rejects.
r=cli('history-offline',['inspect-real-bound','--input',old/'canonical-production.json'])
assert r.returncode==0 and json.loads(r.stdout)['authority']=='none'
for operation in ['inspect-real-bound','replay-real-bound']:
 r=cli('stale-'+operation,[operation,'--input',old/'canonical-production.json','--root',root])
 assert r.returncode==2 and 'stale Real checker' in json.loads(r.stdout)['error']
 rows.append({'case':'stale-'+operation,'status':'invalid','freshCheck':False})
production=json.loads((old/'canonical-production.json').read_text());production['sourceText']+='\n-- changed\n';production['snapshotId']=snapshot_identity(production)
p=out/'changed-source.json';p.write_text(json.dumps(production))
r=cli('rehashed-changed-source',['inspect-real-bound','--input',p])
assert r.returncode==2 and json.loads(r.stdout)['status']=='invalid';rows.append({'case':'rehashed-changed-source','status':'invalid'})
(base/'boundary-checks.json').write_text(json.dumps({'cases':rows,'invalidCases':len(rows),'oldEvidenceReadableOfflineOnly':True},indent=2))
print('Verified public boundary cases:',len(rows))
