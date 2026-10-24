"""Whole-contract antichains partitioned by replay compatibility."""

from ladon._contract_propagation_common import _canonical
from ladon.proof_contracts import compare_contracts


def _compatible(left, right):
    """Dominance cannot discard a route needed by a different downstream scope."""
    keys = ("interfaceId", "localContextRef", "substitutionRefs")
    return all(left["routeWitness"].get(key) == right["routeWitness"].get(key) for key in keys)


def _prune(dominator, removed, prunings):
    evidence = compare_contracts(dominator["contractRecord"], removed["contractRecord"])
    prunings.extend(
        {
            "removedWitness": {"witnessRef": witness},
            "dominatorRef": dominator["routeWitnessRef"],
            "dominanceEvidence": evidence,
        }
        for witness in removed["routeWitnessRefs"]
    )


def _insert(kept, row, prunings):
    for old in list(kept):
        if not _compatible(old, row):
            continue
        if old["contractRecord"] == row["contractRecord"]:
            old["routeWitnessRefs"] = sorted(
                set(old["routeWitnessRefs"]) | set(row["routeWitnessRefs"])
            )
            return
        relation = compare_contracts(old["contractRecord"], row["contractRecord"])["relation"]
        if relation == "dominates":
            _prune(old, row, prunings)
            return
        if relation == "dominated":
            _prune(row, old, prunings)
            kept.remove(old)
    kept.append(row)


def _merge_frontier(rows, *, limit, prunings, statement, pending):
    kept = []
    for row in rows:
        candidate = {**row, "routeWitnessRefs": list(row["routeWitnessRefs"])}
        _insert(kept, candidate, prunings)
    kept.sort(key=lambda row: _canonical(row["contractRecord"]))
    for row in kept[limit:]:
        pending.append(
            {
                "code": "frontier-cap",
                "statementRef": statement,
                "routeWitnessRef": row["routeWitnessRef"],
            }
        )
    return kept[:limit]
