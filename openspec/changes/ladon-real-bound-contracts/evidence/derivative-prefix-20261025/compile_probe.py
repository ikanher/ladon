from pathlib import Path
from dataclasses import asdict
import json,shutil,time
from ladon.proof_slice import pinned_toolchain
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
base=Path('.codex/state/derivative-prefix');root=(base/'compile-probe').resolve();root.mkdir(exist_ok=False)
original=Path('.codex/state/real-bound-admission/consumer-project').resolve()
context=pinned_toolchain(original)
(root/'lean-toolchain').write_bytes((original/'lean-toolchain').read_bytes())
(root/'.lake/build/lib/lean').mkdir(parents=True)
for i,library in enumerate(context.library_roots):
 target=root/f'.lake/packages/import{i}/.lake/build/lib/lean';target.parent.mkdir(parents=True);target.symlink_to(library,target_is_directory=True)
for module in ('LadonRealBound','LadonRealBoundBinding','LadonRealBoundDerivative'):
 source=Path('src/ladon/lean')/(module+'.lean')
 shutil.copy2(source,root/source.name)
 ex=prepare_direct_lean_execution(root,None,pinned_toolchain(root),require_compiled_module=False)
 r=run_bounded_target_process([*ex.command,'-o',f'.lake/build/lib/lean/{module}.olean',source.name],cwd=root,env=ex.environment,
  timeout_seconds=60,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 (base/(module+'-compile.json')).write_text(json.dumps(asdict(r),indent=2));print(module,r.returncode,r.stdout[:2500],r.stderr[:500],flush=True)
 if not r.succeeded:break
