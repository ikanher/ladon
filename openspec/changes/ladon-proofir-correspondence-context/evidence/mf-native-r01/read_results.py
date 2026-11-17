"""Read actual native results and verify custody; does not run Lean."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
OLD = ROOT / "openspec/changes/ladon-semantic-pitfalls-umbrella/evidence"

def read(path):
    return json.loads(path.read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect_case(name, checked_name, parent):
    bundle = read(BASE / name / checked_name)
    view = read(BASE / name / "inspection.json")["native"]
    assert bundle["parentSupport"] == parent
    assert view["coverage"]["complete"]
    assert view["checkEvidence"]["unboundObligations"] == []
    assert view["authority"] == "stored-evidence-only"
    targets = {}
    for row in bundle["checks"]:
        completion = row["completion"]
        assert completion["status"] == "completed"
        assert completion["replay"]["status"] == "accepted"
        assert completion["trust"]["accepted"] is True
        targets[row["obligation"]] = row
    for row in view["checkEvidence"]["rows"]:
        assert row["binding"]["status"] == "matched-stored-records"
        receipt = row["receipt"]["value"]
        checked = targets[receipt["obligation"]]
        assert receipt["checkedGoal"] == (checked["goal"] if checked["mode"] == "prove"
                                           else "¬ (" + checked["goal"] + ")")
        assert receipt["status"] == checked["status"]
    assert {row["receipt"]["value"]["obligation"]
            for row in view["checkEvidence"]["rows"]} == set(targets)
    assert len(targets) == 4
    return {"parentSupport": parent,
            "checks": {key: row["status"] for key, row in targets.items()},
            "executionAccounting": bundle["executionAccounting"],
            "compiledModules": len(bundle["plan"]["slice"]["compiledInventory"]["modules"])}

def main():
    selected = read(BASE / "FINAL-SELECTION.json")
    cases = {name: inspect_case(name, row["checked"], row["parentSupport"])
             for name, row in selected.items()}
    assert cases["fdp"]["checks"]["conclusion"] == "refuted"
    assert all(status == "supported" for status in cases["adam"]["checks"].values())
    for metadata in ["INPUTS-r03.json", "ADAM-INPUTS.json"]:
        for path, expected in read(BASE / metadata)["primaryInputs"].items():
            assert digest(BASE / path) == expected, path
    for path, expected in read(BASE / "INPUTS-r03.json")["directCompiledImports"].items():
        assert digest(Path(path)) == expected, path
    for actual, original in [
        ("project/Fdp.lean", "fdp-ordering-privacy-20261115T072023Z/Countermodel.lean"),
        ("adam-project/AdamCase.lean", "dpadam-source-constructor-r01/Full.lean"),
    ]:
        assert (BASE / actual).read_bytes().startswith((OLD / original).read_bytes())
    output = {"status": "qualified", "cases": cases,
              "nativeChecks": sum(len(case["checks"]) for case in cases.values()),
              "authority": "supplied-proof native qualification; attributed source readings",
              "discoveryOrReaderBenefit": "not measured"}
    path = BASE / "RESULT.json"
    if path.exists():
        assert read(path) == output, 'retained result changed'
    else:
        with path.open("x") as stream:
            json.dump(output, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
    print(json.dumps({"status": output["status"], "nativeChecks": output["nativeChecks"],
                      "cases": {name: row["checks"] for name, row in cases.items()}}, indent=2))

if __name__ == "__main__":
    main()
