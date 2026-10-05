from pathlib import Path
import hashlib,json
root=Path('/home/codex/projects/ladon')
run=Path((root/'.codex/state/source-goal-cli-r56/run-path').read_text().strip())
out=run/'field'; repo=out/'repo'
rows=json.loads((out/'commands.json').read_text())
payloads={r['name']:json.loads((out/(r['name']+'.stdout')).read_text()) for r in rows if not r['name'].endswith('-text')}
results=[p.get('captureResult') if p.get('schema')=='ladon-source-goal-query-result-v1' else p for p in payloads.values()]
receipts=[r for p in results if p for r in p.get('processReceipts',[])]
after={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in repo.rglob('*') if p.is_file()}
fieldsource=(root/'.codex/state/source-goal-cli-r56/field.py').read_text()
prefix=fieldsource[:fieldsource.index('before=')]
# Recover the exact independently generated inputs in another owned directory;
# do not rewrite or rerun the tested source repository.
expected=out/'expected-inputs'; expected.mkdir()
prefix=prefix[prefix.index("(repo/'lean-toolchain').write_text"):]
exec(compile(prefix,'recorded-fixture-inputs','exec'),{'repo':expected})
before={str(p.relative_to(expected)):hashlib.sha256(p.read_bytes()).hexdigest() for p in expected.rglob('*') if p.is_file()}
assert before==after
summary={'status':'passed','candidate':json.loads((run/'identity.json').read_text()),'sourceBefore':before,'sourceAfter':after,'innerHelperCalls':len(receipts),'helperElapsedSeconds':sum(r['elapsedSeconds'] for r in receipts),'helperPeakRssBytes':max((r['peakRssBytes'] or 0 for r in receipts),default=0),'outerCliPeakRssBytes':max(r['peak_rss_bytes'] or 0 for r in rows),'commandCount':len(rows),'textHelperConservativeChargeSeconds':next(r['elapsed_seconds'] for r in rows if r['name'].endswith('-text')),'reportRecovery':'Original field behavior assertions all passed before candidate-identity.json report lookup failed. Summary repaired using identity.json and retained streams; no Lean rerun. Source byte assertions independently repeated.'}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
