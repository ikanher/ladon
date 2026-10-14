"""Real-source M1 integration gate; requires the declared development checkout."""
from pathlib import Path

PRESSURE_ROOT = Path("/home/codex/projects/navier-stokes-retest-4/formalization")
PRESSURE_FILE = "NavierStokes/PressureDatum.lean"

def test_real_pressure_application_slice_preserves_actual_provider_chain():
    from ladon.proof_slice import extract_proof_slice

    result = extract_proof_slice(
        PRESSURE_ROOT, PRESSURE_FILE, "NavierStokes.PressureDatum",
        "NavierStokes.PressureDatum.deriv_pressure_pos_of_active",
        "deriv_pressure_pos", occurrence=0,
    )
    assert result["complete"] is True
    applications = [n for n in result["nodes"] if n.get("kind") == "application"]
    assert applications
    selected = applications[0]
    assert selected["declaration"].endswith("deriv_pressure_pos")
    assert len(selected["arguments"]) >= 3  # h, derived mass positivity, hη
    assert result["source"]["path"] == PRESSURE_FILE

