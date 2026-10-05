#!/usr/bin/env python3
"""Standalone paired benchmark for legacy and candidate ProofIR source trees.

Population is one JSON array of captured envelopes forming a closed batch. No synthetic data is generated. Run only after root freezes
that population and records its SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path
from types import ModuleType
from typing import Any

BASELINE_SHA = {
    "proofir_v3.py": "328678d510ed3bd0ca61babffd8494bd692a6b804a1b69eb21157ff2cf3e7ccd",
    "proofir_v3_batch.py": "97c58c29d6c7a59ae242ad366cf199d9e22310c4d75a8145187e5823926c5430",
    "proofir_v3_payloads.py": "cbf6b2ccf065c15fade8a70b70f04989f2e1559aad2c71d165a1f7f112ce5c6d",
}
MODULES = ("proofir_v3_batch", "proofir_v3", "proofir_v3_payloads")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_owner(root: Path) -> ModuleType:
    """Load one coherent owner set under canonical package names."""
    for short in MODULES:
        path = root / (short + ".py")
        name = "ladon." + short
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load module {path}")
        module = importlib.util.module_from_spec(spec)
        # Dataclasses inspect sys.modules during class creation.
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules["ladon.proofir_v3"]


def install_owner(root: Path) -> tuple[ModuleType, dict[str, ModuleType | None]]:
    saved = {"ladon.proofir_v3": sys.modules.get("ladon.proofir_v3"),
             "ladon.proofir_v3_batch": sys.modules.get("ladon.proofir_v3_batch"),
             "ladon.proofir_v3_payloads": sys.modules.get("ladon.proofir_v3_payloads")}
    # The temporary loader imports dependencies by canonical package name. Clear the
    # prior modules so no private helper can silently come from the other owner.
    for name in saved:
        sys.modules.pop(name, None)
    try:
        module = load_owner(root)
        for short in MODULES:
            loaded = sys.modules["ladon." + short]
            expected_path = (root / (short + ".py")).resolve()
            if Path(loaded.__file__).resolve() != expected_path:
                raise RuntimeError(f"mixed ProofIR helper owner: {short} loaded from {loaded.__file__}")
        return module, saved
    except BaseException:
        restore(saved)
        raise


def restore(saved: dict[str, ModuleType | None]) -> None:
    for name, value in saved.items():
        if value is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = value


def outcome(module: ModuleType, batches: list[list[dict[str, Any]]]) -> tuple[str, float]:
    rows = []
    elapsed_ns = 0
    for batch in batches:
        start = time.perf_counter_ns()
        try:
            result = module.validate_envelope_batch(batch)
            elapsed_ns += time.perf_counter_ns() - start
            rows.append({"ok": [[item.content_id, item.to_dict()] for item in result]})
        except module.ProofIRV3Error as exc:
            elapsed_ns += time.perf_counter_ns() - start
            diagnostic = exc.diagnostic
            rows.append({"error": [str(exc), diagnostic.stage, diagnostic.code,
                                    diagnostic.pointer, diagnostic.artifact_id]})
    payload = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), elapsed_ns / 1_000_000_000


def measure(root: Path, batches: list[list[dict[str, Any]]]) -> tuple[float, str]:
    module, saved = install_owner(root)
    try:
        digest, elapsed = outcome(module, batches)
        return elapsed, digest
    finally:
        restore(saved)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--population-sha256", required=True)
    parser.add_argument("--candidate-sha256", action="append", required=True,
                        help="expected file SHA as NAME=HEX, repeat for all three modules")
    args = parser.parse_args()
    if sha(args.population) != args.population_sha256:
        raise SystemExit("frozen population SHA-256 mismatch")
    baseline_hashes = {name: sha(args.baseline / name) for name in BASELINE_SHA}
    if baseline_hashes != BASELINE_SHA:
        raise SystemExit(f"baseline source identity mismatch: {baseline_hashes}")
    expected_candidate = dict(item.split("=", 1) for item in args.candidate_sha256)
    candidate_hashes = {name: sha(args.candidate / name) for name in BASELINE_SHA}
    if set(expected_candidate) != set(BASELINE_SHA) or candidate_hashes != expected_candidate:
        raise SystemExit(f"candidate source identity mismatch: {candidate_hashes}")
    batch = json.loads(args.population.read_text(encoding="utf-8"))
    if not isinstance(batch, list) or not batch:
        raise SystemExit("population must be a nonempty closed JSON artifact array")
    batches = [batch]
    # Warm both source owners once before measuring. Compare full normalized result digests.
    base_digest = measure(args.baseline, batches)[1]
    cand_digest = measure(args.candidate, batches)[1]
    if base_digest != cand_digest:
        raise SystemExit(f"outcome mismatch: baseline={base_digest} candidate={cand_digest}")
    base_times: list[float] = []
    cand_times: list[float] = []
    for pair in range(5):
        order = (("baseline", args.baseline), ("candidate", args.candidate))
        if pair % 2:
            order = tuple(reversed(order))
        measured = {}
        for label, root in order:
            elapsed, digest = measure(root, batches)
            if digest != base_digest:
                raise SystemExit(f"outcome drift in pair {pair + 1}, {label}")
            measured[label] = elapsed
        base_times.append(measured["baseline"])
        cand_times.append(measured["candidate"])
    bmed = statistics.median(base_times)
    cmed = statistics.median(cand_times)
    improvement = (bmed - cmed) / bmed
    if {name: sha(args.baseline / name) for name in BASELINE_SHA} != baseline_hashes:
        raise SystemExit("baseline sources changed during benchmark")
    if {name: sha(args.candidate / name) for name in BASELINE_SHA} != candidate_hashes:
        raise SystemExit("candidate sources changed during benchmark")
    print(json.dumps({"python": sys.version.split()[0],
                      "population_sha256": args.population_sha256,
                      "baseline_sha256": baseline_hashes,
                      "candidate_sha256": candidate_hashes,
                      "outcome_sha256": base_digest,
                      "baseline_seconds": base_times,
                      "candidate_seconds": cand_times,
                      "baseline_median_seconds": bmed,
                      "candidate_median_seconds": cmed,
                      "relative_improvement": improvement,
                      "meets_20_percent": improvement >= 0.20}, sort_keys=True, indent=2))
    return 0 if improvement >= 0.20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
