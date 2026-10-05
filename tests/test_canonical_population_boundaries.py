"""Request ownership cannot replace subset closure or occurrence preflight."""
import copy
from dataclasses import FrozenInstanceError

import pytest
from support.semantic_evidence import semantic_evidence
from test_canonical_population_reuse import _environment_extra_check

from ladon.proofir_v3 import ProofIRV3Error, validate_envelope_batch


def population(values, **bounds):
    from ladon._canonical_population import _CanonicalPopulation
    return _CanonicalPopulation(values, **bounds)


def test_subset_closure_matches_raw_pair_rejection():
    values = _environment_extra_check()
    owner = population(values)
    with pytest.raises(ProofIRV3Error, match='not present'):
        owner.validate_subset([owner.artifacts[0], owner.artifacts[2]])
    owner.validate_subset(list(owner.artifacts))


def test_owned_members_are_immutable_detached_and_request_specific():
    values, _, _ = semantic_evidence('immutable-population')
    original = copy.deepcopy(values)
    owner = population(values)
    foreign = population(original)
    values[0]['payload']['options']['changed'] = 'outside'
    detached = owner.artifacts[0].to_dict()
    detached['payload']['options']['changed'] = 'copy'
    assert owner.artifacts[0].to_dict() == original[0]
    with pytest.raises(TypeError):
        owner.artifacts[0].payload['payload']['options']['changed'] = 'inside'
    with pytest.raises((FrozenInstanceError, AttributeError)):
        owner.artifacts = ()
    with pytest.raises(ProofIRV3Error, match='member'):
        owner.validate_subset([foreign.artifacts[0], owner.artifacts[1]])
    with pytest.raises(ProofIRV3Error, match='member'):
        owner.validate_subset([detached])


def test_original_and_subset_duplicate_occurrences_count_against_limits():
    values, _, _ = semantic_evidence('duplicate-population')
    with pytest.raises(ProofIRV3Error, match='item limit'):
        population([values[0], values[0], values[1]], max_artifacts=2)
    owner = population([values[0], values[0], values[1]])
    assert len(owner.artifacts) == 3
    repeated = [owner.artifacts[0], owner.artifacts[0]]
    with pytest.raises(ProofIRV3Error, match='item limit'):
        owner.validate_subset(repeated, max_artifacts=1)
    with pytest.raises(ProofIRV3Error, match='aggregate byte limit'):
        owner.validate_subset(repeated, max_batch_bytes=owner.sizes[0])
    with pytest.raises(ProofIRV3Error, match='item limit'):
        validate_envelope_batch([values[0], values[0]], max_artifacts=1)


def test_nested_external_subject_reference_is_not_skipped_on_frozen_members():
    values = _environment_extra_check()
    # The descriptor lives in an input array, which is frozen into a tuple.
    check = values[2]
    check['payload']['inputs']['subjectRefs'].append({
        'artifactRef': values[1]['artifactId'], 'kind': values[1]['subjectRefs'][0]['kind'],
        'localId': values[1]['subjectRefs'][0]['localId'],
    })
    from ladon.proofir_v3 import detached_content_id
    check['artifactId'] = detached_content_id(check)
    owner = population(values)
    with pytest.raises(ProofIRV3Error, match='not present'):
        owner.validate_subset([owner.artifacts[0], owner.artifacts[2]])
    owner.validate_subset(list(owner.artifacts))
