"""Public, bounded derivative admission controls; each result is immutable."""
from pathlib import Path
from dataclasses import asdict
import json,shutil,sys
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/task41').resolve();out=base/'derivative';out.mkdir(exist_ok=False)
root=out/'project';root.mkdir()
original=Path('.codex/state/real-bound-admission/consumer-project').resolve()
(root/'lean-toolchain').write_bytes((original/'lean-toolchain').read_bytes())
(root/'.lake').mkdir();(root/'.lake/packages').symlink_to(original/'.lake/packages',target_is_directory=True)
for fixture in Path('tests/fixtures/derivative_prefix').glob('*.lean'):shutil.copy2(fixture,root/fixture.name)
proof='by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
rows=[]


def no_limits(value):
 if isinstance(value,dict):
  assert not any(value.get(k) is True for k in ('timedOut','memoryLimited','outputLimited','timed_out','memory_limited','output_limited')), 'resource stop is not a semantic negative'
  for child in value.values():no_limits(child)
 elif isinstance(value,list):
  for child in value:no_limits(child)

def save(name,value):
 with (out/name).open('x') as f:json.dump(value,f,indent=2)
def cli(name,args):
 r=run_bounded_target_process([sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)],
  cwd=Path.cwd(),timeout_seconds=660,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 save(name+'-command.json',asdict(r))
 assert not any((r.timed_out,r.memory_limited,r.output_limited)),name
 return r
def run(name,file,declaration,expected,term=proof,selected=root,supplied=None):
 if supplied is None:
  snapshot=produce_formal_snapshot(selected,file,Path(file).stem.replace('/','.'),declaration)
  save(name+'-formal.json',snapshot)
  assert snapshot['observation'] and snapshot['observation']['status']=='observed',(name,snapshot['residuals'])
  obs=observe_bound_snapshot(snapshot,selected)
 else:obs=supplied
 save(name+'-observation.json',obs);assert obs['status']=='observed',(name,obs['residuals'])
 plan=out/(name+'-plan.json')
 r=cli(name+'-plan',['plan-derivative-prefix','--root',selected,'--input',out/(name+'-observation.json'),'--output',plan])
 assert r.returncode==2 and plan.exists(),(name,r.stdout,r.stderr)
 save(name+'-proof.json',{'term':term});resultpath=out/(name+'-result.json')
 r=cli(name,['check-derivative-prefix','--root',selected,'--input',plan,'--proof',out/(name+'-proof.json'),
            '--timeout-seconds','600','--output',resultpath])
 assert resultpath.exists(),(name,r.stdout,r.stderr)
 result=json.loads(resultpath.read_text());no_limits(result);assert result['status']==expected,(name,result['status'])
 assert r.returncode==(0 if expected=='checked-binding' else 2)
 assert result['admission']=='unresolved' and result['contract'] is None and result['paperNormBridge']=='unresolved'
 checked=result['supervision']['result']
 if expected=='checked-binding':
  assert result['derivativeAdmission']=='checked'
  actual=checked['check']['evidence'];assert actual['completion']['trust']['accepted']
 else:assert result['derivativeAdmission']=='unresolved'
 actual=(checked.get('check') or {}).get('evidence',{})
 row={'case':name,'status':result['status'],'loss':obs['candidate']['loss'],'seconds':r.elapsed_seconds,
      'peakRssBytes':r.peak_rss_bytes,'checkStatus':actual.get('status'),
      'diagnostic':actual.get('completion',{}).get('diagnostic') or actual.get('diagnostic')}
 rows.append(row);(out/'progress.json').write_text(json.dumps(rows,indent=2))
 print(json.dumps(row),flush=True)
 return result

run('zero-loss','JointFamilies.lean','CloudBounds.stationary','checked-binding')
run('seven-loss','JointFamilies.lean','RiverBounds.longerInput','checked-binding')
run('parameter-only','NearMisses.lean','DerivativeNearMisses.parameterEstimate','unresolved')
run('restricted-point','NearMisses.lean','DerivativeNearMisses.pointEstimate','unresolved')
run('squared-norm','NearMisses.lean','DerivativeNearMisses.normEstimate','unresolved')
run('missing-instances','NearMisses.lean','WithoutInstances.estimate','unresolved')
run('complex-scalar','ComplexCase.lean','ComplexScalarBounds.estimate','unresolved')
run('proof-parameter','JointFamilies.lean','CloudBounds.proofParameter','unresolved')
run('placeholder','JointFamilies.lean','CloudBounds.stationary','unresolved',term='by sorry')
other=Path('.codex/state/real-bound-binding/fixture-project').resolve()
otherobs=json.loads(Path('.codex/state/real-bound-binding/observation.json').read_text())
run('non-product','','','unresolved',selected=other,supplied=otherobs)
save('RESULTS.json',rows)
