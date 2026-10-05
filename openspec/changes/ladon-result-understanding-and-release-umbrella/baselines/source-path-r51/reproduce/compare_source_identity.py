"""Compare full source digests over a frozen selection using both implementations."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--baseline", type=Path, required=True)
parser.add_argument("--candidate", type=Path, required=True)
parser.add_argument("--paths", type=Path, required=True)
parser.add_argument("--repo", type=Path, required=True)
args = parser.parse_args()
paths = json.loads(args.paths.read_text())
class FrozenEnumeration:
    def paths(self, root: Path) -> tuple[str, ...]:
        assert root == args.repo
        return tuple(paths)

def load(name: str, source: Path):
    spec = importlib.util.spec_from_file_location(name, source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

baseline = load("r51_digest_baseline", args.baseline)
candidate = load("r51_digest_candidate", args.candidate)
results = []
for label, owner in (("baseline-before", baseline), ("candidate", candidate), ("baseline-after", baseline)):
    start = time.perf_counter()
    digest = owner._source_tree_identity(args.repo, FrozenEnumeration())
    results.append({"owner": label, "digest": digest, "seconds": time.perf_counter() - start})
report = {"python": sys.version, "repo": str(args.repo), "rawPathsSha256": "sha256:" + hashlib.sha256(args.paths.read_bytes()).hexdigest(), "results": results, "identical": len({row["digest"] for row in results}) == 1}
print(json.dumps(report, indent=2))
sys.exit(0 if report["identical"] else 1)
