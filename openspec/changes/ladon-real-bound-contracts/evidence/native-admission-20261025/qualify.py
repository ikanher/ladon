"""Serial final-identity public CLI qualification; no target source mutations."""
import hashlib,json,shutil,sys,time
from pathlib import Path
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.derivative_prefix import plan_derivative_prefix
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_native_check import native_checker_identity
from ladon.proofir_v3 import validate_envelope_batch
from ladon.proofir_sqlite_v3 import project_envelopes,validate_v3_database
import sqlite3
base=Path('.codex/state/real-native').resolve();out=base/'qualification-final';out.mkdir(exist_ok=False)
root=out/'project';root.mkdir();original=base.parent/'real-bound-admission/consumer-project'
(root/'lean-toolchain').write_bytes((original/'lean-toolchain').read_bytes())
(root/'.lake').mkdir();(root/'.lake/packages').symlink_to(original/'.lake/packages',target_is_directory=True)
for path in [Path('tests/fixtures/real_bound_native/ScalarExamples.lean'),Path('tests/fixtures/derivative_prefix/JointFamilies.lean'),Path('tests/fixtures/real_bound_binding/DependentBounds.lean')]:
 shutil.copy2(path,root/path.name)
identity=native_checker_identity();started=time.monotonic();rows=[]
terms={'predicate-admission':'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
       'scalar-semantics':'by intros; exact ⟨rfl, rfl, rfl⟩'}
def save(name,value):
 p=out/(name+'.json');p.write_text(json.dumps(value,indent=2));return p
def cli(name,args):
 command=[sys.executable,'-m','ladon.entrypoint','investigation','contract',*map(str,args)]
 actual=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=660,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 save(name+'-command',asdict(actual))
 assert not any([actual.timed_out,actual.memory_limited,actual.output_limited]),name
 return actual

def exercise(label,observation,selected_root,expected,measure=None,proofs=None):
 assert native_checker_identity()==identity
 binding=plan_derivative_prefix(observation) if measure is None else plan_bound_prefix(observation,measure)
 binding_path=save(label+'-binding',binding);plan_path=out/(label+'-plan.json')
 result=cli(label+'-plan',['plan-real-bound','--input',binding_path,'--root',selected_root,'--output',plan_path])
 assert result.returncode==2 and plan_path.exists(),(label,result.stdout,result.stderr)
 pf=save(label+'-proofs',proofs or terms);result_path=out/(label+'-production.json')
 run=cli(label+'-admit',['admit-real-bound','--input',plan_path,'--root',selected_root,'--proofs',pf,'--timeout-seconds',600,'--output',result_path])
 assert result_path.exists(),(label,run.stdout,run.stderr)
 production=json.loads(result_path.read_text());inner=production['check'].get('result') or {}
 row={'case':label,'loss':observation['candidate']['loss'],'status':production['status'],'goals':[c['evidence']['status'] for c in inner.get('checks',[])],'seconds':run.elapsed_seconds,'peakRssBytes':run.peak_rss_bytes,'exitCode':run.returncode}
 rows.append(row);save('PROGRESS',rows);print(json.dumps(row),flush=True)
 assert production['status']==expected,(label,production['check'].get('diagnostic'),inner.get('compilations'))
 assert run.returncode==(0 if expected=='admitted' else 2)
 if expected=='admitted':
  assert production['authority']=='fresh-lean-check' and len(production['artifacts'])==4
  assert production['artifacts'][-1]['payload']['record']['loss']==observation['candidate']['loss']
  validate_envelope_batch(production['artifacts'])
  db=sqlite3.connect(':memory:');project_envelopes(db,production['artifacts']);validate_v3_database(db);assert db.execute('PRAGMA foreign_key_check').fetchall()==[];db.close()
 else:assert production['artifacts']==[] and production['authority']=='none'
 for operation in ['inspect-real-bound','report-real-bound']:
  actual=cli(label+'-'+operation,[operation,'--input',result_path,'--root',selected_root])
  view=json.loads(actual.stdout);assert actual.returncode==0 and view['authority']=='none' and not view['freshCheck']
 return result_path

# Generic positives precede informed cases.
for label,file,decl,measure in [
 ('canonical','ScalarExamples.lean','ScalarExamples.ordinary',None),
 ('loss-seven','JointFamilies.lean','RiverBounds.longerInput',None),
 ('named','DependentBounds.lean','DependentBounds.estimate',{'declaration':'DependentBounds.sample','arguments':['b0','b1']})]:
 formal=produce_formal_snapshot(root,file,Path(file).stem,decl);save(label+'-formal',formal)
 obs=observe_bound_snapshot(formal,root);save(label+'-observation',obs);assert obs['status']=='observed'
 path=exercise(label,obs,root,'admitted',measure)
 if label=='canonical':canonical_path=path;canonical_observation=obs
# Real dictionaries may leave J valid while invalidating scalar semantics.
for label,decl in [('multiplication','ScalarExamples.BadMultiplication.estimate'),('order','ScalarExamples.BadOrder.estimate'),('zero','ScalarExamples.BadZero.estimate')]:
 formal=produce_formal_snapshot(root,'ScalarExamples.lean','ScalarExamples',decl);save(label+'-formal',formal)
 obs=observe_bound_snapshot(formal,root);save(label+'-observation',obs)
 exercise(label,obs,root,'unresolved');assert rows[-1]['goals']==['supported','unresolved']
exercise('placeholder',canonical_observation,root,'unresolved',proofs={**terms,'predicate-admission':'by sorry'})
# Fresh replay must execute both checks again, rather than inspect the stored result.
path=out/'canonical-replay.json';r=cli('canonical-replay',['replay-real-bound','--input',canonical_path,'--root',root,'--timeout-seconds',600,'--output',path])
assert r.returncode==0 and path.exists(),(r.stdout,r.stderr)
replayed=json.loads(path.read_text());old=json.loads(canonical_path.read_text());assert replayed['status']=='admitted' and replayed['authority']=='fresh-lean-check'
assert replayed['check']['workerInputDigest']!=old['check']['workerInputDigest']
save('REPLAY',{'status':'admitted','seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes,'freshJob':True})
# The two informed fixed-loss cases retain exact observed losses/endpoints.
informed_root=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
frozen=Path('openspec/changes/ladon-real-bound-contracts/evidence/shape-observation-20261025')
for name in ['inverse_finiteJets','nonbarPart_finiteJets']:
 obs=json.loads((frozen/(name+'.json')).read_text());exercise(name,obs,informed_root,'admitted')
# Symbolic shape cannot become a native admission plan.
unsupported=json.loads((frozen/'applyMultiplier_finiteJets.json').read_text())
r=cli('symbolic',['plan-derivative-prefix','--root',informed_root,'--input',frozen/'applyMultiplier_finiteJets.json'])
assert r.returncode==2 and json.loads(r.stdout)['status']=='invalid'
assert native_checker_identity()==identity
save('RESULTS',{'cases':rows,'identityUnchanged':True,'seconds':time.monotonic()-started,'symbolic':'unsupported','paperNormBridge':'unresolved','sourceTheoremProof':'not-checked','informedAdmissions':'2/2'})
print('final native qualification passed',flush=True)
