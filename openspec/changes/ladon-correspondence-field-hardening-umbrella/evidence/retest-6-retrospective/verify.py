"""Check retrospective custody and recorded controls, without replaying Lean."""

import hashlib
import json
from pathlib import Path


def verify(base=None):
    base = Path(__file__).resolve().parent if base is None else Path(base)
    manifest = json.loads((base / "source-manifest.json").read_text())
    for row in manifest["files"]:
        data = Path(row["path"]).read_bytes()
        assert len(data) == row["bytes"], row["path"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
    corpus = json.loads((base / "cases.json").read_text())
    cases = corpus["cases"]
    run = Path(corpus["auditRoot"])
    index = json.loads((run / "native-evidence-index-final.json").read_text())
    by_artifact = {s["artifact"]: s for s in index["subjects"]}
    controls = [c for c in cases if c["kind"] == "successful-local-control"]
    assert len(controls) == 6
    assert len(cases) == 8 and len({c["id"] for c in cases}) == 8
    for case in cases:
        if case["kind"] != "reference-discrepancy":
            continue
        path, _, pointer = case["observedIn"].partition("#/")
        evidence = (run / path).read_text()
        if pointer:
            evidence = json.loads(evidence)
            for key in pointer.split("/"):
                evidence = evidence[int(key)] if isinstance(evidence, list) else evidence[key]
        assert case["observedEvidenceQuote"] in evidence
        assert case["expected"]["exactNativeBridge"] == "not-established-in-recorded-run"
        assert case["expected"]["proseFalsity"] == "not-established"
        assert (base / case["source"]).is_file()
    obligations = 0
    for case in controls:
        subject = by_artifact[case["checkedArtifact"]]
        response = json.loads((run / case["review"]).read_text())
        assert subject["sha256"] == case["checkedSha256"]
        assert case["sourceBinding"] == subject["source"]
        assert case["selection"] == subject["selection"]
        source = run.parent.parent / case["sourceBinding"]["path"]
        binding = case["sourceBinding"]
        assert hashlib.sha256(source.read_bytes()).hexdigest() == binding["sha256"]
        quote = "\n".join(source.read_text().splitlines()[binding["startLine"] - 1:binding["endLine"]])
        assert quote == binding["quote"]
        assert response["subject"] == subject["planId"]
        assert response["classification"] == "aligned"
        assert response["method"] == case["expected"]["methodRelation"]
        assert all(c["status"] == "supported" for c in subject["checks"])
        assert subject["residuals"] == []
        assert case["originalObligations"] == [
            {"id": o["id"], "kind": o["kind"]} for o in subject["originalObligations"]]
        obligations += len(subject["originalObligations"])
    assert obligations == 40
    lines = (run / "exposition.txt").read_text().splitlines()
    for name in ("inverse-source.txt", "pressure-source.txt"):
        for row in (base / name).read_text().splitlines():
            number, quote = row.split(": ", 1)
            assert lines[int(number) - 1] == quote
    return {"status": "passed", "sourceIdentities": len(manifest["files"]),
            "developmentCases": len(cases), "historicalControls": len(controls),
            "recordedObligations": obligations, "newLeanChecks": 0,
            "limits": "Identity and recorded-label checks; no semantic proof or new blind evaluation."}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
