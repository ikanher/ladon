# Bounded contract audit driver

The opt-in `ladon investigation contract audit` entrypoint now composes existing
contract operations under one deadline, with immutable outputs and verified
prefix resume. Umbrella task 2.4 is complete. Independent final-byte review
**#977** accepted this bounded orchestration slice, superseding the intermediate
review **#970**. Parent progress is **4/12**.

The runnable workflow and request table are in
[PROOF_CONTRACTS.md](../../../../../docs/PROOF_CONTRACTS.md#bounded-contract-audit).
The portable [fixture](../../../../../tests/fixtures/proof_contract_audit/propagate-inspect.json)
propagates authored native contracts and inspects the result. It requires no
Lean compilation, model service or Quux checkout.

## Observable behavior

- The original plan bytes, source selections and interpretations are frozen
  before algorithm stages. Prose production precedes formal matching.
- Existing producers, propagation, obligations, application probes and
  inspection use fixed supervised adapters. Refinement explicitly reports
  `refinement-unavailable`; it is not implemented by this driver.
- The default shared deadline is 5,400 seconds, with 12 GiB process-tree RSS
  and 8 MiB worker output. Explicit tighter bounds remain effective. The plan
  allows 64 stages; stored results have an aggregate 32 MiB cap.
- Each run uses a new directory. Resume validates the original plan, runtime,
  source/toolchain identity and saved receipts before dispatch, copies exact
  completed-prefix bytes and preserves the original clock and limits. A
  prepublished header supports recovery after an interrupted final receipt.
- Memory stops retain the configured cap, sampled peak and stop-and-report
  guidance. They halt dependent work and refuse automatic resume. Admission
  failures retain their process receipt and mark an initial source binding
  unverified. Stops during resume preserve the original completed prefix.
- A nested probe borrows an explicitly delegated goal lease. The outer
  supervisor retains ownership and preserves nonempty scratch through
  quarantine outside the source root if the stage is killed. No source
  exclusion, recursive deletion or longer kill grace was introduced.
- Completion means orchestration completed. Source fidelity, extraction
  completeness, route support, method correspondence and mathematical falsity
  retain their separate authority. The receipt also records the attempted,
  completed and unresolved stage population.

## Verification

- Initial root replay of the isolated proposal: **47 passed**
  ([proposal-replay.xml](proposal-replay.xml)).
- Integrated portable regression: **149 passed**, including 29 new driver
  cases and existing resource, source identity, ownership and CLI controls
  ([integration-final.xml](integration-final.xml)). Frozen tests remain unchanged
  ([FROZEN-TESTS-final.json](FROZEN-TESTS-final.json)).
- Actual public CLI help, checkpoint, resume, unsupported refinement and
  memory-stop paths passed ([CLI-CHECKS-final.json](CLI-CHECKS-final.json)). The memory
  check used an explicit **1 MiB** cap and sampled **9,986,048 bytes**; it
  performed no retry. Checkpoint/resume retained identical stage bytes,
  original clock and limits.
- Actual Lean 4.32.1 formal production followed by snapshot inspection
  completed in **3.25 seconds** under one **120-second / 12 GiB** audit budget
  ([FORMAL-CHECK-final.json](FORMAL-CHECK-final.json),
  [formal stage](run-formal-final/stages/formal.json)). The statement helper took
  0.98 seconds and sampled a peak of 2,045,255,680 bytes. The selected
  `ProducerCases.supported_base` is deliberately an axiom: this checks
  elaborated statement extraction and freshness, without proving its claim.
- Scoped Ruff, strict Radon/Vulture quality and compilation passed for all
  seven runtime files and ten new test files ([QUALITY-final.json](QUALITY-final.json)).
  Offline lock verification and strict OpenSpec validation passed. No
  dependency was added. Exact commands and test outcomes are in
  [CHECKS-final.json](CHECKS-final.json).
- The earlier localized-obligation packet still verifies **97 unchanged
  files**, and the accepted timeout-scratch packet verifies **27 unchanged
  files**. Their historical runtime identities were preserved.

The original missing-driver red tests, concrete nested-timeout and identity
failures, and resource-classification failures are retained separately.
[resource-causal-red.xml](resource-causal-red.xml) reproduces four resource
failures against the archived causal runtime. The two admission-recovery
checks were positive confirmations after the repair, not claimed failing
prerequisites. Final root acceptance also caught silent replacement of extra nested probe
limits. Two [failing regressions](probe-bounds-red.xml) preceded the narrow
request-validator correction; probe requests now reject fields outside their
documented four-field schema. The earlier 147-test and CLI/Lean runs remain
preserved as intermediate evidence; final verification uses the corrected
runtime. The initial controlled nested probe is preserved in
[NESTED-OWNERSHIP.json](NESTED-OWNERSHIP.json).

The before/after manifests and tar snapshots preserve the earlier 1,206-file
integrated version as history, 1,192 original files
and the 1,207-file final integrated snapshot. Four original files changed (three
runtime modules and documentation); four runtime modules, ten tests and one
fixture were added. [INTEGRATION.json](INTEGRATION.json) binds the accepted
proposal and root integration. The final request-closure correction is bound
by [INTEGRATION-final.json](INTEGRATION-final.json). The formal source bytes and exact toolchain
context remained unchanged when temporary nested Git metadata was moved to
ignored state ([custody receipt](FORMAL-SOURCE-CUSTODY.json)).

## Remaining gates

Resume supports the same host boot and uses both monotonic and UTC expiry.
Cross-host or cross-boot migration is unsupported. Filesystem operations
assume the existing trusted local boundary; hashes do not authenticate a run
against a writer who can replace all metadata. Quarantine preserves scratch
bytes; it does not prove every descendant process terminated.

Repository-wide verification has not been rerun. The pre-existing strict
quality issue in `_proof_contract_probe_domain_contracts.py` is outside this
patch. Investigation finding projection, independently sourced pair
integration, refinement and measured detection benefit retain separate gates.
No paper audit, fault detection, full-proof acceptance, commit or push is
claimed.

The next implementation frontier is umbrella task 2.5: retain contract findings
and their distinct authority through observation, review, aggregation and
final receipts. Independent reviews and exact final-byte identities are retained
in [BOARD.jsonl](BOARD.jsonl).
