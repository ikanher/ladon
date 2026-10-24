"""Snapshot-derived selected-offset capture/completion feasibility probe."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ladon.proof_contract_formal import verify_formal_snapshot
from ladon.proof_contract_recognition import _recognize_estimate
from ladon.proof_slice import pinned_toolchain
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

ROOT = Path(__file__).resolve().parent
RSS = 12 * 1024**3
TIMEOUT = 60
OUTPUT = 8 * 1024**2
source = (ROOT / 'ObligationsRed.lean').read_bytes()
parent = json.loads((ROOT / 'threeStep_snapshot.json').read_text())
provider = json.loads((ROOT / 'middleBound_snapshot.json').read_text())
parent = verify_formal_snapshot(parent, ROOT)
provider = verify_formal_snapshot(provider, ROOT)
assert parent['source']['sha256'] == provider['source']['sha256']
assert parent['source']['sha256'] == hashlib.sha256(source).hexdigest()
assert parent['selection']['declaration'] == 'ObligationsRed.threeStep'
assert provider['selection']['declaration'] == 'ObligationsRed.middleBound'
summary = _recognize_estimate(provider['observation']['normalizedTypeExpr'])

# Read quantifier order, binder names and types from the normalized expression;
# use the recognized structural summary for the symbols and the selected offset.
def binders(node):
    rows = []
    current = node
    while 'forallE' in current:
        row = current['forallE']
        typ = row['type']
        assert typ == {'const': 'Nat', 'levels': []}
        assert row['binderInfo'] == 'explicit'
        rows.append({'name': row['name'], 'type': 'Nat'})
        current = row['body']
    return rows

binder_rows = binders(provider['observation']['normalizedTypeExpr'])
assert len(binder_rows) == len(summary['binders']) == 2
by_id = {f'b{i}': row['name'] for i, row in enumerate(binder_rows)}
s, x = by_id[summary['scaleBinder']], by_id[summary['inputBinder']]
selected_offset = 1
assert type(selected_offset) is int and selected_offset >= 0
left = summary['leftOperator']
map_name = summary['map']
scale = summary['inputScale']
constant = summary['constantName']
assert all(name.startswith('ObligationsRed.') for name in (left, map_name, scale, constant))
statement = (
    f"theorem generatedRequirement ({s} : Nat) ({x} : Nat) :\\n"
    f"    {left} {s} ({map_name} {x}) ≤ {constant} * {scale} ({s} + {selected_offset}) {x} := by\\n"
    "  skip\\n"
).replace('\\n', '\n')
range_ = parent['observation']['declarationRange']
lines = source.decode('utf-8').splitlines(keepends=True)
prefix_offset = len(''.join(lines[:range_['startLine'] - 1]).encode('utf-8'))
prefix_offset += len(lines[range_['startLine'] - 1][:range_['startColumn']].encode('utf-8'))
prefix = source[:prefix_offset]
assert b'theorem threeStep' not in prefix
assert b'theorem firstBound' in prefix and b'theorem middleBound' in prefix
assert b'theorem lastBound' in prefix
# Use the same helper import convention as correspondence_check, then retain the
# exact source prefix; the generated theorem stays in its observed open namespace.
guard = '''\nrun_cmd do
  let env ← Lean.getEnv
  unless (env.find? `ObligationsRed.threeStep).isNone do
    throwError "reserved parent declaration unexpectedly present"
  if env.header.moduleNames.contains `ObligationsRed then
    throwError "source module (which may contain the parent) was imported"

end ObligationsRed
'''
source_text = b'import Lean\n' + prefix + statement.encode() + guard.encode()
path = ROOT / 'GeneratedSourceGoal.lean'
path.write_bytes(source_text)
context = pinned_toolchain(ROOT)
line = next(i for i, value in enumerate(source_text.decode().splitlines(), 1) if value.strip() == 'skip')
capture_result = capture_source_goal(SourceGoalCaptureRequest(
    repo_root=ROOT, source_path=path.name, module='GeneratedSourceGoal',
    line=line, column=6, toolchain=context,
    expected_source_digest='sha256:' + hashlib.sha256(source_text).hexdigest(),
    timeout_seconds=TIMEOUT, max_output_bytes=OUTPUT, max_rss_bytes=RSS,
))
assert capture_result['status'] == 'captured', capture_result
capture = capture_result['capture']
visible = [row['userName'] for row in capture['goal']['localContext']
           if not row['implementationDetail'] and row['userName'] != 'generatedRequirement']
assert visible == [s, x], visible
valid = complete_source_goal(SourceGoalCompletionRequest(
    repo_root=ROOT, capture=capture,
    term=(f'by simpa [ObligationsRed.N1, ObligationsRed.N2, ObligationsRed.C] '
          f'using ObligationsRed.middleBound {s} {x}'), toolchain=context,
    timeout_seconds=TIMEOUT, max_output_bytes=OUTPUT, max_rss_bytes=RSS,
))
negative = complete_source_goal(SourceGoalCompletionRequest(
    repo_root=ROOT, capture=capture,
    term=f'by exact ObligationsRed.threeStep {s} {x}', toolchain=context,
    timeout_seconds=TIMEOUT, max_output_bytes=OUTPUT, max_rss_bytes=RSS,
))
assert valid['status'] == 'completed', valid
assert valid['replay']['status'] == 'accepted' and valid['trust']['accepted'] is True
assert negative['status'] != 'completed', negative
result = {
    'schema': 'source-bridge-capture-completion-probe-v1',
    'parentSnapshotId': parent['snapshotId'], 'providerSnapshotId': provider['snapshotId'],
    'sourceDigest': parent['source']['sha256'],
    'sourcePrefixDigest': 'sha256:' + hashlib.sha256(prefix).hexdigest(),
    'generatedSourceDigest': 'sha256:' + hashlib.sha256(source_text).hexdigest(),
    'selectedOffset': selected_offset, 'recognizedSummary': summary,
    'generatedStatement': statement,
    'capture': {'status': capture_result['status'], 'captureId': capture['captureId'],
                'goalType': capture['goal']['typeDisplay'], 'visibleLocals': visible,
                'imports': capture['environment']['compiledInventory']},
    'positiveCompletion': {'status': valid['status'], 'replay': valid['replay']['status'],
                           'trusted': valid['trust']['accepted']},
    'negativeParentCompletion': {'status': negative['status'],
                                 'diagnostic': negative['diagnostic'],
                                 'replay': negative['replay']['status']},
    'resourceAccounting': {'capture': capture_result['resourceAccounting'],
                           'positive': valid['resourceAccounting'],
                           'negative': negative['resourceAccounting']},
}
(ROOT / 'capture_complete_receipt.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
print(json.dumps({key: result[key] for key in ('parentSnapshotId','providerSnapshotId','sourceDigest',
    'sourcePrefixDigest','generatedSourceDigest','generatedStatement','capture',
    'positiveCompletion','negativeParentCompletion')},indent=2))
