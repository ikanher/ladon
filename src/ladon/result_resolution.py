"""Bind exact manifest targets to supplied canonical subjects without checker replay.

The existing ProofIR owner validates all supplied envelopes first. Association
uses explicit artifact ownership and canonical type/environment/source identities;
review assertions and current working-tree freshness remain independent.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from ladon._canonical_population import _CanonicalPopulation
from ladon.proofir_attachment_policy import resolve_source_map_anchor
from ladon.proofir_v3 import ProofIRV3Error
from ladon.result_manifest import validate_result_manifest
from ladon.result_manifest_io import MAX_RESULT_BYTES, ResultManifestError, canonical_json
from ladon.result_manifest_summary import manifest_summary
from ladon.stored_candidate_type import candidate_type_evidence


def resolve_result_manifest(
    manifest: dict[str, Any], artifacts: list[dict[str, Any]], *, target_id: str | None = None,
) -> dict[str, Any]:
    """Validate the complete evidence population before selecting bounded rows."""
    manifest = validate_result_manifest(manifest)
    if target_id is not None and not any(t['id'] == target_id for t in manifest['targets']):
        raise ResultManifestError('unknown target ID')
    catalog, targets = resolve_result_targets(manifest, artifacts)
    states = {r['targetId']: r['status'] for r in targets}
    links = [{'linkId': link['id'], 'status': _link_status(states[t] for t in link['targetIds'])}
             for link in manifest['links']]
    return _resolution_summary(manifest, targets, links, len(catalog), target_id)


def resolve_result_targets(manifest, artifacts):
    """Resolve all validated manifest targets before any display truncation.

    Callers own manifest validation. Canonical batch validation and attachment
    policy stay here so result inspection and resolution use identical rules.
    """
    return _resolve_population_targets(manifest, _result_population(artifacts))


def _resolve_population_targets(manifest, population):
    catalog, environments, anchors = _catalog_from_population(population)
    return catalog, [_resolve_target(t, catalog, environments, anchors)
                     for t in manifest['targets']]


def _resolution_summary(manifest, targets, links, artifact_count, target_id):
    states = {r['targetId']: r['status'] for r in targets}
    result = manifest_summary(manifest)
    result.update(schema='ladon-result-resolution-v1', operation='resolve',
                  resolutionScope='exact-stored-target-binding', selectedTarget=target_id)
    result['canonicalResolution'] = {
        'status': 'assessed', 'statuses': dict(sorted(Counter(states.values()).items())),
        'linkStatuses': dict(sorted(Counter(r['status'] for r in links).items())),
        'unresolvedLinks': sum(r['status'] != 'resolved' for r in links),
        'artifactCount': artifact_count, 'sourceFreshness': 'not-assessed', 'checking': 'not-assessed',
    }
    selected_targets, selected_links = _selected_rows(targets, links, manifest, target_id)
    result['targetResolutions'] = selected_targets[:100]
    result['linkResolutions'] = selected_links[:100]
    result['omissions'].update(targetResolutions=max(0, len(selected_targets) - 100),
                               linkResolutions=max(0, len(selected_links) - 100))
    result['nonclaims'][1] = (
        'Resolution binds stored canonical subjects; current source freshness, checker '
        'acceptance and informal/formal equivalence are not assessed.'
    )
    _fit(result)
    return result


def _selected_rows(targets, links, manifest, target_id):
    selected_targets = [t for t in targets if target_id is None or t['targetId'] == target_id]
    selected_links = [r for r, link in zip(links, manifest['links'], strict=True)
                      if target_id is None or target_id in link['targetIds']]
    return selected_targets, selected_links


def _result_population(artifacts):
    try:
        return _CanonicalPopulation(artifacts)
    except (ProofIRV3Error, ValueError, TypeError, KeyError) as exc:
        raise ResultManifestError('invalid supplied canonical evidence') from exc


def _catalog(artifacts):
    return _catalog_from_population(_result_population(artifacts))


def _catalog_from_population(population):
    validated = [v.to_dict() for v in population.artifacts]
    catalog = {a['artifactId']: a for a in validated}
    environments = defaultdict(list)
    anchors = defaultdict(list)
    for artifact in validated:
        if artifact['artifactKind'] == 'proofir.environment':
            environments[artifact['environmentRef']].append(artifact)
        if artifact['artifactKind'] == 'proofir.source-map':
            for index, anchor in enumerate(artifact['payload']['anchors']):
                ref = anchor['subjectRef']
                if ref['kind'] == 'declaration':
                    owner = ref.get('artifactRef', artifact['artifactId'])
                    anchors[(owner, ref['localId'])].append((artifact, index, anchor))
    return catalog, environments, anchors


def _resolve_target(target, catalog, environments, anchors):
    row = {'targetId': target['id'], 'targetRevision': target['revision'], 'name': target['name'],
           'status': 'unresolved', 'reason': 'canonical-subject-reference-absent',
           'subjectRef': target.get('subjectRef'), 'sourceFreshness': 'not-assessed',
           'checking': 'not-assessed', 'projectRevisionBasis': 'producer-declared'}
    reference = target.get('subjectRef')
    if reference is None:
        return row
    artifact = catalog.get(reference['artifactId'])
    if artifact is None:
        return _decision(row, 'unresolved', 'canonical-artifact-unavailable')
    subjects = [s for s in artifact['subjectRefs'] if s['kind'] == 'declaration'
                and s['localId'] == reference['subjectId']]
    if not subjects or subjects[0].get('display') != target['name']:
        return _decision(row, 'unresolved', 'canonical-declaration-unavailable')
    problem = _type_problem(target, subjects) or _environment_problem(target, artifact, environments)
    if problem is not None:
        return _decision(row, *problem)
    candidates = anchors.get((reference['artifactId'], reference['subjectId']), [])
    return _resolve_source(row, target, subjects[0], candidates, artifact['environmentRef'])


def _type_problem(target, subjects):
    try:
        evidence = candidate_type_evidence({'subjectRefs': subjects}, target['name'])
    except (ValueError, TypeError, KeyError):
        return 'unresolved', 'canonical-type-unavailable-or-inconsistent'
    if evidence['typeText'] != target['typeText']:
        return 'stale', 'declared-type-mismatch'
    return None


def _environment_problem(target, artifact, environments):
    if artifact['environmentRef'] != target['environment']['digest']:
        return 'stale', 'declared-environment-mismatch'
    environment = environments.get(artifact['environmentRef'], [])
    if not environment:
        return 'unresolved', 'canonical-environment-unavailable'
    if len(environment) != 1:
        return 'ambiguous', 'canonical-environment-ambiguous'
    if target['environment']['toolchain'] not in _toolchain_names(environment[0]):
        return 'stale', 'declared-toolchain-mismatch'
    return None


def _toolchain_names(environment):
    payload = environment['payload']
    toolchain = payload['toolchain']
    names = {f"{toolchain['name']}:{toolchain['version']}"}
    if payload['prover']['name'] == 'Lean':
        names.add('leanprover/lean4:v' + payload['prover']['version'])
    return names


def _resolve_source(row, target, subject, candidates, environment_ref):
    if not candidates:
        return _decision(row, 'unresolved', 'canonical-source-anchor-unavailable')
    if len(candidates) != 1:
        return _decision(row, 'ambiguous', 'canonical-source-anchor-ambiguous')
    artifact, index, anchor = candidates[0]
    if anchor['declName'] != target['name']:
        return _decision(row, 'unresolved', 'canonical-source-declaration-mismatch')
    if (anchor['sourcePath'], anchor['contentDigest']) != (target['source']['path'], target['source']['digest']):
        return _decision(row, 'stale', 'declared-source-mismatch')
    declaration = {'id': subject['localId'], 'declarationName': target['name'],
                   'environmentRef': environment_ref, 'declarationRef': subject['localId'],
                   'declarationFingerprint': subject['fingerprint']['digest'],
                   'sourcePath': target['source']['path'], 'contentHash': target['source']['digest']}
    association = resolve_source_map_anchor(anchor, [declaration], environment_ref=artifact['environmentRef'])
    if (anchor['matchMethod'] != 'environment-fingerprint'
            or association['selectionDecision'] != 'selected'
            or association['candidates'][0]['method'] != 'environment-fingerprint'):
        return _decision(row, 'unresolved', 'canonical-source-association-not-exact')
    row['sourceAnchor'] = {'artifactId': artifact['artifactId'], 'index': index,
                           'basis': 'environment-fingerprint'}
    return _decision(row, 'resolved', 'exact-stored-subject-environment-type-source')


def _decision(row, status, reason):
    row.update(status=status, reason=reason)
    return row


def _link_status(states):
    states = set(states)
    for status in ('stale', 'ambiguous', 'unresolved'):
        if status in states:
            return status
    return 'resolved'


def _fit(result):
    while len(canonical_json(result)) >= MAX_RESULT_BYTES:
        for key in ('reviewObservations', 'linkResolutions', 'targetResolutions'):
            if result[key]:
                result[key].pop()
                result['omissions'][key] += 1
                break
        else:
            raise ResultManifestError('canonical resolution metadata exceeds the compact byte limit')
