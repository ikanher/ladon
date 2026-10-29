from pathlib import Path
from dataclasses import asdict
import json,shutil,sys,time
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES

base=Path('.codex/state/derivative-prefix').resolve()
out=base/'generic-first';out.mkdir(exist_ok=False)
root=out/'project';root.mkdir()
original=base.parent/'real-bound-admission/consumer-project'
(root/'lean-toolchain').write_bytes((original/'lean-toolchain').read_bytes())
(root/'.lake').mkdir();(root/'.lake/packages').symlink_to(original/'.lake/packages',target_is_directory=True)
for path in Path('tests/fixtures/derivative_prefix').glob('*.lean'):shutil.copy2(path,root/path.name)

def save(name,value):
 (out/name).write_text(json.dumps(value,indent=2))
def cli(name,args):
 command=[sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)]
 r=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=660,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 save(name+'-command.json',asdict(r));assert not r.timed_out and not r.memory_limited
 return r
snapshot=produce_formal_snapshot(root,'JointFamilies.lean','JointFamilies','CloudBounds.stationary')
save('formal.json',snapshot);print('formal',snapshot['status'],snapshot['observation']['status'],flush=True)
observation=observe_bound_snapshot(snapshot,root);save('observation.json',observation);assert observation['status']=='observed',observation['residuals']
plan=out/'plan.json'
r=cli('plan',['plan-derivative-prefix','--root',root,'--input',out/'observation.json','--output',plan])
assert r.returncode==2 and plan.exists(),r.stdout+r.stderr
proof='by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl'
save('proof.json',{'term':proof})
r=cli('check',['check-derivative-prefix','--root',root,'--input',plan,'--proof',out/'proof.json','--timeout-seconds','600','--output',out/'result.json'])
result=json.loads((out/'result.json').read_text());print('result',result['status'],r.returncode,r.elapsed_seconds,flush=True)
checked=result['supervision'].get('result') or {}
if checked.get('check'):
 actual=checked['check']['evidence'];print('actual',actual.get('status'),flush=True)
 if actual.get('status')!='supported':
  print('typing',actual.get('typecheck',{}).get('stdout','')[:2000])
  print('completion',actual.get('completion',{}).get('diagnostic'))
 print('goal',actual.get('typedSubject',{}).get('subject',{}).get('display','')[:2000])
else:print('supervision',result['supervision'].get('diagnostic'))
