import dataclasses,json,time,sys,shutil
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
b=Path('.codex/state/prose-shape-v2').resolve();root=Path(sys.argv[3] if len(sys.argv)>3 else 'tests/fixtures/real_bound_observation').resolve()
p=b/'probe-budget.json'
if p.exists():deadline=json.loads(p.read_text())['deadlineMonotonic']
else:
 deadline=time.monotonic()+600;p.write_text(json.dumps({'deadlineMonotonic':deadline,'seconds':600}))
assert deadline>time.monotonic()
label=sys.argv[1];source=b/(sys.argv[2] if len(sys.argv)>2 else 'KernelProbe.lean');dest=b/(label+'.lean');assert not dest.exists();shutil.copy2(source,dest)
ctx=pinned_toolchain(root);exe=prepare_direct_lean_execution(root,None,ctx,require_compiled_module=False)
r=run_bounded_target_process([*exe.command,str(dest)],cwd=root,env=exe.environment,timeout_seconds=deadline-time.monotonic(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(b/(label+'-process.json')).write_text(json.dumps({'command':[*exe.command,str(dest)],**dataclasses.asdict(r)},indent=2)+'\n')
print(r.stdout);print(r.stderr);print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes})
assert not any((r.timed_out,r.memory_limited,r.output_limited)), 'Stop progress and report resource stop to user.'
