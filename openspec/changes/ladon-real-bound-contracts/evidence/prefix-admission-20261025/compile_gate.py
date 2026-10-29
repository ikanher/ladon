import json,shutil,time
from dataclasses import asdict
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
state=Path('.codex/state/real-bound-admission').resolve();root=state/'project'
clock=json.loads((state/'gate-clock.json').read_text())
shutil.copyfile('src/ladon/lean/LadonRealBound.lean',root/'LadonRealBound.lean')
execution=prepare_direct_lean_execution(root,None,pinned_toolchain(root),require_compiled_module=False)
for name,args in [('family',['-o','.lake/build/lib/lean/LadonRealBound.olean','LadonRealBound.lean']),('fixture',['PrefixExamples.lean'])]:
 remaining=clock['deadlineMonotonic']-time.monotonic();assert remaining>0
 p=run_bounded_target_process([*execution.command,*args],cwd=root,env=execution.environment,timeout_seconds=min(60,remaining),max_rss_bytes=12*1024**3,max_output_bytes=1024**2)
 (state/(name+'-compile.json')).write_text(json.dumps(asdict(p),indent=2));print(name,p.returncode,p.stdout[:1500],p.stderr[:500],flush=True)
 if not p.succeeded:break
