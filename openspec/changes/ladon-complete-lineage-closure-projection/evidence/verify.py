"""Verify the frozen field observation; this is not an implementation test."""
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
manifest = json.loads((base / "manifest.json").read_text())
for item in manifest["files"]:
    path = base / item["path"]
    assert path.is_file(), item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["path"]
summary = json.loads((base / "field-summary.json").read_text())
graph = json.loads((base / "field-route-graph.json").read_text())
assert summary["status"] == graph["status"] == "available"
assert summary["closureId"] == graph["closureId"]
assert summary["nodes"]["total"] == 2242
assert summary["nodes"]["projectOwned"] == 278
assert sum(summary["edges"].values()) == 47533
assert summary["omissionCount"] == 0
assert graph["truncated"] is True
assert graph["acquisition"]["recursiveRowLimitReached"] is True
assert graph["acquisition"]["rowsObserved"] == 10000
assert len(graph["nodes"]) == 1072
assert len(graph["edges"]) == 23
assert graph["returned"]["edges"] == 73
assert len({(e["source"], e["target"]) for e in graph["edges"]}) == 23
assert all("kind" not in e for e in graph["edges"])
print("PASS: frozen field evidence and stated discrepancy; no implementation or theorem check")
