"""Private request-owned canonical artifacts and exact subset closure.

Construction always validates raw occurrences. Detached copies and another
population's handles cannot claim membership in this validation scope.
"""
from dataclasses import dataclass
from types import MappingProxyType

from ladon.proofir_v3 import (
    MAX_ARTIFACT_BYTES,
    MAX_ARTIFACTS,
    MAX_BATCH_BYTES,
    ProofIRV3Error,
    _fail,
    _resolve_batch_limits,
    _validate_external_references,
    _validate_owned_batch,
)


@dataclass(frozen=True, init=False)
class _CanonicalPopulation:
    artifacts: tuple
    sizes: tuple
    _members: MappingProxyType
    _by_id: MappingProxyType

    def __init__(self, values, **bounds):
        artifacts, sizes = _validate_owned_batch(values, **bounds)
        object.__setattr__(self, 'artifacts', artifacts)
        object.__setattr__(self, 'sizes', sizes)
        object.__setattr__(self, '_members', MappingProxyType({
            id(artifact): (artifact, size) for artifact, size in zip(artifacts, sizes, strict=True)
        }))
        object.__setattr__(self, '_by_id', MappingProxyType({
            artifact.content_id: artifact for artifact in artifacts
        }))

    def member(self, artifact_id):
        return self._by_id[artifact_id]

    def validate_subset(self, artifacts, *, max_artifact_bytes=MAX_ARTIFACT_BYTES,
                        max_batch_bytes=MAX_BATCH_BYTES, max_artifacts=MAX_ARTIFACTS):
        """Validate the exact subset scope without preparing envelopes again."""
        if type(artifacts) is not list:
            raise ProofIRV3Error('v3 envelope batch must be an array')
        artifact_limit, batch_limit = _resolve_batch_limits(
            None, max_artifact_bytes, max_batch_bytes, max_artifacts)
        if len(artifacts) > max_artifacts:
            _fail('reference-valid', 'batch-item-limit', '',
                  f'v3 envelope batch exceeds item limit: {max_artifacts}')
        subset, total = {}, 0
        for artifact in artifacts:
            member = self._members.get(id(artifact))
            if member is None or member[0] is not artifact:
                raise ProofIRV3Error('artifact is not a member of this canonical population')
            size = member[1]
            if size > artifact_limit:
                _fail('reference-valid', 'artifact-byte-limit', '',
                      f'v3 envelope exceeds artifact byte limit: {artifact_limit}')
            total += size
            if total > batch_limit:
                _fail('reference-valid', 'batch-byte-limit', '',
                      f'v3 envelope batch exceeds aggregate byte limit: {batch_limit}')
            subset[artifact.content_id] = artifact.payload
        for owner_id, artifact in subset.items():
            _validate_external_references(owner_id, artifact, subset)
