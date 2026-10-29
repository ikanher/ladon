import json,shutil,time
from pathlib import Path
from dataclasses import asdict
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
state=Path('.codex/state/real-bound-admission').resolve(); root=state/'project';root.mkdir(exist_ok=True)
original=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
(root/'.lake/build/lib/lean').mkdir(parents=True,exist_ok=True)
packages=root/'.lake/packages'
if not packages.exists(): packages.symlink_to(original/'.lake/packages',target_is_directory=True)
shutil.copyfile(original/'lean-toolchain',root/'lean-toolchain')
shutil.copyfile('tests/fixtures/real_bound_admission/PrefixExamples.lean',root/'PrefixExamples.lean')
context=pinned_toolchain(root);execution=prepare_direct_lean_execution(root,None,context,require_compiled_module=False)
start=time.monotonic();(state/'gate-clock.json').write_text(json.dumps({'startedMonotonic':start,'deadlineMonotonic':start+900,'maxRssBytes':12*1024**3}))
p=run_bounded_target_process([*execution.command,'PrefixExamples.lean'],cwd=root,env=execution.environment,timeout_seconds=60,max_rss_bytes=12*1024**3,max_output_bytes=1024**2)
(state/'lean-red.json').write_text(json.dumps(asdict(p),indent=2));assert not p.succeeded;print(p.stdout[:500],p.stderr[:500])
