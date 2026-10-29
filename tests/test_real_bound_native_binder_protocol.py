"""Native scope consumes the public formal worker's binder-info spellings."""

import pytest
from test_real_bound_native_records import recorded, rehash

from ladon.proofir_v3 import validate_envelope


@pytest.mark.parametrize("binder_info", ["explicit", "implicit", "strict-implicit", "instance-implicit"])
def test_formal_worker_binder_information_is_retained(binder_info):
    artifact = recorded()[-1]
    artifact["payload"]["record"]["telescope"][0]["binderInfo"] = binder_info
    checked = validate_envelope(rehash(artifact)).to_dict()
    assert checked["payload"]["record"]["telescope"][0]["binderInfo"] == binder_info


@pytest.mark.parametrize("binder_info", ["strictImplicit", "instImplicit", "unknown"])
def test_unregistered_api_spellings_are_not_formal_worker_protocol(binder_info):
    artifact = recorded()[-1]
    artifact["payload"]["record"]["telescope"][0]["binderInfo"] = binder_info
    with pytest.raises(ValueError, match="binder"):
        validate_envelope(rehash(artifact))
