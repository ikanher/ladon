"""Fresh, bounded checking of the exact observed predicate's prefix laws."""

import hashlib
import math
import tempfile
import time
from pathlib import Path

from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission import _digest
from ladon.real_bound_admission_check import checker_identity
from ladon.real_bound_binding import plan_bound_prefix
from ladon.real_bound_observation import verify_bound_observation
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.source_association_io import _read_regular


def binding_identity():
    directory = Path(__file__).parent
    names = ("real_bound_binding.py", "real_bound_binding_check.py", "real_bound_binding_worker.py",
             "lean/LadonRealBoundBinding.lean", "derivative_prefix.py", "lean/LadonRealBoundDerivative.lean")
    return _digest({"lawChecker": checker_identity(), "binding": {
        name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names}})


def validate_binding_plan(plan):
    from ladon.derivative_prefix import plan_derivative_prefix

    if not isinstance(plan, dict):
        raise TypeError("invalid bound-prefix plan")
    if plan.get("schema") == "ladon-derivative-prefix-plan-v1":
        expected = plan_derivative_prefix(plan["observation"])
    else:
        expected = plan_bound_prefix(plan["observation"], plan["measure"])
    if plan != expected:
        raise ValueError("stale or altered bound-prefix plan")


def verify_binding_source(root, plan):
    validate_binding_plan(plan)
    root = Path(root).resolve(strict=True)
    observation = verify_bound_observation(plan["observation"], root)
    snapshot = observation["statementSnapshot"]
    path = (root / snapshot["source"]["path"]).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("bound source escapes the selected repository")
    source = _read_regular(path, 8 * 1024**2)
    if hashlib.sha256(source).hexdigest() != snapshot["source"]["sha256"]:
        raise ValueError("stale bound source")
    return root, source, pinned_toolchain(root)


def check_bound_prefix(root, plan, term, *, timeout_seconds=900):
    """Check one live-derived Admission; no saved receipt authorizes a contract."""
    from ladon.proof_contract_obligation_supervision import _execute_job

    started = time.monotonic()
    validate_binding_plan(plan)
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0):
        raise ValueError("timeout budget must be positive and finite")
    if type(term) is not str or not term.strip() or len(term.encode()) > 256 * 1024:
        raise ValueError("bound proof term must be a bounded nonempty string")
    root, _source, _context = verify_binding_source(root, plan)
    bounds = {"timeout_seconds": timeout_seconds, "deadlineMonotonic": started + timeout_seconds,
              "max_output_bytes": 8 * 1024**2, "max_rss_bytes": DEFAULT_MAX_RSS_BYTES}
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    identity = binding_identity()
    with tempfile.TemporaryDirectory(prefix="ladon-bound-prefix-") as directory:
        job = {"version": 1, "root": str(root), "workspace": directory, "plan": plan, "term": term,
               "deadlineMonotonic": bounds["deadlineMonotonic"], "checkerIdentity": identity}
        result = _execute_job(job, bounds, state, None, worker_module="ladon.real_bound_binding_worker")
    verify_binding_source(root, plan)
    if identity != binding_identity():
        raise ValueError("bound-prefix checker changed during execution")
    return result
