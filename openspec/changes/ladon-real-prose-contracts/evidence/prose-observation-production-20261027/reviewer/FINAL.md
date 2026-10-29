# Final independent source audit: Task 1.2

Audited the final revision named by `FINAL-REVISION.json` on 2026-10-27. All 12
listed production, documentation, and test file hashes match the checkpoint.
This was a read-only source review; I did not run tests, Lean, or builds.

## Finding

`src/ladon/real_prose_inputs.py:60-72` computes the implementation identity from
an explicit module list. The list includes the prose modules and several shared
inventory, toolchain, and supervision modules, but omits directly used
`src/ladon/proof_contract_payloads.py` and `src/ladon/proof_contract_io.py`.
`real_prose_history.py`, `real_prose_worker.py`, and `real_prose_expression.py`
use `proof_contract_payloads.closed` for closed-shape validation, while
`real_prose_worker.py` uses `proof_contract_io._decode` for worker transport.
Changing either dependency would change validation/decoding behavior without
changing the stored implementation identity; current-source inspection could
therefore report the implementation as current across that change. Include
these directly used dependencies in the digest (and review the inventory for
other behavior-bearing direct imports) or narrow the identity claim.

## Confirmed in source

- The Lean worker selects a generated local definition, checks both declared
  type and value type are `Prop`, and serializes the proposition value; it
  creates no theorem or proof claim.
- The worker is supervised with the caller-configured RSS/output caps and one
  absolute deadline. Default RSS is 12 GiB; explicit configuration remains
  supported. The outer receipt and both Lean receipts are checked for successful
  status before an observation is accepted.
- Successful observations replay identically around imported compiled-module
  and sidecar inventory checks. Source/context and toolchain stability are
  checked before returning.
- Expression validation enforces the Lean-expression constructors, closed
  bound-variable scopes, depth 128, and 100,000 nodes. History inspection keeps
  authority absent and explicitly says execution receipt authentication is not
  established.
- The frozen replacement keeps the false-proposition observation, malformed
  input/resource controls, replay/history, and consumer-rejection cases. The
  configured-cap forwarding test checks no automatic increase.

## Limits

This does not establish Lean helper compilation in this audit, native Real
profile support, proposition fidelity, admission, or connection to formal
contracts. The checkpoint records prior focused test results; I did not rerun
them. Saved receipts are historical and unauthenticated by design.
