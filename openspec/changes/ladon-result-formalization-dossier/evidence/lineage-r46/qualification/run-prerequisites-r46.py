import hashlib,json,os,subprocess,time
from pathlib import Path
root=Path('/home/codex/.cache/ladon-qualification-r46/ladon-dossier-r46-ppjcv52s/full-qualification');context=json.loads((root/'context-r46.json').read_text());context.pop('sourceManifestPath');context.pop('hostNetworkNamespace');candidate=Path(context['workingDirectory']);commit=json.loads((root/'candidate-r46.json').read_text())['commit'];inv=json.loads((candidate/'openspec/changes/ladon-authority-safe-verified-discovery-umbrella/children/integration-acceptance-inventory.json').read_text());out=root/'prerequisites-r46';out.mkdir(exist_ok=False);rows=[]
env=dict(os.environ);[env.pop(key,None) for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS')];env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['LADON_REQUIRE_EXECUTION_NONLEAKAGE']='1'
for gate in inv['integrationPrerequisites']:
 argv=[p.format(candidateCommit=commit,outputDirectory=str(out)) for p in gate['argvTemplate']];log=out/(gate['gateId']+'.log');start=time.monotonic();print('START '+gate['gateId'],flush=True)
 with log.open('wb') as stream:
  stream.write((json.dumps({'argv':argv,'cwd':str(candidate)})+'\n').encode());stream.flush();result=subprocess.run(argv,cwd=candidate,env=env,stdout=stream,stderr=subprocess.STDOUT)
 row={**context,'candidateCommit':commit,'gateId':gate['gateId'],'argv':argv,'exitCode':result.returncode,'status':'passed' if result.returncode==0 else 'failed','logPath':str(log)};rows.append(row);(out/'commands.json').write_text(json.dumps(rows,indent=2)+'\n');print('DONE '+gate['gateId']+' '+str(result.returncode)+' '+str(round(time.monotonic()-start,1)),flush=True)
 if result.returncode:raise SystemExit(result.returncode)
