from pathlib import Path
import json,os,subprocess,sys,time
root=Path('/home/codex/projects/ladon'); state=root/'.codex/state/application-context-r57'
run=Path((state/'run-path').read_text().strip()); candidate=run/'candidate'
def call(name,argv,cwd=candidate):
 env=dict(os.environ)
 for key in ('PYTHONPATH','PYTHONHOME','PYTEST_ADDOPTS'): env.pop(key,None)
 env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'; env['TMPDIR']='/home/codex/.cache/ladon-qualification-r57'
 env['PATH']='/home/codex/.elan/toolchains/leanprover--lean4---v4.32.1/bin:'+env['PATH']
 start=time.monotonic()
 with (run/(name+'.log')).open('w') as out: result=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT)
 (run/(name+'.command.json')).write_text(json.dumps({'argv':argv,'cwd':str(cwd),'exitCode':result.returncode,'elapsedSeconds':time.monotonic()-start},indent=2)+'\n')
 print(name,result.returncode,flush=True)
 if result.returncode: raise SystemExit(result.returncode)
if sys.argv[1]=='baseline':
 call('clean-baseline',['uv','run','--locked','python','scripts/clean_checkout_gate.py','--candidate',str(candidate),'--baseline-only','--package-resource','ladon:lean/ladon_semantic_candidate_helper.lean'],root)
elif sys.argv[1]=='install':
 call('build-wheel',['uv','build','--wheel','--out-dir',str(run/'dist')])
 names=['test_semantic_context_protocol_marker.py','test_semantic_context_rejected_protocol.py','test_semantic_context_shadowing_fallback.py','test_semantic_application_context_names.py','test_semantic_application_context_compact.py','test_semantic_application_context_ledger.py','test_semantic_application_context_rejections_text.py','test_semantic_application_context_v4.py','test_semantic_application_context_v4_dispatch.py','test_semantic_application_context_v4_text.py','test_semantic_application_context_v4_boundaries.py','test_semantic_candidate_batch_worker.py','test_semantic_candidate_framed_protocol.py','test_semantic_candidate_worker_v3_contract.py','test_semantic_projection_hardening.py','test_semantic_cli_projection.py','test_semantic_residual_text.py','test_semantic_observation_validation.py','test_semantic_evidence_registry.py','test_semantic_stored_receipt.py']
 names=[n for n in names if (candidate/'tests'/n).is_file()]
 for runtime,version in [('py311','3.11'),('py312','3.12')]:
  call(runtime+'-venv',['uv','venv','--python',version,str(run/runtime)])
  call(runtime+'-install',['uv','pip','install','--python',str(run/runtime/'bin/python'),str(run/'dist/ladon-0.2.0-py3-none-any.whl'),'pytest','jsonschema'])
  script=run/(runtime+'-contracts.py')
  script.write_text('''from dataclasses import asdict
from pathlib import Path
import json,time
import ladon.process_supervisor as supervisor
records=[]
original=supervisor.run_bounded_target_process
def observed(argv,**options):
 result=original(argv,**options); records.append(asdict(result)); return result
supervisor.run_bounded_target_process=observed
import pytest
start=time.monotonic()
code=pytest.main('''+repr(['-q']+[str(candidate/'tests'/n) for n in names])+''')
helpers=[r for r in records if '--run' in r['command']]
Path('''+repr(str(run/(runtime+'-helper-records.json')))+''').write_text(json.dumps(records,indent=2)+'\\n')
Path('''+repr(str(run/(runtime+'-summary.json')))+''').write_text(json.dumps({'exitCode':code,'wallSeconds':time.monotonic()-start,'helperCalls':len(helpers),'helperSeconds':sum(r['elapsed_seconds'] for r in helpers),'helperPeakRssBytes':max((r['peak_rss_bytes'] or 0 for r in helpers),default=0)},indent=2)+'\\n')
raise SystemExit(code)
''')
  call(runtime+'-contracts',[str(run/runtime/'bin/python'),'-I',str(script)],Path('/tmp'))
  owners=['_semantic_observation_contract','semantic_local_context','semantic_application_cards','semantic_projection_fit','_semantic_observation_results','semantic_application_context','semantic_candidate_protocol','semantic_candidate_worker','semantic_candidate_batch_worker','semantic_stored_receipt','semantic_projection_cards','proof_search_semantic_cli']
  origin="import hashlib,importlib,json,sys; from pathlib import Path; modules="+repr(owners)+"; paths=[Path(importlib.import_module('ladon.'+m).__file__) for m in modules]; paths += [paths[0].parent/'lean/ladon_semantic_candidate_helper.lean']; assert all('site-packages' in str(p) for p in paths); print(json.dumps({'runtime':sys.version,'files':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}))"
  call(runtime+'-origin',[str(run/runtime/'bin/python'),'-I','-c',origin],Path('/tmp'))
