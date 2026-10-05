"""Read one exact rendered declaration type from a validated stored check.

The existing registry owner validates artifacts and weakens stored receipts.
This adapter compares type text structurally; it never starts Lean, refreshes
an index or inherits applicability for the caller's new goal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping
from typing import Any

from ladon.proof_difference import DifferenceRequest, analyze_difference
from ladon.proof_search_index import ProofSearchIndexError
from ladon.proof_search_semantic_cli import dispatch_semantic_evidence


def explain_stored_candidate(args, repo_root) -> dict[str, Any]:
    """Resolve an explicit typed check and return bounded structural explanation."""
    if not args.check_local_id or args.module or args.freshness != 'stored':
        raise ProofSearchIndexError('stored-check explanation requires --check-local-id, stored freshness and no owner-module filter')
    selection = argparse.Namespace(kind='semantic-check', name=args.check_artifact,
                                   local_id=args.check_local_id, evidence_store=args.evidence_store,
                                   max_evidence_store_mib=args.max_evidence_store_mib)
    expansion = dispatch_semantic_evidence(selection, repo_root)
    if expansion['evidenceReceipt'] is None:
        raise ProofSearchIndexError('stored-check explanation requires an attributable check receipt')
    try:
        evidence = candidate_type_evidence(expansion['artifact'], args.candidate)
    except (ValueError, TypeError, KeyError) as error:
        raise ProofSearchIndexError(str(error)) from error
    evidence.update(source='stored-check-rendered-type', reference=expansion['reference'],
                    evidenceReceipt=expansion['evidenceReceipt'], freshness='stored')
    request = DifferenceRequest(args.goal, args.candidate, assumptions=tuple(args.assumption),
                                suggestion_cap=args.suggestion_cap, raw_signature=args.raw_signature)
    result = analyze_difference(request, candidate_signature=evidence['typeText'], candidate_evidence=evidence)
    result['nonclaims'].append('This stored type comparison neither verifies current source freshness nor establishes applicability to the new goal.')
    return result


def candidate_type_evidence(artifact: Mapping[str, Any], candidate: str) -> dict[str, Any]:
    """Reject absent, ambiguous, truncated or fingerprint-mismatched type rows."""
    rows = [row for row in artifact['subjectRefs']
            if row.get('kind') == 'declaration' and row.get('display') == candidate]
    if len(rows) != 1:
        raise ValueError('stored candidate declaration is absent or ambiguous')
    row = rows[0]
    shape = row.get('searchShape', {})
    text = _rendered_type(shape)
    identity = _type_identity(candidate, shape['typeStructural'])
    if row['fingerprint']['digest'] != identity or row['localId'] != 'declaration:' + identity:
        raise ValueError('stored candidate type does not match its structural identity')
    return {'candidateName': candidate, 'name': candidate, 'typeText': text,
            'typeTextBytes': len(text.encode()), 'typeTextTruncated': False,
            'typeStatus': 'lean-rendered', 'declarationId': row['localId'],
            'typeIdentity': identity, 'module': None}


def _rendered_type(shape) -> str:
    text = shape.get('renderedType')
    if not isinstance(text, str) or not text.strip() or len(text.encode()) > 64 * 1024:
        raise ValueError('stored candidate type is missing, blank or exceeds the supported cap')
    if shape.get('typeStatus') != 'lean-rendered' or shape.get('typeTextTruncated') is not False:
        raise ValueError('stored candidate type is unavailable or truncated')
    return text


def _type_identity(candidate: str, structural: str) -> str:
    data = json.dumps({'qualifiedName': candidate, 'type': structural}, sort_keys=True, separators=(',', ':')).encode()
    return 'sha256:' + hashlib.sha256(data).hexdigest()


__all__ = ['candidate_type_evidence', 'explain_stored_candidate']
