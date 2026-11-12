"""Verify one-case Lean search paths expose only that case and shared definitions."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "cases.json").read_text())["cases"]


def classify_probe(module: str, expect_success: bool, result: subprocess.CompletedProcess) -> str:
    diagnostics = result.stdout + result.stderr
    if expect_success:
        if result.returncode == 0:
            return "imported"
        raise RuntimeError(f"positive import failed: {module}: {diagnostics}")
    lines = [line.strip() for line in diagnostics.splitlines() if line.strip()]
    errors = [line.split("error:", 1)[1].strip() for line in lines if "error:" in line]
    expected = False
    if len(errors) == 1 and lines and "error:" in lines[0]:
        if re.fullmatch(r"object file '[^'\n]+' of module " + re.escape(module) + r" does not exist", errors[0]):
            expected = len(lines) == 1
        elif errors[0] == f"unknown module prefix '{module}'":
            banner = f"No directory '{module}' or file '{module}.olean' in the search path entries:"
            expected = len(lines) >= 3 and lines[1] == banner and all(Path(line).is_absolute() for line in lines[2:])
    if result.returncode == 1 and expected:
        return "module-unavailable"
    raise RuntimeError(f"forbidden import not proven unavailable: {module}: exit {result.returncode}: {diagnostics}")


def env_for(project: Path, support_module: str, case: dict, sibling: dict) -> dict:
    env = subprocess.check_output(["lake", "env", "printenv", "LEAN_PATH"], cwd=project, text=True).strip()
    full_paths = env.split(os.pathsep)
    project_build = str(project / ".lake/build/lib/lean")
    dependency_paths = [p for p in full_paths if p != project_build]
    lean_bin = subprocess.check_output(["elan", "which", "lean"], cwd=project, text=True).strip()
    prefix = subprocess.check_output([lean_bin, "--print-prefix"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="ladon-case-isolation-") as td:
        overlay = Path(td)
        support = project / ".lake/build/lib/lean" / f"{support_module}.olean"
        shutil.copy2(support, overlay / f"{support_module}.olean")
        module_path, _ = case["leanSource"].split("#", 1)
        src = ROOT / module_path
        rel_module = src.relative_to(project).with_suffix(".olean")
        target = project / ".lake/build/lib/lean" / rel_module
        dest = overlay / rel_module
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, dest)
        env2 = dict(os.environ)
        env2["LEAN_PATH"] = os.pathsep.join([str(overlay), *dependency_paths, str(Path(prefix) / "lib/lean")])
        target_mod = ".".join(rel_module.with_suffix("").parts)
        sibling_path, _ = sibling["leanSource"].split("#", 1)
        sibling_mod = ".".join((ROOT / sibling_path).relative_to(project).with_suffix("").parts)
        # Import the target successfully, then prove neither a sibling nor answers resolve.
        probes = []
        for module, expect_success in [(target_mod, True), (sibling_mod, False), ("Validation", False)]:
            probe = overlay / "Probe.lean"
            probe.write_text(f"import {module}\n")
            result = subprocess.run([lean_bin, str(probe)], env=env2, text=True, capture_output=True, timeout=60)
            classification = classify_probe(module, expect_success, result)
            probes.append({"module": module, "exitStatus": result.returncode,
                           "classification": classification, "stdout": result.stdout, "stderr": result.stderr})
        return {"caseId": case["caseId"], "probes": probes}



def main() -> None:
    core = [c for c in CASES if c["family"] != "existence-defaults"]
    math = [c for c in CASES if c["family"] == "existence-defaults"]
    out = []
    for group, project, support in [(core, ROOT / "lean", "Pitfalls"), (math, ROOT / "mathlib", "LeastElement")]:
        for i, case in enumerate(group):
            sibling = group[(i + 1) % len(group)]
            out.append(env_for(project, support, case, sibling))
    print(json.dumps({"schema": "ladon-isolation-check-v2", "cases": out}, indent=2))


if __name__ == "__main__":
    main()
