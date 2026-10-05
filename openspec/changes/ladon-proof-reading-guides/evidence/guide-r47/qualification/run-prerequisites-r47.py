import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r47/ladon-guides-r47b-9nrffih0/full-qualification');context=json.loads((root/'context-r47.json').read_text());context.pop('sourceManifestPath');context.pop('hostNetworkNamespace');candidate=Path(context['workingDirectory']);commit=json.loads((root/'candidate-r47.json').read_text())['commit'];inv=json.loads((candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/integration-acceptance-inventory.json').read_text());out=root/'prerequisites-r47';out.mkdir(exist_ok=False);rows=[]
env=dict(os.environ);[env.pop(key,None) for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS')];env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['LADON_REQUIRE_EXECUTION_NONLEAKAGE']='1';env['TMPDIR']='/home/codex/.cache/ladon-qualification-r47';env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin:'+env['PATH']
for gate in inv['integrationPrerequisites']:
 argv=[p.format(candidateCommit=commit,outputDirectory=str(out)) for p in gate['argvTemplate']];log=out/(gate['gateId']+'.log');start=time.monotonic();print('START '+gate['gateId'],flush=True)
 with log.open('wb') as stream:
  stream.write((json.dumps({'argv':argv,'cwd':str(candidate)})+'\n').encode());stream.flush();result=subprocess.run(argv,cwd=candidate,env=env,stdout=stream,stderr=subprocess.STDOUT)
 row={**context,'candidateCommit':commit,'gateId':gate['gateId'],'argv':argv,'exitCode':result.returncode,'status':'passed' if result.returncode==0 else 'failed','logPath':str(log),'environmentOverrides':{'TMPDIR':env['TMPDIR'],'PATHPrefix':'/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin'}};rows.append(row);(out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n');print('DONE '+gate['gateId']+' '+str(result.returncode)+' '+str(round(time.monotonic()-start,1)),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
