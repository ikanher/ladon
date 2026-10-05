"""Execute comparable baseline subjects and independently replay suggestions.

Native library search uses its own environment-wide population. Text search
and #check have narrower outcome classes; downstream closure verification is
reported separately and never attributed to those tools themselves.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from ladon.evaluation_process import captured_text, measure_command


def proof_source(case, tactic: str, *, check_axioms=True) -> str:
    """Bind the same ordered caller locals and proposition in independent Lean source."""
    binders = ' '.join('(' + row['name'] + ' : ' + row['type'] + ')' for row in case['localContext'])
    source = ('import Lean\nimport ' + case['module'] + '\nset_option autoImplicit false\n'
              'theorem ladonEvaluationReplay ' + binders + ' : ' + case['goal'] + ' := by\n'
              '  intros\n  ' + tactic.replace('\n', '\n  ') + '\n')
    return source + ('#print axioms ladonEvaluationReplay\n' if check_axioms else '')


def suggested_tactics(text: str) -> list[str]:
    """Read only explicit Lean suggestion lines; never interpret admitted tactic output as proof."""
    suggestions = []
    suggestion_block = False
    for line in text.splitlines():
        match = re.search(r'Try (?:this|these):\s*(.*)', line)
        if match:
            suggestion_block = True
        value = match.group(1).strip() if match else line.strip()
        value = re.sub(r'^\[apply\]\s*', '', value)
        if suggestion_block and value.startswith(('exact ', 'apply ', 'refine ', 'rfl')) and value not in suggestions:
            suggestions.append(value)
    return suggestions


def run_baseline(method, case, context, bounds, output: Path) -> dict:
    """Execute one baseline and keep generation and common verification distinct."""
    if method not in ('exact?', 'apply?', '#check', 'rg', 'editor-search'):
        raise ValueError('unsupported evaluation baseline')
    if method == 'editor-search':
        return {'method': method, 'status': 'unavailable', 'reason': 'no automatable editor protocol',
                'assessments': [], 'generation': None}
    argv = _baseline_command(method, case, context, output)
    if argv is None:
        return {'method': method, 'status': 'unavailable', 'reason': 'baseline executable unavailable',
                'assessments': [], 'generation': None}
    generation = measure_command(argv, cwd=context.repo_root, environment=context.environment,
                                 bounds=bounds, output=output, stem='generation')
    text = captured_text(generation) + captured_text(generation, 'stderr')
    proposals = _proposals(method, case, text)
    assessments = _replay_proposals(proposals[:bounds['maxCandidates']], case, context,
                                    bounds, output, generation['runtimeSeconds'])
    return {'method': method, 'status': generation['status'], 'generation': generation,
            'assessments': assessments, 'population': 'environment-wide' if method in ('exact?', 'apply?') else 'registered source/candidate pool',
            'nonclaims': ['Native search populations differ; this is not a pooled leaderboard.',
                          '#check and rg generation do not establish applicability.',
                          'Independent suggestion replay is a separately recorded operation.']}


def _baseline_command(method, case, context, output):
    output.mkdir(parents=True, exist_ok=True)
    if method == 'rg':
        executable = shutil.which('rg')
        return [executable, '-n', '-F', '--', case['pattern'], str(context.repo_root / case['sourceFile'])] if executable else None
    source = ('import Lean\nimport ' + case['module'] + '\n' +
              ''.join('#check ' + candidate + '\n' for candidate in case['candidatePool'])) if method == '#check' else proof_source(case, method, check_axioms=False)
    path = output / 'generation.lean'
    with path.open('x') as stream:
        stream.write(source)
    return [str(context.lean_path), str(path)]


def _proposals(method, case, text):
    if method in ('exact?', 'apply?'):
        return [(tactic, _candidate_label(tactic, case)) for tactic in suggested_tactics(text)]
    proposals = []
    for candidate in case['candidatePool']:
        identifier = candidate if method == '#check' else candidate.rsplit('.', 1)[-1]
        if re.search(r'(?<![\w.])' + re.escape(identifier) + r'(?![\w.])', text):
            proposals.append(('apply ' + candidate + '\nall_goals assumption', candidate))
    return proposals


def _candidate_label(tactic, case):
    return next((candidate for candidate in case['candidatePool'] if candidate in tactic), None)


def _replay_proposals(proposals, case, context, bounds, output, elapsed):
    assessments = []
    for index, (tactic, candidate) in enumerate(proposals):
        source = proof_source(case, tactic)
        path = output / ('replay-' + str(index) + '.lean')
        with path.open('x') as stream:
            stream.write(source)
        record = measure_command([str(context.lean_path), str(path)], cwd=context.repo_root,
                                 environment=context.environment, bounds=bounds, output=output,
                                 stem='replay-' + str(index), remaining_seconds=bounds['timeoutSeconds'] - elapsed)
        elapsed += record['runtimeSeconds']
        outcome = _replay_outcome(record)
        assessments.append({'candidate': candidate, 'tactic': tactic, 'status': outcome,
                            'sourcePath': str(path), 'measurement': record,
                            'availableAfterSeconds': elapsed})
    return assessments


def _replay_outcome(record):
    if record['status'] == 'not-run' or any(record.get(key) for key in ('timedOut', 'memoryLimited', 'outputLimited')):
        return 'unassessed'
    text = captured_text(record) + captured_text(record, 'stderr')
    if record['status'] == 'passed':
        return 'admitted' if 'sorryAx' in text or 'declaration uses' in text and 'sorry' in text else 'closed'
    return _failed_replay_outcome(text)


def _failed_replay_outcome(text):
    if re.search(r':(?:1|2):\d+: error: (?:unknown module prefix|object file .* does not exist)', text):
        return 'unassessed'
    if "tactic 'assumption' failed" in text or 'unsolved goals' in text:
        return 'partial'
    return 'invalid'
