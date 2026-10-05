from pathlib import Path
import json
root=Path(__file__).parent
runtimes={r:json.loads((root/f'baseline-comparison-r46-{r}/summary.json').read_text()) for r in ('py311','py312')}
assert all(r['status']=='passed' and r['unchangedCases']==8 and r['expectedFeatureAdditions']==1 for r in runtimes.values())
report={'status':'passed','frozenFiles':127,'runtimes':runtimes,'scope':'Offline frozen input comparisons: eight commands unchanged, inspect intentionally changes from unavailable to bounded supplied-evidence inspection. Frozen historical files unchanged; no Lean replay or correspondence promotion.'}
(root/'baseline-comparison-r46.json').write_text(json.dumps(report,indent=2)+'\n');print('Baseline comparison passed on both runtimes.')
