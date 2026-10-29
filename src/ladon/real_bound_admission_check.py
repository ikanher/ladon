"""Fresh bounded law checks. No saved receipt or caller flag grants admission."""

import hashlib
import math
import tempfile
import time
from pathlib import Path

from ladon.proof_contract_payloads import closed
from ladon.proof_slice import pinned_toolchain
from ladon.real_bound_admission import plan_prefix_admission
from ladon.resource_limits import DEFAULT_MAX_RSS_BYTES
from ladon.source_association_io import _read_regular


def checker_identity():
    from ladon.correspondence_implementation import implementation_digest
    from ladon.proofir_v3 import canonical_bytes

    directory = Path(__file__).parent
    files = ("real_bound_admission.py", "real_bound_admission_check.py",
             "real_bound_admission_worker.py", "lean/LadonRealBound.lean",
             "proof_contract_obligation_supervision.py")
    identities = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in files}
    identities["completionPipeline"] = implementation_digest()
    return "sha256:" + hashlib.sha256(canonical_bytes(identities)).hexdigest()


def verify_plan_source(root, plan):
    """Regenerate the plan and bind it to current source and toolchain state."""
    if plan != plan_prefix_admission(plan["request"]):
        raise ValueError("stale or altered prefix admission plan")
    root = Path(root).resolve(strict=True)
    reference = plan["request"]["source"]
    path = (root / reference["path"]).resolve(strict=True)
    if not path.is_relative_to(root):
        raise ValueError("source path escapes the selected repository")
    source = _read_regular(path, 8 * 1024**2)
    if hashlib.sha256(source).hexdigest() != reference["sha256"]:
        raise ValueError("stale prefix admission source")
    context = pinned_toolchain(root)
    if context.context_identity != plan["request"]["environmentRef"]:
        raise ValueError("stale prefix admission environment")
    return root, source, context


def _validate_check(plan, terms, timeout):
    if type(timeout) not in (float, int) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout budget must be positive and finite")
    if not isinstance(plan, dict) or plan != plan_prefix_admission(plan["request"]):
        raise ValueError("stale or altered prefix admission plan")
    _validate_terms(plan, terms)


def _validate_terms(plan, terms):
    closed(terms, {row["id"] for row in plan["goals"]}, "proof terms")
    if any(type(term) is not str or not term.strip() or len(term.encode()) > 256 * 1024
           for term in terms.values()):
        raise ValueError("proof terms must be bounded nonempty strings")


def check_prefix_admission(root, plan, terms, *, timeout_seconds=900):
    """Check generated laws freshly; full observed-contract admission stays open."""
    from ladon.proof_contract_obligation_supervision import _execute_job

    started = time.monotonic()
    _validate_check(plan, terms, timeout_seconds)
    root, _source, _context = verify_plan_source(root, plan)
    bounds = {"timeout_seconds": timeout_seconds, "deadlineMonotonic": started + timeout_seconds,
              "max_output_bytes": 8 * 1024**2, "max_rss_bytes": DEFAULT_MAX_RSS_BYTES}
    state = {"receipt": None, "inputDigest": None, "bounds": None}
    implementation = checker_identity()
    # The parent owns cleanup even if the bounded child is killed mid-compilation.
    with tempfile.TemporaryDirectory(prefix="ladon-prefix-admission-") as directory:
        job = {"version": 1, "root": str(root), "workspace": directory, "plan": plan,
               "terms": terms, "deadlineMonotonic": bounds["deadlineMonotonic"],
               "checkerIdentity": implementation}
        result = _execute_job(job, bounds, state, None, worker_module="ladon.real_bound_admission_worker")
    verify_plan_source(root, plan)
    if implementation != checker_identity():
        raise ValueError("prefix-law checker changed during execution")
    return result
