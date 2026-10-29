import dataclasses,json,sys,time
from pathlib import Path
from ladon.proof_slice import pinned_toolchain
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.process_supervisor import run_bounded_target_process
from ladon.real_bound_shape import observe_bound_shape
b=Path('.codex/state/real-prose-integration').resolve()
root=Path('.codex/state/navier-stokes-informed-diagnostic/formalization').resolve()
p=b/'budget.json'
if p.exists():deadline=json.loads(p.read_text())['deadlineMonotonic']
else:
 deadline=time.monotonic()+600;p.write_text(json.dumps({'deadlineMonotonic':deadline,'seconds':600}))
assert deadline>time.monotonic()
label,target=sys.argv[1:3]
source=b/(sys.argv[3] if len(sys.argv)>3 else 'ProseCases.lean')
assert not (b/(label+'-process.json')).exists()
ctx=pinned_toolchain(root);exe=prepare_direct_lean_execution(root,None,ctx,require_compiled_module=False)
cmd=[*exe.command,'--run',str(b/'observe_proposition.lean'),source.stem,source.name,str(source),target,str(b/(label+'-value.json'))]
r=run_bounded_target_process(cmd,cwd=root,env=exe.environment,timeout_seconds=deadline-time.monotonic(),max_rss_bytes=12*1024**3,max_output_bytes=8*1024**2)
(b/(label+'-process.json')).write_text(json.dumps({'command':cmd,'libraryRoots':[str(x) for x in exe.library_roots],**dataclasses.asdict(r)},indent=2)+'\n')
assert not any((r.timed_out,r.memory_limited,r.output_limited)), 'Stop progress and report resource stop to user.'
print({'exit':r.returncode,'seconds':r.elapsed_seconds,'peakRssBytes':r.peak_rss_bytes})
if r.returncode:
 print(r.stdout);print(r.stderr)
else:
 j=json.loads((b/(label+'-value.json')).read_text());print({'status':j['status']})
 if j['status']=='observed':
  result=observe_bound_shape(j['normalizedTypeExpr']);(b/(label+'-shape.json')).write_text(json.dumps(result,indent=2)+'\n');print({'hasCandidate':result['candidate'] is not None,'residuals':result['residuals']})
