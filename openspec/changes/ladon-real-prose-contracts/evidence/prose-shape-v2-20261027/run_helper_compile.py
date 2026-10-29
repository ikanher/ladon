import dataclasses,json,time,sys
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
b=Path('.codex/state/prose-shape-v2').resolve();root=Path('tests/fixtures/real_bound_observation').resolve()
p=b/'helper-integration-budget.json'
if p.exists():deadline=json.loads(p.read_text())['deadlineMonotonic']
else:
 deadline=time.monotonic()+600;p.write_text(json.dumps({'deadlineMonotonic':deadline,'seconds':600,'scope':'production helper compiler integration after successful kernel feasibility gate'}))
label=sys.argv[1];source=Path(sys.argv[2]).resolve();dest=b/(label+'.lean');assert not dest.exists();dest.write_bytes(source.read_bytes())
ctx=pinned_toolchain(root);exe=prepare_direct_lean_execution(root,None,ctx,require_compiled_module=False)
r=run_bounded_target_process([*exe.command,str(dest)],cwd=root,env=exe.environment,timeout_seconds=deadline-time.monotonic(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(b/(label+'-process.json')).write_text(json.dumps({'command':[*exe.command,str(dest)],**dataclasses.asdict(r)},indent=2)+'\n')
print(r.stdout);print(r.stderr);print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes})
assert not any((r.timed_out,r.memory_limited,r.output_limited)), 'Stop progress and report resource stop to user.'
