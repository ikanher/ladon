from pathlib import Path
import hashlib,json,shutil
base=Path('.codex/state/real-native');out=Path('openspec/changes/ladon-real-bound-contracts/evidence/native-admission-20261025');out.mkdir(parents=True,exist_ok=False)
for folder in ['qualification','qualification-final','scalar-probe','boundaries','native-cli','consumers','trust','frozen-test-lint']:
 target=out/folder;target.mkdir()
 for p in (base/folder).iterdir():
  if p.is_file():shutil.copy2(p,target/p.name)
for name in ['contract.txt','route-decision.txt','baseline.json','portfolio.jsonl','red-plan.log','red-records.log','red-records-final.log','red-inspection.log','red-evidence.log','red-consumers.log','focused-tests.log','parent-consumers.log','INTEGRATED-IDENTITY.json','VERIFICATION.json','frozen-tests.json','scalar_probe.py','qualify.py','verify.py','package.py','qualification.log','scalar-probe.log','wheel.log','wheel-check.json','quality.json','boundary-checks.json','board-native.jsonl','final-tests.log','native-final-tests.log','red-binder-protocol.log','qualification-final.log','qualify-attempt1.py','attempt1-INTEGRATED-IDENTITY.json','boundaries.py','boundaries.log','wheel-final.log','report.py','native-cli-results.json','native_cli_roundtrip.py']:
 shutil.copy2(base/name,out/name)
paths=[*Path('src/ladon').glob('real_bound_native*.py'),Path('src/ladon/lean/LadonRealBoundScalars.lean'),Path('src/ladon/proof_contract_cli.py'),Path('src/ladon/proof_contract_payloads.py'),Path('src/ladon/proofir_v3_cli.py'),Path('src/ladon/_proof_contract_probe_pair.py'),*Path('tests').glob('test_real_bound_native*.py'),*Path('tests/fixtures/real_bound_native').glob('*')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(out/'IMPLEMENTATION.json').write_text(json.dumps({'files':{str(p):sha(p) for p in paths}},indent=2)+'\n')
shutil.copy2('src/ladon/lean/LadonRealBoundScalars.lean',out/'LadonRealBoundScalars.lean')
skills=[Path('skills/ladon/SKILL.md'),Path('../codex-skills/ladon/SKILL.md'),Path('../codex-skills/ladon/references/contract-analysis.md')]
(out/'SKILLS.json').write_text(json.dumps({str(p.resolve()):sha(p) for p in skills},indent=2)+'\n')
for name,p in zip(['bundled-ladon-skill.md','shared-ladon-skill.md','shared-contract-analysis.md'],skills):shutil.copy2(p,out/name)
print('Native evidence copied; report and frozen manifest follow.')
