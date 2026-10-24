# Matched runtime baseline before search changes

The current checkout was frozen after the bounded domain, producer and propagation
functional gates, with beam search disabled. [RUNTIME.json](RUNTIME.json) binds
447 source/metadata/launcher files; [runtime.tar.gz](runtime.tar.gz) preserves the
bytes. The source snapshot passed 615 contract/native/context tests and 61
search/evaluation/context checks, plus lint and strict quality. This qualification
covers those components; the umbrella and unfamiliar-paper audit remain incomplete.

The unchanged legacy harnesses then ran the same eight portable cases, 64 finite
graphs and real matrix-factorization application pair. Inputs, selected matrix
source/object files, budgets and runtime hashes verified before and after execution.
Original first reports remain unchanged. [SCORES.json](SCORES.json) records both
arms, while [RUNNER.json](RUNNER.json) explains the explicit snapshot overrides.

| Measure | Legacy pre-contract runtime | Current runtime, no beam |
| --- | ---: | ---: |
| Portable positives with independently replayed closed support | 4/4 | 4/4 |
| Portable controls with false closure | 0/4 | 0/4 |
| Unresolved portable cases | 0/8 | 0/8 |
| Terminal assessments: closed / partial / rejected | 4 / 13 / 7 | 4 / 13 / 7 |
| Independent closure replays accepted | 4/4 | 4/4 |
| Summed portable case process time | 37.22 s | 36.47 s |
| Preparation process time, separately | 1.75 s | 1.79 s |
| Matrix A: supplied boundary premise | accepted, no residual | accepted, no residual |
| Matrix B: omitted boundary premise | applicable with residual | applicable with same residual |
| Matrix A / B process time | 29.24 / 19.85 s | 26.24 / 17.91 s |
| Matrix peak sampled process-group RSS | 8.20 GiB | 8.20 GiB |
| Time, memory or output stops | 0 | 0 |

All 192 finite graph results are identical across runtimes, including selected
route transitions. At expansion caps 8/32/128, support was found on 57/64, 64/64
and 64/64 cases with 500/1839/3654 total expanded states. Every graph label is
positive, so graph false-positive rate has no denominator. Candidate assessment
statuses also agree exactly across the portable arms.

Raw current outputs are retained in [portable results](../portable-no-beam-20261018/results/MEASUREMENTS.json)
and [matrix results](../matrix-no-beam-20261018/MEASUREMENTS.json), with commands,
first reports, replay sources and stdout/stderr. The matrix task is the existing
OpenSpec r49 known-candidate pair in `../lean/matrix-factorization`; it measures
application checking rather than retrieval. Both arms retain the precise residual
`0 ≤ Mf.DP.fixedEpochCenterGap point h boundary` in context B. This establishes
neither impossibility of the target nor an exposition defect.

The 60-second, 12 GiB and 8 MiB process limits and serial Lean execution were
unchanged. Each arm has a separate same-depth input/output directory. The legacy
arm ran earlier; there is only one observation per case and no randomized order.
Timing differences therefore do not establish a causal speedup. Neither harness
invokes the new contract analysis, and no beam policy has been implemented or
measured. These known development cases do not complete the original A/B/C tracks;
held-out C still has zero admitted cases. Detection benefit remains unestablished.

Future search-policy comparisons must freeze another exact runtime after any
further implementation, retain identical inputs and budgets, and add harder
multistep/interpretation cases before claiming useful improvement. Preserve this
runtime as the no-beam reference for the present implementation state.

[Independent evidence review](INDEPENDENT-REVIEW.json) verified both runtime trees,
the current archive, preserved legacy first results, all 72 captured-output digests,
matched inputs/bounds, graph transitions and score claims. The root also replayed
the [verification script](verify_evidence.py). This adds artifact review rather
than a new Lean run or a fault-discovery trial.
