"""A row-local canonical contradiction never erases a valid sibling receipt."""
import sys

import pytest
from test_semantic_candidate_batch_worker import _stream

from ladon.process_supervisor import ProcessResult
from ladon.semantic_candidate_batch_worker import check_semantic_candidates
from ladon.semantic_candidate_worker import SEMANTIC_BATCH_PROTOCOL, SemanticCandidateRequest


@pytest.mark.parametrize('names', [('Main.good', 'Main.conflict'), ('Main.conflict', 'Main.good')])
def test_canonical_failure_is_attributed_without_publishing_invalid_artifacts(tmp_path, names):
    olean = tmp_path / 'Main.olean'
    olean.write_bytes(b'compiled')

    def runner(command, **_kwargs):
        header = {
            'protocol': SEMANTIC_BATCH_PROTOCOL, 'frameVersion': 1,
            'frameKind': 'header', 'sequence': 0, 'terminal': False,
            'requestId': command[-4], 'goalRequestDigest': command[-6],
            'executionContextRef': 'unbound', 'universePolicy': 'lean-level-mvar-succ-zero/v1',
            'leanVersion': '4.fixture', 'leanCommit': 'fixture', 'executablePath': sys.executable,
            'module': 'Main', 'probe': {'name': command[-5], 'typeDisplay': 'Nat', 'typeStructural': 'Nat'},
            'importedModules': [{'module': 'Main', 'oleanPath': str(olean)}], 'localContext': [],
        }
        rows = []
        for name in names:
            rows.append({
                'candidate': name, 'status': 'accepted',
                'candidateSubject': {'name': name, 'typeDisplay': 'Nat', 'typeStructural': 'Nat'},
                'applicationTerm': name, 'dischargedHypotheses': [], 'substitutions': [],
                'residualPremises': [], 'failureStage': '', 'diagnostic': '',
            })
        invalid = next(row for row in rows if row['candidate'] == 'Main.conflict')
        invalid['substitutions'] = [
            {'variable': 'x', 'termDisplay': '0', 'termStructural': 'zero'},
            {'variable': 'x', 'termDisplay': '1', 'termStructural': 'one'},
        ]
        return ProcessResult(command, 0, _stream(header, rows), '', 0.1)

    result = check_semantic_candidates(
        SemanticCandidateRequest(tmp_path, 'Main', 'Nat', 'Main.good'),
        names, runner=runner,
    )
    assert result.status == 'partial', result.diagnostic
    assert [row['candidate'] for row in result.rows] == ['Main.good']
    assert result.rows[0]['evidenceReceipt']['authorityBasis'] == 'elaborator-check'
    assert result.diagnostic['failedCandidates'] == ['Main.conflict']
    failure = result.diagnostic['candidateFailures'][0]
    assert failure['candidate'] == 'Main.conflict'
    assert 'conflict' in failure['message'].lower()
