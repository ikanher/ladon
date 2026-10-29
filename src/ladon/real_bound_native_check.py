"""Fresh supervised predicate/scalar checks; saved results convey no live authority."""

import hashlib
import math
import tempfile
import time
from pathlib import Path

from ladon.real_bound_admission import _digest
from ladon.real_bound_admission_check import _validate_terms
from ladon.real_bound_binding_check import binding_identity, verify_binding_source
from ladon.real_bound_native_plan import validate_real_plan
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES


def native_checker_identity():
    directory = Path(__file__).parent
    paths = sorted(directory.glob("real_bound_native*.py"))
    paths += [directory / "lean/LadonRealBoundScalars.lean",
              directory / "lean/LadonRealBoundPrefix.lean",
              directory / "lean/LadonRealBoundCoefficient.lean",
              directory / "lean/LadonRealBoundComposition.lean",
              directory / "lean/LadonRealBoundTransfer.lean",
              directory / "proof_contract_payloads.py", directory / "proofir_v3.py"]
    return _digest({"bindingChecker": binding_identity(), "native": {
        str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}})


def check_real_bound(root, plan, terms, *, timeout_seconds=600):
    from ladon.proof_contract_obligation_supervision import _execute_job

    started = time.monotonic()
    validate_real_plan(plan)
    _validate_terms(plan, terms)
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0):
        raise ValueError("timeout budget must be positive and finite")
    root, _source, _context = verify_binding_source(root, plan["bindingPlan"])
    identity = native_checker_identity()
    bounds = {"timeout_seconds": timeout_seconds, "deadlineMonotonic": started + timeout_seconds,
              "max_output_bytes": 8 * 1024**2, "max_rss_bytes": DEFAULT_MAX_RSS_BYTES}
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    with tempfile.TemporaryDirectory(prefix="ladon-real-native-") as directory:
        job = {"version": 1, "root": str(root), "workspace": directory, "plan": plan, "terms": terms,
               "deadlineMonotonic": bounds["deadlineMonotonic"], "checkerIdentity": identity}
        result = _execute_job(job, bounds, state, None, worker_module="ladon.real_bound_native_worker")
    verify_binding_source(root, plan["bindingPlan"])
    if identity != native_checker_identity():
        raise ValueError("Real admission checker changed during execution")
    return result


def check_real_bound_relation(root, left_plan, right_plan, *, timeout_seconds=600):
    """Check the exact live-derived Iff between two Real predicate declarations."""
    from ladon.proof_contract_obligation_supervision import _execute_job

    started = time.monotonic()
    validate_real_plan(left_plan)
    validate_real_plan(right_plan)
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0 or timeout_seconds > 600):
        raise ValueError("timeout budget must be positive, finite, and at most 600 seconds")
    root = Path(root).resolve(strict=True)
    identity = native_checker_identity()
    bounds = {"timeout_seconds": timeout_seconds, "deadlineMonotonic": started + timeout_seconds,
              "max_output_bytes": 8 * 1024**2, "max_rss_bytes": DEFAULT_MAX_RSS_BYTES}
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    with tempfile.TemporaryDirectory(prefix="ladon-real-relation-") as directory:
        job = {"version": 1, "root": str(root), "workspace": directory,
               "leftPlan": left_plan, "rightPlan": right_plan,
               "deadlineMonotonic": bounds["deadlineMonotonic"],
               "checkerIdentity": identity}
        result = _execute_job(job, bounds, state, None,
                              worker_module="ladon.real_bound_native_relation_worker")
    if identity != native_checker_identity():
        raise ValueError("Real relation checker changed during execution")
    return result
