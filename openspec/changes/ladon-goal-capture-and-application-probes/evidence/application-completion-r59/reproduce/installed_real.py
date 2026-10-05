from pathlib import Path
import json,os
from ladon.process_supervisor import run_bounded_target_process
root=Path.cwd();state=root/'.codex/state/application-completion-r59';run=Path((state/'run-path').read_text().strip());script=run/'py311-real-completion.py'
script.write_text('''from pathlib import Path
from dataclasses import asdict
import json,time
import ladon.process_supervisor as supervisor
records=[]
original=supervisor.run_bounded_target_process
def observed(argv,**options):
 result=original(argv,**options);records.append(asdict(result));return result
supervisor.run_bounded_target_process=observed
import pytest
start=time.monotonic()
code=pytest.main(['-q', '''+repr(str(run/'candidate/tests/test_source_goal_completion_lean.py'))+'''])
Path('''+repr(str(run/'py311-real-completion-processes.json'))+''').write_text(json.dumps(records,indent=2)+'\\n')
Path('''+repr(str(run/'py311-real-completion-summary.json'))+''').write_text(json.dumps({'exitCode':code,'wallSeconds':time.monotonic()-start,'processCalls':len(records),'processSeconds':sum(r['elapsed_seconds'] for r in records),'peakRssBytes':max((r['peak_rss_bytes'] or 0 for r in records),default=0)},indent=2)+'\\n')
raise SystemExit(code)
''')
env=dict(os.environ)
for k in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV'):env.pop(k,None)
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin:'+env['PATH']
r=run_bounded_target_process([str(run/'py311/bin/python'),'-I',str(script)],cwd=Path('/tmp'),env=env,timeout_seconds=55,max_output_bytes=8388608,max_rss_bytes=34359738368)
(run/'py311-real-completion.stdout').write_text(r.stdout);(run/'py311-real-completion.stderr').write_text(r.stderr)
print(json.dumps({'returnCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'stdout':r.stdout,'stderr':r.stderr}));raise SystemExit(r.returncode or 0)
