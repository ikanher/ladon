from pathlib import Path
from dataclasses import asdict
import json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path((state/'run-path').read_text().strip());candidate=Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip());identity=json.loads((run/'fixture-identity.json').read_text());position=identity['positions']['ContextA'];repo=run/'fixture';lean=Path('/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean')
env=dict(os.environ)
for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(key,None)
command=[str(candidate/'py312/bin/ladon'),'proof-search','goal','capture','--repo-root',str(repo),'--source','ContextA.lean','--module','ContextA','--line',str(position['line']),'--column',str(position['column']),'--lean-path',str(lean),'--lake-path',str(lean.with_name('lake')),'--timeout-seconds','30','--format','json']
r=run_bounded_target_process(command,cwd=Path('/tmp'),env=env,timeout_seconds=55,max_output_bytes=8388608,max_rss_bytes=34359738368);(run/'capture-a.stdout').write_text(r.stdout);(run/'capture-a.stderr').write_text(r.stderr);row=asdict(r);row.pop('stdout');row.pop('stderr');(run/'capture-a.command.json').write_text(json.dumps(row,indent=2)+'\n')
print(json.dumps({'returnCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'stdoutEnd':r.stdout[-800:],'stderr':r.stderr[-800:]}));raise SystemExit(r.returncode or 0)
