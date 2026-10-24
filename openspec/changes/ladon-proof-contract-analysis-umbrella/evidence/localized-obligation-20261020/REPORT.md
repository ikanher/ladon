# Localized obligation integration acceptance

Umbrella task 2.2 passes for the constructed, supported natural-number profile.
The accepted [bidirectional child](../../../ladon-proof-contract-bidirectional/evidence/ROUTE-CONTEXT-20261018/REPORT.md)
and [archived probe child](../../../archive/2026-10-19-ladon-proof-contract-probes/evidence/TASK-3-ACCEPTANCE-20261019/REPORT.md)
are complemented by a fresh current-checkout source campaign. This does not
close the independently sourced statement-pair gate, task 2.1.

## Checked result

- All 13 positive obligations passed completion, independent replay and trust,
  including the exact closed requirement composed from the checked original
  reading and its transfer. The context excludes the selected provider theorem
  and the parent endpoint theorem. Citing the excluded endpoint did not gain
  support; neither did citing an absent assumption or assuming the closed goal.
- The middle source bound has offset 2 while its selected requirement asks for
  offset 0. Its original reading checked, but the transfer remained unresolved
  and the dependent closed requirement was not attempted. Alternative route
  comparisons remained intact. Failed search establishes no non-implication.
- Changed identities, rules, order and checkpoints were rejected. Both expired
  clock controls stopped before preparation. The deliberate final 1 MiB memory
  control retained the stop/report diagnostic and had no retry.

[Verification](VERIFICATION.json) recomputes the exact plan and goal digests,
checks the frozen runtime archive and reloads all **18** raw goal receipts with
their content hashes and exact projections. Portable copies are listed in
[RAW-EVIDENCE.json](RAW-EVIDENCE.json). Source fixture bytes remain unchanged.
The readings and graph are constructed development inputs, not independently
interpreted manuscript evidence.

## Attempts, bounds and recovery

The campaign completed in **981.41 / 1,200 seconds** on the original absolute
clock, including failed attempts and recovery time. Ordinary workers retained
30-second, 12 GiB RSS and 8 MiB output limits. Maximum recorded process-tree RSS
was **3.55 GiB**; see [resource metrics](RESOURCE-METRICS.json).

The original unchanged driver exited 1 after its excluded-parent control hit a
worker timeout. Its outputs and [log](driver.log) remain in `run/`; it produced
no acceptance record. Independent audit **#893 rejected that incomplete run**.

The explicit follow-up first refused a stale environment before checking any
goal. The timed-out worker had left a generated
`.ladon/correspondence/goal-e6nayf80/LadonCorrespondence.lean` file in the selected
source tree. Git-backed source enumeration included it. Root preserved the
entire generated directory in `timeout-residue/`, moved it outside the source
root, and recomputed the actual environment digest: it again exactly matched
the original snapshot. [TIMEOUT-RESIDUE.json](TIMEOUT-RESIDUE.json) records the
bytes, hashes and context identities. No original Lean source or premise was
changed, and no stale check was bypassed. The refusal remains in `follow-up/`.

The remaining controls used a fully qualified excluded-parent term under the
same original clock and caps. The [inherited clock](follow-up-restored/INHERITED-CLOCK.json),
[log](follow-up-restored.log) and [final acceptance](follow-up-restored/acceptance.json)
retain the bounded recovery; neither failure is relabeled as a successful
historical run. Revised independent audit **#896 accepts this resumed packet**
and preserves #893. The auditor checked recorded context equality and the
resumed checker bindings, but did not independently reconstruct the complete
toolchain context digest. These are local integrity checks, not authenticated
signatures or a new source-fidelity judgment.

The timeout residue is a remaining product issue for the umbrella's existing
partial-stage-resume gate, task 2.4. This qualification recovered the owned
scratch state explicitly; it did not implement a production cleanup fix.

## Archive consumer repair and regressions

The first focused run retained **59 passes and 9 failures** in
[regressions.xml](regressions.xml): reviewer tests still used the probe child's
old active directory. Root changed only fixture directory literals in two live
test files. [PATH-REPAIR.json](PATH-REPAIR.json) proves that all **45 assertion
ASTs and 14 test cases** are unchanged; original file bytes remain in
`path-repair-before/`. The corrected route, review-export and native-consumer
suite passed **73/73** in **10.94 seconds**, recorded in
[the second JUnit report](regressions-after-path-repair.xml). Ruff passed on the
two tests and the new evidence helpers.

Four frozen-test records were explicitly superseded to identical archived file
hashes. The live native test's old revision and reason were preserved before
refreezing its path-only replacement. [Frozen verification](frozen-after-archive-repair.json)
passes. The archived probe packet still verifies all 1,000 original files,
14 manifests and 972 bindings unchanged.

[RUNTIME.json](RUNTIME.json) and `runtime.tar.gz` freeze 1,188 producer/runtime
files before execution. [RUNTIME-DELTA.json](RUNTIME-DELTA.json) discloses only
the two test path edits; neither test module is imported by the source driver.
No production source changed. Full repository regression and global strict
quality were not rerun; the previously recorded domain-contract complexity
issue remains outside this change.

## Reverification and limits

From the repository root, verify the frozen packet without modifying it:

```sh
uv run --locked python openspec/changes/ladon-proof-contract-analysis-umbrella/evidence/localized-obligation-20261020/verify_packet.py
```

`PYTHONPATH=src:tests .venv/bin/python .../verify_run.py` additionally rebuilds
the derived `RAW-EVIDENCE.json` and `VERIFICATION.json` deterministically; it is
not read-only and does not replay Lean. Those outputs and the verifier itself
are included in the packet manifest. Root and auditor invocations occurred
before the final manifest freeze.

Source fidelity remains attributed/unreviewed, mathematical falsity remains
not established, whole-method authority remains none and detection benefit
remains unmeasured. No unfamiliar-source or Navier–Stokes fault-detection claim
follows. No code was pushed.
