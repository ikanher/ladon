"""Read-only reports preserve supplementary branches and their original clock."""

import copy
import json
from pathlib import Path

from ladon._investigation_contract_observations import contract_dimensions
from ladon.investigation import MAX_RECORDS, _object, assess
from ladon.investigation_observations import review_relation, validated_observations
from ladon.proof_slice import digest

MAX_REPORT_BYTES = 128 * 1024**2


def _compatible_plans(plans):
    if not isinstance(plans, list) or not 1 <= len(plans) <= 16:
        raise ValueError("report requires 1..16 plans")
    size, unique = 0, {}
    for plan in plans:
        _object(plan, "report plan")
        size += len(json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode())
        if size > MAX_REPORT_BYTES:
            raise ValueError("combined report inputs exceed 128 MiB")
        unique[digest(plan)] = plan
        for key in ("scope", "startedAt", "budgetSeconds"):
            if plan.get(key) != plans[0].get(key):
                raise ValueError("incompatible report scope, clock or budget")
    return unique


def _bounded_insert(rows, identity, value):
    if identity not in rows:
        if len(rows) >= MAX_RECORDS:
            raise ValueError("report record population exceeds 4096")
        rows[identity] = value
    return rows[identity]


def _collect_observations(plans, root):
    grouped, firsts, names = {}, {}, {}
    for plan_id, plan in plans.items():
        for entry in validated_observations(plan, root):
            identity = entry["observationId"]
            _check_observation_identity(entry, names, firsts)
            row = _bounded_insert(grouped, identity, {"observationId": identity,
                                  "record": copy.deepcopy(entry["record"]), "branches": []})
            if row["record"] != entry["record"]:
                raise ValueError("conflicting immutable observation identity")
            row["branches"].append({"planId": plan_id,
                                    "responses": copy.deepcopy(entry["responses"]),
                                    "reconciliations": copy.deepcopy(entry["reconciliations"])})
    return list(grouped.values())


def _check_native_firsts(plans):
    firsts = {}
    for plan in plans.values():
        for response in plan.get("responses", []):
            owner = (response["subject"], response["reviewer"], response["challengeDigest"])
            if owner in firsts and firsts[owner] != response:
                raise ValueError("conflicting immutable first response")
            firsts[owner] = response


def _check_observation_identity(entry, names, firsts):
    name = entry["record"]["id"]
    identity = entry["observationId"]
    if name in names and names[name] != identity:
        raise ValueError("conflicting immutable observation name")
    names[name] = identity
    for response in entry["responses"]:
        owner = (identity, response["reviewer"], response["challengeDigest"])
        if owner in firsts and firsts[owner] != response:
            raise ValueError("conflicting immutable first response")
        firsts[owner] = response


def _relation(rows, key):
    values = {row.get(key, "unresolved") for row in rows}
    return next(iter(values)) if len(values) == 1 else "conflicted"


def _project_group(rows):
    first = copy.deepcopy(rows[0]["finding"])
    first["planIds"] = [row["planId"] for row in rows]
    first["branchFindings"] = copy.deepcopy(rows)
    first["pendingPlanIds"] = [row["planId"] for row in rows if row["pending"]]
    for key in ("statementRelation", "methodRelation", "sourceFidelity", "formalSupport"):
        if key in first:
            first[key] = _relation([row["finding"] for row in rows], key)
    effective = _effective_union(rows)
    if _should_project_effective(first, effective):
        first["effectiveResponses"] = list(effective.values())
        _set_effective_relations(first, effective)
    _refresh_contract_dimensions(first, effective)
    return first


def _should_project_effective(finding, effective):
    contract = finding.get("projectionSchema") == "ladon-investigation-contract-finding-v1"
    return bool(effective) and (not finding["pendingPlanIds"] or contract)


def _refresh_contract_dimensions(finding, effective):
    if finding.get("projectionSchema") == "ladon-investigation-contract-finding-v1":
        finding["contractDimensions"] = contract_dimensions(
            finding["contractAnalysis"], list(effective.values()))


def _effective_union(rows):
    effective = {}
    for row in rows:
        for response in row["finding"].get("effectiveResponses", []):
            effective[digest(response)] = response
    return effective


def _set_effective_relations(finding, effective):
    for output, response_key in (("statementRelation", "classification"),
                                 ("methodRelation", "method"), ("sourceFidelity", "sourceFidelity")):
        finding[output] = review_relation(effective.values(), response_key)


def _branch_findings(branch, plan):
    from ladon.investigation_correspondence import effective_responses
    from ladon.investigation_findings import native_findings

    rows = {row.get("findingId", digest(row)): row for row in branch["findings"]}
    if plan["version"] == 3:
        entries = plan["correspondenceBundles"]
        for row in native_findings(plan, entries, effective_responses(plan, entries), include_aligned=True):
            rows[row["findingId"]] = row
    return list(rows.values())


def _collect_findings(branches, plans):
    grouped = {}
    for branch in branches:
        for finding in _branch_findings(branch, plans[branch["planId"]]):
            identity = finding.get("findingId", digest(finding))
            rows = _bounded_insert(grouped, identity, [])
            rows.append({"planId": branch["planId"], "finding": finding,
                         "pending": _finding_pending(finding, branch["next"])})
    return [_project_group(rows) for rows in grouped.values()]


def _finding_pending(finding, queue):
    subject = finding.get("subject", finding.get("findingId"))
    return any(work.get("subject") == subject or
               ("claim" in finding and work.get("claim") == finding["claim"])
               for work in queue)


def aggregate_report(plans, root, now=None, refinements=None):
    """Validate every branch; this view is neither a merged plan nor a terminal receipt."""
    from ladon._investigation_refinement_reporting import (
        associate_refinements,
        inspect_refinements,
    )

    refinement_evidence = inspect_refinements(refinements, root)
    unique = _compatible_plans(plans)
    branches = [{"planId": identity, **assess(plan, Path(root), now=now)}
                for identity, plan in unique.items()]
    primary = next(iter(unique.values()))
    _check_native_firsts(unique)
    has_contract = any(entry["record"].get("schema") == "ladon-investigation-observation-v2"
                       for plan in unique.values() for entry in plan.get("observations", []))
    result = {"schema": ("ladon-investigation-report-v3" if refinement_evidence else
                         "ladon-investigation-report-v2" if has_contract else
                         "ladon-investigation-report-v1"), "planIds": list(unique),
              "scope": copy.deepcopy(primary["scope"]), "startedAt": primary["startedAt"],
              "budgetSeconds": primary["budgetSeconds"], "branches": branches,
              "observations": _collect_observations(unique, root),
              "findings": _collect_findings(branches, unique),
              "mathematicalFalsity": "not-established", "wholePaperCertified": False,
              "authority": ("Source-bound attributed evidence; bounded native attachment shape and references validated, with no checker or Lean replay."
                            if has_contract else "Source-bound attributed evidence; no Lean replay or semantic detection."),
              "nonclaims": ["Branch completion does not certify the exposition or aggregate coverage.",
                            "Pending branch work is retained even when another branch resolved it."]}
    if refinement_evidence:
        associate_refinements(result["findings"], refinement_evidence)
        result["refinementEvidence"] = refinement_evidence
        result["authority"] += (
            " Refinement supplements are id-only-attributed historical evidence; "
            "saved Lean evidence was not replayed."
        )
        result["nonclaims"].append(
            "Refinement association identifies a report finding by ID only and does not "
            "establish source formula fidelity or resolve review work."
        )
    if has_contract:
        result["nonclaims"].append(
            "Native attachment validation does not establish source interpretation, theorem truth, or whole-paper coverage."
        )
    if len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode()) > MAX_REPORT_BYTES:
        raise ValueError("report output exceeds 128 MiB")
    return result
