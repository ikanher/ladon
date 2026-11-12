"""Run preserved-Lean import isolation probes for one registered family batch."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

RUNTIME = Path(sys.argv[1]).resolve(strict=True)
RUN = Path(sys.argv[2]).resolve(strict=True)
CORPUS = Path(sys.argv[3]).resolve(strict=True)
sys.path.insert(0, str(RUNTIME / "src"))
from ladon.lean_toolchain import resolve_toolchain_context
from ladon.process_supervisor import run_bounded_target_process


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module_for(source_path: str) -> str:
    parts = Path(source_path).with_suffix("").parts[1:]
    return ".".join(parts)


def classify_unavailable(module: str, result) -> str | None:
    diagnostics = result.stdout + result.stderr
    lines = [line.strip() for line in diagnostics.splitlines() if line.strip()]
    errors = [line.split("error:", 1)[1].strip() for line in lines if "error:" in line]
    if result.returncode != 1 or len(errors) != 1 or not lines or "error:" not in lines[0]:
        return None
    if re.fullmatch(
        r"object file '[^'\n]+' of module " + re.escape(module) + r" does not exist",
        errors[0],
    ):
        return "module-unavailable" if len(lines) == 1 else None
    match = re.fullmatch(r"unknown module prefix '([^']+)'", errors[0])
    if match:
        prefix = match.group(1)
        if len(lines) < 3 or not all(Path(line).is_absolute() for line in lines[2:]):
            return None
        expected_banner = f"No directory '{prefix}' or file '{prefix}.olean' in the search path entries:"
        if lines[1] != expected_banner:
            return None
        if prefix == module:
            return "module-unavailable"
        # Lean reports the earliest missing namespace prefix when the project
        # has no directory for that package. Bind that prefix to the requested
        # module; do not accept unrelated missing-module diagnostics.
        if module.startswith(prefix + "."):
            return "parent-namespace-unavailable"
    return None


def run_import(tc, env, repo: Path, probe: Path, module: str) -> dict:
    process = run_bounded_target_process(
        [str(tc.lean_path), str(probe)],
        cwd=repo,
        env=env,
        timeout_seconds=60,
        max_output_bytes=8 * 1024**2,
        max_rss_bytes=12 * 1024**3,
        observe_resources=True,
    )
    record = {
        "module": module,
        "command": list(process.command),
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
        "elapsedSeconds": process.elapsed_seconds,
        "timedOut": process.timed_out,
        "memoryLimited": process.memory_limited,
        "outputLimited": process.output_limited,
        "peakRssBytes": process.peak_rss_bytes,
        "resourceObservations": process.resource_observations,
    }
    return record


def probe(tc, env, repo: Path, root: Path, name: str, module: str) -> dict:
    path = root / f"{name}.lean"
    path.write_text(f"import {module}\n", encoding="utf-8")
    item = run_import(tc, env, repo, path, module)
    item["probePath"] = str(path)
    item["probeSha256"] = digest(path)
    item["classification"] = (
        "imported" if item["returncode"] == 0 else
        classify_unavailable(module, type("R", (), item)()) or
        "unrelated-or-unclassified-failure"
    )
    return item


def main() -> None:
    corpus = json.loads((CORPUS / "cases.json").read_text(encoding="utf-8"))["cases"]
    all_modules = sorted({module_for(case["leanSource"].split("#", 1)[0]) for case in corpus})
    all_modules.append("Validation")
    evidence = []
    for slot in sorted(RUN.glob("slot-*")):
        receipt_path = slot / "workspace-receipt.json"
        if not receipt_path.is_file():
            continue
        wr = json.loads(receipt_path.read_text(encoding="utf-8"))
        repo = slot / "case-workspace"
        actual_before = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
        allowed = sorted(wr["allowedFiles"])
        if actual_before != allowed:
            raise RuntimeError(f"workspace differs from allowlist before probes: {slot.name}")
        selected = module_for(next(c["leanSource"].split("#", 1)[0] for c in corpus if c["caseId"] == wr["caseId"]))
        tc = resolve_toolchain_context(
            repo,
            lean_path=RUNTIME / "lean-core/bin/lean",
            lake_path=RUNTIME / "lean-core/bin/lake",
            selection_mode="explicit",
        )
        env = dict(tc.environment)
        env["LD_LIBRARY_PATH"] = os.pathsep.join(
            [str(RUNTIME / "lean-core/lib"), str(RUNTIME / "hostlib")]
        )
        probes_dir = slot / "isolation-probes"
        probes_dir.mkdir(exist_ok=True)
        rows = [probe(tc, env, repo, probes_dir, "positive-selected", selected)]
        forbidden = [module for module in all_modules if module != selected]
        for index, module in enumerate(forbidden):
            rows.append(probe(tc, env, repo, probes_dir, f"excluded-{index:02d}", module))
        # Validation is explicitly excluded even when its module name aliases a fixture module.
        if "Validation" not in forbidden:
            rows.append(probe(tc, env, repo, probes_dir, "excluded-validation", "Validation"))

        # Expose one reviewed sibling artifact, prove it imports, then require the
        # registered workspace allowlist guard to reject the injected file.
        other = next(c for c in corpus if c["caseId"] != wr["caseId"] and c["family"] == "premise-provenance")
        other_module = module_for(other["leanSource"].split("#", 1)[0])
        artifact = CORPUS / "reviews/r3-preparation.json"
        prep = json.loads(artifact.read_text(encoding="utf-8"))
        source = other["leanSource"].split("#", 1)[0]
        row = next(x for x in prep["artifacts"] if x["source"] == source)
        rel_artifact = Path(*Path(row["artifact"]).parts[1:])
        source_artifact = CORPUS / row["artifact"]
        injected = repo / rel_artifact
        injected.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_artifact, injected)
        injection_result = probe(tc, env, repo, probes_dir, "injected-excluded", other_module)
        after_injection = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
        guard_rejected = after_injection != allowed and injected.relative_to(repo).as_posix() not in allowed
        injected.unlink()
        rows.append({"module": other_module, "classification": injection_result["classification"],
                     "returncode": injection_result["returncode"], "stdout": injection_result["stdout"],
                     "stderr": injection_result["stderr"], "injectedArtifact": str(injected),
                     "injectedArtifactSha256": digest(source_artifact), "guardRejectedUnexpectedFile": guard_rejected})

        # An unrelated syntax failure must never be credited as a missing import.
        unrelated_path = probes_dir / "unrelated-compiler-failure.lean"
        unrelated_path.write_text("theorem broken : True := by this_is_not_a_tactic\n", encoding="utf-8")
        unrelated = run_import(tc, env, repo, unrelated_path, "<unrelated-compiler-failure>")
        unrelated["probePath"] = str(unrelated_path)
        unrelated["probeSha256"] = digest(unrelated_path)
        unrelated["classification"] = (
            "unrelated-compiler-failure-not-isolation-evidence"
            if unrelated["returncode"] != 0 and "unknown module prefix" not in unrelated["stdout"] + unrelated["stderr"]
            else "invalid-countercheck"
        )
        rows.append(unrelated)
        remaining = sorted(p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file())
        if remaining != allowed:
            raise RuntimeError(f"workspace mutated after isolation probes: {slot.name}")
        excluded = [r for r in rows if r.get("classification") in {
            "module-unavailable", "parent-namespace-unavailable"
        }]
        evidence.append({"caseId": wr["caseId"], "caseSlot": wr["slot"], "selectedModule": selected,
                         "allowedFiles": allowed, "probes": rows,
                         "allExcludedModulesProvedUnavailable": len(excluded) == len(forbidden),
                         "injectionImported": injection_result["classification"] == "imported",
                         "injectionGuardRejected": guard_rejected,
                         "unrelatedFailureRejected": unrelated["classification"] == "unrelated-compiler-failure-not-isolation-evidence",
                         "workspaceRestored": remaining == allowed})
    output = RUN / "isolation-check-v5.json"
    output.write_text(json.dumps({"schema": "ladon-pitfall-live-isolation-v1", "results": evidence},
                                 indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if any(not all(item[key] for key in ("allExcludedModulesProvedUnavailable", "injectionImported",
                                          "injectionGuardRejected", "unrelatedFailureRejected", "workspaceRestored"))
           for item in evidence):
        raise SystemExit("isolation qualification failed; inspect isolation-check-v5.json")
    print(json.dumps({"status": "passed", "cases": len(evidence),
                      "output": str(output), "sha256": digest(output)}))


if __name__ == "__main__":
    main()
