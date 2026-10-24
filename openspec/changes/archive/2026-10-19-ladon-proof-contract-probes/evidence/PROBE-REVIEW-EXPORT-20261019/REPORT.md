# Source-bound probe reviewer export

## Outcome

Task 2.2's reviewer-export path is implemented. `review-probe` inspects the
native planning artifact, checks original source quotations, exports exact
source/formal context and generated goals, and projects all supplied result
envelopes in caller order without Ladon's proposed semantic verdict. Repeated
attempts remain repeated. Successful and failed raw checker receipts are
embedded only after the content-addressed evidence loader verifies them.

The evidence records attempts that fail before preparation as visible but
unbound when no plan artifact is available. Unsupported probes retain their
native planning residual. This does not create a persistent run ledger: callers
must pass the first result and every subsequent result they want reviewed.

## Reproducible samples

- `samples/uniformity-reviewer-input.json` comes from four saved runs in order:
  a completed result, a failed-term result, a missing-terms result, and an
  expired-deadline result. The expired result has no native artifact and is
  therefore visibly unbound. Two raw checker receipts are embedded.
- `samples/unsupported-reviewer-input.json` comes from an actual saved
  unsupported witness-dependence result and its matching native artifact. Its
  `template-unsupported` execution observation and native residual remain
  visible.
- The sample packets contain no `checked-local-implication` or
  `checked-local-nonimplication` labels. A separate regression injects these
  strings into nested attempt statuses/diagnostics and verifies they are
  removed.

The input runs are previously captured local qualification evidence; the
unsupported/stopped behaviors are also exercised by current tests. Export itself
performs no fresh proof check.

## Verification

- Frozen reviewer acceptance and malformed-envelope regressions: 5 passed;
  their hashes are verified by the frozen-test registry.
- Reviewer/CLI acceptance suite: 14 passed, including duplicate ordering,
  partial goal coverage, stage attribution, unbound cross-plan evidence, actual
  unsupported/expired results, verdict redaction, and receipt consistency.
- Integrated application-probe planner, checker, CLI, inspect, reviewer export,
  and reuse regressions: 31 passed.
- Ruff, radon/vulture, and compile checks on touched Python modules/tests passed.
- `openspec validate ladon-proof-contract-probes --strict` and
  `openspec validate ladon-proof-contract-analysis-umbrella --strict` passed.
- Frozen-test registry verification passed without hash mismatches.
- The repository-wide strict-quality run was interrupted during its full test
  phase at 8%; it is not recorded as a full-project test pass. Focused acceptance
  and integration suites above completed successfully.

See `VALIDATION.json` for exact commands and exit states. The independent
integrated audit was accepted with no remaining material findings in scope;
see `AUDIT.json`.

## Implementation and limits

The reviewer projection lives in `src/ladon/proof_contract_probe_review.py`;
CLI parsing/dispatch is in `src/ladon/proof_contract_probe_cli.py` and
`src/ladon/proof_contract_cli.py`. User-facing details are in
`docs/CLI.md` and `docs/PROOF_CONTRACTS.md`.

The output preserves source quotations, source-map anchors, contract and
correspondence context, exact goals, attempt-level execution receipts, compact
goal result references, and raw checker evidence where available. It never
turns application rejection, timeout, search failure, or unsupported scope into
semantic non-implication. Receipt content addressing trusts the local Ladon
store and is not writer authentication. The packet does not establish current
formal-source freshness or natural-language source fidelity, and no whole-method
or paper-error claim follows. A `checks-completed` observation additionally
requires exact goal coverage, completed execution receipts, and loaded raw
receipts with supported status, accepted replay/trust, and a matching proof-term
digest; inconsistent evidence is marked unverified.
