"""Single informed regression for the new exact-goal boundary, not admission."""
import copy
import hashlib
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

base = Path(__file__).resolve().parent
root = base / 'informed-project'
root.mkdir()
tmp = root / 'tmp'
tmp.mkdir()
os.environ['TMPDIR'] = str(tmp)

from ladon.process_supervisor import run_bounded_target_process
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_binding import _alpha_expression
from ladon.semantic_lean_execution import prepare_direct_lean_execution
from ladon.source_goal_capture import SourceGoalCaptureRequest, capture_source_goal
from ladon.source_goal_completion import SourceGoalCompletionRequest, complete_source_goal

started = time.monotonic()
deadline = started + 600
caps = {'seconds': 600, 'maxRssBytes': 12 * 1024**3, 'maxOutputBytes': 8 * 1024**2,
        'startedMonotonic': started, 'deadlineMonotonic': deadline,
        'scope': 'one informed exact-owner boundary regression, no admission or native connection'}
(base / 'INFORMED-BUDGET.json').write_text(json.dumps(caps, indent=2) + '\n')
old = base.parent / 'prose-observation-production/live/project'
(root / 'lean-toolchain').write_bytes((old / 'lean-toolchain').read_bytes())
context = pinned_toolchain(old)
(root / '.lake/build/lib/lean').mkdir(parents=True)
for i, library in enumerate(context.library_roots):
    target = root / f'.lake/packages/import{i}/.lake/build/lib/lean'
    target.parent.mkdir(parents=True)
    target.symlink_to(library, target_is_directory=True)
helper = Path('src/ladon/lean/LadonProseExactGoal.lean').resolve()
(root / helper.name).write_bytes(helper.read_bytes())
context = pinned_toolchain(root)
execution = prepare_direct_lean_execution(root, None, context, require_compiled_module=False)
receipts = []


def lean(args):
    remaining = deadline - time.monotonic()
    assert remaining > 0
    result = run_bounded_target_process([*execution.command, *args], cwd=root,
                                      env=execution.environment, timeout_seconds=min(60, remaining),
                                      max_output_bytes=caps['maxOutputBytes'],
                                      max_rss_bytes=caps['maxRssBytes'])
    receipts.append(asdict(result))
    (base / 'INFORMED-LEAN-PROCESSES.json').write_text(json.dumps(receipts, indent=2) + '\n')
    assert result.succeeded, result.stdout + result.stderr


lean(['-o', '.lake/build/lib/lean/LadonProseExactGoal.olean', helper.name])
prior = base.parent / 'real-prose-connection'
source = (prior / 'Context-before-canonical.lean').read_text().split('namespace LadonExactConnectionProbe')[0]
formal = json.loads(Path('openspec/changes/ladon-real-bound-contracts/evidence/qualification-20261027/native/inverse_finiteJets-production.json').read_text())
assert source.encode().startswith(formal['sourceText'].encode())
snapshot = formal['request']['plan']['bindingPlan']['observation']['statementSnapshot']
old_owners = json.loads((prior / 'PROBE-OWNERS.json').read_text())
name = old_owners['authoredOwners']['five']['declaration']
source = 'import LadonProseExactGoal\n' + source
path = root / 'ExactCase.lean'
path.write_text(source)
observation = root / 'authored.json'
lean(['--run', str(Path('src/ladon/lean/ladon_prose_observation.lean').resolve()),
      'ExactCase', 'ExactCase.lean', str(path), name, str(observation)])
authored = json.loads(observation.read_text())
assert authored['status'] == 'observed'
formal_range = copy.deepcopy(snapshot['observation']['declarationRange'])
for key in formal_range:
    if key.endswith('Line'):
        formal_range[key] += 1
request = {'schema': 'ladon-prose-exact-goal-v1', 'module': 'ExactCase',
           'formal': {'name': snapshot['selection']['declaration'], 'kind': 'theorem-type',
                      'range': formal_range,
                      'expression': _alpha_expression(snapshot['observation']['normalizedTypeExpr'])},
           'authored': {'name': name, 'kind': 'proposition-value',
                        'range': authored['declarationRange'],
                        'expression': _alpha_expression(authored['propositionExpr'])},
           'premises': []}
(base / 'INFORMED-REQUEST.json').write_text(json.dumps(request, indent=2) + '\n')
goal = 'ladon_prose_exact_goal% ' + json.dumps(json.dumps(request, sort_keys=True, ensure_ascii=False, separators=(',', ':')), ensure_ascii=False)
term = json.loads((prior / 'probe-five.json').read_text())['term']
source += f'\ntheorem ExactBoundaryWitness : {goal} := ({term})\n'
source += f'example : {goal} := by\n  skip\n'
path.write_text(source)
context = pinned_toolchain(root)
capture = capture_source_goal(SourceGoalCaptureRequest(root, 'ExactCase.lean', 'ExactCase',
    len(source.splitlines()), 4, context, timeout_seconds=min(60, deadline-time.monotonic())))
(base / 'INFORMED-CAPTURE.json').write_text(json.dumps(capture, indent=2) + '\n')
assert capture['status'] == 'captured', capture.get('diagnostic')
completion = complete_source_goal(SourceGoalCompletionRequest(root, capture['capture'],
    'ExactBoundaryWitness', context, timeout_seconds=min(60, deadline-time.monotonic())))
(base / 'INFORMED-COMPLETION.json').write_text(json.dumps(completion, indent=2) + '\n')
assert completion['status'] == 'completed', completion.get('diagnostic')
assert completion['replay']['status'] == 'accepted'
assert completion['trust']['accepted'] is True and completion['trust']['coverage'] == 'complete'
assert not set(completion['trust']['observedAxioms']) - {'propext', 'Classical.choice', 'Quot.sound'}
assert helper.read_bytes() == (root / helper.name).read_bytes()
assert time.monotonic() <= deadline
result = {'schema': 'ladon-exact-goal-boundary-regression-v1', 'status': 'kernel-replayed',
          'seconds': time.monotonic()-started, 'requestBytes': len(goal.encode()),
          'helperDigest': hashlib.sha256(helper.read_bytes()).hexdigest(),
          'copiedFormalPrefixExact': True, 'formalOriginalRangeShift': 1,
          'authoredFreshlyObserved': True, 'formalBodyUsedAsProof': False,
          'formalPremiseRetained': True, 'nativeConnection': False, 'freshFormalAdmission': False,
          'sourceFidelity': 'unreviewed', 'scope': caps['scope']}
(base / 'INFORMED-RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
