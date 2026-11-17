import dataclasses,json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
root=Path('/home/codex/projects/lean/matrix-factorization')
out=Path(__file__).resolve().parent
execution=prepare_direct_lean_execution(root,None,None,require_compiled_module=False)
started=datetime.now(timezone.utc).isoformat()
source=out/(sys.argv[2] if len(sys.argv)>2 else 'BatchPair.lean')
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
result=run_bounded_target_process(['/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean',str(out/(sys.argv[2] if len(sys.argv)>2 else 'BatchPair.lean'))],cwd=root,env=execution.environment,timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=12288*1024**2,observe_resources=True)
record=dataclasses.asdict(result)
record.update(startedAt=started, finishedAt=datetime.now(timezone.utc).isoformat(), source=str(source), sourceSha256=source_hash, sourceUnchanged=hashlib.sha256(source.read_bytes()).hexdigest()==source_hash, command=['/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean',str(source)], cwd=str(root))
record['libraryRoots']=[str(p) for p in execution.library_roots]
path=out/(sys.argv[1]+'.json')
path.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ['returncode','stdout','stderr','elapsed_seconds','timed_out','memory_limited','peak_rss_bytes']},indent=2))
sys.exit(0 if result.succeeded else 1)
