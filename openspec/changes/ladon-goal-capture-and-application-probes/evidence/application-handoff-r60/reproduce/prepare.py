from pathlib import Path
import tempfile,json,shutil
root=Path.cwd();state=root/'.codex/state/application-handoff-r60';run=Path(tempfile.mkdtemp(prefix='ladon-handoff-r60-',dir='/home/codex/.cache'));repo=run/'fixture';repo.mkdir();matrix=(root/'../lean/matrix-factorization').resolve()
(repo/'lean-toolchain').write_bytes((matrix/'lean-toolchain').read_bytes());(repo/'.lake/build/lib').mkdir(parents=True);(repo/'.lake/build/lib/lean').symlink_to(matrix/'.lake/build/lib/lean',target_is_directory=True);(repo/'.lake/packages').symlink_to(matrix/'.lake/packages',target_is_directory=True)
header='import Mf.DP.PoissonFixedEpochCenterGapPropagation\n\n'
base='example (point : Mf.DP.PoissonFixedEpochPoint) (h boundary query : ℝ)\n    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)\n    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query)'
for name,extra in [('ContextA','\n    (hBoundaryGap : 0 ≤ Mf.DP.fixedEpochCenterGap point h boundary)'),('ContextB','')]:
 text=header+base+extra+' :\n    0 < Mf.DP.fixedEpochCenterGap point h query := by\n  skip\n';(repo/(name+'.lean')).write_text(text)
 positions=locals().get('positions',{});positions[name]={'line':len(text.splitlines()),'column':6}
identity={'qualifiedCandidate':json.loads(Path((root/'.codex/state/application-completion-r59/run-path').read_text().strip(),'identity.json').read_text()),'matrixRepository':str(matrix),'fixtureRepository':str(repo),'compiledLibraries':'explicit private fixture symlinks to existing matrix compiled roots; no builds or source copies from excluded projects','positions':positions}
(run/'fixture-identity.json').write_text(json.dumps(identity,indent=2)+'\n');(state/'run-path').write_text(str(run)+'\n');(state/'budget.json').write_text(json.dumps({'budgetSeconds':180,'chargedUpperBoundSeconds':0,'scope':'new OpenSpec3.1 read-only fixed-epoch handoff acceptance; r59 completion integration budget remains frozen at214.7006761688972/240','trials':[]},indent=2)+'\n');print(json.dumps(identity))
