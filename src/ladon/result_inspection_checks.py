"""Stored check observations with exact subject and environment associations."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from copy import deepcopy

from ladon.evidence_receipt_readers import _stored_check_receipt_owned, stored_check_receipt
from ladon.result_manifest_io import ResultManifestError


class CheckCards(Sequence):
    """An input-validated population whose expensive cards are built by page."""

    def __init__(self, index, catalog, resolutions, receipts, selected):
        self.index = index
        self.catalog = catalog
        self.resolutions = resolutions
        self.receipts = receipts
        self.selected = selected

    def __len__(self):
        return len(self.selected)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return [self[i] for i in range(*key.indices(len(self)))]
        artifact_id = self.selected[key]
        return _check_card(self.index, artifact_id, self.catalog[artifact_id],
                           self.receipts[artifact_id], self.resolutions)


def checking_cards(manifest, catalog, resolutions, *, target_ids=None):
    """Validate every check, but postpone display allocation until pagination."""
    receipts = {key: _receipt(artifact, catalog) for key, artifact in sorted(catalog.items())
                if artifact['artifactKind'] == 'proofir.check-run'}
    return _cards_from_receipts(manifest, catalog, resolutions, receipts, target_ids)


def _checking_cards_owned(manifest, catalog, resolutions, population, *, target_ids=None):
    receipts = {key: _owned_receipt(population, key, artifact, catalog)
                for key, artifact in sorted(catalog.items())
                if artifact['artifactKind'] == 'proofir.check-run'}
    return _cards_from_receipts(manifest, catalog, resolutions, receipts, target_ids)


def _cards_from_receipts(manifest, catalog, resolutions, receipts, target_ids):
    targets = manifest['targets']
    if target_ids is not None:
        targets = [t for t in targets if t['id'] in target_ids]
    index = (*_target_index({'targets': targets}), manifest['revision'])
    selected = [key for key in receipts if target_ids is None or _has_targets(catalog[key], index)]
    return CheckCards(index, catalog, resolutions, receipts, selected)


def project_checking_cards(manifest, complete, target_ids):
    """Project a validated complete check population onto selected targets."""
    if target_ids is None:
        return complete
    targets = [t for t in manifest['targets'] if t['id'] in target_ids]
    index = (*_target_index({'targets': targets}), manifest['revision'])
    selected = [key for key in complete.receipts
                if _has_targets(complete.catalog[key], index)]
    return CheckCards(index, complete.catalog, complete.resolutions,
                      complete.receipts, selected)


def _receipt(artifact, catalog):
    try:
        return stored_check_receipt(artifact, projection_kind='dossier',
                                    environment_artifacts=_input_environments(artifact, catalog))
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise ResultManifestError('invalid stored check receipt or canonical owner') from error


def _owned_receipt(population, key, artifact, catalog):
    try:
        environments = [population.member(row['artifactId'])
                        for row in _input_environments(artifact, catalog)]
        return _stored_check_receipt_owned(population, population.member(key),
                                          environments, projection_kind='dossier')
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        raise ResultManifestError('invalid stored check receipt or canonical owner') from error


def _has_targets(artifact, index):
    names, references, _ = index
    return any(names.get(name) for name in _check_names(artifact)) or any(
        references.get((ref.get('artifactRef', artifact['artifactId']), ref['localId']))
        for ref in _check_references(artifact))


def _check_card(index, artifact_id, artifact, receipt, resolutions):
    payload = artifact.get("payload")
    if not isinstance(payload, Mapping):
        raise ResultManifestError("canonical check artifact has no payload")
    targets = _check_targets(artifact, index)
    bindings = [
        _binding(target, artifact, resolutions[target["id"]])
        for target in targets
    ]
    row = {
        "artifactId": artifact_id,
        "operation": payload.get("operation"),
        "results": deepcopy(payload.get("results")),
        "guarantee": deepcopy(payload.get("guarantee")),
        "evidenceReceipt": receipt,
        "targetBindings": bindings,
        "sourceFreshness": "not-assessed",
        "environmentRef": artifact.get("environmentRef"),
        "producer": deepcopy(artifact.get("producer")),
        "limitations": deepcopy(artifact.get("limitations", [])),
        "references": {
            "": {"input": "canonical", "revision": artifact_id, "pointer": ""},
            "/results": {"input": "canonical", "revision": artifact_id, "pointer": "/payload/results"},
            "/guarantee": {"input": "canonical", "revision": artifact_id, "pointer": "/payload/guarantee"},
            "/targetBindings": {"input": "manifest", "revision": index[2], "pointer": "/targets", "appendPath": False},
            "/evidenceReceipt": {
                "input": "canonical", "revision": artifact_id,
                "pointer": "/extensions/ladon.process-observation~1v1/evidenceReceipt",
            },
        },
    }
    application = _input_owned_application(artifact)
    if application is not None:
        subject, index = application
        row["candidateApplication"] = deepcopy(subject.get("searchShape"))
        row["references"]["/candidateApplication"] = {
            "input": "canonical", "revision": artifact_id,
            "pointer": f"/subjectRefs/{index}/searchShape",
        }
    return row


def _check_names(artifact):
    names = set()
    for subject in artifact.get("subjectRefs", []):
        if subject.get("kind") == "declaration" and isinstance(subject.get("display"), str):
            names.add(subject["display"])
        if subject.get("kind") == "candidate-application":
            shape = subject.get("searchShape")
            candidate = shape.get("candidate") if isinstance(shape, Mapping) else None
            if isinstance(candidate, str):
                names.add(candidate)
    return names


def _target_index(manifest):
    names, references = defaultdict(list), defaultdict(list)
    for target in manifest['targets']:
        names[target['name']].append(target)
        ref = target.get('subjectRef', {})
        references[(ref.get('artifactId'), ref.get('subjectId'))].append(target)
    return names, references


def _check_targets(artifact, index):
    names, references, _ = index
    selected = {t['id']: t for name in _check_names(artifact) for t in names[name]}
    refs = _check_references(artifact)
    for ref in refs:
        key = (ref.get('artifactRef', artifact['artifactId']), ref['localId'])
        selected.update((t['id'], t) for t in references[key])
    return [selected[key] for key in sorted(selected)]


def _input_owned_application(artifact):
    payload = artifact.get("payload", {})
    inputs = payload.get("inputs", {})
    owned = inputs.get("subjectRefs", []) if isinstance(inputs, Mapping) else []
    owned_pairs = {(row.get("kind"), row.get("localId")) for row in owned if isinstance(row, Mapping)}
    for index, subject in enumerate(artifact.get("subjectRefs", [])):
        if (subject.get("kind"), subject.get("localId")) in owned_pairs and subject.get("kind") == "candidate-application":
            return subject, index
    return None


def _binding(target, check, resolution):
    reference = target.get('subjectRef', {})
    owner = reference.get('artifactId')
    sid = reference.get('subjectId')
    same_check_owner = owner == check['artifactId']
    references = list(check['payload']['inputs']['subjectRefs'])
    references.extend(row['subjectRef'] for row in check['payload']['results'])
    exact_owner = any(ref['kind'] == 'declaration' and ref['localId'] == sid
                      and ref.get('artifactRef', check['artifactId']) == owner for ref in references)
    environment_matches = check['environmentRef'] == target['environment']['digest']
    if exact_owner and environment_matches and resolution['status'] == 'resolved':
        status, reason = 'resolved', 'exact-check-declaration-owner-and-resolved-manifest-target'
    elif same_check_owner or exact_owner:
        status, reason = 'historical-or-mismatched', resolution['reason']
    else:
        status, reason = 'unassociated', 'matching-name-does-not-establish-canonical-target-ownership'
    return {'targetId': target['id'], 'status': status, 'reason': reason}


def _input_environments(artifact, catalog):
    environment_refs = artifact["payload"].get("inputs", {}).get("artifactRefs", [])
    return [
        candidate for ref in environment_refs
        if (candidate := catalog.get(ref)) is not None
        and candidate.get("artifactKind") == "proofir.environment"
        and candidate.get("artifactId") == ref
        and candidate.get("environmentRef") == artifact.get("environmentRef")
    ]


def _check_references(artifact):
    refs = list(artifact['payload']['inputs']['subjectRefs']) + artifact['subjectRefs']
    refs.extend(row['subjectRef'] for row in artifact['payload']['results'])
    return refs
