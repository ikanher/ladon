#!/usr/bin/env python3
"""Compare frozen and candidate source path filtering on captured real inputs."""
from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from types import ModuleType


def load_module(name: str, source: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_paths(path: Path, summary_path: Path, baseline_source: Path) -> tuple[str, ...]:
    raw = path.read_bytes()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if "sha256:" + hashlib.sha256(raw).hexdigest() != (
        "sha256:67165804ec816113283a1960a328098f76d99557d4e717fb5a939758e974b4a6"
    ) or summary["pathsSha256"] != (
        "sha256:67165804ec816113283a1960a328098f76d99557d4e717fb5a939758e974b4a6"
    ):
        raise ValueError("captured path corpus does not match independently frozen digest")
    if hashlib.sha256(baseline_source.read_bytes()).hexdigest() != (
        "3dcddd3ba3a571f601d83031b94b1fe00c090428248f2ac9e9314f2dfeb4aa75"
    ):
        raise ValueError("baseline source bytes do not match frozen contract")
    paths = json.loads(raw)
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise ValueError("captured paths must be a JSON string array")
    if len(paths) != 108553 or len(paths) != summary["rawPaths"]:
        raise ValueError("captured path count does not match independently frozen count")
    return tuple(paths)


def elapsed_ns(function: object, paths: tuple[str, ...], rounds: int) -> float:
    start = time.perf_counter_ns()
    for _ in range(rounds):
        function(paths)  # type: ignore[operator]
    return (time.perf_counter_ns() - start) / rounds


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", type=Path, required=True, help="root-captured paths.json")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=7)
    parser.add_argument("--inner", type=int, default=1)
    parser.add_argument("--minimum-improvement", type=float, default=0.20)
    args = parser.parse_args()
    if args.rounds < 3 or args.inner < 1 or not 0 <= args.minimum_improvement < 1:
        parser.error("rounds must be >=3, inner >=1, and improvement between 0 and 1")

    paths = load_paths(args.paths, args.summary, args.baseline)
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    baseline = load_module("_r51_baseline_lean_toolchain", args.baseline)
    candidate = load_module("_r51_candidate_lean_toolchain", args.candidate)
    expected = baseline._filter_source_material(paths)
    actual = candidate._filter_source_material(paths)
    selected_digest = "sha256:" + hashlib.sha256(
        json.dumps(expected, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if (
        len(expected) != 10981 or len(expected) != summary["selectedPaths"]
        or selected_digest != "sha256:536ac7603d90a1c9bfa24bfc3fad721c5b21f1cb32ac4969749f49db7d39db9f"
        or selected_digest != summary["selectedPathsDigest"]
    ):
        raise SystemExit("baseline selected paths do not match independent frozen digest")
    if actual != expected:
        raise SystemExit("semantic mismatch between baseline and candidate filtered paths")

    measurements: dict[str, list[float]] = {"baseline": [], "candidate": []}
    pair_order = ("baseline", "candidate")
    functions = {
        "baseline": baseline._filter_source_material,
        "candidate": candidate._filter_source_material,
    }
    for index in range(args.rounds):
        for label in pair_order if index % 2 == 0 else reversed(pair_order):
            measurements[label].append(elapsed_ns(functions[label], paths, args.inner))
    baseline_median = statistics.median(measurements["baseline"])
    candidate_median = statistics.median(measurements["candidate"])
    improvement = 1.0 - candidate_median / baseline_median
    print(json.dumps({
        "path_count": len(paths), "selected_count": len(expected),
        "rounds": args.rounds, "inner": args.inner,
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "sample_order": ["baseline,candidate" if i % 2 == 0 else "candidate,baseline" for i in range(args.rounds)],
        "baseline_samples_ns": [round(value) for value in measurements["baseline"]],
        "candidate_samples_ns": [round(value) for value in measurements["candidate"]],
        "baseline_median_ns": round(baseline_median),
        "candidate_median_ns": round(candidate_median),
        "improvement": improvement, "required_improvement": args.minimum_improvement,
        "gate_passed": improvement >= args.minimum_improvement,
    }, sort_keys=True))
    return 0 if improvement >= args.minimum_improvement else 1


if __name__ == "__main__":
    raise SystemExit(main())
