# Existing-search engineering baseline

Measured the exact pre-contract local runtime on 2026-10-18, before any beam
implementation. All 422 runtime files matched the original [baseline
manifest](../BASELINE.json). [FREEZE.json](FREEZE.json) bound the harness, case
inputs, labels and budgets before execution. Final identity verification passed.
This is a legacy engineering baseline; it is not the contract-enhanced, no-beam
arm needed to isolate a future beam change.

The [raw measurements](results/MEASUREMENTS.json), per-case `FIRST.json` files,
command vectors and stdout/stderr captures are preserved. [SCORES.json](SCORES.json)
contains the case denominators and resource totals.

| Actual Lean candidate checking | Result |
| --- | --- |
| Positive cases with independently replayed closed support | 4/4 |
| Nearby controls with a false closure claim | 0/4 |
| Unresolved cases | 0/8 |
| Terminal candidate assessments | 24: 4 closed, 13 partial, 7 rejected |
| Independent closure replays | 4/4 accepted |
| Additional advisory scratch replays | 4/4 compiled |
| Summed measured case command time | 37.22 seconds |
| Summed measured compilation/index preparation time | 1.75 seconds |
| Median positive time to independently verified candidate | 5.12 seconds |
| Peak sampled process-group RSS | 3.52 GiB |
| Time, memory or output stops | 0 |

The positive cases reuse four portable logic/arithmetic cases. Four nearby
controls remove required assumptions or change the target. A control label means
no closed support from the selected candidate population; it does not diagnose
an exposition error. Each case used the public CLI, a 60-second command/remaining
replay budget, at most eight shortlisted candidates and a 12 GiB RSS cap. Lean
processes ran serially. Preparation is reported separately; the summed command
times are not a measurement of the entire controller's wall time.

The unchanged route planner was also measured on 64 seeded eight-node finite
AND/OR graphs with three alternatives per node. The independent truth recurrence
labels all 64 as supported. These graph labels are synthetic and are not Lean
proof certificates.

| Maximum expanded states per case | Supported cases found | Not found within bound | Total expanded states |
| --- | --- | --- | --- |
| 8 | 57/64 | 7/64 | 500 |
| 32 | 64/64 | 0/64 | 1839 |
| 128 | 64/64 | 0/64 | 3654 |

There are no negative graph cases, so graph false-positive rate is undefined.
Finding a route is separate from exhausting all alternatives. No greedy/beam
comparison has been run, and this baseline establishes no beam benefit.

Before a beam comparison, freeze the functionally qualified contract-enhanced
runtime with beam disabled, retain identical inputs and budgets across policies,
and include harder multistep cases and interpretation alternatives. Independent
unfamiliar-source fault detection still has no admitted corpus: original track C
remains blocked with zero cases. These development results do not satisfy A, B,
C or the umbrella's detection-benefit gate.

Reproduction uses the frozen local checkout, never pip Ladon:

```sh
PYTHONPATH=.codex/state/proof-contract-analysis/baseline/src .venv/bin/python \
  openspec/changes/ladon-proof-contract-evaluation/evidence/search-baseline-20261018/measure.py measure
```

The command deliberately refuses to overwrite the original `results` directory.
Replay in a new copy of the evidence directory, retaining the frozen input bytes
and the same repository-relative depth. A new run must not replace first reports.
