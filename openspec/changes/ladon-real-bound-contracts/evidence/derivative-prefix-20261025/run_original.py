"""Replay frozen informed observations only after generic derivative controls pass."""
from pathlib import Path
from dataclasses import asdict
import json,sys
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/derivative-prefix').resolve()
matrix=json.loads((base/'matrix/RESULTS.json').read_text());assert len(matrix)==9
assert matrix[0]['status']=='checked-binding' and all(r['status']=='unresolved' for r in matrix[1:])
out=base/'original';out.mkdir(exist_ok=False)
root=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
frozen=Path('openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025')
proof='by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
rows=[]
def cli(name,args):
 r=run_bounded_target_process([sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)],
  cwd=Path.cwd(),timeout_seconds=660,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (out/(name+'-command.json')).write_text(json.dumps(asdict(r),indent=2))
 assert not any((r.timed_out,r.memory_limited,r.output_limited)),(name,r.stdout,r.stderr)
 return r
for name in ('inverse_finiteJets','nonbarPart_finiteJets'):
 observed=frozen/(name+'.json');obs=json.loads(observed.read_text())
 plan=out/(name+'-plan.json')
 r=cli(name+'-plan',['plan-derivative-prefix','--root',root,'--input',observed,'--output',plan])
 assert r.returncode==2 and plan.exists(),(name,r.stdout,r.stderr)
 pf=out/(name+'-proof.json');pf.write_text(json.dumps({'term':proof}))
 resultpath=out/(name+'-result.json')
 r=cli(name,['check-derivative-prefix','--root',root,'--input',plan,'--proof',pf,'--timeout-seconds','600','--output',resultpath])
 assert resultpath.exists(),(name,r.stdout,r.stderr)
 result=json.loads(resultpath.read_text())
 checked=result['supervision'].get('result') or {};actual=(checked.get('check') or {}).get('evidence',{})
 row={'case':name,'loss':obs['candidate']['loss'],'status':result['status'],'derivativeAdmission':result['derivativeAdmission'],
      'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'exitCode':r.returncode,
      'diagnostic':actual.get('completion',{}).get('diagnostic') or actual.get('diagnostic')}
 rows.append(row);(out/'progress.json').write_text(json.dumps(rows,indent=2));print(json.dumps(row),flush=True)
 if result['status']!='checked-binding':
  print('typing',actual.get('typecheck',{}).get('stdout','')[:2000],flush=True)
 assert r.returncode==0 and result['status']=='checked-binding',name
 assert result['paperNormBridge']=='unresolved' and result['admission']=='unresolved' and result['contract'] is None
unsupported=frozen/'applyMultiplier_finiteJets.json'
r=cli('symbolic',['plan-derivative-prefix','--root',root,'--input',unsupported])
assert r.returncode==2 and json.loads(r.stdout)['status']=='invalid'
(out/'RESULTS.json').write_text(json.dumps(rows,indent=2))
print('original derivative bindings2/2; symbolic remains unsupported',flush=True)
