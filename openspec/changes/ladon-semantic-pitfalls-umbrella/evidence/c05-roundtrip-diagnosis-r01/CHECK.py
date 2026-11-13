from pathlib import Path
import json,subprocess,sys,os
root=Path('/home/codex/projects/ladon');e=Path(__file__).resolve().parent;s=json.loads((e/'SESSION.json').read_text());name=sys.argv[1];row=json.loads((e/'INPUTS.json').read_text())[name]
for op in ['capture','complete']:
 output=e/(name+'-'+op+'.json')
 args=[str(root/'.venv/bin/python'),'-m','ladon.entrypoint','proof-search','goal',op,'--repo-root',s['project'],'--lean-path','/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lean','--lake-path','/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/lake','--timeout-seconds','600','--max-rss-mib','12288','--max-output-mib','16','--format','json','--output',str(output)]
 if op=='capture':args+=['--source',row['source'],'--module',row['module'],'--line',str(row['line']),'--column',str(row['column'])]
 else:args+=['--capture-file',str(e/(name+'-capture.json')),'--term',(e/(name+'.term')).read_text()]
 subprocess.run([str(root/'.venv/bin/python'),str(e/'DO.py'),name+'-'+op,*args],check=True,env={**os.environ,'PYTHONPATH':str(root/'src')})
 report=json.loads(output.read_text());print(name,op,report['status'],flush=True)
 if op=='capture' and report['status']!='captured':break
