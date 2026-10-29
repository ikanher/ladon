import subprocess,sys
from pathlib import Path
b=Path('.codex/state/real-prose-native/live')
for label,reading in [('global-produced','global-five-reading.json'),
                      ('set-produced','set-seven-reading.json'),
                      ('wrong-produced','wrong-product-reading.json')]:
 subprocess.run([sys.executable,str(b/'run_public.py'),label,'produce-real-prose-bound',
  '--root','.codex/state/prose-shape-v2/live/generic-project',
  '--interpretation',str(b/reading),'--context',str(b/'generic-context.json'),
  '--alternative-id','generic:'+label,'--author','generic-qualification'],check=True)
