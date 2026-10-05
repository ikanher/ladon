from pathlib import Path
from dataclasses import asdict
import json, tempfile, sys
from ladon.lean_toolchain import resolve_toolchain_context
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal
from ladon.process_supervisor import run_bounded_target_process
out=Path('.codex/state/application-completion-r59/root-trials')/(sys.argv[1] if len(sys.argv)>1 else 'positive-observed-01');out.mkdir()
def observe(command, **options):
 r=run_bounded_target_process(command,**options)
 p=out/(str(len(list(out.glob('process-*.json'))))+'.json')
 p=out/('process-'+p.name)
 p.write_text(json.dumps({'result':asdict(r),'input':options.get('input_bytes',b'').decode(),'limits':{k:options[k] for k in ['timeout_seconds','max_rss_bytes','max_output_bytes']}},indent=2))
 return r
with tempfile.TemporaryDirectory(prefix='ladon-completion-fixture-') as d:
 root=Path(d)
 (root/'lean-toolchain').write_text('leanprover/lean4:v4.32.1\n')
 (root/'Owner.lean').write_text('namespace Owner\nvariable {α : Type} [Inhabited α]\nexample (x : α) (h : x = x) : x = x := by\n  have z : x = x := h\n  skip\nend Owner\n')
 lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin/lean')
 ctx=resolve_toolchain_context(root,lean_path=lean,lake_path=lean.with_name('lake'),selection_mode='explicit')
 cap=capture_source_goal(SourceGoalCaptureRequest(repo_root=root,source_path='Owner.lean',module='Owner',line=5,column=6,toolchain=ctx,timeout_seconds=30),runner=observe)
 (out/'capture.json').write_text(json.dumps(cap,indent=2))
 result=complete_source_goal(SourceGoalCompletionRequest(repo_root=root,capture=cap['capture'],term='z',toolchain=ctx,timeout_seconds=30),runner=observe)
 (out/'completion.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({'status':result['status'],'diagnostic':result['diagnostic']}))
