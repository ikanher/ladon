from pathlib import Path
import json,os
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path((state/'run-path').read_text().strip());cwd=run/'recorder-preflight-v2';cwd.mkdir()
(cwd/'probe.py').write_text("from pathlib import Path\nPath('observation.txt').write_text('unicode α\\n')\nprint('r62-recorder-start\\n' + 'z' * 40000 + '\\nr62-recorder-end')\n")
prompt='Tool-recording preflight only. Run python probe.py in the current directory, then run cat observation.txt as a separate command. Do not inspect other directories or edit probe.py. Finally say whether both commands succeeded. No network or mathematics task.'
(cwd/'prompt.txt').write_text(prompt)
argv=['/home/codex/node_modules/.bin/codex','exec','--json','--ephemeral','--ignore-user-config','--skip-git-repo-check','-m','gpt-6-luna','-c','model_reasoning_effort="medium"','-c','approval_policy="never"','-s','workspace-write','-C',str(cwd),'-o',str(cwd/'final.txt'),prompt]
env=dict(os.environ)
for key in ['PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV']:env.pop(key,None)
r=run_bounded_target_process(argv,cwd=cwd,env=env,timeout_seconds=90,max_output_bytes=8388608,max_rss_bytes=34359738368)
(cwd/'events.jsonl').write_text(r.stdout);(cwd/'stderr.txt').write_text(r.stderr)
x=asdict(r);x.pop('stdout');x.pop('stderr');(cwd/'command.json').write_text(json.dumps(x,indent=2)+'\n')
items=[v.get('item',{}) for v in map(json.loads,r.stdout.splitlines()) if v.get('type')=='item.completed'];commands=[i for i in items if i.get('type')=='command_execution'];full=any(i.get('aggregated_output')=='r62-recorder-start\n'+'z'*40000+'\nr62-recorder-end\n' for i in commands)
print(json.dumps({'exitCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'commandCount':len(commands),'commandExits':[i['exit_code'] for i in commands],'rawOutputPreserved':full,'recordedOutputLengths':[len(i.get('aggregated_output','')) for i in commands],'unicodeRead':any('unicode α' in i.get('aggregated_output','') for i in commands)}))
