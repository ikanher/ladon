"""Bound and attribute historical refinement supplements in reports."""

import json

from ladon.investigation import _object

MAX_REFINEMENTS = 4
MAX_REFINEMENT_BYTES = 32 * 1024**2


def inspect_refinements(refinements, root):
    if refinements is None:
        return []
    if not isinstance(refinements, list) or len(refinements) > MAX_REFINEMENTS:
        raise ValueError("report accepts at most four refinement supplements")
    size = 0
    seen = set()
    inspected = []
    for artifact in refinements:
        _object(artifact, "refinement supplement")
        encoded = json.dumps(artifact, ensure_ascii=False, separators=(",", ":"),
                             allow_nan=False).encode("utf-8")
        size += len(encoded)
        if size > MAX_REFINEMENT_BYTES:
            raise ValueError("combined refinement supplements exceed 32 MiB")
        if artifact.get("schema") != "ladon-proof-contract-refinement-workflow-v1":
            raise ValueError("unsupported refinement supplement schema")
        artifact_id = artifact.get("artifactId")
        if not isinstance(artifact_id, str) or artifact_id in seen:
            raise ValueError("duplicate or missing refinement artifact identity")
        seen.add(artifact_id)
        from ladon.proof_contract_refinement_workflow import inspect_refinement

        inspected.append(inspect_refinement(artifact, root))
    return inspected


def associate_refinements(findings, inspected):
    by_finding = {}
    ids = set()
    for evidence in inspected:
        artifact = evidence["artifact"]
        artifact_id = artifact["artifactId"]
        if artifact_id in ids:
            raise ValueError("duplicate refinement artifact identity")
        ids.add(artifact_id)
        finding_id = artifact["request"]["originalFinding"]["id"]
        matches = [row for row in findings if row.get("findingId") == finding_id]
        if len(matches) != 1:
            raise ValueError("refinement finding identity must bind exactly one report finding")
        by_finding.setdefault(finding_id, []).append(artifact_id)
    for finding in findings:
        identities = by_finding.get(finding.get("findingId"))
        if identities:
            finding["refinementIds"] = identities

