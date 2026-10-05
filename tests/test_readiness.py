from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta

import pytest
from test_child_acceptance import bundle

from ladon.readiness import assess_readiness


def _evidence(now: datetime) -> dict[str, object]:
    return {
        name: {
            "status": "passed",
            "timestamp": now.isoformat(),
            "command": f"gate {name}",
            "outcome": "passed",
            "producerIdentity": "ladon-tests/v1",
            "sourceTreeIdentity": "sha256:" + "c" * 64,
            "environmentRef": "sha256:" + "d" * 64,
            "commandVector": ["python", "-m", "pytest"],
            "workingDirectory": "/repo",
            "resultArtifactRefs": ["sha256:" + "e" * 64],
            "logArtifactRefs": ["sha256:" + "f" * 64],
            "candidates": ["fixture.goal"] if name == "externalOutcome" else None,
            "metrics": {"recall": 1.0} if name == "externalOutcome" else None,
        }
        for name in (
            "installedSmoke",
            "adversarialContract",
            "resourceGate",
            "externalOutcome",
            "platformPosture",
            "ownerDecision",
        )
    }


def test_digest_labels_without_resolved_bytes_cannot_promote() -> None:
    now = datetime.now(UTC)
    result = assess_readiness(_evidence(now), now=now)
    assert result["level"] == "experimental"


def test_readiness_demotes_stale_evidence() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now - timedelta(days=2))
    result = assess_readiness(evidence, now=now)
    assert result["level"] == "experimental"


def test_readiness_rejects_status_without_command_and_outcome() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now)
    evidence["installedSmoke"] = {"status": "passed", "timestamp": now.isoformat()}
    assert assess_readiness(evidence, now=now)["level"] == "experimental"


def test_readiness_rejects_help_only_external_evidence() -> None:
    now = datetime.now(UTC)
    evidence = _evidence(now)
    evidence["externalOutcome"] = {
        "status": "passed",
        "timestamp": now.isoformat(),
        "command": "ladon --help",
        "outcome": "help displayed",
    }
    assert assess_readiness(evidence, now=now)["level"] == "experimental"


@pytest.fixture
def qualified_case(tmp_path):
    import json

    case = bundle.__wrapped__(tmp_path)
    from ladon.child_acceptance import canonical_digest

    now = datetime.now(UTC)
    receipt = case.receipt
    manifest = json.loads((case.root / case.objects[receipt['sourceTreeIdentity']]['path']).read_bytes())
    manifest['candidateCommit'] = '1' * 40
    receipt['sourceTreeIdentity'] = case.put_json(manifest)
    candidate = {'candidateCommit': manifest['candidateCommit'],
                 'sourceTreeIdentity': receipt['sourceTreeIdentity'], 'wheelDigest': receipt['wheelDigest']}
    receipt['candidateIdentity'] = canonical_digest(candidate)
    receipt['candidateArtifactRef'] = case.put_json(candidate)
    for row in case.results:
        row.update(candidateIdentity=receipt['candidateIdentity'], sourceTreeIdentity=receipt['sourceTreeIdentity'],
                   startedAt=(now - timedelta(seconds=1)).isoformat(), completedAt=now.isoformat())
    case.refresh()
    reference = case.put_json(receipt)
    scope = ('candidateIdentity', 'sourceTreeIdentity', 'wheelDigest', 'producerIdentity',
             'environmentRef', 'workingDirectory')
    base = {**{key: receipt[key] for key in scope}, 'receiptArtifactRef': reference,
            'candidateCommit': manifest['candidateCommit'], 'timestamp': now.isoformat(),
            'status': 'passed', 'outcome': 'recorded acceptance passed',
            'resultArtifactRefs': receipt['resultArtifactRefs'], 'logArtifactRefs': receipt['logArtifactRefs'],
            'command': case.results[0]['command'], 'commandVector': case.results[0]['commandVector']}
    names = ('installedSmoke', 'adversarialContract', 'resourceGate', 'platformPosture')
    evidence = {name: copy.deepcopy(base) for name in names}
    context = {'now': now, 'evidence_root': case.root,
               'inventories': dict.fromkeys(names, case.inventory),
               'test_requirements': dict.fromkeys(names, ('tests/test_alpha.py::test_case',))}
    return evidence, context


def test_recorded_contract_promotes_without_inventing_external_outcomes(qualified_case):
    evidence, context = qualified_case
    result = assess_readiness(evidence, **context)
    assert result['level'] == 'contract-supported'
    assert 'externalOutcome' in result['validationIssues']


@pytest.mark.parametrize(('key', 'bad'), [
    ('candidateCommit', '2' * 40), ('candidateIdentity', 'sha256:' + '0' * 64),
    ('command', 'ladon --help'), ('commandVector', ['ladon', '--help']),
    ('receiptArtifactRef', 'sha256:' + '0' * 64),
])
def test_rehashed_metadata_cannot_change_recorded_execution(qualified_case, key, bad):
    evidence, context = qualified_case
    evidence['installedSmoke'][key] = bad
    assert assess_readiness(evidence, **context)['level'] == 'experimental'


@pytest.mark.parametrize('node', ['tests/test_alpha.py::test_help', 'tests/test_alpha.py::test_not_collected'])
def test_help_only_or_unexecuted_named_nodes_demote(qualified_case, node):
    evidence, context = qualified_case
    context['test_requirements']['installedSmoke'] = (node,)
    assert assess_readiness(evidence, **context)['level'] == 'experimental'


def test_stale_verified_execution_demotes_without_relabeling(qualified_case):
    evidence, context = qualified_case
    context['now'] += timedelta(days=2)
    assert assess_readiness(evidence, **context)['level'] == 'experimental'


def test_fresh_metadata_timestamp_cannot_refresh_an_old_execution(qualified_case):
    evidence, context = qualified_case
    evidence['installedSmoke']['timestamp'] = (context['now'] + timedelta(seconds=1)).isoformat()
    assert assess_readiness(evidence, **context)['level'] == 'experimental'


def test_readiness_rejects_future_naive_and_malformed_age_evidence() -> None:
    now = datetime.now(UTC)
    for timestamp, max_age in (
        ((now + timedelta(days=1)).isoformat(), 86_400),
        (now.replace(tzinfo=None).isoformat(), 86_400),
        (now.isoformat(), "invalid"),
    ):
        evidence = _evidence(now)
        evidence["installedSmoke"]["timestamp"] = timestamp  # type: ignore[index]
        evidence["installedSmoke"]["maxAgeSeconds"] = max_age  # type: ignore[index]
        assert assess_readiness(evidence, now=now)["level"] == "experimental"
