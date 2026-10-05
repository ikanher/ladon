from dataclasses import asdict
from pathlib import Path
import json,sys,time
import ladon.process_supervisor as supervisor
state=Path('/home/codex/projects/ladon/.codex/state/application-context-r57')
label=sys.argv[1]
original=supervisor.run_bounded_target_process
records=[]
def observed(argv,**options):
 result=original(argv,**options)
 records.append(asdict(result))
 (state/(label+'-processes.json')).write_text(json.dumps(records,indent=2)+'\n')
 return result
supervisor.run_bounded_target_process=observed
import pytest
start=time.monotonic()
code=pytest.main(['-q','tests/test_semantic_application_context_lean.py'])
helpers=[r for r in records if '--run' in r['command']]
(state/(label+'-summary.json')).write_text(json.dumps({'exitCode':code,'wallSeconds':time.monotonic()-start,'helperCalls':len(helpers),'helperSeconds':sum(r['elapsed_seconds'] for r in helpers),'helperPeakRssBytes':max((r['peak_rss_bytes'] or 0 for r in helpers),default=0),'buildCalls':sum('-o' in r['command'] for r in records),'otherPreflightCalls':sum('--run' not in r['command'] and '-o' not in r['command'] for r in records)},indent=2)+'\n')
raise SystemExit(code)
