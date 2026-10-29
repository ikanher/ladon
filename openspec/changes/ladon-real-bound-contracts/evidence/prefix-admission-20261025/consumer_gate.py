import json,hashlib,time,shutil
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission import plan_prefix_admission
from ladon.real_bound_admission_check import check_prefix_admission
state=Path('.codex/state/real-bound-admission').resolve();root=state/'consumer-project';root.mkdir(exist_ok=True)
(root/'.lake').mkdir(exist_ok=True)
p=root/'.lake/packages'
if not p.exists():p.symlink_to(Path('.codex/state/navier-stokes-informed-diagnostic/formalization/.lake/packages').resolve(),target_is_directory=True)
shutil.copyfile(state/'project/lean-toolchain',root/'lean-toolchain')
source=Path('tests/fixtures/real_bound_admission/PrefixExamples.lean').read_bytes();(root/'PrefixExamples.lean').write_bytes(source)
clock=json.loads((state/'gate-clock.json').read_text())
context=pinned_toolchain(root)
req={'source':{'path':'PrefixExamples.lean','sha256':hashlib.sha256(source).hexdigest()},'environmentRef':context.context_identity,'predicate':'SequenceBounds.envelope','measure':'SequenceBounds.sample','objectType':'SequenceBounds.Object','parameterType':'Nat','pointType':'Unit'}
plan=plan_prefix_admission(req);terms={'predicate-equivalence':'SequenceBounds.adapter.1','order-prefix':'SequenceBounds.adapter.2.1','bound-monotonicity':'SequenceBounds.adapter.2.2'}
(state/'consumer-plan.json').write_text(json.dumps(plan,indent=2));(state/'consumer-terms.json').write_text(json.dumps(terms,indent=2))
remaining=clock['deadlineMonotonic']-time.monotonic();assert remaining>0
result=check_prefix_admission(root,plan,terms,timeout_seconds=remaining)
(state/'consumer-result.json').write_text(json.dumps(result,indent=2))
print(result['status'], (result.get('result') or {}).get('status'),result.get('diagnostic'),flush=True)
