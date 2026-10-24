"""Run unchanged legacy measurement harnesses on the frozen current runtime."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

root = Path.cwd()
evidence = root / 'openspec/changes/ladon-proof-contract-evaluation/evidence'
snapshot = root / '.codex/state/proof-contract-analysis/current-no-beam-20261018'
manifest = evidence / 'current-no-beam-20261018/RUNTIME.json'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


for name, old_name in [('portable', 'search-baseline-20261018'), ('matrix', 'matrix-baseline-20261018')]:
    old = evidence / old_name
    target = evidence / f'{name}-no-beam-20261018'
    target.mkdir()
    shutil.copy2(old / 'measure.py', target / 'measure.py')
    module = load(target / 'measure.py', name)
    module.MANIFEST = manifest
    if name == 'portable':
        shutil.copy2(old / 'CASES.json', target / 'CASES.json')
        shutil.copytree(old / 'inputs', target / 'inputs',
                        ignore=shutil.ignore_patterns('.lake', '__pycache__'))
        module.BASELINE = snapshot
        module.freeze()
        assert (old / 'ROUTES.json').read_bytes() == (target / 'ROUTES.json').read_bytes()
        module.measure()
    else:
        module.BASE = snapshot
        module.main()
    print(f'Completed {name} no-beam arm', flush=True)
