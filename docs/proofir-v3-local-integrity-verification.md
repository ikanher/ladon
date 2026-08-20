# ProofIR v3 local-integrity verification

The umbrella change is verified with the repository's locked environment.  The
commands below are the authoritative repeatable checks; the recorded outcomes
are from the final implementation run.

```text
uv run --locked openspec validate ladon-proofir-local-integrity-hardening-umbrella --strict
uv run --locked pytest -q tests/test_proofir_derivation_queries.py tests/test_proofir_identity.py tests/test_proofir_link_observations.py tests/test_lean_toolchain.py tests/test_semantic_candidate_worker_v3_contract.py tests/test_proofir_result_dimensions.py tests/test_proofir_projection_corpus.py
uv run --locked python scripts/python_quality.py --strict
uv run --locked python -m compileall -q src tests
git diff --check
```

The quality command includes the full Python suite, Ruff, radon, and vulture.
The installed CLI contract is additionally exercised by
`tests/test_proof_search_installed_v3_contract.py` and the candidate checker
accepts explicit `--lake-path`/`--lean-path` selection.

These checks establish local integrity and projection behavior only.  They do
not establish theorem truth, kernel authority for ambient toolchains, or
compatibility with the separate Quux repository.
