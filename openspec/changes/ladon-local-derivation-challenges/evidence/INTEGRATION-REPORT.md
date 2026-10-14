# Local derivation challenges: integration result

The bounded packet is complete. Ladon can now prioritize disputed derivations,
record exact source-bound steps, export challenge inputs without prior judgments,
and replay proposed rational counterexamples against the stored assumptions and
conclusion. This does not establish detection of the Navier–Stokes exposition
error. No full-paper experiment was restarted.

## Delivered behavior

- `src/ladon/investigation.py` and `investigation_derivation.py`: opt-in v2
  derivations, earlier-step dependencies, discrepancy-first work queues, complete
  context binding, and separate author/challenger assessments. Existing v1 remains
  the default. Unresolved or conflicting assessments retain work.
- `src/ladon/investigation_cli.py`: public `init --derivations`, `challenge`, and
  `witness` commands. Export whitelists source and obligation fields. Witness
  evaluation uses the stored goal rather than a replacement supplied by a caller.
- `src/ladon/rational_witness.py`: bounded exact rational expression checking,
  including every premise. Distinct results are `counterexample`,
  `outside-assumptions`, and `not-counterexample`; invalid input is rejected.
- `docs/DERIVATION_CHALLENGES.md`, related procedure guides, and the packaged
  Ladon skill describe use and limits. `scripts/demo_derivation_challenges.py`
  generates challenge inputs from the public six-case fixtures.

## Verification

Root observed the expected missing behavior before implementation; the red logs
are `red-cli.txt` and `red-contract.txt`. The frozen contract and test artifacts
still verify; see `frozen-artifact-verification.txt`.

After the final production edit, the following parent/consumer suite passed:
**174 tests in 15.03 seconds**.

```sh
uv run pytest tests/test_derivation_contract.py tests/test_derivation_workflow.py tests/test_investigation_derivation_cli.py tests/test_investigation.py tests/test_investigation_binding.py tests/test_investigation_cli.py tests/test_entrypoint.py tests/test_result_assessments.py tests/test_result_manifest.py tests/test_proofir_packet_manifest.py tests/test_clean_cli.py tests/test_installed_cli_contract.py tests/test_cli_execution.py tests/test_version_cli.py -q
```

Ruff check and format check passed for all four investigation/witness modules,
the three new test modules, and the demo script (eight files). `git diff --check`
and strict OpenSpec validation passed. A distinct final auditor found no
actionable defect in the assigned integrated source and evidence review; that
auditor did not run tests. The complete assignment/result is preserved in
`independent-audit.txt`. Root owns the executable verification.

No dependencies were added. This packet required no Lean build. Nothing was
committed, archived, published, or deployed.

## Six-case exercise

A separate case author supplied three elementary valid implications and three
invalid implications. A fresh challenger received the public challenge inputs
without the answer key, prior assessments, or conversation history. This used a
shared filesystem, not an enforced access sandbox.

The original first response is preserved unchanged in
`exercise/first-response.json`. Its classifications matched the separate key:
three supported controls and three refutations. Root replayed all six assignments
through the public CLI: three genuine counterexamples, and three samples that
did not refute the controls. Conventional reasoning for the controls was
inspected separately; successful samples are not universal proofs.

One response first proposed an unsuccessful example, then corrected itself. That
text remains intact. Root later replayed the discarded example and obtained
`not-counterexample`; a separate premise-violating candidate returned
`outside-assumptions`. The checker did not cause the challenger's earlier
self-correction. Exact commands, receipts, the key, and limitations are in
`exercise/`; `exercise/replay-summary.json` records all eight replays.

## Evidence boundaries and remaining work

The six cases demonstrate the checking path on elementary rational implications.
They provide no estimate of general detection performance, no comparison against
ordinary auditing tools, and no evidence that a difficult analytic derivation
can now be resolved. Translating prose into the stored scalar goal remains an
authored interpretation. Reviewer labels do not authenticate independent identity.
An attributed mathematical assessment remains distinct from a checked witness.

`integration-identities.json` binds the integrated source, tests, fixture inputs,
and documentation. It also records unchanged hashes for both historical findings,
the second experiment's plan and queue summary, the unrelated pre-existing dirty
`FIRST-HAND-REPORT.md`, and unchanged CLI/entrypoint baseline inputs. Historical
experiments were preserved. Quux's active packet was left unchanged.

Before another full-paper restart, the remaining research question is whether
this workflow can resolve independently chosen, substantially harder derivations
with correct controls. The present packet does not answer that question.
