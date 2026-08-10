from ladon.proofir_fingerprint_registry import SCHEMES, is_exact_scheme
from ladon.semantic_candidate_worker import FINGERPRINT_SCHEME


def test_worker_scheme_is_registered_for_exact_search() -> None:
    key = (FINGERPRINT_SCHEME["name"], FINGERPRINT_SCHEME["version"])
    assert key in SCHEMES
    assert is_exact_scheme(*key)
