from pathlib import Path
import json
root=Path(__file__).parent
runtimes={r:json.loads((root/f'baseline-comparison-r48-{r}/summary.json').read_text()) for r in ('py311','py312')}
assert all(r['status']=='passed' and r['unchangedCases']==7 and r['expectedFeatureAdditions']==2 for r in runtimes.values())
report={'status':'passed','frozenFiles':127,'runtimes':runtimes,'scope':'Offline frozen input comparisons: seven commands unchanged; inspect adds bounded supplied-evidence inspection and guide adds an explicit missing-annotation view. Frozen historical files unchanged; no Lean replay or correspondence promotion.'}
(root/'baseline-comparison-r48.json').write_text(json.dumps(report,indent=2)+'\n');print('Baseline comparison passed on both runtimes.')
