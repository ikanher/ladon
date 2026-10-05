from pathlib import Path
import json,tempfile,os
from dataclasses import asdict
from ladon.process_supervisor import run_bounded_target_process
root=Path('/home/codex/projects/ladon');state=root/'.codex/state/benefit-readers-r62';run=Path(tempfile.mkdtemp(prefix='ladon-benefit-r62-',dir='/home/codex/.cache'));(state/'run-path').write_text(str(run)+'\n');cwd=run/'recorder-preflight';cwd.mkdir()
prompt='This is a tool-recording preflight, not a mathematical task. Execute exactly one shell command: python -c "from pathlib import Path; Path(\"observation.txt\").write_text(\"unicode α\\n\"); print(\"r62-recorder-ok\")". Read observation.txt with one separate shell command. Then reply with only recorder-preflight-complete. Do not inspect other directories or use network tools.'
(cwd/'prompt.txt').write_text(prompt)
argv=['/home/codex/node_modules/.bin/codex','exec','--json','--ephemeral','--ignore-user-config','--skip-git-repo-check','-m','gpt-6-luna','-c','model_reasoning_effort="medium"','-c','approval_policy="never"','-s','workspace-write','-C',str(cwd),'-o',str(cwd/'final.txt'),prompt]
env=dict(os.environ)
for key in ['PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS','VIRTUAL_ENV']:env.pop(key,None)
r=run_bounded_target_process(argv,cwd=cwd,env=env,timeout_seconds=90,max_output_bytes=8388608,max_rss_bytes=34359738368)
(cwd/'events.jsonl').write_text(r.stdout);(cwd/'stderr.txt').write_text(r.stderr)
x=asdict(r);x.pop('stdout');x.pop('stderr');(cwd/'command.json').write_text(json.dumps(x,indent=2)+'\n')
print(json.dumps({'exitCode':r.returncode,'seconds':r.elapsed_seconds,'rss':r.peak_rss_bytes,'stderr':r.stderr[-1800:],'eventsTail':r.stdout[-2000:]}))
