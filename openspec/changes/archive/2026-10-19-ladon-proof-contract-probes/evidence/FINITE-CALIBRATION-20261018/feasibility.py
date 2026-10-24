import hashlib,json,shutil,time
from pathlib import Path
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_contract_bridge import _accepted_check,_resource_stop
from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
p=Path('.codex/state/proof-contract-analysis/probe-calibration');started=time.monotonic();deadline=started+180
(p/'FEASIBILITY-START.json').write_text(json.dumps({'startedMonotonic':started,'deadlineMonotonic':deadline,'budgetSeconds':180}))
root=(p/'probe-repo').resolve();root.mkdir();shutil.copyfile('tests/fixtures/proof_contract_planned_source/lean-toolchain',root/'lean-toolchain');source=(p/'Separator.lean').read_bytes();(root/'Separator.lean').write_bytes(source)
limits={'timeout_seconds':30,'max_rss_bytes':12*1024**3,'max_output_bytes':8*1024**2};execution=prepare_direct_lean_execution(root,None,pinned_toolchain(root),require_compiled_module=False)
process=run_bounded_target_process([*execution.command,'Separator.lean'],cwd=root,env=execution.environment,timeout_seconds=min(30,deadline-time.monotonic()),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(p/'compile.json').write_text(json.dumps({'returnCode':process.returncode,'stdout':process.stdout,'stderr':process.stderr,'elapsedSeconds':process.elapsed_seconds,'peakRssBytes':process.peak_rss_bytes,'timedOut':process.timed_out,'memoryLimited':process.memory_limited,'outputLimited':process.output_limited},indent=2));assert process.succeeded,process.stdout+process.stderr
family='([0, 1, 2, 3, 4] : List (Fin 5))';small='([0, 1, 2, 3] : List (Fin 5))';zero='(fun (_ : Fin 5) => false)';last='(fun (i : Fin 5) => if i.val = 4 then true else false)'
goals=[('separator',f'∀ (f g : Fin 5 → Bool), (∀ i ∈ {family}, f i = g i) → f = g','LadonProbeCalibration.full_separates'),('incomplete-counterexample',f'(∀ i ∈ {small}, {zero} i = {last} i) ∧ {zero} ≠ {last}','LadonProbeCalibration.incomplete_counterexample'),('application',f'{zero} = {zero}','LadonProbeCalibration.full_separates _ _ (by decide)')]
for name,goal,term in goals:
 result=run_bridge_job('check-goal',{'repoRoot':str(root),'sourcePath':'Separator.lean','sourceDigest':'sha256:'+hashlib.sha256(source).hexdigest(),'goal':goal,'term':term,'symbols':{}},deadline_monotonic=deadline,limits=limits)
 (p/(name+'-process.json')).write_text(json.dumps(result,separators=(',',':'),ensure_ascii=False));assert result['status']=='completed' and _accepted_check(result['result']),(name,result.get('diagnostic'),result.get('result'))
 print(name,'accepted',result['processReceipt']['elapsedSeconds'],flush=True)
(p/'FEASIBILITY.json').write_text(json.dumps({'status':'PASS','elapsedSeconds':time.monotonic()-started,'budgetSeconds':180,'goals':3,'sourceSha256':hashlib.sha256(source).hexdigest(),'incompleteFamily':'Actual agree-but-not-equal conjunction checked','sourceUnchanged':(root/'Separator.lean').read_bytes()==source},indent=2));print('PASS',time.monotonic()-started,flush=True)
