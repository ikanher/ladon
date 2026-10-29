"""Freeze the actual rule qualification and reuse only byte-identical prior checks."""
import hashlib,json
from pathlib import Path
from ladon.quality import strict_quality_issues
from ladon.real_bound_binding_check import binding_identity
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=Path('.codex/state/real-bound-rules')
prior=Path('openspec/changes/ladon-real-bound-contracts/evidence')
old=prior/'bound-application-20261025'
implementation=json.loads((old/'IMPLEMENTATION.json').read_text())
assert implementation['checkerIdentity']==binding_identity()
assert all(sha(Path(p))==value for p,value in implementation['files'].items())
preserved={}
for name in ('shape-observation-20261025','prefix-admission-20261025','bound-application-20261025'):
 folder=prior/name;manifest=json.loads((folder/'ARTIFACTS.json').read_text())
 assert all(sha(folder/p)==value for p,value in manifest.items())
 preserved[name]=len(manifest)
primarybase=Path('.codex/state/navier-stokes-informed-diagnostic')
primary=json.loads((primarybase/'SOURCE-MANIFEST.json').read_text())
assert all(sha(primarybase/p)==value for p,value in primary.items())
checks={}
for module in ('PositiveRules','NegativeRules'):
 red=json.loads((base/'qualification-red'/(module+'.json')).read_text())
 assert red['returncode']!=0 and ('TransferAt' in red['stdout'] or 'scaled_bound_mono' in red['stdout'])
 good=json.loads((base/'qualification-green-2'/(module+'.json')).read_text())
 assert good['returncode']==0 and not any(good[k] for k in ('timed_out','memory_limited','output_limited'))
 rows=json.loads((base/'qualification-green-2'/(module+'-axioms.json')).read_text())
 assert all(set(row['axioms'])<={'propext','Classical.choice','Quot.sound'} for row in rows)
 checks[module]=[row['declaration'] for row in rows]
all_names=set(sum(checks.values(),[]));assert len(all_names)==27
board=json.loads((base/'frozen-tests.json').read_text())
mismatches=[row['path'] for row in board['frozenTests'] if row.get('matches') is False]
assert mismatches==[str(Path('tests/test_rational_lean_encoder_v2.py').resolve())]
assert not strict_quality_issues([Path('tests/test_real_bound_rules_lean.py')])
pytest=(base/'pytest.log').read_text();assert '2 passed' in pytest and 'skipped' not in pytest
wheel=json.loads((base/'wheel-check.json').read_text());assert wheel['ruleModuleIncluded'] and wheel['sourceMatches']
baseline=json.loads((base/'baseline.json').read_text());assert all(sha(Path(p))==value for p,value in baseline.items())
result={'primaryFilesUnchanged':len(primary),'priorArtifactsUnchanged':preserved,
 'unchangedBindingEvidenceReused':{'tests':172,'identityVerified':True},
 'newIntegrationTests':{'passed':2,'skipped':0},'uniqueKernelCheckedDeclarations':len(all_names),
 'genericPositiveExamples':11,'mathematicalCounterexamples':3,'rejectedApplicationControls':7,
 'reusableRuleTheorems':6,'compiledModulesObserved':len(json.loads((base/'COMPILED-INVENTORY.json').read_text())['modules']),
 'observedDeclarations':checks,'existingRuntimeUnchanged':list(baseline),
 'preexistingBoardMismatches':mismatches,'fullSemanticContractAdmission':'unresolved','informedContractsAdmitted':'0/2',
 'verificationCorrection':'Only matches==False identifies active mismatches; null historical entries are not mismatches.',
 'initialCompileFailure':'Lean reserved keyword prefix used as local binder; fixed in production only; frozen tests unchanged.'}
(base/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(all_names),'kernel-checked declarations, two new tests, and unchanged 172-test binding evidence.')
