"""Small live feasibility gate before dependent native schema/storage work."""
from pathlib import Path
from dataclasses import asdict
import json,shutil
from ladon.proof_contract_formal import produce_formal_snapshot
from ladon.real_bound_observation import observe_bound_snapshot
from ladon.derivative_prefix import plan_derivative_prefix
from ladon.real_bound_native_plan import plan_real_bound
from ladon.real_bound_native_check import check_real_bound

base=Path('.codex/state/real-native').resolve();out=base/'scalar-probe';out.mkdir(exist_ok=False)
root=out/'project';root.mkdir();original=base.parent/'real-bound-admission/consumer-project'
(root/'lean-toolchain').write_bytes((original/'lean-toolchain').read_bytes())
(root/'.lake').mkdir();(root/'.lake/packages').symlink_to(original/'.lake/packages',target_is_directory=True)
shutil.copy2('tests/fixtures/real_bound_native/ScalarExamples.lean',root/'ScalarExamples.lean')
terms={'predicate-admission':'by intros; apply Ladon.RealBound.admit_of_equiv; intro f S n C; rfl',
       'scalar-semantics':'by intros; exact ⟨rfl, rfl, rfl⟩'}
rows=[]
for label,decl,expected in [('canonical','ScalarExamples.ordinary','checked'),
 ('multiplication','ScalarExamples.BadMultiplication.estimate','unresolved'),
 ('order','ScalarExamples.BadOrder.estimate','unresolved'),
 ('zero','ScalarExamples.BadZero.estimate','unresolved')]:
 formal=produce_formal_snapshot(root,'ScalarExamples.lean','ScalarExamples',decl)
 (out/(label+'-formal.json')).write_text(json.dumps(formal,indent=2))
 assert formal['observation'] and formal['observation']['status']=='observed',formal['residuals']
 obs=observe_bound_snapshot(formal,root);assert obs['status']=='observed',obs['residuals']
 plan=plan_real_bound(plan_derivative_prefix(obs))
 (out/(label+'-plan.json')).write_text(json.dumps(plan,indent=2))
 actual=check_real_bound(root,plan,terms,timeout_seconds=600)
 (out/(label+'-result.json')).write_text(json.dumps(actual,indent=2))
 result=actual.get('result') or {}
 checks=result.get('checks') or []
 row={'case':label,'status':result.get('status'),'goals':[c['evidence']['status'] for c in checks],
      'diagnostic':actual.get('diagnostic')}
 rows.append(row);print(row,flush=True)
 if result.get('status')!=expected:
  if checks:print(checks[-1]['evidence'].get('typecheck',{}).get('stdout','')[:2400],checks[-1]['evidence'].get('completion',{}).get('diagnostic'))
  else:print('compile:',result.get('compilations'))
 assert result.get('status')==expected,label
 if label!='canonical':
  assert len(checks)==2 and checks[0]['evidence']['status']=='supported' and checks[1]['evidence']['status']=='unresolved'
(out/'RESULTS.json').write_text(json.dumps(rows,indent=2))
