"""One bounded real-Lean check of the supervised generated-goal lifecycle."""
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path

from ladon.lean_toolchain import verify_toolchain_identities
from ladon.proof_contract_bridge_supervision import run_bridge_job
from ladon.proof_slice import pinned_toolchain


def main():
    deadline = time.monotonic() + 90
    with tempfile.TemporaryDirectory(prefix="ladon-owned-goal-smoke-") as temporary:
        root = Path(temporary) / "repo"
        root.mkdir()
        (root / "lean-toolchain").write_text("leanprover/lean4:v4.32.1\n")
        source = b"import Lean\n"
        (root / "Source.lean").write_bytes(source)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        context = pinned_toolchain(root)
        request = {
            "repoRoot": str(root), "sourcePath": "Source.lean",
            "sourceDigest": "sha256:" + hashlib.sha256(source).hexdigest(),
            "goal": "True", "term": "True.intro", "symbols": {},
        }
        result = run_bridge_job("check-goal", request, deadline_monotonic=deadline)
        environment_restored = True
        try:
            verify_toolchain_identities(context)
        except ValueError:
            environment_restored = False
        summary = {
            "supervision": result,
            "environmentRestored": environment_restored,
            "sourceUnchanged": (root / "Source.lean").read_bytes() == source,
            "remainingGoals": [str(p.relative_to(root)) for p in root.rglob("LadonCorrespondence.lean")],
            "deadlineRemainingSeconds": deadline - time.monotonic(),
        }
        print(json.dumps(summary, indent=2))
        checked = result.get("result") or {}
        return 0 if (result["status"] == "completed" and checked.get("status") == "supported"
                     and environment_restored and summary["sourceUnchanged"]
                     and not summary["remainingGoals"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
