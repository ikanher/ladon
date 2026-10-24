# Targeted original-provider expansion

Ladon now emits exact requests for missing provider evidence and can dispatch one
through `investigation contract expand-provider`. The public CLI observes a real
application in the original provider proof. Generated bridge goals and original
source observations retain separate provenance. Observation does not discharge
the demand or certify the paper.

The ordinary `check-obligations` run emitted four targeted requests. Selecting
`ThreeSteps.firstBound`, application `Eq.trans`, occurrence zero, produced a
complete scoped source slice with status `observed`. The source, native contract,
source-map anchor, selected route, demand and reading identity were rebound and
checked before extraction. Requests without a unique usable source anchor carry
an unavailable diagnostic and no invented source selection. Extraction remains
explicit; missing-provider planning does not automatically dispatch it.

| Constructed control | Result |
|---|---|
| Actual original provider application | observed; complete application slice |
| Application absent from that provider | incomplete; incomplete slice |
| Source bytes changed after planning | rejected before fresh observation |
| Forged desired reading identity | rejected before provider worker |
| Expired shared deadline | incomplete before native validation |
| Deliberate 1 MiB memory limit | incomplete; stop/report instruction; no retry |

The [final serial source run](final-source-run/acceptance.json), including five
fresh statement snapshots, both public CLI operations and the controls above,
took **21.30 seconds within 180 seconds**. The preserved first run took 21.61
seconds before the final request-admission fix. These are separate acceptance
runs, not a speed comparison. The 1 MiB control was last in each run and was not
retried with a larger cap.

## Authority and resource boundaries

The dispatcher reconstructs the entire request from validated native owners and
rejects caller drift. It checks fresh statement/source-map ownership and source
bytes, then extracts the selected original application under a process-tree
supervisor. The result is `observation-only`, retains the exact unresolved demand,
sets `demandDischarged: false`, and leaves provider/proof-body coverage incomplete.
Whole-method authority remains none, mathematical falsity is not established,
and prose fidelity remains attributed and unreviewed.

Every stage preserves stricter caller limits, with hard ceilings of 30 seconds,
12 GiB RSS and 8 MiB output. Original, saved and inherited deadlines bound later
work; native UTC deadlines also stop expired requests before validation. Legacy
inner helper timeouts remain subordinate to the enclosing supervisor. A resource
stop prevents later work; memory stops retain the requested stop/report guidance.
Aggregate input validation precedes recursive owner processing, and malformed
application/occurrence selections fail before launching any worker.

Request admission reserves summary bytes before appending each request. Native
coverage remains visible when a later request exceeds the evidence budget.
The final source-check directory occupies **145,826 bytes**, exactly matching its
reported accounting, below 8 MiB. Each of the six API/CLI result files is also
below 8 MiB. Their combined sizes are not one invocation's output budget.
Normal controls have no memory/output/timeout flags. The intentional 1 MiB stop
alone has the expected memory flag. See [root verification](source-verification.json)
and the [independent custody review](reviews/FINAL-RUNTIME-CUSTODY-REVIEW.json).

## Verification and custody

The full relevant regression gate passed **928 tests across 144 files** in
**393.83 seconds**, with no failures, errors or skips. See
[command](integration-command.json), [log](integration.log),
[exit status](integration-status.json), [JUnit](integration.xml) and
[verification](verification.json). Strict repository quality, no-cache Ruff,
frozen-test verification and both selected OpenSpec validations pass; logs are
retained beside this report. The 40 new checks are included in the 928 total.

Eight new test files contain **40 checks**, covering identity rebinding, stale
requests, bounded supervision, missing source anchors, CLI behavior, early input
rejection, all deadline channels, bounded output and request admission. Initial
failing cases and the reviewed helper-only refactor are preserved in [TDD](TDD).
The eight binding regressions strengthen coverage after implementation and are
not presented as failing-first tests. One new frozen test file received an
independently approved helper-only refactor preserving its 33 assertion AST nodes
and test cases; older frozen tests were not changed.

The independent red, green and audit roles and root integration are recorded in
[board posts](board-posts.json), with [participant provenance](board-participants.json).
Initial audit findings on aggregate input bounds and early malformed selection
were fixed and tested. Later reviews cover deadline propagation, output fallback,
request reservation and the final raw source evidence. The independent custody
review predates completion of the full regression gate; the root records that
separate final result here.

[The final runtime manifest](FINAL-RUNTIME.json) and
[archive](final-runtime.tar.gz) preserve **488 entries**; all live hashes and archive
entries match. The first-run manifest/archive are retained separately and differ
only in the final request-admission change. [Tests and fixture manifest](TESTS.json)
and [archive](provider-tests.tar.gz) preserve the new test inputs. The original
fixture source was restored after the stale-source control and matches its
captured digest. No dependencies were added.

Exploratory `Nat.le_refl` selection found no such application; an inspected actual
`Eq.trans` application established feasibility. An initial API harness mixed
snapshots from different environments and failed before Lean; fresh matching
snapshots were used for acceptance. Neither exploratory outcome is mathematical
fault evidence. Source acceptance and the full regression gate run serially,
with the root as the only Lean owner.

## Remaining scope

Bidirectional task 2.3 is complete; task 1.2 remains open for broader ordered
premise/domain/representation contexts. The preceding bridge checker continues
to support its bounded universal-Nat identity-transport profile; its separate
CLI dispatch remains open. The parent umbrella remains 2/12 complete. This run
adds no beam policy, corpus admission, matrix baseline or Navier–Stokes retest.
Held-out C still has zero admitted cases. Detection benefit remains unmeasured.
Earlier baselines, evidence and handoffs are preserved. Nothing was pushed.

To reproduce with the current checkout, create an empty output directory and
choose a repository destination that does not exist:

```bash
mkdir /tmp/ladon-provider-evidence-fresh
PYTHONPATH=src:tests .venv/bin/python \
  openspec/changes/ladon-proof-contract-bidirectional/evidence/PROVIDER-EXPANSION-20261018/run_acceptance.py \
  /tmp/ladon-provider-evidence-fresh /tmp/ladon-provider-repo-fresh
```

The retained driver was executed for both serial acceptance runs. Saved monotonic
deadlines describe those runs; replay uses fresh inputs and fresh deadlines.
