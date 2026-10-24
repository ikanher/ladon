# Statement producer supervision

The public `produce_formal_contract` and `produce_formal_snapshot` APIs now accept
optional `runner` and `max_output_bytes` arguments. This lets an obligation
adapter use a shared deadline supervisor through the ordinary statement,
source-goal capture and completion paths. Defaults remain 8 MiB of output and
12 GiB RSS. No retry or new proof authority is introduced.

The output bound applies both to the subprocess streams and to reading the
helper's result file. The default supervisor is looked up when called, preserving
existing callers that patch that boundary. Invalid bounds stop before target
input capture.

Root verification:

```sh
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_proof_contract_producer_bounds.py \
  tests/test_proof_contract_production.py::test_core_statement_is_extracted_from_the_exact_lean_declaration \
  tests/test_proof_contract_instances.py::test_formal_process_bounds_reject_nonfinite_or_boolean_values \
  tests/test_proof_contract_instances.py::test_memory_failure_uses_shared_cap_and_peak_diagnostic
```

Result: 15 passed, including one actual Lean statement observation. The eight
new frozen tests first produced three missing-parameter failures, then passed.
No-cache Ruff and strict quality checks passed on both changed modules and the
new test file. Independent Luna medium audit, board post 360, checked exact
source hashes and reran the eight tests without additional findings.

Reviewed hashes:

| File | SHA-256 |
| --- | --- |
| `src/ladon/proof_contract_production.py` | `7af5326c4ad83f32eb99ee250de91eba1977b192362660e0aa233c57ac68415c` |
| `src/ladon/proof_contract_formal.py` | `d75bed7a8bb2ac99b0d511ae1c5558a8f483457dd88145af61e8483bbea63318` |
| `tests/test_proof_contract_producer_bounds.py` | `ddaf01693cf3252b892e87fd69ab65944f43275102b77053e7ebd200c579f37d` |

This is supporting budget plumbing. It does not establish source-bound goal
construction, source fidelity, successful obligation replay, whole-method
support, or manuscript error detection. Tasks 1.2 and 2.2 remain open.
