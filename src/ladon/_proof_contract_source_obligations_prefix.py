"""Strict frontend check of the shared prefix before incomplete-goal capture."""

from ladon.proof_contract_formal import produce_formal_snapshot


def check_generated_prefix(root, subject, context, limits, runner):
    snapshot = produce_formal_snapshot(
        root, subject["path"], "Probe", subject["declaration"], runner=runner,
        timeout_seconds=limits["timeout_seconds"], max_output_bytes=limits["max_output_bytes"],
        max_rss_bytes=limits["max_rss_bytes"],
    )
    observed = snapshot.get("observation") or {}
    if observed.get("status") != "observed":
        raise ValueError("strict generated-prefix frontend check failed")
    true = {"const": "True", "levels": []}
    if observed.get("typeExpr") != true or observed.get("normalizedTypeExpr") != true:
        raise ValueError("generated-prefix check anchor has an unexpected context or type")
    if snapshot["source"]["sha256"] != subject["digest"].removeprefix("sha256:"):
        raise ValueError("generated-prefix source changed")
    if snapshot["environment"] != context:
        raise ValueError("generated-prefix execution context differs from the source context")
    return {"scope": "generated-prefix-elaboration-and-exclusion",
            "subject": dict(subject), "snapshot": snapshot}
