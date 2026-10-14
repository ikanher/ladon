"""Ambient source variables cannot repair the generated original obligation."""

import json
import shutil
from pathlib import Path

from ladon.correspondence_check import _check_goal, check_correspondence, prepare_correspondence
from ladon.proof_slice import extract_proof_slice, pinned_toolchain


def test_generated_goals_drop_source_section_hypotheses_and_reject_self_support(tmp_path):
    root = tmp_path / "repo"
    fixture = Path(__file__).parent / "fixtures/correspondence_m1"
    shutil.copytree(fixture, root, ignore=shutil.ignore_patterns(".ladon", "*.olean"))
    source = root / "Proof.lean"
    source.write_text(source.read_text() + "\nsection\nvariable (hLeak : False)\ninclude hLeak\n")
    actual = extract_proof_slice(root, "Proof.lean", "Proof", "Correspondence.term", "bridge")
    assert actual["complete"]
    plan = prepare_correspondence(json.loads((root / "false.json").read_text()), actual, {"n": "n"})
    result = check_correspondence(
        plan,
        [
            {
                "obligation": "conclusion",
                "mode": "prove",
                "term": "by intros; exact False.elim hLeak",
            }
        ],
        root,
    )
    assert result["checks"][0]["status"] == "unresolved"
    assert result["conditionalValidity"] == "supported"
    for row in result["checks"]:
        if row.get("capture", {}).get("status") == "captured":
            assert all(
                local["implementationDetail"]
                for local in row["capture"]["capture"]["goal"]["localContext"]
            )
    recursive = _check_goal(
        "False", "by exact _example", root, source.read_bytes(), {}, pinned_toolchain(root)
    )
    assert recursive["status"] == "unresolved"
