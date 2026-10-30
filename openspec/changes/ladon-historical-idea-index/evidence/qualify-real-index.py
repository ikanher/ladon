"""Measure an independent snapshot; never publish into the shared live index."""
import json
import sqlite3
import time
import statistics
from pathlib import Path
from ladon.idea_migration import migrate_index, OBSERVATIONS
from ladon.proof_search_index import query_proof_search_index

root = Path('/home/codex/projects/lean/matrix-factorization')
source = root / '.ladon/index/proof-search.sqlite'
destination = Path('temp/idea-history-baseline/project-final-copy.sqlite').resolve()
assert not destination.exists(), 'qualification copy already exists'
start = time.monotonic()
with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as original:
    identity = dict(original.execute('SELECT key,value FROM metadata'))
    assert identity['indexSchema'] == 'ladon-proof-search-index-v6', identity
    with sqlite3.connect(destination) as copy:
        original.backup(copy)
print('snapshot ready', destination.stat().st_size, flush=True)

def observe(path):
    timings = {}
    with sqlite3.connect(path) as db:
        for name, sql in OBSERVATIONS.items():
            db.execute(sql).fetchall()
            samples = []
            for _ in range(9):
                t = time.perf_counter()
                db.execute(sql).fetchall()
                samples.append(time.perf_counter() - t)
            timings[name] = statistics.median(samples)
    results = {}
    for term in ['Robbins', 'martingale', 'Adam']:
        data = query_proof_search_index(root, index_path=path, text=term, limit=10)
        results[term] = data['results']
    return timings, results

before_times, before = observe(destination)
report = migrate_index(root, index_path=destination)
after_times, after = observe(destination)
report['publicQueriesPreserved'] = before == after
report['warmQueryTimings'] = {key: {'beforeSeconds': before_times[key], 'afterSeconds': after_times[key], 'ratio': after_times[key] / before_times[key]} for key in before_times}
report['qualificationElapsedSeconds'] = time.monotonic() - start
report['sourcePath'] = str(source)
report['sourceGenerationIdentity'] = identity.get('generationIdentity')
report['sourceModified'] = False
Path('temp/idea-history-baseline/real-index-final-report.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'metrics'}, indent=2), flush=True)
print(json.dumps({k: v for k, v in report['metrics'].items() if k not in {'tables','queries'}}, indent=2), flush=True)
