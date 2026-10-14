"""The selected application profile must retain leading values and implicit arguments."""

from pathlib import Path

from ladon.proof_slice import extract_proof_slice


def test_leading_local_value_and_actual_implicit_argument():
    root = Path(__file__).parent / "fixtures/correspondence_m1"
    result = extract_proof_slice(
        root, "Profile.lean", "Profile", "Profile.localValue", "Profile.bridge"
    )
    assert result["complete"] is True
    k = next(row for row in result["localContext"] if row["name"] == "k")
    assert k["letValue"] is not None
    assert k["isProp"] is False
    arguments = result["nodes"][0]["arguments"]
    assert len(arguments) == 2
    assert "implicit" in arguments[0]["binderInfo"]
    assert [row["isProp"] for row in arguments] == [False, True]
