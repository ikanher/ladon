# Matrix-factorization targets and application baseline

OpenSpec already contains real mathematical targets and prior baseline trials.
They are suitable development/calibration material for the contract work and
future search comparisons. Earlier statements that no real targets were
available were too broad. The missing prerequisite is an independently held-out
fault-discovery corpus, not mathematical examples with actual Lean counterparts.

## Recovered targets

| Existing record | Reusable work |
| --- | --- |
| [Fixed-epoch exposition v1](../../../ladon-result-understanding-and-release-umbrella/baselines/fixed-epoch-v1/README.md) | 18 boxed statements, 20 selected Lean declarations and an explicit partial correspondence inventory |
| [Read/find/check r49](../../../ladon-result-understanding-and-release-umbrella/baselines/read-find-check-r49/REPORT.md) | The same center-gap goal with and without a boundary premise; prior actual reader/application trials |
| [Offset bridge r63](../../../ladon-result-understanding-and-release-umbrella/baselines/offset-bridge-r63/REPORT.md) | A nontrivial exact asymptotic adapter, two saved Lean proofs and separate compiler replays |
| [Proof companion r69](../../../ladon-result-understanding-and-release-umbrella/baselines/proof-companion-r69/REPORT.md) | Source exposition, a reader question and a separately retained explanatory revision |

[TARGETS.json](TARGETS.json) records the 20 exact declarations and current source
hashes. All 20 match the historical inventory, across nine source owners. The
frozen exposition and coverage addendum also match the live files. The r05
source archive is available and its SHA-256 matches the recorded digest.
This checks selected source bytes, not freshness of the entire compiled import
closure. The surrounding checkout is dirty. Selected source and compiled inputs remained
unchanged; no Lake build was run. Ignored caches were not inventoried.

The prior r63 trial reports ordinary/augmented reader times of 256.43/222.27
seconds, with both proving the unchanged statement. The augmented reader used
only Ladon help, so the timing difference does not establish software benefit.
These historical trials used a 32 GiB cap; they are not current 12 GiB runs.

## New bounded real-source check

The existing r49 task was frozen unchanged before execution, with the known
supporting declaration supplied to both contexts. This tests application
checking and preservation of a missing premise; it does not measure retrieval,
interpretation accuracy or autonomous fault discovery.

The runtime is the exact 422-file pre-contract local snapshot. Every runtime
hash and all selected input hashes matched before and after execution. The
public `proof-search discover` command used one supplied candidate, explicit
Lean 4.33.0 executables, advisory scratch replay, 60 seconds per outer command,
8 MiB captured output and a 12 GiB process-group RSS cap. The two commands ran
serially. No index build, target rebuild, retry or memory-limit increase occurred.

| Context | Observed outcome | Command time | Peak sampled process-group RSS |
| --- | --- | ---: | ---: |
| A: boundary premise supplied | Accepted; zero residual premises; advisory scratch compilation succeeded | 29.24 s | 8.16 GiB |
| B: boundary premise omitted | Applicable with a residual premise; no closed proof claim | 19.85 s | 8.20 GiB |

Both cases remain in the denominator: 2/2 returned the expected application
classification; zero time, output or memory stops. The missing premise in B is
`0 ≤ Mf.DP.fixedEpochCenterGap point h boundary`. This result concerns the
selected lemma's application; it does not refute the desired conclusion or rule
out another proof. Scratch compilation in A is recorded as advisory replay;
this run did not add a separate root proof replay or an independent reviewer.

[FREEZE.json](FREEZE.json) contains pre-execution identities and expectations.
[MEASUREMENTS.json](MEASUREMENTS.json) and per-case `results/*/FIRST.json`
preserve command vectors, process measurements and complete projected outputs.
The runner is [measure.py](measure.py); it imports only the frozen local Ladon
runtime and refuses to overwrite first reports.

## Use in the active evaluation

Reuse these real-source cases as development baselines alongside the portable
search fixtures. Preserve the older reports and keep the same original goals,
contexts and resource caps when measuring a later implementation. Freeze the
functionally qualified contract-enhanced/no-beam runtime before any beam policy
change; that matched arm is required to isolate a search-policy effect.

One manuscript with 20 selected declarations is one source family. These known
targets do not satisfy the original held-out track C. The original A/B/C counts,
promotion policy and blocked zero-admitted C status remain unchanged. No beam
policy or comparative benefit has been established by this replay.
