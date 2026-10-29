from pathlib import Path
from dataclasses import asdict
import json,sys
from ladon.process_supervisor import run_bounded_target_process
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.quality import strict_quality_issues
base=Path('.codex/state/real-bound-binding')
names=['test_real_bound_shape.py','test_real_bound_shape_origins.py','test_real_bound_observation.py',
 'test_real_bound_admission_plan.py','test_real_bound_admission_check.py','test_real_bound_admission_cli.py','test_real_bound_admission_freshness.py',
 'test_proof_contracts.py','test_proof_contract_formal_snapshot.py','test_proof_contract_formal_cli.py',
 'test_proof_contract_cli.py','test_proof_contract_producer_bounds.py','test_proof_contract_native.py',
 'test_proof_contract_native_audit.py','test_proof_contract_propagation_native.py']
paths=[Path('tests')/name for name in names]
paths+=sorted(Path('tests').glob('test_real_bound_binding*.py'))
paths+=sorted(Path('tests').glob('test_source_goal_completion_*.py'))
commands=[('pytest',[sys.executable,'-m','pytest','-q',*map(str,paths)])]
changed=[*Path('src/ladon').glob('real_bound_binding*.py'),Path('src/ladon/proof_contract_cli.py'),
 *Path('tests').glob('test_real_bound_binding*.py'),Path('tests/test_source_goal_completion_universes.py'),Path('tests/test_source_goal_completion_universe_terms.py')]
commands += [('ruff',[str(Path('.venv/bin/ruff').resolve()),'check',*map(str,changed)]),
 ('openspec',['openspec','validate','ladon-real-bound-contracts','--strict']),('diff',['git','diff','--check'])]
results={}
for label,command in commands:
 r=run_bounded_target_process(command,cwd=Path.cwd(),timeout_seconds=900,max_output_bytes=8*1024**2,max_rss_bytes=DEFAULT_MAX_RSS_BYTES)
 results[label]=asdict(r)
 (base/'CHECKS.json').write_text(json.dumps(results,indent=2))
 print(label,r.returncode,r.stdout[-2000:],r.stderr[-500:],flush=True)
 assert r.succeeded,label
issues=strict_quality_issues(changed)
results['strictQuality']=[asdict(i) for i in issues]
(base/'CHECKS.json').write_text(json.dumps(results,indent=2));assert not issues,issues
