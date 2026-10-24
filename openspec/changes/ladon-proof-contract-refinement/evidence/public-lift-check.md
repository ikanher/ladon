# Public source-owned lift checking

The production API `check_nat_rational_lift(request, plan_id, term)` now owns
fresh natural-number/rational lift checks. It regenerates the plan and reads the
exact source, then supervises Lean goal capture, completion, independent replay
and the existing standard axiom policy. It derives the outcome from the requested
mode after checking the full evidence, rather than accepting a caller's status
or proof receipt. The original abstract witness remains visible on failure.

A positive realization refutes the selected complete formal claim. A positive
incompatibility establishes that the exact rational witness has no natural-number
preimage. Neither establishes the intended manuscript's falsity:
`originalClaimRefuted` remains false and `sourceFormulaFidelity` remains
`unverified`. Analytical profiles and unavailable canonical observations remain
unsupported. The generic imported-JSON lift classifier is unchanged.

## Semantic and execution boundaries

Fully qualifying `Rat` does not fix the interpretation of its numerals or
operators. A constructed source can install `OfNat Rat 1` with value minus one,
letting Lean accept a purported incompatibility proof for the abstract witness
`q = 1`. The local direct probe reproduced that discrepancy before implementation.
The production checker independently elaborates the generated proposition in a
clean core context and compares its structural expression with the actual typed
subject, captured goal and completed original goal. Opaque claim/predicate names
are used only in the clean type observation, never in checking the supplied proof.

The canonical imports must be covered by the actual capture's import closure.
After the clean observation, the worker reverifies that closure, including
compiled sidecars, plus the original source, pinned context and checker identity.
The parent verifies the attempt/plan/witness/interpretation/source/term bindings,
rechecks native evidence and rereads source/context/checker before projection.
No public runner, cache or externally supplied receipt parameter is available.
The output explicitly identifies itself as local Ladon evidence, not an
authenticated external certificate.

Each attempt uses the caller's absolute deadline, at most 120 seconds,
12 GiB process-tree RSS and 8 MiB output. Supervisor-owned scratch leases cover
both material observations and are cleaned or quarantined on interruption;
a cleanup failure cannot produce a positive result. Stops preserve the witness,
plan identity and open obligation. Memory limits retain the existing stop-and-report
guidance and do not trigger automatic retries.

## Preserved qualification history

All public native attempts share the first run's 1,800-second absolute deadline
`2295486.439205765`. The raw records are under
`.codex/state/refinement-lift-check/native-gate-01/` through `native-gate-04/`.

- Gate 01 passed 5/7. The two valid proofs were rejected because the new
  validator compared the replay observation's declaration-body digest with the
  digest of the complete generated replay source. The existing completion
  schema distinguishes these fields. The fixture was corrected to represent
  both digests distinctly, preserving all assertions and mutation cases.
- Gate 02 passed 7/7 after that correction and extraction of the evidence helper
  to satisfy the repository's maintainability threshold.
- Independent audit #1283 found that two absent digest fields could compare
  equal; the same issue was reproduced for environment/executable identities.
  Four failing tests preceded the fix. Gate 03 passed 7/7 afterward.
- Audit #1286 found absent replay axiom observations could masquerade as an
  explicit empty set. A broader presence suite added six failing cases and two
  controls, covering axiom lists, local contexts and typed expressions. Review
  #1289 accepted the complete presence correction, pending the final native gate.

Independent review **#1292 accepted Task 1.3** after checking every manifest
artifact hash/size, the current checker identity, final positive bindings,
unchanged sources and scratch cleanup. The final gate passed **7/7** in
**166.732 seconds**:

| Case | Public result |
| --- | --- |
| Realization, `q = 1` | `lifted-counterexample` |
| No Nat preimage, `q = -1` | `spurious-countermodel` |
| Analytical interpretation | `unsupported`, no Lean process |
| Changed witness, `q = 1/2`, old proof | Rejected by trust policy |
| Omitted original assumption | Proof rejected |
| Admitted proof | Rejected by trust policy |
| Source overrides Rat numeral `1` | Rejected: `semantic-goal-mismatch` |

All four runs used the same deadline. Combined native execution was **659.079
seconds**; wall time from the first start to final completion, including fixes
and review, was **869.226 seconds (14.49 minutes)**. Peak process-tree RSS was
**3,834,101,760 bytes (3.571 GiB)**, within the 12 GiB cap. No resource stop
occurred, and no generated goal leases remained.

The [versioned manifest](public-lift-check-results.json) retains the earlier
failures and intermediate successes alongside the final implementation evidence.

## Verification

- 94 new public-boundary, mutation, resource, binding and qualification-policy tests.
- 302 focused tests passed, one existing slow integration skipped. The selection
  covers rational refinement/witnesses, branch identities and checked reporting,
  prior lift planning, the new API and supervisor scratch ownership.
- Scoped Ruff, `ladon.quality.strict_quality_issues`, and compilation passed;
  OpenSpec strict validation passed. This is not repository-wide qualification.
- All seven new active test files match their frozen hashes. The previously
  recorded unrelated mismatch in `tests/test_rational_lean_encoder_v2.py`
  remains; global frozen-test verification is not claimed clean.

The native qualification command uses the checkout, not an installed Ladon:

```bash
PYTHONPATH=src python scripts/check_public_nat_rational_lift.py \
  --output .codex/state/a-new-public-lift-check
```

The output directory must be new. The historical reruns passed the original
`--deadline-monotonic` explicitly; that historical clock value is not reusable
on another host or after expiration. No network access, dependency addition,
Mathlib build, commit or push was performed.

## Remaining work

Task 3.1 still needs the public refine/inspect CLI and report aggregation that
preserves original and revised evidence through a justified refinement and a
separate proposed repair. Generic analytic lifting, manuscript fidelity,
unfamiliar-source detection benefit and the Navier–Stokes audit remain
unestablished. The constructed qualification is not a paper-detection benchmark.
