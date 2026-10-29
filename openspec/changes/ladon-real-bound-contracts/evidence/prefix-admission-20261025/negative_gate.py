import json,time,sys
from pathlib import Path
from dataclasses import asdict
from ladon.correspondence_check import _check_goal
from ladon.proof_slice import pinned_toolchain
from ladon.process_supervisor import run_bounded_target_process
from ladon.semantic_lean_execution import prepare_direct_lean_execution
s=Path('.codex/state/real-bound-admission').resolve();root=s/'project';clock=json.loads((s/'gate-clock.json').read_text());assert time.monotonic()<clock['deadlineMonotonic']
source=(root/'PrefixExamples.lean').read_bytes()
# Keep the declaration names, but change the admitted domain in a new file.
changed=source.replace(b'forall impossible',b'forall impossible').replace(b'\xe2\x88\x80 j \xe2\x89\xa4 n',b'\xe2\x88\x80 j < n')
assert changed!=source
(root/'Changed.lean').write_bytes(changed)
exe=prepare_direct_lean_execution(root,None,pinned_toolchain(root),require_compiled_module=False)
r=run_bounded_target_process([*exe.command,'Changed.lean'],cwd=root,env=exe.environment,timeout_seconds=max(0.1,min(10,clock['deadlineMonotonic']-time.monotonic())),max_rss_bytes=12*1024**3,max_output_bytes=1024**2)
(s/'changed-definition.json').write_text(json.dumps(asdict(r),indent=2));assert not r.succeeded;print('changed definition rejected',flush=True)
goal=json.loads((s/'plan.json').read_text())['goals'][0]['proposition']
a=_check_goal(goal,'by sorry',root,source,{},pinned_toolchain(root));(s/'sorry-negative.json').write_text(json.dumps(a,indent=2));print('sorry result',a['status'],a.get('completion',{}).get('status'),flush=True);assert a['status']!='supported'
