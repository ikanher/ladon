"""Inspect retained MF evidence; never compile Lean or manufacture native checks."""

import gzip
import hashlib
import json
from pathlib import Path

from ladon.correspondence_evidence import _accepted

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
EVIDENCE = ROOT / "openspec/changes/ladon-semantic-pitfalls-umbrella/evidence"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def manifest(name):
    directory = EVIDENCE / name
    value = read(directory / "MANIFEST.json")
    rows = value.items() if isinstance(value, dict) else (
        (row["path"], row["sha256"]) for row in value
    )
    count = 0
    for relative, expected in rows:
        assert digest(directory / relative) == expected, relative
        count += 1
    return count


def source_receipt(name, source, receipt):
    directory = EVIDENCE / name
    result = read(directory / receipt)
    assert result["returncode"] == 0
    assert result["sourceUnchanged"] is True
    assert result["sourceSha256"] == digest(directory / source)
    for flag in ("timed_out", "output_limited", "memory_limited"):
        assert result[flag] is False
    axiom_lines = [line for line in result["stdout"].splitlines()
                   if "depends on axioms:" in line]
    assert axiom_lines
    for line in axiom_lines:
        axioms = line.split("depends on axioms: [", 1)[1].removesuffix("]")
        assert set(axioms.split(", ")) <= {"propext", "Classical.choice", "Quot.sound"}
    # A deliberately proposed promotion exercises the existing admission guard.
    # Rejection is expected: ordinary compilation is not native completion.
    try:
        _accepted({"status": "supported"}, result)
    except ValueError as error:
        admission = str(error)
    else:
        raise AssertionError("ordinary receipt unexpectedly admitted")
    return {
        "source": str((directory / source).relative_to(ROOT)),
        "sourceSha256": result["sourceSha256"],
        "receipt": str((directory / receipt).relative_to(ROOT)),
        "receiptSha256": digest(directory / receipt),
        "axiomLines": axiom_lines,
        "nativePromotionRejected": admission,
        "authority": "historical ordinary Lean compilation; no fresh replay",
    }


def scalar_receipt():
    directory = EVIDENCE / "dpadam-batch-pair-r01"
    summary = read(directory / "NATIVE-SUMMARY.json")
    for row in summary["raw"]:
        raw = gzip.decompress((directory / row["path"]).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row["uncompressedSha256"]
    raw = json.loads(gzip.decompress(
        (directory / "privacy-slope-completion.json.gz").read_bytes()
    ))
    assert raw["status"] == summary["status"] == "completed"
    assert all(raw["application"]["originalGoal"][key] == value
               for key, value in summary["originalGoal"].items())
    assert raw["replay"]["status"] == "accepted"
    assert raw["trust"]["accepted"] is True
    assert _accepted({"status": "supported"}, raw)
    return {
        "originalGoalSummary": summary["originalGoal"],
        "localContext": [{k: row[k] for k in ("localId", "typeDisplay", "implementationDetail") if k in row}
                         for row in raw["application"]["originalGoal"]["localContext"]],
        "admissionGuard": "accepted completion/replay/trust fields",
        "authority": "retained native scalar completion only; not whole DP-Adam support",
    }


def anchors():
    """Capture exact inspected source spans; their interpretation remains authored."""
    selected = [
        ("fdp-ordering-privacy-20261115T072023Z/Countermodel.lean", 1, 171),
        ("fdp-source-interpretation-r01/INTERPRETATION.md", 1, 43),
        ("dpadam-source-constructor-r01/Full.lean", 232, 253),
        ("dpadam-source-constructor-r01/Full.lean", 390, 479),
        ("dpadam-source-constructor-r01/Full.lean", 519, 640),
        ("dpadam-batch-pair-r01/exposition.tex", 24, 40),
        ("dpadam-batch-pair-r01/exposition.tex", 425, 465),
        ("pitfalls-consumer-fdp-20261114T131246Z/inputs/paper/theory/mu-dp/fDP/fDP.tex", 30, 37),
        ("pitfalls-consumer-fdp-20261114T131246Z/inputs/paper/theory/mu-dp/subsample.tex", 30, 45),
    ]
    result = []
    for relative, start, end in selected:
        path = EVIDENCE / relative
        lines = path.read_text().splitlines()
        end = min(end, len(lines))
        assert 1 <= start <= end
        result.append({"path": str(path.relative_to(ROOT)), "sha256": digest(path),
                       "startLine": start, "endLine": end,
                       "text": "\n".join(lines[start - 1:end])})
    return result


def main():
    result = {
        "kind": "exposed-review-trace-not-proofir",
        "manifestEntriesVerified": {
            name: manifest(name) for name in (
                "fdp-ordering-privacy-20261115T072023Z", "dpadam-source-constructor-r01"
            )
        },
        "fdp": source_receipt("fdp-ordering-privacy-20261115T072023Z",
                              "Countermodel.lean", "attempt-07.json"),
        "dpadam": source_receipt("dpadam-source-constructor-r01",
                                 "Full.lean", "full-attempt-12.json"),
        "nativeScalar": scalar_receipt(),
        "anchors": anchors(),
        "implementation": {
            name: digest(ROOT / "src/ladon" / name) for name in (
                "correspondence_evidence.py", "proofir_correspondence_payloads.py",
                "correspondence_cli.py", "proofir_v3_queries.py",
            )
        },
        "limits": ["No Lean execution", "No live donor freshness check",
                   "No independent review", "No accepted correspondence bundle produced",
                   "Admission guard probe is not full artifact validation"],
    }
    target = HERE / "TRACE.json"
    if target.exists():
        assert read(target) == result, "retained trace differs from current inputs"
    else:
        with target.open("x") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    print("Verified 69 manifest entries, two source receipts, native scalar custody and admission boundaries.")


if __name__ == "__main__":
    main()
