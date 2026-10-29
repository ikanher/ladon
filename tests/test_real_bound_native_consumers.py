"""Real summaries stay historical in native views and fail closed in Nat consumers."""

import json

import pytest
from test_real_bound_native_records import recorded

from ladon.proofir_v3_cli import proofir_v3_main


def test_proofir_inspection_exposes_historical_real_profile(tmp_path, capsys):
    artifact = tmp_path / "contract.json"
    artifact.write_text(json.dumps(recorded()[-1]))
    assert proofir_v3_main(["inspect", str(artifact)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["contract"]["profileId"] == "real-bound-v1"
    assert result["contract"]["authority"] == "none"
    assert result["contract"]["admission"] == "recorded-checked"


def test_nat_propagation_reader_rejects_real_contract():
    from ladon._contract_propagation_inputs import read_contracts

    contract = recorded()[-1]
    with pytest.raises(ValueError):
        read_contracts([contract], contract["environmentRef"])


def test_nat_probe_rejects_real_before_resolving_correspondence():
    from ladon._proof_contract_probe_pair import _resolve_side

    contract = recorded()[-1]
    side = {"contractRef": {"artifactRef": contract["artifactId"], "kind": "contract",
                             "localId": contract["payload"]["contractId"]},
            "correspondenceRef": {"artifactRef": "sha256:" + "a" * 64,
                                  "kind": "correspondence", "localId": "absent"}}
    with pytest.raises(ValueError, match="profile"):
        _resolve_side([contract], side)
